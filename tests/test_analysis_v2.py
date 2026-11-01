"""Checks of scripts/analysis_v2.py against the locked scorer and the data it reads (no model is called).

1. The sub-classes of 'utolket' agree with score_v2: on every v1 answer with an answer line, count_numbers() is 1 exactly
   when score_v2.read() reads a number, apart from the lines where read() finds one number it cannot convert
   (sub-class ett_tall_uleselig).
2. rejected_values() finds every primary series in data/v3_items.jsonl, with one accepted flag per version.
3. Duplicate (model, id, run) rows stop the analysis.
4. A missing answer row stops the analysis (only complete runs are analysed).
5. Outside the primary analysis the per-model decision is the nominal p, not Holm (section 7.5).
6. The 24-month window of S9 keeps only 'before' items that took effect in the 24 months before the cutoff.
7. An age answer «X år og Y måneder» is normalised (v1 protocol 3.5) and counted; the same count on the v1 answers is 0 for
   every model, as in docs/RESULTS.md.

  .venv/bin/python -I tests/test_analysis_v2.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import analysis_v2 as A2  # noqa: E402
from norregel import score_v2 as S2  # noqa: E402


def test_subclasses() -> Counter:
    items = {i["id"]: i for i in A2.load("items.jsonl")}
    items.update({i["id"]: i for i in A2.load("items_h3.jsonl")})
    tally = Counter()
    for l in (ROOT / "logs" / "run_v1" / "answers.jsonl").open(encoding="utf-8"):
        a = json.loads(l)
        line = S2.answer_line(a["completion"] or "")
        if line is None or a["error"]:
            continue
        kind = items[a["id"]]["type"]
        k = A2.count_numbers(line, kind)
        n = S2.read(line, kind)
        if n is not None:
            assert k == 1, (a["model"], a["id"], k)
            tally["lest, ett tall"] += 1
        else:
            tally[f"ikke lest, {'ett tall (uleselig)' if k == 1 else 'null tall' if k == 0 else 'flere tall'}"] += 1
    return tally


def test_rejected() -> int:
    items = A2.load("items.jsonl")
    out = A2.rejected_values({i["serie_id"] for i in items})
    return sum(1 for v in out.values() if v)


def test_duplicates() -> bool:
    ans = [{"model": "m", "id": "norregel-00001", "run": 1, "completion": "", "error": False}] * 2
    try:
        A2.analyse([{"id": "m", "provider": "x", "h1": False, "cutoff": None, "runs": 1}], ans, ROOT / "data" / "items_h3_v2.jsonl")
    except SystemExit as e:
        return "duplicate" in str(e)
    return False


def test_missing() -> bool:
    items = [i["id"] for i in A2.load("items.jsonl")]
    ans = [{"model": "m", "id": i, "run": 1, "completion": "SVAR: 1", "error": False} for i in items[1:]]  # one main row missing
    try:
        A2.analyse([{"id": "m", "provider": "x", "h1": False, "cutoff": None, "runs": 1}], ans, ROOT / "data" / "items_h3_v2.jsonl")
    except SystemExit as e:
        return "missing answer rows" in str(e)
    return False


def test_nominal() -> tuple[str, str]:
    rows = {"m1": [], "m2": []}
    for m in rows:
        for k in range(60):
            after = k < 30
            rows[m].append({"id": f"i{k}", "serie_id": f"s{k}", "gyldig_fra": "2026-01-01" if after else "2020-01-01",
                            "klasse": "utdatert" if (after and k % 2 == 0) else "korrekt", "under": None})
    cut = {"m1": "2025-01-31", "m2": "2025-01-31"}
    h1set = {f"i{k}" for k in range(60)}
    series = sorted({f"s{k}" for k in range(60)})
    a = A2.h1_table(rows, cut, h1set, series, "tolkbare", holm_on=True)
    b = A2.h1_table(rows, cut, h1set, series, "tolkbare", holm_on=False)
    return a["beslutning_per_modell"] + (" (holm_forkastet)" if "holm_forkastet" in a["per_modell"]["m1"] else ""), \
        b["beslutning_per_modell"] + (" (nominelt_forkastet)" if "nominelt_forkastet" in b["per_modell"]["m1"] else "")


def test_window() -> tuple[int, int]:
    rows = {"m": [{"id": f"i{k}", "serie_id": f"s{k}", "gyldig_fra": g, "klasse": "korrekt", "under": None}
                  for k, g in enumerate(["2026-01-01", "2024-06-30", "2023-02-01", "2023-01-31", "2010-01-01"])]}
    h1set = {f"i{k}" for k in range(5)}
    full = A2.h1_table(rows, {"m": "2025-01-31"}, h1set, sorted({f"s{k}" for k in range(5)}), "tolkbare")["samlet"]["n_foer"]
    win = A2.h1_table(rows, {"m": "2025-01-31"}, h1set, sorted({f"s{k}" for k in range(5)}), "tolkbare", before_months=24)["samlet"]["n_foer"]
    return full, win


def test_normalised() -> tuple[bool, dict]:
    items = {i["id"]: i for i in A2.load("items.jsonl")}
    age = next(i for i in items.values() if i["type"] == "alder")
    one = A2.classify({"completion": "SVAR: 67 år og 6 måneder", "error": False}, age, {})["normalisert"]
    v1 = Counter()
    for l in (ROOT / "logs" / "run_v1" / "answers.jsonl").open(encoding="utf-8"):
        a = json.loads(l)
        if a["id"] in items:
            v1[a["model"]] += A2.classify(a, items[a["id"]], {})["normalisert"]
    return one, dict(v1)


if __name__ == "__main__":
    print("underklasser mot score_v2.read på alle v1-svar med svarlinje:", dict(test_subclasses()))
    print("serier med minst én forkastet versjon (av 97):", test_rejected())
    print("dubletter stopper analysen:", test_duplicates())
    print("manglende rad stopper analysen:", test_missing())
    print("beslutning per modell (primær, sensitivitet):", test_nominal())
    print("S9-vinduet: n før uten og med 24 måneder (forventet 4 og 2):", test_window())
    print("normalisering: «67 år og 6 måneder» normalisert, og antall per v1-modell:", test_normalised())
