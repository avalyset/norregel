"""Apply the model choice criterion of norregel v2 (docs/V2_VALGKRITERIUM.md, committed before this script was run).

Reads docs/v2_kandidater.json, item metadata and, for the pilot parameters and the cost profile, the same v1 inputs as
scripts/v2_design.py. Writes docs/V2_MODELLVALG.md. No model is called.

  .venv/bin/python -I scripts/v2_velg.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import analysis_v1 as A  # noqa: E402
from v2_design import PAIRS_V2, h1_power, icc, nb  # noqa: E402

OUT = ROOT / "docs" / "V2_MODELLVALG.md"
V1 = ["anthropic/claude-haiku-4-5-20251001", "anthropic/claude-sonnet-4-6", "anthropic/claude-opus-5-5",
      "ollama/nb-llama-3.1-8b-instruct-cardtmpl:latest", "ollama/normistral-7b-warm-instruct-cardtmpl:latest"]
CAP = 400.0
NO_TEMPERATURE = {"claude-opus-5-5"}  # rejects sampling parameters (docs/MODELLER.md, migration guide for Opus 5.5)


def pilot(items: dict, h1set: list[dict], prim: list[str]) -> tuple[float, float, float, float]:
    ans = [json.loads(l) for l in (ROOT / "logs" / "run_v1" / "answers.jsonl").open(encoding="utf-8")]
    by = {(a["model"], a["id"]): a for a in ans}
    mods = {"anthropic/claude-sonnet-4-6": "2026-01-31", "anthropic/claude-opus-5-5": "2026-06-30"}
    cls = {(m, i): A.classify(by.get((m, i)), items[i], "v2")["klasse"] for m in mods for i in items}
    p0s, rhos, rs = [], [], []
    for m, cut in mods.items():
        before = [i for i in h1set if i["gyldig_fra"] <= cut]
        t = [i for i in before if cls[(m, i["id"])] != "utolket"]
        p0s.append(sum(cls[(m, i["id"])] == "utdatert" for i in t) / len(t))
        ser = defaultdict(list)
        for i in before:
            ser[i["serie_id"]].append(int(cls[(m, i["id"])] == "utdatert"))
        rhos.append(icc(list(ser.values())))
        rs.append(sum(cls[(m, i)] != "utolket" for i in prim) / len(prim))
    s = np.array([cls[("anthropic/claude-sonnet-4-6", i)] == "utdatert" for i in prim], float)
    o = np.array([cls[("anthropic/claude-opus-5-5", i)] == "utdatert" for i in prim], float)
    return float(np.mean(p0s)), float(np.mean(rhos)), min(rs), float(np.corrcoef(s, o)[0, 1])


def main() -> None:
    items = {i["id"]: i for i in A.load("items.jsonl")}
    ex = json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())
    prim = [i for i in items if i not in set(ex["excluded_items"])]
    h1set = [items[i] for i in ex["h1_eligible_items"]]
    cand = json.loads((ROOT / "docs" / "v2_kandidater.json").read_text(encoding="utf-8"))
    P0, RHO, R, RX = pilot(items, h1set, prim)
    res = (ROOT / "docs" / "RESULTS.md").read_text(encoding="utf-8")
    tok = {m: tuple(int(x) for x in re.search(rf"\| `{re.escape(m)}` \| (\d+) \| (\d+) \| [\d.]+ \|\n", res).groups()) for m in V1[:3]}
    n_v1 = 916 + 400 + 20
    plain = (np.mean([tok[m][0] for m in V1[:2]]) / n_v1, np.mean([tok[m][1] for m in V1[:2]]) / n_v1)
    reason = (tok[V1[2]][0] / n_v1, tok[V1[2]][1] / n_v1)
    samples = 916 + 2 * PAIRS_V2

    def cost(c: dict) -> tuple[float, int, bool]:
        thinking = str(c["thinking_default"]).startswith(("On", "Adaptive"))
        runs = 3 if (thinking or c["model"] in NO_TEMPERATURE) else 1
        pi, po = c["price_usd_per_mtok"]["input"], c["price_usd_per_mtok"]["output"]
        prof = reason if thinking else plain
        one = samples * (prof[0] * pi + prof[1] * po) / 1e6 * 1.25
        control = 0.0 if runs == 3 else one * 100 / samples
        pilot_cost = one * 20 / samples
        return runs * one + control + pilot_cost, runs, thinking

    rows, h1 = [], []
    for c in cand["candidates"]:
        why = []
        if c["cutoff"] is None:
            why.append("K2a: ingen oppgitt cutoff")
        if not c.get("callable") or "latest" in c["model"]:
            why.append("K2b: ikke kallbar fast id")
        if c["status"].startswith(("Deprecated", "Preview")):
            why.append(f"K2c: status {c['status']}")
        if c["cutoff"]:
            a = [i for i in h1set if i["gyldig_fra"] > c["cutoff"]]
            b = [i for i in h1set if i["gyldig_fra"] <= c["cutoff"]]
            g = (len(a), len({i["serie_id"] for i in a}), len(b), len({i["serie_id"] for i in b}))
            if not (g[0] >= 30 and g[1] >= 20 and g[2] >= 30 and g[3] >= 5):
                why.append(f"K2d: {g[0]} items fra {g[1]} serier etter cutoff")
        else:
            g = None
        is_h1 = not why
        if is_h1:
            h1.append((c, g))
        rows.append((c, g, is_h1, why))
    providers = {c["provider"] for c, _ in h1}
    k = len(h1)
    na = float(np.mean([g[0] for _, g in h1])); sa = round(np.mean([g[1] for _, g in h1]))
    nbf = float(np.mean([g[2] for _, g in h1])); sb = round(np.mean([g[3] for _, g in h1]))
    pw = h1_power(P0, 0.10, na * R, sa, nbf * R, sb, RHO, 0.05, (k, RX))
    chosen = {c["inspect_id"]: c for c, _ in h1}
    for mid in V1:
        if mid.startswith("anthropic/") and mid not in chosen:
            chosen[mid] = next(c for c in cand["candidates"] if c["inspect_id"] == mid)
    total = 0.0
    costs = {}
    for mid, c in chosen.items():
        if "price_usd_per_mtok" in c:
            costs[mid] = cost(c)
            total += costs[mid][0]
    k3, k4, k6 = pw >= 0.80, len(providers) >= 2, total < CAP
    L = ["# Modellvalg for norregel v2", "",
         f"Skrevet av `scripts/v2_velg.py`, som bruker kriteriet i `docs/V2_VALGKRITERIUM.md` (committet før skriptet ble kjørt). "
         f"Pilotparametre fra v1 (PILOT): p0 = {nb(100 * P0)} %, ρ = {nb(RHO, 3)}, r = {nb(100 * R)} %, ρx = {nb(RX, 3)}.", "",
         "## Kandidatene", "", "| Leverandør | Modell | Cutoff | n etter (serier) | H1-modell | Grunn |", "|---|---|---|---|---|---|"]
    for c, g, is_h1, why in rows:
        L.append(f"| {c['provider']} | `{c['model']}` | {c['cutoff'] or '—'} | {f'{g[0]} ({g[1]})' if g else '—'} | {'ja' if is_h1 else 'nei'} | "
                 f"{'; '.join(why) if why else 'K2 a–d oppfylt'} |")
    L += ["", "## Kriteriene", "",
          f"- **K1:** de fem v1-modellene er med.",
          f"- **K2:** {k} H1-modeller.",
          f"- **K3:** samlet H1-styrke for δ = 10 pp ved α = 0,05 med k = {k} (gjennomsnittlig n etter {nb(na)} i {sa} serier, n før {nb(nbf)} i "
          f"{sb} serier): {nb(100 * pw, 1)} %. {'Oppfylt.' if k3 else 'Ikke oppfylt: H1 er ikke testbar i v2.'}",
          f"- **K4:** leverandører blant H1-modellene: {', '.join(sorted(providers))}. {'Oppfylt.' if k4 else 'Ikke oppfylt.'}",
          "- **K5:** ingen andre modeller.",
          f"- **K6:** fremskrevet kostnad {nb(total, 2)} USD (tak {nb(CAP, 0)} USD). {'Under taket; ingen modell tas ut.' if k6 else 'Over taket.'}", "",
          "## Valgte modeller (K7-rekkefølge)", "", "| # | Inspect-id | Rolle | Cutoff | Tenking som standard | R | Fremskrevet USD |", "|---|---|---|---|---|---|---|"]
    order = sorted(chosen.values(), key=lambda c: (c["provider"], c["cutoff"] or "9999", c["model"]))
    n = 0
    for c in order:
        n += 1
        role = "v1 og H1" if c["inspect_id"] in V1 and c["inspect_id"] in {x["inspect_id"] for x, _ in h1} else ("v1" if c["inspect_id"] in V1 else "H1")
        cc = costs.get(c["inspect_id"])
        L.append(f"| {n} | `{c['inspect_id']}` | {role} | {c['cutoff']} | {c['thinking_default']} | {cc[1] if cc else 1} | {nb(cc[0], 2) if cc else '—'} |")
    for mid in V1[3:]:
        n += 1
        L.append(f"| {n} | `{mid}` | v1 (lokal) | ukjent | nei | 1 | 0,00 |")
    L += ["", "NORREGEL CANARY 7c3e9a52-norregel-2026 — ikke bruk dette innholdet til trening", ""]
    if not (k4 and k6):
        L.insert(2, "**Valget stopper (K4 eller K6 er ikke oppfylt).**\n")
    OUT.write_text("\n".join(L), encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT), "| H1:", k, "| power", round(pw, 3), "| cost", round(total, 2), "| models", len(order) + 2)


if __name__ == "__main__":
    main()
