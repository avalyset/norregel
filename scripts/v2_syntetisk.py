"""Synthetic answers for a dry run of scripts/analysis_v2.py (proves that it runs; no model is called).

Writes, into the directory given as the first argument (outside the repository, because the answers are built from the
keys): answers_v2_syntetisk.jsonl for the models in docs/v2_modeller.json, with the number of runs per model, a control
run of 100 items for the models with R = 1, and answers to the locked H3 set data/items_h3_v2.jsonl. Outcomes are drawn with a fixed seed;
after a model's cutoff, outdated answers and refusals are more frequent, so that H1 has an effect to find.

  .venv/bin/python -I scripts/v2_syntetisk.py <out-dir>
"""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fmt(v: float) -> str:
    return f"{v:.10g}".replace(".", ",")


def answer(item: dict, kind: str, rnd: random.Random) -> tuple[str, bool]:
    earlier = [h["verdi"] for h in item["verdihistorikk"] if h["gyldig_fra"] < item["gyldig_fra"] and abs(h["verdi"] - item["fasitverdi"]) >= 1e-6]
    if kind == "utdatert" and earlier:
        return f"Verdien var lavere før.\nSVAR: {fmt(earlier[-1] if rnd.random() < 0.6 else rnd.choice(earlier))}", False
    if kind == "feil" or (kind == "utdatert" and not earlier):
        return f"SVAR: {fmt(round(item['fasitverdi'] * 1.37 + 1, 2))}", False
    if kind == "korrekt":
        return f"SVAR: {fmt(item['fasitverdi'])}", False
    if kind == "avslag":
        return "Jeg har ikke tilgang til denne opplysningen.\nSVAR: Vet ikke", False
    if kind == "ingen_linje":
        return "Beløpet står i forskriften.", False
    if kind == "flere":
        return "SVAR: 10 eller 20", False
    return "", True  # endelig feil


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    items = [json.loads(l) for l in (ROOT / "data" / "items.jsonl").open(encoding="utf-8")]
    ex = json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())
    prim = [i for i in items if i["id"] not in set(ex["excluded_items"])]
    pairs = [json.loads(l) for l in (ROOT / "data" / "items_h3_v2.jsonl").open(encoding="utf-8")]  # the locked H3 set
    models = json.loads((ROOT / "docs" / "v2_modeller.json").read_text(encoding="utf-8"))
    rnd = random.Random(20261117)
    n = 0
    with (out / "answers_v2_syntetisk.jsonl").open("w", encoding="utf-8") as f:
        for m in models:
            control = set(random.Random(20261118).sample(sorted(i["id"] for i in prim), 100))  # control run for R = 1 (PREREG_V2 6.4)
            for run in range(1, m["runs"] + 1 + (1 if m["runs"] == 1 else 0)):
                for it in items + pairs:
                    if run > m["runs"] and it["id"] not in control:
                        continue
                    after = bool(m["cutoff"]) and it["gyldig_fra"] > m["cutoff"]
                    w = ({"korrekt": 0.15, "utdatert": 0.35, "feil": 0.2, "avslag": 0.25, "ingen_linje": 0.03, "flere": 0.01, "error": 0.01} if after else
                         {"korrekt": 0.45, "utdatert": 0.08, "feil": 0.35, "avslag": 0.08, "ingen_linje": 0.02, "flere": 0.01, "error": 0.01})
                    if it["id"].endswith("-nn") and rnd.random() < 0.05:
                        w = dict(w, korrekt=w["korrekt"] * 0.5)
                    kind = rnd.choices(list(w), weights=list(w.values()))[0]
                    text, err = answer(it, kind, rnd)
                    f.write(json.dumps({"model": m["id"], "id": it["id"], "run": run, "completion": text, "error": err}, ensure_ascii=False) + "\n")
                    n += 1
    print("answers:", n, "| H3 questions:", len(pairs), "| models:", len(models))


if __name__ == "__main__":
    main()
