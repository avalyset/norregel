"""Apply the three pilot rules of norregel v2 (docs/PREREG_V2.md, sections 6.3, 6.9 and 9). No model is called.

Reads the pilot logs in <pilot-root>/<model dir>/ (written by `scripts/run_v2.sh pilot`) and docs/v2_modeller.json, and
writes <out> (JSON) and the same decisions as Markdown next to it. scripts/run_v2.sh and scripts/svar_v2.py read the JSON.

1. Temperature: if the provider rejected temperature 0 in the pilot, run_v2.sh has written the file TEMPERATUR_AVVIST in
   the model's pilot directory and run the pilot again without temperature. The model then runs without temperature and
   gets R = 3.
2. Thinking for Gemma 4: if the complete pilot log of a Gemma 4 model counts reasoning tokens (> 0), the model gets R = 3.
3. Cost: projected cost = actual pilot cost + for each API model the pilot cost per sample x the planned samples
   (R x (916 + 1 760), plus 100 for the control run when R = 1) x 1.25. If it is above the cap of 400 USD, H1 models that
   are not v1 models are taken out one at a time in falling projected cost, as long as K3 (pooled H1 power >= 80 % for
   delta = 10 pp with the PILOT parameters of section 8) and K4 (H1 models from at least two providers) still hold
   (docs/V2_VALGKRITERIUM.md, K6). If the cost is still above the cap, `fortsett` is false and the run stops for the
   author's decision.

Google rule (section 10, from docs/V2_FORHAANDSKONTROLL.md): Gemma 4 is kept only with `google_eos: ja`, Gemini 2.5 only
with `google_eos: ja` or `google_betalt: ja`; a model taken out on this rule needs no pilot and is listed as a deviation.

An API model without a complete pilot log (status success, the 20 pilot ids) also gives `fortsett` = false: the pilot is
then run again under the restart rule of the v1 protocol, section 3.4. The local models are piloted for timing only.

  .venv/bin/python -I scripts/pilot_regler_v2.py [--pilot-root logs/run_v2/_pilot] [--out logs/run_v2/pilot_utfall.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import kostnad_v2 as K  # noqa: E402
from v2_design import h1_power  # noqa: E402

P0, RHO, R_INT, RX = 0.099, 0.243, 0.876, 0.137  # PILOT parameters, docs/PREREG_V2.md section 8
N_MAIN, N_H3, N_CONTROL, N_PILOT, MARGIN = 916, 1760, 100, 20, 1.25
V1 = {"anthropic/claude-haiku-4-5-20251001", "anthropic/claude-sonnet-4-6", "anthropic/claude-opus-5-5",
      "ollama/nb-llama-3.1-8b-instruct-cardtmpl:latest", "ollama/normistral-7b-warm-instruct-cardtmpl:latest"}


def safe_dir(model_id: str) -> str:
    return model_id.replace("/", "__").replace(":", "_")


def groups(models: list[dict]) -> dict[str, tuple[int, int, int, int]]:
    """H1 groups from item metadata: (n after, series after, n before, series before) per H1 model."""
    items = {i["id"]: i for i in (json.loads(l) for l in (ROOT / "data" / "items.jsonl").open(encoding="utf-8"))}
    h1set = [items[i] for i in json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())["h1_eligible_items"]]
    out = {}
    for m in models:
        if m["h1"]:
            a = [i for i in h1set if i["gyldig_fra"] > m["cutoff"]]
            b = [i for i in h1set if i["gyldig_fra"] <= m["cutoff"]]
            out[m["id"]] = (len(a), len({i["serie_id"] for i in a}), len(b), len({i["serie_id"] for i in b}))
    return out


def google_fields() -> dict[str, str]:
    f = ROOT / "docs" / "V2_FORHAANDSKONTROLL.md"
    out = {}
    for l in f.read_text(encoding="utf-8").splitlines() if f.exists() else []:
        if l.startswith("- google_"):
            k, v = l[2:].split(":", 1)
            out[k.strip()] = v.strip().lower()
    return out


def google_out(mid: str, g: dict[str, str]) -> bool:
    if not mid.startswith("google/"):
        return False
    eos, paid = g.get("google_eos") == "ja", g.get("google_betalt") == "ja"
    return not eos if "gemma-4" in mid else not (eos or paid)


def k3(ids: list[str], g: dict) -> float:
    na = float(np.mean([g[m][0] for m in ids])); sa = round(np.mean([g[m][1] for m in ids]))
    nbf = float(np.mean([g[m][2] for m in ids])); sb = round(np.mean([g[m][3] for m in ids]))
    return h1_power(P0, 0.10, na * R_INT, sa, nbf * R_INT, sb, RHO, 0.05, (len(ids), RX))


def main() -> None:
    from inspect_ai.log import read_eval_log
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot-root", default="logs/run_v2/_pilot")
    ap.add_argument("--out", default="logs/run_v2/pilot_utfall.json")
    a = ap.parse_args()
    root, out = (ROOT / a.pilot_root).resolve(), (ROOT / a.out).resolve()
    models = json.loads((ROOT / "docs" / "v2_modeller.json").read_text(encoding="utf-8"))
    pilot_ids = set((ROOT / "data" / "pilot_ids.txt").read_text().split())
    cost = K.collect([root])
    per_file = {f["fil"]: f for f in cost["filer"]}
    res, avvik, stop = [], [], []
    gf = google_fields()
    for m in models:
        d = root / safe_dir(m["id"])
        e = {"id": m["id"], "temperature0": m["temperature0"], "runs": m["runs"], "tatt_ut": False, "grunn": None,
             "pilot_komplett": False, "pilot_logg": None, "usd_per_sample": None, "reasoning_tokens": None, "fremskrevet_usd": 0.0}
        if google_out(m["id"], gf):
            e["tatt_ut"], e["grunn"] = True, "Google-regelen i avsnitt 10 er ikke oppfylt"
            avvik.append(f"{m['id']}: tatt ut fordi Google-regelen i avsnitt 10 ikke er oppfylt (EØS: {gf.get('google_eos') or '—'}, "
                         f"betalt: {gf.get('google_betalt') or '—'})")
            res.append(e)
            continue
        if (d / "TEMPERATUR_AVVIST").exists():
            e["temperature0"], e["runs"] = False, 3
            avvik.append(f"{m['id']}: leverandøren avviste temperatur 0 i piloten; kjøres uten temperatur med R = 3 (6.3)")
        complete = None
        for p in sorted(d.glob("*.eval")) if d.exists() else []:
            lg = read_eval_log(str(p), header_only=False)
            if lg.status == "success" and {str(s.id) for s in lg.samples or []} == pilot_ids:
                complete = (p, lg)  # the last complete pilot log counts (after a temperature rejection: the run without it)
        if complete:
            p, lg = complete
            e["pilot_komplett"], e["pilot_logg"] = True, p.name
            mu = (lg.stats.model_usage or {}) if lg.stats else {}
            e["reasoning_tokens"] = sum((u.reasoning_tokens or 0) for u in mu.values())
            if "gemma-4" in m["id"] and e["reasoning_tokens"] > 0:
                e["runs"] = 3
                avvik.append(f"{m['id']}: piloten talte {e['reasoning_tokens']} tenketokens; R = 3 (6.3)")
            f = next((x for k, x in per_file.items() if k.endswith(p.name)), None)
            if f and not m["id"].startswith("ollama/"):
                e["usd_per_sample"] = f["usd"] / N_PILOT
                planned = e["runs"] * (N_MAIN + N_H3) + (N_CONTROL if e["runs"] == 1 else 0)
                e["fremskrevet_usd"] = e["usd_per_sample"] * planned * MARGIN
        elif not m["id"].startswith("ollama/"):
            stop.append(f"{m['id']}: ingen komplett pilotlogg")
        res.append(e)
    by = {e["id"]: e for e in res}
    g = groups(models)
    h1 = [m["id"] for m in models if m["h1"]]
    total = cost["usd"] + sum(e["fremskrevet_usd"] for e in res)
    removed = []
    if total > K.CAP:
        for mid in sorted((x for x in h1 if x not in V1), key=lambda x: -by[x]["fremskrevet_usd"]):
            if total <= K.CAP:
                break
            rest = [x for x in h1 if x != mid and not by[x]["tatt_ut"]]
            if k3(rest, g) < 0.80 or len({x.split("/")[0] for x in rest}) < 2:
                continue
            by[mid]["tatt_ut"], by[mid]["grunn"] = True, f"K6: fremskrevet kostnad {total:.2f} USD over taket"
            total -= by[mid]["fremskrevet_usd"]
            removed.append(mid)
            avvik.append(f"{mid}: tatt ut etter K6 (fremskrevet {by[mid]['fremskrevet_usd']:.2f} USD)")
    if total > K.CAP:
        stop.append(f"fremskrevet kostnad {total:.2f} USD er over taket {K.CAP:.0f} USD etter K6")
    rest = [x for x in h1 if not by[x]["tatt_ut"]]
    report = {"pilot_usd": cost["usd"], "fremskrevet_usd": total, "tak_usd": K.CAP, "k3_styrke": k3(rest, g),
              "h1_modeller": rest, "tatt_ut": removed, "avvik": avvik, "stopp": stop, "fortsett": not stop, "modeller": res}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# Pilotutfall v2", "", f"Skrevet av `scripts/pilot_regler_v2.py`. Pilotkostnad {cost['usd']:.2f} USD; fremskrevet totalt "
         f"{total:.2f} USD (tak {K.CAP:.0f}). K3 for de gjenværende H1-modellene: {100 * report['k3_styrke']:.1f} %. "
         f"Fortsett: {'ja' if not stop else 'nei'}.", "", "| Modell | Pilot komplett | Temperatur 0 | R | Tenketokens | USD per sample | Fremskrevet USD | Tatt ut |",
         "|---|---|---|---|---|---|---|---|"]
    for e in res:
        rt = "—" if e["reasoning_tokens"] is None else str(e["reasoning_tokens"])
        ups = "—" if e["usd_per_sample"] is None else f"{e['usd_per_sample']:.5f}"
        L.append(f"| `{e['id']}` | {'ja' if e['pilot_komplett'] else 'nei'} | {'ja' if e['temperature0'] else 'nei'} | {e['runs']} | "
                 f"{rt} | {ups} | {e['fremskrevet_usd']:.2f} | {e['grunn'] or 'nei'} |")
    L += ["", "**Avvik:** " + ("; ".join(avvik) if avvik else "ingen"), "", "**Stopp:** " + ("; ".join(stop) if stop else "ingen"), ""]
    out.with_suffix(".md").write_text("\n".join(L), encoding="utf-8")
    print(f"pilot {cost['usd']:.2f} USD; projected {total:.2f} USD; removed {removed}; deviations {len(avvik)}; continue {not stop}")
    sys.exit(0 if not stop else 1)


if __name__ == "__main__":
    main()
