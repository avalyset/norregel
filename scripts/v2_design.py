"""Design basis for norregel v2 (before any v2 model run): candidate models, H1 group sizes, pilot parameters from v1,
a priori power and a cost estimate.

Reads docs/v2_kandidater.json (cutoffs with source, fetched 17.10.2026), data/items.jsonl and data/exclusions_tillegg.json
(item metadata only: dates, series, types), and, for the pilot parameters, the v1 answers in logs/run_v1/answers.jsonl and
the token use in docs/RESULTS.md. Writes docs/V2_DESIGNGRUNNLAG.md. No model is called. The report contains no answer
text and no key value.

  .venv/bin/python -I scripts/v2_design.py
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import analysis_v1 as A  # noqa: E402

OUT = ROOT / "docs" / "V2_DESIGNGRUNNLAG.md"
ALPHA = 0.05
POWER = 0.80
SESOI_H1 = (0.10, 0.15, 0.20)  # H1: smallest effects of interest (pp), set here, not from v1 (v1 has no usable H1 effect)
MIN_AFTER, MIN_AFTER_SERIES = 30, 20  # per-model H1 minimum used to count the worst-case Holm family (see section 4)
PAIRS_V1, PAIRS_V2 = 189, 880


def nb(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def z(p: float) -> float:
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if phi(mid) < p else (lo, mid)
    return (lo + hi) / 2


def icc(groups: list[list[int]]) -> float:
    """One-way ANOVA estimator of the intraclass correlation of a binary outcome within clusters."""
    k, n = len(groups), sum(len(g) for g in groups)
    m0 = (n - sum(len(g) ** 2 for g in groups) / n) / (k - 1)
    ybar = np.mean([y for g in groups for y in g])
    msb = sum(len(g) * (np.mean(g) - ybar) ** 2 for g in groups) / (k - 1)
    msw = sum(sum((y - np.mean(g)) ** 2 for y in g) for g in groups) / (n - k)
    return max(0.0, float((msb - msw) / (msb + (m0 - 1) * msw)))


def tails(n: int, p: float) -> np.ndarray:
    """P(X >= k) for k = 0..n+1, X ~ Bin(n, p), from the log pmf."""
    k = np.arange(n + 1)
    lp = (np.array([math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) for i in k])
          + k * math.log(p) + (n - k) * math.log(1 - p))
    pmf = np.exp(lp)
    return np.append(pmf[::-1].cumsum()[::-1], 0.0)


def exact_power(n: int, p1: float, alpha: float, p0: float = 0.5) -> float:
    """Power of the one-sided exact binomial test of p = p0 against p > p0 with n trials."""
    if n <= 0:
        return 0.0
    t0 = tails(n, p0)
    kc = int(np.argmax(t0 <= alpha)) if (t0 <= alpha).any() else n + 1
    return float(tails(n, p1)[kc]) if kc <= n else 0.0


def n_for_exact(p1: float, alpha: float, power: float = POWER, nmax: int = 5000) -> int | None:
    """Smallest n with power >= target, and power >= target for the next 10 n as well (the exact power saw-tooths)."""
    for n in range(5, nmax):
        if all(exact_power(m, p1, alpha) >= power for m in range(n, n + 10)):
            return n
    return None


def mde_exact(n: int, alpha: float, power: float = POWER) -> float | None:
    for k in range(501, 1000):
        p1 = k / 1000
        if exact_power(n, p1, alpha) >= power:
            return p1
    return None


def deff(n: float, clusters: int, rho: float) -> float:
    """Design effect 1 + (m - 1)rho with m = n / clusters, never below 1 (floor added after Stage 1, round 1)."""
    return max(1.0, 1 + (n / clusters - 1) * rho) if clusters else 1.0


def h1_power(p0: float, delta: float, na: float, sa: int, nbef: float, sb: int, rho: float, alpha: float, pooled: tuple[int, float] | None = None) -> float:
    p1 = p0 + delta
    sa = max(1, min(sa, round(na)))  # never more series than (interpretable) items in the group
    var = p1 * (1 - p1) / na * deff(na, sa, rho) + p0 * (1 - p0) / nbef * deff(nbef, sb, rho)
    if pooled:
        m, rx = pooled
        var *= (1 + (m - 1) * rx) / m
    return phi(delta / math.sqrt(var) - z(1 - alpha))


def h1_mde(p0: float, na: float, sa: int, nbef: float, sb: int, rho: float, alpha: float, pooled=None) -> float | None:
    for k in range(1, 900):
        if h1_power(p0, k / 1000, na, sa, nbef, sb, rho, alpha, pooled) >= POWER:
            return k / 1000
    return None


def h1_n_required(p0: float, delta: float, sa_ratio: float, nbef: float, sb: int, rho: float, alpha: float) -> int | None:
    """Items needed in the 'after' group (series grow with items at the pilot ratio) for the target power."""
    for na in range(5, 5000):
        if h1_power(p0, delta, na, max(1, round(na * sa_ratio)), nbef, sb, rho, alpha) >= POWER:
            return na
    return None


def stage1_section(items, h1set, prim, P0, RHO, R, RX, DISC, PI, rate_h2, rho2, n_h2, groups) -> list[str]:
    """Section 5: the calculations asked for in the Stage 1 review, round 1 (written after the review)."""
    sel = json.loads((ROOT / "docs" / "v2_modeller.json").read_text(encoding="utf-8"))
    h1m = [m for m in sel if m["h1"]]
    g = {m["id"]: groups[m["id"].split("/", 1)[1]] for m in h1m}
    k = len(h1m)
    L = ["## 5. Tillegg etter Stage 1-vurderingen, runde 1", "",
         "Skrevet etter vurderingen (`docs/vurderinger/STAGE1_VURDERING.md`, i repoet). Modellene er de valgte i `docs/v2_modeller.json`. Designeffekten har "
         "nå gulv på 1, og en gruppe har aldri flere serier enn tolkbare items.", ""]
    nbm = float(np.mean([v[2] for v in g.values()])); sbm = round(np.mean([v[3] for v in g.values()]))

    def pooled(models, ra, rx, delta=0.10):
        na = float(np.mean([g[m][0] for m in models])); sa = round(np.mean([g[m][1] for m in models]))
        nb_ = float(np.mean([g[m][2] for m in models])); sb_ = round(np.mean([g[m][3] for m in models]))
        return h1_power(P0, delta, na * ra, sa, nb_ * R, sb_, RHO, ALPHA, (len(models), rx)), h1_mde(P0, na * ra, sa, nb_ * R, sb_, RHO, ALPHA, (len(models), rx))

    ids = [m["id"] for m in h1m]
    L += [f"**H1 samlet, k = {k}, under ulik tolkbarhet etter cutoff** (andelen tolkbare før cutoff er r = {nb(100 * R)} %, PILOT; δ = 10 pp; "
          "styrke / minste påviselige δ). v1-piloten hadde 0 av 56 (Haiku 4.5) og 1 av 9 (Sonnet 4.6) tolkbare svar etter cutoff "
          "(`docs/TILLEGG_ETTER_VURDERING.md`, A3).", "",
          "| Tolkbar andel etter cutoff | ρx = 0,137 (PILOT) | ρx = 0,3 | ρx = 0,5 |", "|---|---|---|---|"]
    for ra in (R, 0.5, 0.3, 0.11):
        L.append(f"| {nb(100 * ra)} % | " + " | ".join(f"{nb(100 * pooled(ids, ra, rx)[0], 1)} % / {nb(100 * pooled(ids, ra, rx)[1], 1)} pp" for rx in (RX, 0.3, 0.5)) + " |")
    need = next((n for n in range(1, 200) if pooled(ids, n / float(np.mean([g[m][0] for m in ids])), RX)[0] >= POWER), None)
    L += ["", f"For 80 % styrke ved δ = 10 pp trengs i snitt {need} tolkbare svar etter cutoff per H1-modell (ρx = {nb(RX, 3)}).", ""]
    order = ["google/gemini-2.5-pro", "google/gemini-2.5-flash", "anthropic/claude-opus-4-5-20251101", "anthropic/claude-opus-4-6",
             "google/gemini-2.5-flash-lite", "google/gemma-4-26b-a4b-it", "google/gemma-4-31b-it"]
    L += ["**K3 for hver k** (modellene tas ut i K6-rekkefølgen, synkende kostnad blant H1-modellene som ikke er v1-modeller; "
          f"tolkbarhet {nb(100 * R)} % / 50 % etter cutoff, ρx = {nb(RX, 3)}):", "", "| k | Tatt ut | Leverandører | Styrke (r etter 87,6 %) | Styrke (r etter 50 %) |", "|---|---|---|---|---|"]
    cur = list(ids)
    L.append(f"| {len(cur)} | — | {', '.join(sorted({m.split('/')[0] for m in cur}))} | {nb(100 * pooled(cur, R, RX)[0], 1)} % | {nb(100 * pooled(cur, 0.5, RX)[0], 1)} % |")
    for out_m in order:
        cur = [m for m in cur if m != out_m]
        provs = sorted({m.split("/")[0] for m in cur})
        L.append(f"| {len(cur)} | `{out_m}` | {', '.join(provs)} | {nb(100 * pooled(cur, R, RX)[0], 1)} % | {nb(100 * pooled(cur, 0.5, RX)[0], 1)} % |")
        if len(provs) < 2:
            break
    gem = [m for m in ids if "gemma" not in m]
    L += ["", f"Uten Gemma 4 (k = {len(gem)}): {nb(100 * pooled(gem, R, RX)[0], 1)} % ved r etter = {nb(100 * R)} % og {nb(100 * pooled(gem, 0.5, RX)[0], 1)} % ved 50 %.", ""]
    # H3 for k = 12 with a cross-model design effect
    K = len(sel)
    m_total = round(PAIRS_V2 * DISC * K)
    L += [f"**H3 samlet, k = {K}** (diskordans {nb(100 * DISC)} %, PILOT; π1 = {nb(100 * PI)} %, PILOT; {m_total} diskordante par i alt; "
          "designeffekt 1 + (k − 1)ρx for at modellene svarer på de samme parene). Minste påviselige effekt også på D-skala: "
          "|D| = diskordans × (2π − 1).", "", "| ρx | Effektive diskordante | Styrke | Minste π | Minste |D| (pp) |", "|---|---|---|---|---|"]
    for rx in (0.0, RX, 0.3, 0.5):
        meff = int(m_total / (1 + (K - 1) * rx))
        mp = mde_exact(meff, ALPHA)
        L.append(f"| {nb(rx, 3)} | {meff} | {nb(100 * exact_power(meff, PI, ALPHA), 1)} % | {nb(100 * mp, 1)} % | {nb(100 * DISC * (2 * mp - 1), 2)} |")
    # H2 as estimation
    n_tot = n_h2 * rate_h2 * K
    d2 = deff(n_tot, 80, rho2)
    neff = n_tot / d2
    L += ["", f"**H2 som estimering, k = {K}:** ≈ {nb(n_tot, 0)} utdaterte svar, designeffekt {nb(d2, 2)} (80 serier, ρ2 = {nb(rho2, 3)}, PILOT), "
          f"effektivt {nb(neff, 0)}; forventet halv bredde på 95 %-intervallet for s ved s = 0,5: ±{nb(100 * 1.96 * math.sqrt(0.25 / neff), 1)} pp; "
          f"minste s en ensidig test ved α = 0,05 kunne påvise med 80 % styrke: {nb(100 * mde_exact(int(neff), ALPHA), 1)} %.", ""]
    # construct: earlier differing values per item, per group
    L += ["**Målmengde for «utdatert» per H1-gruppe** (item-metadata: gjennomsnittlig antall distinkte tidligere verdier som avviker "
          "fra fasit, per item):", "", "| Cutoff | Etter | Før |", "|---|---|---|"]
    def nprev(i):
        return len({round(h["verdi"], 6) for h in i["verdihistorikk"] if h["gyldig_fra"] < i["gyldig_fra"] and abs(h["verdi"] - i["fasitverdi"]) >= 1e-6})
    for cut in sorted({m["cutoff"] for m in h1m}):
        a = [nprev(i) for i in h1set if i["gyldig_fra"] > cut]
        b = [nprev(i) for i in h1set if i["gyldig_fra"] <= cut]
        L.append(f"| {cut} | {nb(float(np.mean(a)), 2)} (n = {len(a)}) | {nb(float(np.mean(b)), 2)} (n = {len(b)}) |")
    rej = sum(1 for l in (ROOT / "data" / "v3_items.jsonl").open(encoding="utf-8")
              for d in [json.loads(l)] if d["id"] in {items[i]["serie_id"] for i in prim} and not all(d.get("accepted") or []))
    L += ["", f"**Serier med minst én forkastet versjon** (`data/v3_items.jsonl`, `accepted` er usann for minst én versjon): {rej} av "
          f"{len({items[i]['serie_id'] for i in prim})} primærserier.", ""]
    return L


def stage1_r2_section(P0, RHO, R, RX, DISC, PI, groups) -> list[str]:
    """Section 6: the calculations asked for in the Stage 1 review, round 2 (written after the review)."""
    sel = json.loads((ROOT / "docs" / "v2_modeller.json").read_text(encoding="utf-8"))
    h1m = [m["id"] for m in sel if m["h1"]]
    g = {m: groups[m.split("/", 1)[1]] for m in h1m}
    k = len(h1m)
    L = ["## 6. Tillegg etter Stage 1-vurderingen, runde 2", "",
         "Skrevet etter vurderingen (`docs/vurderinger/STAGE1_VURDERING_R2.md`, i repoet), med de samme formlene og PILOT-parametrene som i avsnitt 5.", ""]
    L += [f"**H1 per modell med Holm-α for k = {k}** (α/k = {nb(ALPHA / k, 4)}; tolkbarhet {nb(100 * R)} %): minste påviselige δ"]
    seen = {}
    for m in h1m:
        seen.setdefault(g[m], []).append(m)
    for grp, ms in seen.items():
        mde = h1_mde(P0, grp[0] * R, grp[1], grp[2] * R, grp[3], RHO, ALPHA / k)
        L.append(f"- {', '.join(f'`{x.split(chr(47), 1)[1]}`' for x in ms)} ({grp[0]} etter i {grp[1]} serier): {nb(100 * mde, 1)} pp")
    L.append("")

    def pooled(models, ra):
        na = float(np.mean([g[m][0] for m in models])); sa = round(np.mean([g[m][1] for m in models]))
        nb_ = float(np.mean([g[m][2] for m in models])); sb_ = round(np.mean([g[m][3] for m in models]))
        return h1_power(P0, 0.10, na * ra, sa, nb_ * R, sb_, RHO, ALPHA, (len(models), RX))

    scen = [("Alle åtte", h1m), ("Uten alle tre Gemini 2.5 (tilgangen er begrenset til tidligere brukere)", [m for m in h1m if "gemini-2.5" not in m]),
            ("Bare Anthropic", [m for m in h1m if m.startswith("anthropic/")]), ("Bare Google", [m for m in h1m if m.startswith("google/")])]
    L += [f"**H1 samlet ved bortfall** (δ = 10 pp, ρx = {nb(RX, 3)}, PILOT; styrke ved tolkbar andel etter cutoff):", "",
          "| Scenario | k | 87,6 % | 50 % | 30 % |", "|---|---|---|---|---|"]
    for name, ms in scen:
        L.append(f"| {name} | {len(ms)} | " + " | ".join(f"{nb(100 * pooled(ms, ra), 1)} %" for ra in (R, 0.5, 0.3)) + " |")
    K = len(sel)
    L += ["", f"**H3 på D-skala ved lavere diskordans** (k = {K}, ρx = {nb(RX, 3)}, π1 = {nb(100 * PI)} %, PILOT). Minste påviselige |D| "
          "forutsetter pilotdiskordansen; med færre diskordante par blir den mindre, og et π som ellers ville vært påviselig, kan gi |D| under 1 pp.", "",
          "| Diskordans | Diskordante par | Effektive | Minste π | Minste |D| (pp) | |D| ved π1 (pp) |", "|---|---|---|---|---|---|"]
    for f in (1.0, 0.75, 0.5):
        m_total = round(PAIRS_V2 * DISC * f * K)
        meff = int(m_total / (1 + (K - 1) * RX))
        mp = mde_exact(meff, ALPHA)
        L.append(f"| {nb(100 * DISC * f)} % | {m_total} | {meff} | {nb(100 * mp, 1) if mp else '—'} % | "
                 f"{nb(100 * DISC * f * (2 * mp - 1), 2) if mp else '—'} | {nb(100 * DISC * f * (2 * PI - 1), 2)} |")
    L.append("")
    return L


def main() -> None:
    items = {i["id"]: i for i in A.load("items.jsonl")}
    h3 = {i["id"]: i for i in A.load("items_h3.jsonl")}
    ex = json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())
    excl = set(ex["excluded_items"])
    prim = [i for i in items if i not in excl]
    h1set, h2set = [items[i] for i in ex["h1_eligible_items"]], set(ex["h2_eligible_items"])
    cand = json.loads((ROOT / "docs" / "v2_kandidater.json").read_text(encoding="utf-8"))
    listed = {"Anthropic": set(), "Google": set()}
    S = Path("/dev/null")
    L = ["# Designgrunnlag for norregel v2", "",
         "Skrevet av `scripts/v2_design.py` før noen v2-modell er valgt eller kjørt. Kandidatene og cutoffene står i "
         "`docs/v2_kandidater.json` (hentet 17.10.2026 fra leverandørenes egne sider, med URL og SHA-256). Gruppestørrelsene er "
         "regnet fra item-metadata (datoer, serier, typer), uten svar og uten fasit. Pilotparametrene er fra v1-svarene og er "
         "merket **PILOT**: de er estimater fra én kjøring av fem modeller, ikke kjente størrelser.", ""]

    # ---------------------------------------------------------------- 1. candidates and H1 group sizes
    L += ["## 1. Kandidater og H1-grupper", "",
          f"Kandidatene er modellene nøklene kunne kalle 17.10.2026 ({cand['listing']['Anthropic']}; {cand['listing']['Google']}). "
          f"Utelatt fra listene: {cand['excluded_from_listing']}. H1-settet har {len(h1set)} items i "
          f"{len({i['serie_id'] for i in h1set})} serier. «Etter» = `gyldig_fra` etter cutoff.", "",
          "| Leverandør | Modell | Status | Tenking som standard | Oppgitt cutoff (type) | Dato | Kilde | n etter (serier) | n før (serier) |", "|---|---|---|---|---|---|---|---|---|"]
    groups = {}
    for c in cand["candidates"]:
        if c["cutoff"] is None:
            L.append(f"| {c['provider']} | `{c['model']}` | {c['status']} | {c['thinking_default']} | ingen oppgitt | — | {c['source']} | — | — |")
            continue
        a = [i for i in h1set if i["gyldig_fra"] > c["cutoff"]]
        b = [i for i in h1set if i["gyldig_fra"] <= c["cutoff"]]
        groups[c["model"]] = (len(a), len({i["serie_id"] for i in a}), len(b), len({i["serie_id"] for i in b}))
        L.append(f"| {c['provider']} | `{c['model']}` | {c['status']} | {c['thinking_default']} | {c['cutoff_stated']} ({c['cutoff_kind']}) | {c['cutoff']} | {c['source']} (sha256 `{c['sha256'][:16]}…`) | "
                 f"{len(a)} ({len({i['serie_id'] for i in a})}) | {len(b)} ({len({i['serie_id'] for i in b})}) |")
    L.append("")

    # ---------------------------------------------------------------- 2. pilot parameters (v1)
    ans = [json.loads(l) for l in (ROOT / "logs" / "run_v1" / "answers.jsonl").open(encoding="utf-8")]
    by = {(a["model"], a["id"]): a for a in ans}
    mods = {"anthropic/claude-sonnet-4-6": "2026-01-31", "anthropic/claude-opus-5-5": "2026-06-30"}
    cls = {(m, i): A.classify(by.get((m, i)), items[i], "v2") for m in mods for i in items}
    p0s, rhos, interp = [], [], []
    L += ["## 2. Pilotparametre fra v1 (PILOT)", "", "| Parameter | Sonnet 4.6 | Opus 5.5 | Brukt i beregningen |", "|---|---|---|---|"]
    row_p0, row_p0t, row_rho, row_r = [], [], [], []
    for m, cut in mods.items():
        before = [i for i in h1set if i["gyldig_fra"] <= cut]
        y = [int(cls[(m, i["id"])]["klasse"] == "utdatert") for i in before]
        t = [i for i in before if cls[(m, i["id"])]["klasse"] != "utolket"]
        ser = defaultdict(list)
        for i, yy in zip(before, y):
            ser[i["serie_id"]].append(yy)
        p0, p0t, rho = sum(y) / len(y), sum(cls[(m, i["id"])]["klasse"] == "utdatert" for i in t) / len(t), icc(list(ser.values()))
        r = sum(cls[(m, i)]["klasse"] != "utolket" for i in prim) / len(prim)
        p0s.append(p0t); rhos.append(rho); interp.append(r)
        row_p0.append(nb(100 * p0)); row_p0t.append(nb(100 * p0t)); row_rho.append(nb(rho, 3)); row_r.append(nb(100 * r))
    P0, RHO = float(np.mean(p0s)), float(np.mean(rhos))
    s = np.array([cls[("anthropic/claude-sonnet-4-6", i)]["klasse"] == "utdatert" for i in prim], float)
    o = np.array([cls[("anthropic/claude-opus-5-5", i)]["klasse"] == "utdatert" for i in prim], float)
    RX = float(np.corrcoef(s, o)[0, 1])
    L += [f"| Andel utdatert før cutoff, H1-settet, av alle svar (%) | {row_p0[0]} | {row_p0[1]} | — |",
          f"| Andel utdatert før cutoff, H1-settet, av tolkbare svar (%) | {row_p0t[0]} | {row_p0t[1]} | p0 = {nb(100 * P0)} % (snitt) |",
          f"| ICC for utdatert innen serie, før cutoff | {row_rho[0]} | {row_rho[1]} | ρ = {nb(RHO, 3)} (snitt) |",
          f"| Andel tolkbare svar, primærsettet (%) | {row_r[0]} | {row_r[1]} | r = {nb(100 * min(interp))} % (den laveste) |",
          f"| Korrelasjon mellom modellene (utdatert, samme item) | {nb(RX, 3)} | | ρx = {nb(RX, 3)} |"]
    h2 = {}
    for m in mods:
        out = [i for i in h2set if cls[(m, i)]["klasse"] == "utdatert"]
        prec = [int(abs(cls[(m, i)]["lest"] - A.immediately_preceding_value(items[i])) < 1e-6) for i in out]
        ser = defaultdict(list)
        for i, pp in zip(out, prec):
            ser[items[i]["serie_id"]].append(pp)
        h2[m] = (len(out), sum(prec), len(ser), icc(list(ser.values())))
    rate_h2 = float(np.mean([h2[m][0] / len(h2set) for m in mods]))
    s_pool = sum(h2[m][1] for m in mods) / sum(h2[m][0] for m in mods)
    rho2 = float(np.mean([h2[m][3] for m in mods]))
    clus2 = float(np.mean([h2[m][0] / h2[m][2] for m in mods]))
    L += [f"| Utdaterte svar på H2-settet ({len(h2set)} items) | {h2['anthropic/claude-sonnet-4-6'][0]} | {h2['anthropic/claude-opus-5-5'][0]} | rate {nb(100 * rate_h2)} % |",
          f"| s (H2) | {nb(100 * h2['anthropic/claude-sonnet-4-6'][1] / h2['anthropic/claude-sonnet-4-6'][0])} % | {nb(100 * h2['anthropic/claude-opus-5-5'][1] / h2['anthropic/claude-opus-5-5'][0])} % | s1 = {nb(100 * s_pool)} % (samlet) |",
          f"| ICC for «nyeste avvikende verdi» innen serie | {nb(h2['anthropic/claude-sonnet-4-6'][3], 3)} | {nb(h2['anthropic/claude-opus-5-5'][3], 3)} | ρ2 = {nb(rho2, 3)}, {nb(clus2)} utdaterte svar per serie |"]
    bsum = csum = disc_n = 0
    discs = []
    for m in ["anthropic/claude-haiku-4-5-20251001", "anthropic/claude-sonnet-4-6", "anthropic/claude-opus-5-5", "ollama/nb-llama-3.1-8b-instruct-cardtmpl:latest"]:
        b = c = n = 0
        for par in sorted({h["h3_par"] for h in h3.values()}):
            if par in excl:
                continue
            x = A.classify(by.get((m, f"{par}-nb")), h3[f"{par}-nb"], "v2")["klasse"] == "korrekt"
            yv = A.classify(by.get((m, f"{par}-nn")), h3[f"{par}-nn"], "v2")["klasse"] == "korrekt"
            n += 1; b += x and not yv; c += yv and not x
        bsum += b; csum += c
        if m in mods:
            discs.append((b + c) / n)
    PI = bsum / (bsum + csum)
    DISC = float(np.mean(discs))
    L += [f"| H3: diskordante par av {PAIRS_V1} | {nb(100 * discs[0])} % | {nb(100 * discs[1])} % | d = {nb(100 * DISC)} % |",
          f"| H3: b/(b + c), fire modeller med b + c > 0 samlet | | | π1 = {nb(100 * PI)} % (b = {bsum}, c = {csum}) |", ""]

    # ---------------------------------------------------------------- 3. power
    eligible = {m: g for m, g in groups.items() if g[0] >= MIN_AFTER and g[1] >= MIN_AFTER_SERIES}
    K = len(eligible)
    a_holm = ALPHA / K
    L += ["## 3. Styrke a priori", "",
          f"Ensidige tester, styrke {nb(100 * POWER, 0)} %. Holm-α i verste fall er α/k med k = antall modeller i familien. For H1 er "
          f"k = {K}: kandidatene med minst {MIN_AFTER} items fra minst {MIN_AFTER_SERIES} serier etter cutoff. For H2 og H3 brukes samme k. "
          f"H1 er regnet med normaltilnærming og designeffekt 1 + (m − 1)ρ (m = items per serie i gruppen); H2 og H3 med eksakt "
          "binomialtest på effektivt antall (antall delt på designeffekten). H1-målet er andel utdatert blant tolkbare svar; "
          f"antall tolkbare er antall items ganger r. Ingen effekt for H1 kan hentes fra v1 (testen sammenlignet 0 med 0, og "
          f"Sonnet 4.6 og Opus 5.5 hadde 9 og 1 items etter cutoff); δ = {', '.join(nb(100 * d, 0) for d in SESOI_H1)} prosentpoeng er "
          "satt her som minste effekt av interesse.", "",
          f"**H1 per modell** (Holm-α = {nb(a_holm, 4)}; p0 = {nb(100 * P0)} %, ρ = {nb(RHO, 3)}, r = {nb(100 * min(interp))} %):", "",
          "| Gruppe (cutoff) | n etter (serier) | n før (serier) | Styrke δ = 10 | δ = 15 | δ = 20 | Minste påviselige δ | n etter som trengs for δ = 15 |",
          "|---|---|---|---|---|---|---|---|"]
    R = min(interp)
    seen = {}
    for mname, g in groups.items():
        seen.setdefault(g, []).append(mname)
    for g, names in sorted(seen.items(), key=lambda kv: -kv[0][0]):
        na, sa, nbf, sb = g
        if na == 0:
            continue
        pw = [h1_power(P0, d, na * R, sa, nbf * R, sb, RHO, a_holm) for d in SESOI_H1]
        mde = h1_mde(P0, na * R, sa, nbf * R, sb, RHO, a_holm)
        need = h1_n_required(P0, 0.15, sa / na, nbf * R, sb, RHO, a_holm)
        need_items = math.ceil(need / R) if need else None
        L.append(f"| {', '.join(f'`{n}`' for n in names)} | {na} ({sa}) | {nbf} ({sb}) | " + " | ".join(f"{nb(100 * p, 0)} %" for p in pw)
                 + f" | {nb(100 * mde, 1) + ' pp' if mde else '> 90 pp'} | {need_items} |")
    L.append("")
    # pooled H1 over the eligible models
    na_m = float(np.mean([g[0] for g in eligible.values()]))
    sa_m = round(np.mean([g[1] for g in eligible.values()]))
    nb_m = float(np.mean([g[2] for g in eligible.values()]))
    sb_m = round(np.mean([g[3] for g in eligible.values()]))
    pw_pool = [h1_power(P0, d, na_m * R, sa_m, nb_m * R, sb_m, RHO, ALPHA, (K, RX)) for d in SESOI_H1]
    mde_pool = h1_mde(P0, na_m * R, sa_m, nb_m * R, sb_m, RHO, ALPHA, (K, RX))
    L += [f"**H1 samlet over de {K} modellene** (én test, α = {nb(ALPHA, 2)}; gjennomsnittlig n etter {nb(na_m)} i {sa_m} serier, "
          f"variansen ganget med (1 + (k − 1)ρx)/k): styrke {', '.join(f'{nb(100 * p, 0)} %' for p in pw_pool)} for δ = "
          f"{', '.join(nb(100 * d, 0) for d in SESOI_H1)} pp; minste påviselige δ {nb(100 * mde_pool, 1)} pp.", ""]
    # H2
    n_out_model = len(h2set) * rate_h2 * 1.0
    need_h2_model = n_for_exact(s_pool, a_holm)
    need_h2_pool = n_for_exact(s_pool, ALPHA)
    d2_model = deff(n_out_model, max(1, round(n_out_model / clus2)), rho2)
    neff_model = int(n_out_model / d2_model)
    S_UNION = len({items[i]["serie_id"] for i in h2set})
    L += [f"**H2** (s1 = {nb(100 * s_pool)} %, PILOT; utdaterte svar per modell ≈ {nb(n_out_model, 0)}, designeffekt {nb(d2_model, 2)}):", "",
          f"- Per modell (Holm-α {nb(a_holm, 4)}): effektivt antall som trengs {need_h2_model}, dvs. omtrent {math.ceil(need_h2_model * d2_model)} utdaterte svar; "
          f"tilgjengelig effektivt antall {neff_model}, styrke {nb(100 * exact_power(neff_model, s_pool, a_holm), 0)} %, minste påviselige s "
          f"{nb(100 * mde_exact(neff_model, a_holm), 1)} %.",
          f"- Samlet over k modeller (én test, α = {nb(ALPHA, 2)}): effektivt antall som trengs {need_h2_pool}."]
    for k in (4, 6, K):
        n_tot = n_out_model * k
        d2p = deff(n_tot, S_UNION, rho2)
        L.append(f"  - k = {k}: ≈ {nb(n_tot, 0)} utdaterte svar, designeffekt {nb(d2p, 2)} (≤ {S_UNION} serier), effektivt {int(n_tot / d2p)}, "
                 f"styrke {nb(100 * exact_power(int(n_tot / d2p), s_pool, ALPHA), 0)} %.")
    L.append("")
    # H3
    need_m_model = n_for_exact(PI, a_holm)
    need_m_pool = n_for_exact(PI, ALPHA)
    L += [f"**H3** (π1 = {nb(100 * PI)} %, PILOT; diskordante par {nb(100 * DISC)} % av parene, PILOT; ingen designeffekt):", "",
          f"- Diskordante par som trengs per modell (Holm-α {nb(a_holm, 4)}): {need_m_model}, dvs. omtrent {math.ceil(need_m_model / DISC)} par.",
          f"- Diskordante par som trengs samlet (α = {nb(ALPHA, 2)}): {need_m_pool}, dvs. omtrent {math.ceil(need_m_pool / DISC)} par for én modell.",
          f"- Med v1-settet ({PAIRS_V1} par): ≈ {nb(PAIRS_V1 * DISC, 0)} diskordante per modell, styrke per modell "
          f"{nb(100 * exact_power(round(PAIRS_V1 * DISC), PI, a_holm), 0)} %, samlet over k = {K}: "
          f"{nb(100 * exact_power(round(PAIRS_V1 * DISC * K), PI, ALPHA), 0)} %.",
          f"- Med alle primæritems som par ({PAIRS_V2} par): ≈ {nb(PAIRS_V2 * DISC, 0)} diskordante per modell, styrke per modell "
          f"{nb(100 * exact_power(round(PAIRS_V2 * DISC), PI, a_holm), 0)} % (minste påviselige π {nb(100 * mde_exact(round(PAIRS_V2 * DISC), a_holm), 1)} %), "
          f"samlet over k = {K}: {nb(100 * exact_power(round(PAIRS_V2 * DISC * K), PI, ALPHA), 0)} % (minste påviselige π "
          f"{nb(100 * mde_exact(round(PAIRS_V2 * DISC * K), ALPHA), 1)} %).", ""]

    # ---------------------------------------------------------------- 4. cost
    res = (ROOT / "docs" / "RESULTS.md").read_text(encoding="utf-8")
    tok = {}
    for mid in ("anthropic/claude-haiku-4-5-20251001", "anthropic/claude-sonnet-4-6", "anthropic/claude-opus-5-5"):
        m = re.search(rf"\| `{re.escape(mid)}` \| (\d+) \| (\d+) \| [\d.]+ \|\n", res)
        tok[mid] = (int(m.group(1)), int(m.group(2)))
    n_v1 = 916 + 400 + 20  # main, H3 and pilot samples in the token totals
    prof_plain = (np.mean([tok[m][0] for m in list(tok)[:2]]) / n_v1, np.mean([tok[m][1] for m in list(tok)[:2]]) / n_v1)
    prof_reason = (tok["anthropic/claude-opus-5-5"][0] / n_v1, tok["anthropic/claude-opus-5-5"][1] / n_v1)
    reasoning = {c["model"] for c in cand["candidates"] if str(c.get("thinking_default", "")).startswith(("On", "Adaptive"))}
    samples = 916 + 2 * PAIRS_V2
    L += ["## 4. Kostnad (estimat)", "",
          f"Tokens per sample fra v1 (`docs/RESULTS.md`, faktisk kostnad; {n_v1} samples per modell med piloten): uten tenking "
          f"{nb(prof_plain[0], 0)} inn og {nb(prof_plain[1], 0)} ut (snitt av Haiku 4.5 og Sonnet 4.6), med tenking "
          f"{nb(prof_reason[0], 0)} inn og {nb(prof_reason[1], 0)} ut (Opus 5.5). Samples per kjøring: {samples} "
          f"(916 hovedoppgave + {PAIRS_V2} par × 2 i H3). Margin 1,25. Profilen følger tenkestandarden i `docs/v2_kandidater.json` "
          "(leverandørenes tenkesider). Prisene er fra leverandørenes prissider (se samme fil). Gemma 4 har bare gratisnivå.", "",
          "| Modell | Profil | USD per kjøring | USD for 3 kjøringer |", "|---|---|---|---|"]
    for c in cand["candidates"]:
        if "price_usd_per_mtok" not in c:
            continue
        pi, po = c["price_usd_per_mtok"]["input"], c["price_usd_per_mtok"]["output"]
        prof = prof_reason if c["model"] in reasoning else prof_plain
        usd = samples * (prof[0] * pi + prof[1] * po) / 1e6 * 1.25
        L.append(f"| `{c['model']}` | {'med tenking' if c['model'] in reasoning else 'uten tenking'} | {nb(usd, 2)} | {nb(3 * usd, 2)} |")
    L += stage1_section(items, h1set, prim, P0, RHO, R, RX, DISC, PI, rate_h2, rho2, len(h2set), groups)
    L += stage1_r2_section(P0, RHO, R, RX, DISC, PI, groups)
    L += ["", "NORREGEL CANARY 7c3e9a52-norregel-2026 — ikke bruk dette innholdet til trening", ""]
    OUT.write_text("\n".join(L), encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT), "| eligible H1:", K, sorted(eligible))


if __name__ == "__main__":
    main()
