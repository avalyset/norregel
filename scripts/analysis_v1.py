"""Reference implementation of the norregel v1 analysis (docs/PREREG_TILLEGG.md, section 4).

Normative for every computational detail the addendum describes: analysis sets, scorer
classes, the cluster bootstrap (draws, dropped resamples, quantiles, p-values), the tests
and Holm–Bonferroni. No model is called; the input is model answers.

Usage:
  python scripts/analysis_v1.py --models docs/modeller.json --answers answers.jsonl --out report.json
answers.jsonl: one line per answer {"model", "id", "completion", "error"} where id is an item id
(main run) or an H3 id ("norregel-NNNNN-nb"/"-nn"). `answers_from_logs` builds it from Inspect logs.
docs/modeller.json: [{"id", "cutoff": "YYYY-MM-DD" or null, "reasoning": bool}].
"""

from __future__ import annotations

import argparse
import json
import sys
from math import comb
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from norregel.score import score as score_v1  # noqa: E402
from norregel.score_v2 import score as score_v2  # noqa: E402

B = 10_000
SEED = 20261018
ALPHA = 0.05
CLASSES = ("korrekt", "utdatert", "feil", "utolket")


def load(name: str) -> list[dict]:
    return [json.loads(l) for l in (ROOT / "data" / name).open(encoding="utf-8")]


def classify(answer: dict | None, item: dict, scorer: str) -> dict:
    """Class of one answer. A missing answer or an error left after retries is utolket."""
    if answer is None or answer.get("error"):
        return {"klasse": "utolket", "alder": None, "lest": None, "senere": [], "error": True}
    r = (score_v2 if scorer == "v2" else score_v1)(answer.get("completion") or "", item)
    return {"klasse": r.klasse, "alder": getattr(r, "alder", None), "lest": r.lest,
            "senere": getattr(r, "senere", []), "error": False}


def draws(series: list[str], b: int = B) -> np.ndarray:
    """Resample indices for one analysis set: a fresh default_rng(SEED) per analysis set, series
    sorted with Python's sorted() on serie_id, shape (b, number of series)."""
    rng = np.random.default_rng(SEED)
    return rng.integers(0, len(series), size=(b, len(series)))


def boot(per_series: dict[str, tuple], series: list[str], stat, b: int = B):
    """Bootstrap a statistic of per-series count tuples. stat(sum_tuple) returns a float or None
    (undefined). Undefined resamples are dropped and counted."""
    arr = np.array([per_series[s] for s in series], dtype=float)
    idx = draws(series, b)
    sums = arr[idx].sum(axis=1)  # (b, k)
    vals = [stat(tuple(row)) for row in sums]
    kept = np.array([v for v in vals if v is not None], dtype=float)
    return kept, b - len(kept)


def quantiles(kept: np.ndarray) -> dict:
    if len(kept) == 0:
        return {"lo95": None, "hi95": None, "lo90_onesided": None}
    q = np.quantile(kept, [0.025, 0.975, 0.05], method="linear")
    return {"lo95": float(q[0]), "hi95": float(q[1]), "lo90_onesided": float(q[2])}


def p_greater(kept: np.ndarray, theta0: float) -> float | None:
    """One-sided bootstrap p-value for theta > theta0: (1 + #{theta* <= theta0}) / (B' + 1)."""
    return None if len(kept) == 0 else float((1 + np.sum(kept <= theta0)) / (len(kept) + 1))


def holm(pvals: dict[str, float]) -> dict[str, bool]:
    """Holm–Bonferroni at ALPHA over the models that were tested (None = not tested)."""
    tested = sorted(((p, m) for m, p in pvals.items() if p is not None))
    out, k, stop = {m: None for m in pvals}, len(tested), False
    for rank, (p, m) in enumerate(tested):
        if stop or p > ALPHA / (k - rank):
            stop = True
            out[m] = False
        else:
            out[m] = True
    return out


def previous_versions(item: dict) -> list[dict]:
    return sorted((h for h in item["verdihistorikk"] if h["gyldig_fra"] < item["gyldig_fra"]), key=lambda h: h["gyldig_fra"])


def immediately_preceding_value(item: dict) -> float | None:
    """The value of the most recent earlier version whose value differs from the key."""
    for h in reversed(previous_versions(item)):
        if abs(h["verdi"] - item["fasitverdi"]) >= 1e-6:
            return h["verdi"]
    return None


def class_shares(rows: list[dict]) -> dict:
    """Primary measures: share of each class with cluster-bootstrap 95 % intervals."""
    series = sorted({r["serie_id"] for r in rows})
    out = {"n": len(rows), "series": len(series)}
    for c in CLASSES:
        per = {s: (0, 0) for s in series}
        for r in rows:
            k, n = per[r["serie_id"]]
            per[r["serie_id"]] = (k + (r["klasse"] == c), n + 1)
        est = sum(v[0] for v in per.values()) / len(rows) if rows else None
        kept, dropped = boot(per, series, lambda t: t[0] / t[1] if t[1] else None)
        out[c] = {"share": est, **quantiles(kept), "dropped_resamples": dropped}
    return out


def h1(rows: list[dict], cutoff: str | None, eligible: set[str]) -> dict:
    if cutoff is None:
        return {"tested": False, "reason": "no stated cutoff"}
    rows = [r for r in rows if r["id"] in eligible]
    after = [r for r in rows if r["gyldig_fra"] > cutoff]
    before = [r for r in rows if r["gyldig_fra"] <= cutoff]

    def share(g):
        return sum(r["klasse"] == "utdatert" for r in g) / len(g) if g else None

    d = None if not after or not before else share(after) - share(before)
    res = {"n_after": len(after), "n_before": len(before), "series_after": len({r["serie_id"] for r in after}),
           "series_before": len({r["serie_id"] for r in before}), "d": d}
    series = sorted({r["serie_id"] for r in rows})
    per = {s: (0, 0, 0, 0) for s in series}  # (outdated after, n after, outdated before, n before)
    for r in rows:
        a = per[r["serie_id"]]
        if r["gyldig_fra"] > cutoff:
            per[r["serie_id"]] = (a[0] + (r["klasse"] == "utdatert"), a[1] + 1, a[2], a[3])
        else:
            per[r["serie_id"]] = (a[0], a[1], a[2] + (r["klasse"] == "utdatert"), a[3] + 1)
    kept, dropped = boot(per, series, lambda t: t[0] / t[1] - t[2] / t[3] if t[1] and t[3] else None)
    res.update(quantiles(kept), dropped_resamples=dropped)
    enough = min(len(after), len(before)) >= 30 and min(res["series_after"], res["series_before"]) >= 5
    res["tested"] = enough and d is not None
    res["p"] = p_greater(kept, 0.0) if res["tested"] else None
    return res


def h2(rows: list[dict], items: dict, eligible: set[str]) -> dict:
    rows = [r for r in rows if r["id"] in eligible and r["klasse"] == "utdatert"]
    for r in rows:
        r["preceding"] = abs(r["lest"] - immediately_preceding_value(items[r["id"]])) < 1e-6
    s = sum(r["preceding"] for r in rows) / len(rows) if rows else None
    series = sorted({r["serie_id"] for r in rows})
    per = {x: (0, 0) for x in series}
    for r in rows:
        a = per[r["serie_id"]]
        per[r["serie_id"]] = (a[0] + r["preceding"], a[1] + 1)
    kept, dropped = boot(per, series, lambda t: t[0] / t[1] if t[1] else None) if series else (np.array([]), 0)
    res = {"n_outdated": len(rows), "series": len(series), "s": s, **quantiles(kept), "dropped_resamples": dropped}
    res["tested"] = len(rows) >= 30
    res["p"] = p_greater(kept, 0.5) if res["tested"] else None
    return res


def fs2(rows: list[dict]) -> dict:
    ages = [r["alder"] for r in rows if r["klasse"] == "utdatert"]
    bins = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6-10": 0, ">10": 0}
    for a in ages:
        bins[str(a) if a <= 5 else ("6-10" if a <= 10 else ">10")] += 1
    res = {"n_outdated": len(ages), "bins": bins}
    if ages:
        q = np.quantile(ages, [0.25, 0.5, 0.75], method="linear")
        res.update(q1=float(q[0]), median=float(q[1]), q3=float(q[2]))
        series = sorted({r["serie_id"] for r in rows if r["klasse"] == "utdatert"})  # series with an outdated answer
        idx = draws(series)
        by = {s: [r["alder"] for r in rows if r["serie_id"] == s and r["klasse"] == "utdatert"] for s in series}
        meds = []
        for row in idx:
            pool = [a for k in row for a in by[series[k]]]
            if pool:
                meds.append(float(np.quantile(pool, 0.5, method="linear")))
        res.update(median_ci=quantiles(np.array(meds)), dropped_resamples=B - len(meds))
    return res


def mcnemar_one_sided(b: int, c: int) -> float | None:
    """Exact McNemar, H1: b > c. p = P(X >= b), X ~ Bin(b + c, 0.5)."""
    n = b + c
    return None if n == 0 else sum(comb(n, k) for k in range(b, n + 1)) / 2 ** n


def h3(pairs: list[dict]) -> dict:
    b = sum(p["nb"] and not p["nn"] for p in pairs)
    c = sum(p["nn"] and not p["nb"] for p in pairs)
    series = sorted({p["serie_id"] for p in pairs})
    per = {s: (0, 0, 0) for s in series}  # (nn correct, nb correct, n pairs)
    for p in pairs:
        a = per[p["serie_id"]]
        per[p["serie_id"]] = (a[0] + p["nn"], a[1] + p["nb"], a[2] + 1)
    est = (sum(p["nn"] for p in pairs) - sum(p["nb"] for p in pairs)) / len(pairs) if pairs else None
    kept, dropped = boot(per, series, lambda t: (t[0] - t[1]) / t[2] if t[2] else None)
    return {"pairs": len(pairs), "series": len(series), "b": b, "c": c, "p": mcnemar_one_sided(b, c),
            "tested": b + c > 0, "diff_nn_minus_nb": est, **quantiles(kept), "dropped_resamples": dropped}


def analyse(models: list[dict], answers: list[dict], scorer: str = "v2", subset: str = "primary") -> dict:
    items = {i["id"]: i for i in load("items.jsonl")}
    h3items = {i["id"]: i for i in load("items_h3.jsonl")}
    ex = json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())
    excluded = set(ex["excluded_items"]) | (set(ex["flagged_kept"]) if subset == "sensitivity3" else set())
    if subset == "all916":
        excluded = set()
    main_ids = [i for i in items if i not in excluded]
    h1_set = set(ex["h1_eligible_items_all916" if subset == "all916" else
                    "sensitivity3_h1_eligible" if subset == "sensitivity3" else "h1_eligible_items"])
    h2_set = set(ex["h2_eligible_items_all916" if subset == "all916" else
                    "sensitivity3_h2_eligible" if subset == "sensitivity3" else "h2_eligible_items"])
    by = {(a["model"], a["id"]): a for a in answers}
    report = {"scorer": scorer, "subset": subset, "models": {}}
    for m in models:
        mid = m["id"]
        rows = []
        for iid in main_ids:
            it = items[iid]
            rows.append({"id": iid, "serie_id": it["serie_id"], "gyldig_fra": it["gyldig_fra"],
                         **classify(by.get((mid, iid)), it, scorer)})
        pairs = []
        for par in sorted({h["h3_par"] for h in h3items.values()}):
            if par in excluded:
                continue
            nb, nn = h3items[f"{par}-nb"], h3items[f"{par}-nn"]
            pairs.append({"serie_id": nb["serie_id"],
                          "nb": classify(by.get((mid, nb["id"])), nb, scorer)["klasse"] == "korrekt",
                          "nn": classify(by.get((mid, nn["id"])), nn, scorer)["klasse"] == "korrekt"})
        def counts(sub):  # counts and shares without intervals (addendum section 4)
            n = len(sub)
            return {"n": n, **{c: {"count": sum(x["klasse"] == c for x in sub),
                                   "share": (sum(x["klasse"] == c for x in sub) / n) if n else None} for c in CLASSES}}
        by_type = {t: counts([x for x in rows if items[x["id"]]["type"] == t])
                   for t in sorted({items[x["id"]]["type"] for x in rows})}
        groups = {g: counts([{"id": iid, **classify(by.get((mid, iid)), items[iid], scorer)} for iid in ids])
                  for g, ids in ex["groups"].items()} if subset == "primary" else {}
        r = {"primary": class_shares(rows), "errors": sum(x["error"] for x in rows),
             "by_type": by_type, "exclusion_groups": groups,
             "h1": h1(rows, m.get("cutoff"), h1_set), "h3": h3(pairs)}
        if scorer == "v2":
            r["h2"] = h2(rows, items, h2_set)
            r["fs2"] = fs2(rows)
            r["feil_later_value"] = sum(1 for x in rows if x["klasse"] == "feil" and x["senere"])
            r["feil_not_in_history"] = sum(1 for x in rows if x["klasse"] == "feil" and not x["senere"])
        report["models"][mid] = r
    for hyp in ("h1", "h2", "h3"):
        if subset == "primary" and all(hyp in r for r in report["models"].values()):
            dec = holm({m: (r[hyp]["p"] if r[hyp].get("tested") else None) for m, r in report["models"].items()})
            for m, d in dec.items():
                report["models"][m][hyp]["holm_reject"] = d
    return report


def answers_from_logs(paths: list[str]) -> list[dict]:
    from inspect_ai.log import read_eval_log
    out = []
    for p in paths:
        log = read_eval_log(p)
        for s in log.samples:
            out.append({"model": log.eval.model, "id": s.id, "completion": s.output.completion if s.output else "",
                        "error": s.error is not None})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True)
    ap.add_argument("--answers")
    ap.add_argument("--logs", nargs="*")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    models = json.loads(Path(a.models).read_text())
    answers = [json.loads(l) for l in Path(a.answers).open()] if a.answers else answers_from_logs(a.logs)
    report = {"primary_v2": analyse(models, answers, "v2", "primary"),
              "sensitivity1_all916_v2": analyse(models, answers, "v2", "all916"),
              "sensitivity2_v1": analyse(models, answers, "v1", "primary"),
              "sensitivity3_v2": analyse(models, answers, "v2", "sensitivity3")}
    Path(a.out).write_text(json.dumps(report, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()
