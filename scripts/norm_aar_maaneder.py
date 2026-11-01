"""Run protocol decision for Known limitation 5 (docs/RUN_PROTOCOL.md section 3.5).

An age answer «X år og Y måneder» is read as the single value X + Y/12 years. The locked scorers
(score.py, score_v2.py) are not changed: this module rewrites the answer line of an *age* answer
before the stored completion is scored in the analysis (scripts/run_analysis.py). Nothing else is touched.
No model is called.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from norregel.score_v2 import LABEL, PLACEHOLDER, number_word  # noqa: E402

N = r"(\d+(?:[.,]\d+)?|[^\W\d_]+)"
PAT = re.compile(rf"\b{N}\s*(?:år|aar|gammel|gamal)?\s*(?:og|,)?\s*{N}\s*(?:måneder|måned|månader|månad|mnd)\b\.?", re.I)
YEARS = re.compile(rf"\b{N}\s*år\b(?:\s*gammel|\s*gamal)?\s*(?:og\s*)?{N}\s*(?:måneder|måned|månader|månad|mnd)\b\.?", re.I)


def _num(tok: str) -> float | None:
    if tok[0].isdigit():
        return float(tok.replace(",", "."))
    return None if (v := number_word(tok.lower())) is None else float(v)


def normalise(completion: str, item_type: str) -> tuple[str, bool]:
    """Return (completion, changed). Only item type 'alder'; only the answer line (the same line
    score_v2 reads: the last one labelled «svar» that is not the <verdi> placeholder)."""
    if item_type != "alder" or not completion:
        return completion, False
    lines = completion.splitlines()
    idx = None
    for k, line in enumerate(lines):
        m = LABEL.match(line)
        if not m:
            continue
        rest = m.group(1).strip()
        if not rest:
            nxt = next((j for j in range(k + 1, len(lines)) if lines[j].strip()), None)
            if nxt is None or PLACEHOLDER.search(lines[nxt]):
                continue
            idx = nxt
        elif not PLACEHOLDER.search(rest):
            idx = k
    if idx is None:
        return completion, False
    line = lines[idx]
    text = re.sub(r"[*_`]", " ", line)
    m = YEARS.search(text)
    if not m:
        return completion, False
    x, y = _num(m.group(1)), _num(m.group(2))
    if x is None or y is None:
        return completion, False
    value = x + y / 12
    lines[idx] = f"SVAR: {value:.2f}"  # two decimals: score_v2 reads «62.083» as a thousands group
    return "\n".join(lines), True
