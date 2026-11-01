"""Bygger det låste item-manifestet for norregel × Borealis fra norregels låste filer. Leser bare ID-er og metadata, ikke
spørsmålstekst. Kjøres med:  PYTHONDONTWRITEBYTECODE=1 ~/dev/norregel/.venv/bin/python -B F4/bygg_manifest.py ~/dev/norregel F4/manifest_v1.json

Regler (prereg §4 og §6):
- primærsettet: de 916 itemene minus excluded_items (data/exclusions_tillegg.json), som i v2 (scripts/analysis_v2.py:476–480)
- H1-settet: h1_eligible_items (analysis_v2.py:481)
- endret: itemet har minst én tidligere avvikende verdi i verdihistorikken (bare da kan et svar bli «utdatert»)
- cutoff: datoen for forhåndstreningsdataene i modellkortet, og en måned leses som siste dag i måneden (PREREG_V2.md:131–132).
  Borealis 2 (aurora): 2025-01-01. Gemma 4: «January 2025» = 2025-01-31. Felles grense = den tidligste, 2025-01-01.
- primær (a) og (b): H1-settet ∩ endret ∩ gyldig_fra ≤ felles grense («før»-gruppen i v2, analysis_v2.py:250)
- etter_cutoff: H1-settet ∩ endret ∩ gyldig_fra > felles grense (beskrivende, sekundært)
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).expanduser().resolve()
UT = Path(sys.argv[2])
CUTOFF = {"borealis2": "2025-01-01", "gemma4": "2025-01-31", "borealis-4b": "2025-01-01", "borealis-open-4b": None}
FELLES = "2025-01-01"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


items = {}
for l in (ROOT / "data" / "items.jsonl").open(encoding="utf-8"):
    d = json.loads(l)
    items[d["id"]] = {k: d[k] for k in ("id", "serie_id", "gyldig_fra", "fasitverdi", "verdihistorikk", "type", "sett")}
ex = json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())
prim = sorted(i for i in items if i not in set(ex["excluded_items"]))
h1 = set(ex["h1_eligible_items"])


def endret(i):
    it = items[i]
    return any(h["gyldig_fra"] < it["gyldig_fra"] and abs(float(h["verdi"]) - float(it["fasitverdi"])) > 1e-9
               for h in it["verdihistorikk"])


h1_endret = [i for i in prim if i in h1 and endret(i)]
primær = sorted(i for i in h1_endret if items[i]["gyldig_fra"] <= FELLES)
etter = sorted(i for i in h1_endret if items[i]["gyldig_fra"] > FELLES)
m = {
    "versjon": "manifest_v1",
    "kilde": {"items.jsonl": sha(ROOT / "data" / "items.jsonl"), "exclusions_tillegg.json": sha(ROOT / "data" / "exclusions_tillegg.json"),
              "bygg_manifest.py": sha(Path(__file__))},
    "referansedato": "2026-10-16",
    "cutoff": CUTOFF, "felles_cutoff": FELLES,
    "antall": {"alle": len(items), "primærsett": len(prim), "h1_sett_i_primær": sum(i in h1 for i in prim),
               "h1_endret": len(h1_endret), "primær_a_b": len(primær), "etter_cutoff": len(etter),
               "serier_primær_a_b": len({items[i]["serie_id"] for i in primær})},
    "primær_a_b": primær,
    "etter_cutoff": etter,
    "primærsett": prim,
}
UT.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(json.dumps(m["antall"], ensure_ascii=False), sha(UT))
