"""Build the H3 question set of norregel v2: every primary item in both Bokmål and Nynorsk (docs/PREREG_V2.md, section 4).

The questions come from the renderer in scripts/build_items.py, run unchanged in a temporary directory that holds copies
of its inputs, so that no locked file in the repository is written. Before anything is written, two checks must pass:
the run reproduces data/items.jsonl and data/items_h3.jsonl of lock 4 byte for byte (same SHA-256), and the 378 questions
of the 189 primary v1 pairs (the 11 excluded pairs are left out, as all excluded items) are character for character the
locked ones. The result is data/items_h3_v2.jsonl (880 pairs, 1 760 questions), with the fields of data/items_h3.jsonl.
No model is called.

  .venv/bin/python -I scripts/build_h3_v2.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ["data/v3_items.jsonl", "data/candidates.jsonl", "data/yearseries.jsonl", "data/simpleaudit_facts.json", "docs/NAVNGITTE_SATSER.md"]
OUT = ROOT / "data" / "items_h3_v2.jsonl"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_items as BI  # noqa: E402

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        for rel in INPUTS:
            (t / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, t / rel)
        BI.ROOT = t
        captured: dict = {}
        original = BI.build_h3

        def capture(out, both):
            captured["out"], captured["both"] = out, both
            return original(out, both)

        BI.build_h3 = capture
        BI.main()
        for name in ("items.jsonl", "items_h3.jsonl"):
            a, b = sha(t / "data" / name), sha(ROOT / "data" / name)
            if a != b:
                raise SystemExit(f"the renderer does not reproduce data/{name} of lock 4 ({a} vs {b}); nothing written")
        out, both = captured["out"], captured["both"]
    ex = json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())
    excluded = set(ex["excluded_items"])
    pairs = []
    for o in out:
        if o["id"] in excluded:
            continue
        for form in ("nb", "nn"):
            pairs.append({**o, "id": f"{o['id']}-{form}", "h3_par": o["id"], "målform": form, "spørsmål": both[o["id"]][form],
                          "ekstra_språkversjon": form != o["målform"]})
    v1 = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "data" / "items_h3.jsonl").open(encoding="utf-8")}
    same = sum(1 for p in pairs if p["id"] in v1 and p["spørsmål"] == v1[p["id"]]["spørsmål"])
    in_v1 = sum(1 for p in pairs if p["id"] in v1)
    if same != in_v1:
        raise SystemExit(f"v1 pairs differ: {in_v1 - same} questions; nothing written")
    with OUT.open("w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"lock 4 reproduced (items.jsonl and items_h3.jsonl identical); v1 questions in the new set: {in_v1}, identical: {same}; "
          f"wrote {OUT.relative_to(ROOT)}: {len(pairs) // 2} pairs, {len(pairs)} questions, sha256 {sha(OUT)}")


if __name__ == "__main__":
    main()
