"""Write docs/LOCK_V2.md: SHA-256 of the v2 preregistration, the code and every input the v2 runs and analysis depend on
(docs/PREREG_V2.md, top). No model is called.

  .venv/bin/python -I scripts/lock_v2.py           write docs/LOCK_V2.md
  .venv/bin/python -I scripts/lock_v2.py --check   exit 1 unless every file in docs/LOCK_V2.md has the locked SHA-256
                                                   (scripts/run_v2.sh runs this before any call)
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GROUPS = {
    "Preregistrering": ["docs/PREREG_V2.md"],
    "Kjøring": ["scripts/run_v2.sh", "scripts/pilot_regler_v2.py", "scripts/kostnad_v2.py", "scripts/cost_usage.py",
                "scripts/ollama_preflight_v2.py"],
    "Analyse, svarfil og rapport": ["scripts/analysis_v2.py", "scripts/svar_v2.py", "scripts/rapport_v2.py",
                                    "scripts/norm_aar_maaneder.py", "src/norregel/score_v2.py", "src/norregel/score.py",
                                    "scripts/analysis_v1.py"],
    "Oppgave og H3-sett": ["src/norregel/inspect_task_v2.py", "src/norregel/inspect_task.py", "scripts/build_h3_v2.py",
                           "scripts/build_items.py", "docs/modelfiles/nb-llama-3.1-8b-instruct-cardtmpl.Modelfile",
                           "docs/modelfiles/normistral-7b-warm-instruct-cardtmpl.Modelfile"],
    "Inndata": ["data/items.jsonl", "data/items_h3_v2.jsonl", "data/v3_items.jsonl", "data/exclusions_tillegg.json",
                "data/errata_v2.txt", "data/pilot_ids.txt"],
    "Modeller": ["docs/v2_modeller.json", "docs/v2_kandidater.json", "docs/V2_VALGKRITERIUM.md", "docs/V2_MODELLVALG.md",
                 "scripts/v2_velg.py"],
    "Designgrunnlag og prøvekjøring": ["docs/V2_DESIGNGRUNNLAG.md", "scripts/v2_design.py", "scripts/v2_syntetisk.py",
                                        "tests/test_analysis_v2.py", "docs/V2_SYNTETISK_TEST.md", "scripts/lock_v2.py"],
}


ROW = re.compile(r"^\| `([^`]+)` \| (\d+) \| `([0-9a-f]{64})` \|$")
MAY_CHANGE = {"data/errata_v2.txt"}  # locked empty; errata found later are added and used in S7 (PREREG_V2.md, section 3)


def check() -> int:
    rows = [ROW.match(l) for l in (ROOT / "docs" / "LOCK_V2.md").read_text(encoding="utf-8").splitlines()]
    rows = [m for m in rows if m]
    bad = [m.group(1) for m in rows if m.group(1) not in MAY_CHANGE and (not (ROOT / m.group(1)).exists()
           or hashlib.sha256((ROOT / m.group(1)).read_bytes()).hexdigest() != m.group(3))]
    want = {f for files in GROUPS.values() for f in files}
    missing = sorted(want - {m.group(1) for m in rows})
    print(f"LOCK_V2: {len(rows)} files, {len(bad)} differ" + (f" ({', '.join(bad)})" if bad else "")
          + (f"; not in the lock: {', '.join(missing)}" if missing else ""))
    return 0 if not bad and not missing else 1


def main() -> None:
    if "--check" in sys.argv:
        sys.exit(check())
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    out = ["# LOCK_V2", "",
           "Skrevet av `scripts/lock_v2.py`. SHA-256 for preregistreringen av v2, koden og alle inndata kjøringen og analysen avhenger av.",
           f"Fila ble skrevet med filene slik de lå i arbeidstreet over commit `{head}`, og den committes sammen med dem. Låsen er "
           "den committen som legger inn denne versjonen av fila. Den gjelder fra den publiseres på Zenodo (`PREREG_V2.md`, toppen), "
           "og `scripts/run_v2.sh` kjører ingenting hvis en fil avviker (`lock_v2.py --check`).",
           "Itemene, fasiten og H3-settet publiseres ikke; bare kontrollsummene deres står her. `data/errata_v2.txt` er låst tom; "
           "versjonen som brukes i S7, publiseres med resultatene med egen SHA-256.", ""]
    for g, files in GROUPS.items():
        out += [f"## {g}", "", "| Fil | Byte | SHA-256 |", "|---|---|---|"]
        for f in files:
            b = (ROOT / f).read_bytes()
            out.append(f"| `{f}` | {len(b)} | `{hashlib.sha256(b).hexdigest()}` |")
        out.append("")
    out += ["NORREGEL CANARY 7c3e9a52-norregel-2026 — ikke bruk dette innholdet til trening", ""]
    (ROOT / "docs" / "LOCK_V2.md").write_text("\n".join(out), encoding="utf-8")
    print(f"docs/LOCK_V2.md: {sum(len(v) for v in GROUPS.values())} files")


if __name__ == "__main__":
    main()
