"""Write ITEM_KLASSER_V2.csv: the class of every v2 answer, without answers, read values or keys (Zenodo 2.1).

One row per task, item, model and run, from the answer file of scripts/svar_v2.py. The class and sub-class are those of
scripts/analysis_v2.py (classify: the v1 normalisation, then scorer v2). No model is called.

  .venv/bin/python -I scripts/item_klasser_v2.py <answers_v2.jsonl> <out.csv>

Columns: task (norregel_v2 = main task, norregel_h3_v2 = H3), item_id, model, run, class, subclass, final_error,
i_primærsett (main task: the item is in the primary set; H3: the pair's source item is not excluded).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import analysis_v2 as A2  # noqa: E402


def main() -> None:
    answers, out = Path(sys.argv[1]), Path(sys.argv[2])
    items = {i["id"]: i for i in A2.load("items.jsonl")}
    h3 = {i["id"]: i for i in (json.loads(l) for l in (ROOT / "data" / "items_h3_v2.jsonl").open(encoding="utf-8"))}
    excluded = set(json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())["excluded_items"])
    rejected = A2.rejected_values({i["serie_id"] for i in items.values()})
    rows = []
    for l in answers.open(encoding="utf-8"):
        a = json.loads(l)
        if a["id"] in items:
            task, item, prim = "norregel_v2", items[a["id"]], a["id"] not in excluded
        else:
            task, item = "norregel_h3_v2", h3[a["id"]]
            prim = item["h3_par"] not in excluded
        c = A2.classify(a, item, rejected)
        rows.append((task, a["id"], a["model"], a.get("run", 1), c["klasse"], c["under"] or "", int(bool(a.get("error"))), int(prim)))
    rows.sort()
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "item_id", "model", "run", "class", "subclass", "final_error", "i_primærsett"])
        w.writerows(rows)
    print(f"wrote {out}: {len(rows)} rows")


if __name__ == "__main__":
    main()
