"""Reference implementation of the norregel v2 analysis (docs/PREREG_V2.md, section 7). Normative for every computational detail.

No model is called; the input is model answers. Scorer v2 (src/norregel/score_v2.py, locked) gives the class; this module
adds the preregistered sub-classes, the two denominators, the stratified cluster bootstrap for H1, the pooled and per-model
tests of H1–H3 with Holm, the chance-match estimate, the sensitivity analyses and the variation between runs.

Usage (the model list is the one scripts/svar_v2.py writes: the models complete on both tasks in run 1):
  python scripts/analysis_v2.py --models <dir>/v2_modeller_komplette.json --answers <dir>/answers_v2.jsonl --pairs data/items_h3_v2.jsonl --out report_v2.json
answers_v2.jsonl: one line per answer {"model", "id", "run", "completion", "error"}. id is an item id (main task) or a pair id
"norregel-NNNNN-nb"/"-nn" (H3 task). run is 1..R; run 1 is primary.
data/items_h3_v2.jsonl: the H3 questions, one per item and written standard, with the fields of data/items.jsonl and "h3_par".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from norregel import score_v2 as S2  # noqa: E402
from norregel.score import score as score_v1  # noqa: E402
from norm_aar_maaneder import normalise  # noqa: E402  (the v1 «X år og Y måneder» rule, applied before scoring as in v1)

B = 10_000
SEED = 20261117
ALPHA = 0.05
MIN_POOLED_AFTER, MIN_POOLED_AFTER_SERIES = 30, 20  # H1 pooled: interpretable rows after the cutoff
MIN_MODEL, MIN_MODEL_SERIES = 30, 5  # per-model minimums (as v1)
MEI_H1, MEI_H3 = 0.10, 0.01  # smallest effects of interest: d for H1, |D| for H3 (section 7.6)
CLASSES = ("korrekt", "utdatert", "feil", "utolket")


def load(name: str) -> list[dict]:
    return [json.loads(l) for l in (ROOT / "data" / name).open(encoding="utf-8")]


# ------------------------------------------------------------------------------------------- classes

def count_numbers(line: str, kind: str) -> int:
    """Numbers on an answer line, read exactly as score_v2.read() reads them (digits; number words only without digits)."""
    text = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", line)
    text = re.sub(r"[*_`]", " ", text).lower()
    text = re.sub(r"(?<=\d),[-–]", " ", text)
    text = re.sub(r"(?<=\d)\.[-–]", " ", text)
    text = re.sub(r"(?<=\d)-år\w*", " år", text)
    nums = S2.NUM.findall(text)
    words = [w for w in re.findall(r"[^\W\d_]+", text) if S2.number_word(w) is not None]
    return len(nums) if nums else len(words)


def rejected_values(series_ids: set[str]) -> dict[str, set[float]]:
    """Values of the versions of a provision that the cleanliness rule did not accept (data/v3_items.jsonl), per series.
    Every series must be found, and `accepted` must have one flag per version; otherwise the analysis stops."""
    out: dict[str, set[float]] = defaultdict(set)
    found = set()
    for l in (ROOT / "data" / "v3_items.jsonl").open(encoding="utf-8"):
        d = json.loads(l)
        if d["id"] not in series_ids:
            continue
        found.add(d["id"])
        acc, hist = d.get("accepted") or [], d.get("history") or []
        if len(acc) != len(hist):
            raise SystemExit(f"v3_items.jsonl: {d['id']} has {len(acc)} accepted flags for {len(hist)} versions")
        for k, h in enumerate(hist):
            if acc[k]:
                continue
            for v in h.get("values") or []:
                try:
                    out[d["id"]].add(float(v))
                except (TypeError, ValueError):
                    continue
    missing = series_ids - found
    if missing:
        raise SystemExit(f"v3_items.jsonl: {len(missing)} series not found, e.g. {sorted(missing)[:3]}")
    return out


def classify(answer: dict | None, item: dict, rejected: dict[str, set[float]], scorer: str = "v2") -> dict:
    """Class and sub-class of one answer. A missing answer or an error left after retries is utolket/endelig_feil."""
    if answer is None:  # no row in the answer file: shown as its own status, never as a final error
        return {"klasse": "utolket", "under": "mangler", "lest": None, "alder": None, "normalisert": False}
    if answer.get("error"):
        return {"klasse": "utolket", "under": "endelig_feil", "lest": None, "alder": None, "normalisert": False}
    text, changed = normalise(answer.get("completion") or "", item["type"])
    r = S2.score(text, item) if scorer == "v2" else score_v1(text, item)
    out = {"klasse": r.klasse, "under": None, "lest": getattr(r, "lest", None), "alder": getattr(r, "alder", None),
           "normalisert": bool(changed)}
    if r.klasse == "utolket":
        line = S2.answer_line(text)
        if line is None:
            out["under"] = "ingen_svarlinje"
        else:
            k = count_numbers(line, item["type"])
            out["under"] = "avslag" if k == 0 else ("flere_tall" if k > 1 else "ett_tall_uleselig")
    elif r.klasse == "feil":
        if getattr(r, "senere", None):
            out["under"] = "senere_verdi"
        elif r.lest is not None and r.lest == r.lest and any(abs(r.lest - v) < S2.TOL for v in rejected.get(item["serie_id"], ())):
            out["under"] = "forkastet_versjon"
        else:
            out["under"] = "utenfor_historikken"
    return out


def interpretable(c: dict) -> bool:
    return c["klasse"] != "utolket"


# ----------------------------------------------------------------------------------------- bootstrap

def draws(n: int, b: int, rng: np.random.Generator) -> np.ndarray:
    return rng.integers(0, n, size=(b, n))


def boot(per: dict[str, tuple], strata: list[list[str]], stat, b: int | None = None) -> tuple[np.ndarray, int]:
    """Cluster bootstrap over series. Each stratum is resampled with replacement to its own size, with one fresh
    default_rng(SEED) per call; strata in the given order and series sorted. Undefined resamples are dropped and counted."""
    b = B if b is None else b
    rng = np.random.default_rng(SEED)
    sums = None
    for st in strata:
        st = sorted(st)
        if not st:
            continue
        arr = np.array([per[s] for s in st], dtype=float)
        part = arr[draws(len(st), b, rng)].sum(axis=1)
        sums = part if sums is None else sums + part
    if sums is None:  # no series at all: nothing to resample
        return np.array([], dtype=float), b
    vals = [stat(tuple(r)) for r in sums]
    kept = np.array([v for v in vals if v is not None], dtype=float)
    return kept, b - len(kept)


def interval(kept: np.ndarray) -> dict:
    if len(kept) == 0:
        return {"lo95": None, "hi95": None}
    q = np.quantile(kept, [0.025, 0.975], method="linear")
    return {"lo95": float(q[0]), "hi95": float(q[1])}


def p_greater(kept: np.ndarray, theta0: float) -> float | None:
    """One-sided p for theta > theta0 by inverting the percentile interval: (1 + #{theta* <= theta0}) / (B' + 1)."""
    return None if len(kept) == 0 else float((1 + np.sum(kept <= theta0)) / (len(kept) + 1))


def p_less(kept: np.ndarray, theta0: float) -> float | None:
    return None if len(kept) == 0 else float((1 + np.sum(kept >= theta0)) / (len(kept) + 1))


def holm(pvals: dict[str, float | None]) -> dict[str, bool | None]:
    tested = sorted((p, m) for m, p in pvals.items() if p is not None)
    out, k, stop = {m: None for m in pvals}, len(tested), False
    for rank, (p, m) in enumerate(tested):
        if stop or p > ALPHA / (k - rank):
            stop = True
            out[m] = False
        else:
            out[m] = True
    return out


def state(tested: bool, rejected: bool | None, lo: float | None, hi: float | None, mei: float, direction: str) -> str:
    """The three preregistered states (section 7.6), from the test decision and the observed interval only."""
    if not tested or lo is None:
        return "ikke testet"
    if rejected:
        return "støttet"
    reaches = hi >= mei if direction == "greater" else lo <= -mei
    return "inkonklusiv" if reaches else "ingen effekt av interesse"


def against_half(lo: float | None, hi: float | None) -> str | None:
    """H2 is estimation: where the interval for s lies relative to 0.5 (no test)."""
    if lo is None:
        return None
    return "over 0,5" if lo > 0.5 else ("under 0,5" if hi < 0.5 else "inneholder 0,5")


def mcnemar_less(b: int, c: int) -> float | None:
    """Exact McNemar, one-sided for 'Nynorsk lower': H0 b <= c; p = P(X >= b), X ~ Bin(b + c, 0.5)."""
    n = b + c
    return None if n == 0 else sum(comb(n, k) for k in range(b, n + 1)) / 2 ** n


def immediately_preceding_value(item: dict) -> float | None:
    prev = sorted((h for h in item["verdihistorikk"] if h["gyldig_fra"] < item["gyldig_fra"]), key=lambda h: h["gyldig_fra"])
    for h in reversed(prev):
        if abs(h["verdi"] - item["fasitverdi"]) >= 1e-6:
            return h["verdi"]
    return None


# ----------------------------------------------------------------------------------------- measures

def shares(rows: list[dict], denom: str) -> dict:
    """Class shares with cluster-bootstrap intervals; denom 'alle' (all answers) or 'tolkbare' (interpretable)."""
    rows = rows if denom == "alle" else [r for r in rows if interpretable(r)]
    series = sorted({r["serie_id"] for r in rows})
    out = {"n": len(rows), "serier": len(series)}
    for c in (CLASSES if denom == "alle" else CLASSES[:3]):
        per = {s: (0, 0) for s in series}
        for r in rows:
            k, n = per[r["serie_id"]]
            per[r["serie_id"]] = (k + (r["klasse"] == c), n + 1)
        kept, dropped = boot(per, [series], lambda t: t[0] / t[1] if t[1] else None)
        k = sum(v[0] for v in per.values())
        out[c] = {"andel": (k / len(rows)) if rows else None, **interval(kept), "forkastet": dropped}
        if rows and k == 0:  # the percentile interval is [0, 0]; also give the exact upper bound for 0 of n (ignores clustering)
            out[c]["eksakt_oevre_97_5"] = 1 - 0.025 ** (1 / len(rows))
    return out


def h1_table(rows_by_model: dict[str, list[dict]], cut: dict[str, str], h1set: set[str], series_all: list[str], denom: str,
             items: dict | None = None, only_preceding: bool = False, holm_on: bool = True, before_months: int | None = None) -> dict:
    """d = share outdated after minus before the cutoff, pooled over the given models and per model.
    Stratified bootstrap: series with an item after the cutoff of at least one of the models form one stratum, the rest
    the other, so the 'after' group is never empty by construction. holm_on = False (the sensitivity analyses) decides
    per model on the nominal p. before_months (S9) keeps in the 'before' group only items that took effect in the last
    before_months months before the cutoff."""
    def too_old(gyldig_fra: str, c: str) -> bool:
        if before_months is None:
            return False
        y, mth = int(c[:4]), int(c[5:7]) - before_months
        while mth < 1:
            y, mth = y - 1, mth + 12
        return gyldig_fra <= f"{y:04d}-{mth:02d}{c[7:]}"

    def per_series(models):
        per = {s: [0, 0, 0, 0] for s in series_all}
        after_series = set()
        for m in models:
            for r in rows_by_model[m]:
                if r["id"] not in h1set or (r["gyldig_fra"] <= cut[m] and too_old(r["gyldig_fra"], cut[m])):
                    continue
                if denom == "tolkbare" and not interpretable(r):
                    if r["gyldig_fra"] > cut[m]:
                        after_series.add(r["serie_id"])
                    continue
                a = r["gyldig_fra"] > cut[m]
                if a:
                    after_series.add(r["serie_id"])
                p = per[r["serie_id"]]
                hit = r["klasse"] == "utdatert"
                if only_preceding and hit:  # S8 (H1'): only the most recent value that differs from the key counts
                    pv = immediately_preceding_value(items[r["id"]])
                    hit = pv is not None and abs(r["lest"] - pv) < 1e-6
                if a:
                    p[0] += hit; p[1] += 1
                else:
                    p[2] += hit; p[3] += 1
        return {s: tuple(v) for s, v in per.items()}, after_series

    def run(models):
        per, after = per_series(models)
        oa, na, ob, nbf = (sum(v[k] for v in per.values()) for k in range(4))
        n_after_series = sum(1 for v in per.values() if v[1])
        d = (oa / na - ob / nbf) if na and nbf else None
        kept, dropped = boot(per, [sorted(after), sorted(set(per) - after)],
                             lambda t: t[0] / t[1] - t[2] / t[3] if t[1] and t[3] else None)
        return {"n_etter": na, "serier_etter": n_after_series, "n_foer": nbf, "utdatert_etter": oa, "utdatert_foer": ob, "d": d,
                **interval(kept), "forkastet": dropped, "kept": kept}

    pooled = run(list(rows_by_model))
    kept = pooled.pop("kept")
    pooled["testet"] = pooled["n_etter"] >= MIN_POOLED_AFTER and pooled["serier_etter"] >= MIN_POOLED_AFTER_SERIES and pooled["d"] is not None
    pooled["p"] = p_greater(kept, 0.0) if pooled["testet"] else None
    pooled["tilstand"] = state(pooled["testet"], pooled["p"] is not None and pooled["p"] < ALPHA, pooled["lo95"], pooled["hi95"], MEI_H1, "greater")
    per_model = {}
    for m in rows_by_model:
        r = run([m])
        kept = r.pop("kept")
        r["testet"] = min(r["n_etter"], r["n_foer"]) >= MIN_MODEL and r["serier_etter"] >= MIN_MODEL_SERIES and r["d"] is not None
        r["p"] = p_greater(kept, 0.0) if r["testet"] else None
        per_model[m] = r
    decisions = holm({m: r["p"] for m, r in per_model.items()}) if holm_on else \
        {m: (None if r["p"] is None else r["p"] < ALPHA) for m, r in per_model.items()}
    for m, d in decisions.items():
        r = per_model[m]
        r["holm_forkastet" if holm_on else "nominelt_forkastet"] = d
        r["tilstand"] = state(r["testet"], d, r["lo95"], r["hi95"], MEI_H1, "greater")
    return {"samlet": pooled, "per_modell": per_model, "beslutning_per_modell": "Holm" if holm_on else "nominell p"}


def h2_table(rows_by_model: dict[str, list[dict]], items: dict, h2set: set[str]) -> dict:
    """H2 as estimation (section 7.3): s with a cluster-bootstrap interval over every series of the H2 set; no test."""
    series = sorted({items[i]["serie_id"] for i in h2set})

    def run(models):
        per = {s: [0, 0] for s in series}
        for m in models:
            for r in rows_by_model[m]:
                if r["id"] in h2set and r["klasse"] == "utdatert":
                    pv = immediately_preceding_value(items[r["id"]])
                    per[r["serie_id"]][0] += pv is not None and abs(r["lest"] - pv) < 1e-6
                    per[r["serie_id"]][1] += 1
        per = {s: tuple(v) for s, v in per.items()}
        k, n = sum(v[0] for v in per.values()), sum(v[1] for v in per.values())
        kept, dropped = boot(per, [series], lambda t: t[0] / t[1] if t[1] else None)
        return {"utdaterte": n, "serier_med_utdatert": sum(1 for v in per.values() if v[1]), "s": (k / n) if n else None,
                **interval(kept), "forkastet": dropped, "kept": kept}

    out = {}
    for key, models in [("samlet", list(rows_by_model))] + [(m, [m]) for m in rows_by_model]:
        r = run(models)
        r.pop("kept")
        r["rapportert"] = r["utdaterte"] >= MIN_MODEL  # estimate shown only from 30 outdated answers
        r["intervall_mot_0_5"] = against_half(r["lo95"], r["hi95"]) if r["rapportert"] else None
        out[key] = r
    return {"samlet": out.pop("samlet"), "per_modell": out}


def h3_table(pairs_by_model: dict[str, list[dict]], holm_on: bool = True) -> dict:
    """D = (c - b) / pairs pooled and per model, and pi = b / (b + c) (the share of discordant pairs with only Bokmål
    correct; section 8 assumes the pilot discordance for the smallest effect on the D scale), both with intervals."""
    series = sorted({p["serie_id"] for ps in pairs_by_model.values() for p in ps})

    def run(models):
        per = {s: [0, 0, 0] for s in series}  # (Nynorsk correct only, Bokmål correct only, pairs)
        for m in models:
            for p in pairs_by_model[m]:
                per[p["serie_id"]][0] += p["nn"] and not p["nb"]
                per[p["serie_id"]][1] += p["nb"] and not p["nn"]
                per[p["serie_id"]][2] += 1
        per = {s: tuple(v) for s, v in per.items()}
        c, b, n = (sum(v[k] for v in per.values()) for k in range(3))
        kept, dropped = boot(per, [series], lambda t: (t[0] - t[1]) / t[2] if t[2] else None)
        kept_pi, dropped_pi = boot(per, [series], lambda t: t[1] / (t[0] + t[1]) if t[0] + t[1] else None)
        pi = {"pi": b / (b + c) if b + c else None, **{f"pi_{k}": v for k, v in interval(kept_pi).items()}, "pi_forkastet": dropped_pi}
        return {"b": b, "c": c, "par": n, "D": (c - b) / n if n else None, **interval(kept), "forkastet": dropped, **pi, "kept": kept}

    pooled = run(list(pairs_by_model))
    kept = pooled.pop("kept")
    pooled["testet"] = pooled["b"] + pooled["c"] > 0
    pooled["p"] = p_less(kept, 0.0) if pooled["testet"] else None
    pooled["tilstand"] = state(pooled["testet"], pooled["p"] is not None and pooled["p"] < ALPHA, pooled["lo95"], pooled["hi95"], MEI_H3, "less")
    per_model = {}
    for m in pairs_by_model:
        r = run([m])
        r.pop("kept")
        r["testet"] = r["b"] + r["c"] > 0
        r["p"] = mcnemar_less(r["b"], r["c"]) if r["testet"] else None
        per_model[m] = r
    decisions = holm({m: r["p"] for m, r in per_model.items()}) if holm_on else \
        {m: (None if r["p"] is None else r["p"] < ALPHA) for m, r in per_model.items()}
    for m, d in decisions.items():
        r = per_model[m]
        r["holm_forkastet" if holm_on else "nominelt_forkastet"] = d
        r["tilstand"] = state(r["testet"], d, r["lo95"], r["hi95"], MEI_H3, "less")
    return {"samlet": pooled, "per_modell": per_model, "beslutning_per_modell": "Holm" if holm_on else "nominell p"}


def chance_match(rows_by_model: dict[str, list[dict]], items: dict, prim: list[str], cut: dict | None = None, h1set: set | None = None) -> dict:
    """Expected share of interpretable answers that would be 'outdated' by chance: for each answer value v to item i of
    type t, the share of the other primary items j of type t in other series for which v equals an earlier version of j
    that differs from j's key. Averaged over the interpretable answers of a model, per type and over all."""
    by_type: dict[str, list[str]] = defaultdict(list)
    for i in prim:
        by_type[items[i]["type"]].append(i)
    earlier: dict[str, dict[float, set[str]]] = {}
    for t, ids in by_type.items():
        idx: dict[float, set[str]] = defaultdict(set)
        for j in ids:
            it = items[j]
            for h in it["verdihistorikk"]:
                if h["gyldig_fra"] < it["gyldig_fra"] and abs(h["verdi"] - it["fasitverdi"]) >= 1e-6:
                    idx[round(h["verdi"], 6)].add(j)
        earlier[t] = idx
    out = {}
    for m, rows in rows_by_model.items():
        acc: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            if r["id"] not in prim or not interpretable(r) or r["lest"] is None or r["lest"] != r["lest"]:
                continue
            it = items[r["id"]]
            pool = [j for j in by_type[it["type"]] if items[j]["serie_id"] != it["serie_id"]]
            hits = earlier[it["type"]].get(round(r["lest"], 6), set())
            rate = sum(1 for j in hits if items[j]["serie_id"] != it["serie_id"]) / len(pool) if pool else 0.0
            acc[it["type"]].append(rate)
            acc["alle"].append(rate)
            if cut and cut.get(m) and r["id"] in h1set:  # per H1 group (table T7)
                acc["H1_etter" if it["gyldig_fra"] > cut[m] else "H1_foer"].append(rate)
        out[m] = {t: {"n": len(v), "forventet_tilfeldig_utdatert": float(np.mean(v)) if v else None} for t, v in acc.items()}
    return out


def fs2(rows: list[dict]) -> dict:
    """Age in years of outdated answers: quartiles (numpy linear), a cluster-bootstrap interval for the median over the
    series with at least one outdated answer, and counts per age group (as in v1)."""
    ages = [r for r in rows if r["klasse"] == "utdatert" and r["alder"] is not None]
    bins = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6-10": 0, ">10": 0}
    for r in ages:
        a = int(r["alder"])
        bins[str(a) if a <= 5 else ("6-10" if a <= 10 else ">10")] += 1
    out = {"n": len(ages), "grupper": bins}
    if ages:
        q = np.quantile([r["alder"] for r in ages], [0.25, 0.5, 0.75], method="linear")
        series = sorted({r["serie_id"] for r in ages})
        by = {s: [r["alder"] for r in ages if r["serie_id"] == s] for s in series}
        rng = np.random.default_rng(SEED)
        meds = [float(np.quantile([a for k in row for a in by[series[k]]], 0.5, method="linear")) for row in draws(len(series), B, rng)]
        out.update(q1=float(q[0]), median=float(q[1]), q3=float(q[2]), **{f"median_{k}": v for k, v in interval(np.array(meds)).items()})
    return out


def around_cutoff(rows: list[dict], cutoff: str | None, h1set: set[str]) -> dict:
    """Uninterpretable answers and refusals after and before the cutoff in the H1 set (descriptive, table T19)."""
    if not cutoff:
        return {}
    out = {}
    for g, sel in (("etter", lambda r: r["gyldig_fra"] > cutoff), ("foer", lambda r: r["gyldig_fra"] <= cutoff)):
        rs = [r for r in rows if r["id"] in h1set and sel(r)]
        out[g] = {"n": len(rs), "utolket": sum(r["klasse"] == "utolket" for r in rs), "avslag": sum(r["under"] == "avslag" for r in rs)}
    return out


SELF = re.compile(r"kunnskapsgrens|treningsdata|kunnskapsbase|knowledge cutoff|training data", re.I)
PERIOD = re.compile(r"(tidlig|midten av|slutten av|januar|februar|mars|april|mai|juni|juli|august|september|oktober|november|"
                    r"desember|early|mid|late|january|february|march|may|june|july|october|december)[ -]?(?:of )?((?:19|20)\d\d)", re.I)


def self_reported(answers: list[dict], model: str, ids: set[str]) -> dict:
    """Answers that mention the model's own knowledge limit, and the first month or period with a year in the 40
    characters after the keyword, in the same sentence (the method of supplement A6; table T20)."""
    per, n = Counter(), 0
    for a in answers:
        if a["model"] != model or a.get("run", 1) != 1 or a["id"] not in ids:
            continue
        text = a.get("completion") or ""
        hits = list(SELF.finditer(text))
        if not hits:
            continue
        n += 1
        found = None
        for k in hits:
            m = PERIOD.search(re.split(r"[.!?\n]", text[k.end():k.end() + 40])[0])
            if m:
                found = f"{m.group(1).lower()} {m.group(2)}"
                break
        per[found or "uten tidsangivelse"] += 1
    return {"svar_med_omtale": n, "tidsangivelser": dict(sorted(per.items()))}


def counts(rows: list[dict], key) -> dict:
    groups: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        groups[key(r)][r["klasse"]] += 1
        if r["under"]:
            groups[key(r)][r["under"]] += 1
        groups[key(r)]["n"] += 1
    return {g: dict(c) for g, c in sorted(groups.items())}


# ------------------------------------------------------------------------------------------- driver

def analyse(models: list[dict], answers: list[dict], pairs_file: Path, scorer: str = "v2", subset: str = "primary",
            run: int = 1, denom: str = "tolkbare", cutoff_field: str = "cutoff", holm_on: bool = False,
            before_months: int | None = None) -> dict:
    """One analysis. holm_on is True only for the primary analysis; every sensitivity analysis decides per model on the
    nominal p (section 7.5). A model with a missing answer row (main task or H3) in the analysed run stops the analysis:
    only complete runs are analysed (section 6.5)."""
    items = {i["id"]: i for i in load("items.jsonl")}
    h3 = {i["id"]: i for i in (json.loads(l) for l in pairs_file.open(encoding="utf-8"))}
    ex = json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())
    errata = [l.strip() for l in (ROOT / "data" / "errata_v2.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    excluded = (set(ex["excluded_items"]) | (set(ex["flagged_kept"]) if subset == "uten_flaggede" else set())
                | (set(errata) if subset == "uten_errata" else set()))
    if subset == "alle_916":
        excluded = set()
    prim = [i for i in items if i not in excluded]
    h1set = set(ex["h1_eligible_items_all916" if subset == "alle_916" else "sensitivity3_h1_eligible" if subset == "uten_flaggede" else "h1_eligible_items"])
    h2set = set(ex["h2_eligible_items_all916" if subset == "alle_916" else "sensitivity3_h2_eligible" if subset == "uten_flaggede" else "h2_eligible_items"])
    rejected = rejected_values({items[i]["serie_id"] for i in items})
    keys = Counter((a["model"], a["id"], a.get("run", 1)) for a in answers)
    dup = [k for k, n in keys.items() if n > 1]
    if dup:
        raise SystemExit(f"answer file: {len(dup)} duplicate (model, id, run) rows, e.g. {dup[:2]}")
    by = {(a["model"], a["id"]): a for a in answers if a.get("run", 1) == run}
    rows_by_model, pairs_by_model = {}, {}
    for m in models:
        mid = m["id"]
        rows = []
        for i in prim:
            it = items[i]
            rows.append({"id": i, "serie_id": it["serie_id"], "gyldig_fra": it["gyldig_fra"], "type": it["type"], "sett": it["sett"],
                         "målform": it["målform"], **classify(by.get((mid, i)), it, rejected, scorer)})
        rows_by_model[mid] = rows
        pairs = []
        for par in sorted({h["h3_par"] for h in h3.values()}):
            if par in excluded:
                continue
            nbq, nnq = h3[f"{par}-nb"], h3[f"{par}-nn"]
            pairs.append({"serie_id": nbq["serie_id"],
                          "nb": classify(by.get((mid, nbq["id"])), nbq, rejected, scorer)["klasse"] == "korrekt",
                          "nn": classify(by.get((mid, nnq["id"])), nnq, rejected, scorer)["klasse"] == "korrekt"})
        pairs_by_model[mid] = pairs
        missing = sum(r["under"] == "mangler" for r in rows) + sum(1 for q in h3 if (mid, q) not in by and h3[q]["h3_par"] not in excluded)
        if missing:
            raise SystemExit(f"{mid}: {missing} missing answer rows in run {run}; only complete runs are analysed")
    h1_models = [m["id"] for m in models if m.get("h1") and m.get("cutoff")]
    cut = {m["id"]: (m.get(cutoff_field) or m.get("cutoff")) for m in models}  # S5: reliable-knowledge cutoff where stated
    series_all = sorted({items[i]["serie_id"] for i in prim if i in h1set})  # the series of the H1 set
    rep = {"scorer": scorer, "utvalg": subset, "kjøring": run, "nevner_h1": denom, "cutoff": cutoff_field,
           "før_vindu_måneder": before_months, "beslutning_per_modell": "Holm" if holm_on else "nominell p", "modeller": {}}
    for m in models:
        rows = rows_by_model[m["id"]]
        rep["modeller"][m["id"]] = {
            "alle_svar": shares(rows, "alle"), "tolkbare_svar": shares(rows, "tolkbare"),
            "underklasser": dict(Counter(r["under"] for r in rows if r["under"])),
            "per_verditype": counts(rows, lambda r: r["type"]), "per_serietype": counts(rows, lambda r: r["sett"]),
            "per_målform": counts(rows, lambda r: r["målform"]),
            "fs2": fs2(rows) if scorer == "v2" else None,
            "rundt_cutoff": around_cutoff(rows, (m.get(cutoff_field) or m.get("cutoff")) if m.get("h1") else None, h1set),
            "egen_kunnskapsgrense": self_reported(answers, m["id"], set(items)),
            "normaliserte_aldersvar": sum(r["normalisert"] for r in rows),
            "mangler": sum(r["under"] == "mangler" for r in rows)}
    if scorer == "v2":
        rep["h1"] = h1_table({m: rows_by_model[m] for m in h1_models}, cut, h1set, series_all, denom, holm_on=holm_on,
                             before_months=before_months)
        rep["h1_nevner_alle"] = h1_table({m: rows_by_model[m] for m in h1_models}, cut, h1set, series_all, "alle", holm_on=False)
        rep["h1_bare_nyeste_verdi"] = h1_table({m: rows_by_model[m] for m in h1_models}, cut, h1set, series_all, denom, items, True,
                                               holm_on=False)  # S8
        rep["h1_per_leverandoer"] = {prov: h1_table({m["id"]: rows_by_model[m["id"]] for m in models if m["id"] in h1_models and m["provider"] == prov},
                                                    cut, h1set, series_all, denom)["samlet"]
                                     for prov in sorted({m["provider"] for m in models if m["id"] in h1_models})}
        rep["tidligere_avvikende_verdier"] = {m: {g: float(np.mean([len({round(h["verdi"], 6) for h in items[i]["verdihistorikk"]
                                                                         if h["gyldig_fra"] < items[i]["gyldig_fra"] and abs(h["verdi"] - items[i]["fasitverdi"]) >= 1e-6})
                                                                    for i in h1set if (items[i]["gyldig_fra"] > cut[m]) == (g == "etter")] or [0]))
                                                  for g in ("etter", "foer")} for m in h1_models}
        rep["h2"] = h2_table(rows_by_model, items, h2set)
        rep["tilfeldig_treff"] = chance_match(rows_by_model, items, prim, cut, h1set)
        groups = {g: ids for g, ids in ex["groups"].items()} if subset == "primary" else {}
        rep["eksklusjonsgrupper"] = {m["id"]: {g: dict(Counter(classify(by.get((m["id"], i)), items[i], rejected)["klasse"] for i in ids))
                                               for g, ids in groups.items()} for m in models}
    else:
        rep["h1"] = h1_table({m: rows_by_model[m] for m in h1_models}, cut, h1set, series_all, denom, holm_on=holm_on)
    rep["h3"] = h3_table(pairs_by_model, holm_on=holm_on)
    return rep


def metadata_table() -> dict:
    """Table T21 from item metadata only: time span, series lengths and versions per series of the primary set, per set
    type and over all, and the primary series with at least one version the cleanliness rule did not accept."""
    items = [i for i in load("items.jsonl")]
    ex = json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())
    prim = [i for i in items if i["id"] not in set(ex["excluded_items"])]
    series = {i["serie_id"] for i in prim}
    versions, rejected = {}, set()
    for l in (ROOT / "data" / "v3_items.jsonl").open(encoding="utf-8"):
        d = json.loads(l)
        if d["id"] in series:
            versions[d["id"]] = len(d.get("history") or [])
            if not all(d.get("accepted") or []):
                rejected.add(d["id"])
    out = {}
    for g in ["alle"] + sorted({i["sett"] for i in prim}):
        sel = [i for i in prim if g == "alle" or i["sett"] == g]
        per = Counter(i["serie_id"] for i in sel)
        years = sorted(int(i["gyldig_fra"][:4]) for i in sel)
        vs = [versions[s] for s in per if s in versions]
        out[g] = {"items": len(sel), "serier": len(per), "år_fra": years[0], "år_til": years[-1],
                  "items_per_serie": {"min": min(per.values()), "median": float(np.median(list(per.values()))), "maks": max(per.values())},
                  "versjoner_per_serie": {"min": min(vs), "median": float(np.median(vs)), "maks": max(vs)} if vs else None,
                  "serier_med_forkastet_versjon": len(rejected & set(per))}
    return out


def complete_in_run(m: dict, answers: list[dict], r: int, pairs_file: Path) -> bool:
    """All main-task items and all H3 questions of the primary pairs answered in run r (S6 uses only complete runs)."""
    got = {a["id"] for a in answers if a["model"] == m["id"] and a.get("run", 1) == r}
    ex = set(json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())["excluded_items"])
    main = {i["id"] for i in load("items.jsonl")}
    h3q = {q["id"] for q in (json.loads(l) for l in pairs_file.open(encoding="utf-8")) if q["h3_par"] not in ex}
    return main <= got and h3q <= got


def variation(models: list[dict], answers: list[dict]) -> dict:
    """Agreement between runs (table T17): for each model with more than one run (repeats or the control run), the share of
    primary items with the same class in run k as in run 1, and the class shares of each run on the items both runs have.
    The class is the one of the analysis (normalisation, then scorer v2)."""
    items = {i["id"]: i for i in load("items.jsonl")}
    ex = json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())
    items = {k: v for k, v in items.items() if k not in set(ex["excluded_items"])}  # primary set (table T17)
    out = {}
    for m in models:
        runs = sorted({a.get("run", 1) for a in answers if a["model"] == m["id"]})
        if len(runs) < 2:
            continue
        cls = {r: {a["id"]: classify(a, items[a["id"]], {})["klasse"]
                   for a in answers if a["model"] == m["id"] and a.get("run", 1) == r and a["id"] in items} for r in runs}
        base = cls[runs[0]]
        out[m["id"]] = {}
        for r in runs:
            common = sorted(set(base) & set(cls[r]))
            out[m["id"]][f"kjøring_{r}"] = {
                "felles_items": len(common),
                "lik_klasse": float(np.mean([base[i] == cls[r][i] for i in common])) if common else None,
                "andeler_felles_items": {c: sum(cls[r][i] == c for i in common) / len(common) for c in CLASSES} if common else None}
    return out


def main() -> None:
    global B
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True)
    ap.add_argument("--answers", required=True)
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--b", type=int, default=B, help="bootstrap resamples; the preregistered value is 10 000")
    a = ap.parse_args()
    B = a.b
    models = json.loads(Path(a.models).read_text(encoding="utf-8"))
    answers = [json.loads(l) for l in Path(a.answers).open(encoding="utf-8")]
    pairs = Path(a.pairs)
    sha = {k: hashlib.sha256(Path(v).read_bytes()).hexdigest() for k, v in (("modeller", a.models), ("svar", a.answers), ("h3", a.pairs))}
    rep = {"B": B, "seed": SEED, "primærrapport": B == 10_000, "inndata_sha256": sha,
           "primær": analyse(models, answers, pairs, holm_on=True),
           "S1_alle_916": analyse(models, answers, pairs, subset="alle_916"),
           "S2_scorer_v1": analyse(models, answers, pairs, scorer="v1"),
           "S3_uten_flaggede": analyse(models, answers, pairs, subset="uten_flaggede"),
           "S4_nevner_alle_svar": analyse(models, answers, pairs, denom="alle"),
           "S5_reliable_knowledge_cutoff": analyse(models, answers, pairs, cutoff_field="reliable_knowledge_cutoff"),
           "S7_uten_errata": analyse(models, answers, pairs, subset="uten_errata"),
           "S9_foer_siste_24_maaneder": analyse(models, answers, pairs, before_months=24),
           "variasjon_mellom_kjøringer": variation(models, answers),
           "T21_metadata": metadata_table()}
    for r in sorted({x.get("run", 1) for x in answers} - {1}):  # S6: run r, for the models with R >= r that are complete in run r
        cand = [m for m in models if m.get("runs", 1) >= r]
        sub = [m for m in cand if complete_in_run(m, answers, r, pairs)]
        rep[f"S6_kjøring_{r}_utelatt"] = [m["id"] for m in cand if m not in sub]
        if sub:
            rep[f"S6_kjøring_{r}"] = analyse(sub, answers, pairs, run=r)
    Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    if B != 10_000:
        print(f"B = {B}: this is a trial run, not the primary report (the preregistered B is 10 000)", file=sys.stderr)


if __name__ == "__main__":
    main()
