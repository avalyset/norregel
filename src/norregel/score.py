"""Deterministic scorer for norregel items. No model is involved.

An answer is read from its last "SVAR:" line, normalised (thousands separators, currency,
percent, G and time-unit words, number words) and classified against the item:

- korrekt: equals the item's answer (fasitverdi);
- utdatert: equals another value in the item's own value history; every year with that
  value is reported;
- feil: read, but neither;
- utolket: no "SVAR:" line, or the answer does not normalise to exactly one number
  (for durations: a number and a unit).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

TOL = 0.005
WORDS = {
    "null": 0, "en": 1, "ett": 1, "én": 1, "ein": 1, "eitt": 1, "ei": 1, "to": 2, "tre": 3,
    "fire": 4, "fem": 5, "seks": 6, "sju": 7, "syv": 7, "åtte": 8, "ni": 9, "ti": 10,
    "elleve": 11, "tolv": 12, "tretten": 13, "fjorten": 14, "femten": 15, "seksten": 16,
    "sytten": 17, "atten": 18, "nitten": 19, "tjue": 20, "tjuge": 20,
}
TIME_UNITS = {  # bokmål and nynorsk forms -> canonical unit
    "virkedager": "virkedager", "virkedag": "virkedager", "verkedagar": "virkedager", "verkedag": "virkedager",
    "kalenderdager": "dager", "kalenderdag": "dager", "kalenderdagar": "dager",
    "dager": "dager", "dag": "dager", "dagar": "dager", "døgn": "dager",
    "uker": "uker", "uke": "uker", "veker": "uker", "veke": "uker",
    "måneder": "måneder", "måned": "måneder", "månader": "måneder", "månad": "måneder",
    "år": "år",
}
# Units that carry no information for kroner/percent/G items; removed before reading the number.
NOISE = re.compile(
    r"\bnok\b|\bkroner\b|\bkr\b\.?|,-|,–|\.-|\bprosent\b|\bpst\b\.?|%"
    r"|\bganger\s+(?:folketrygdens\s+)?grunnbeløpet\b|\bgonger\s+grunnbeløpet\b|\bgrunnbeløp(?:et)?\b|(?<=\d)\s*g\b|\bg\b",
    re.I,
)
NUM = re.compile(r"\d{1,3}(?:[   .,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?")


@dataclass
class Result:
    klasse: str  # korrekt | utdatert | feil | utolket
    lest: float | None = None
    enhet: str | None = None
    år: list[int] = field(default_factory=list)  # for utdatert: every year with that value


def answer_line(completion: str) -> str | None:
    lines = [m.group(1) for m in re.finditer(r"(?im)^\s*\**\s*svar\s*:\s*\**\s*(.*)$", completion or "")]
    if not lines:
        return None
    text = lines[-1].strip().strip("*").strip()
    return text or None


def to_float(token: str, thousands: bool = True) -> float:
    """One number token; a separator before exactly three digits in a run of such groups is a
    thousands separator (unless the integer part is 0), the last other separator is the decimal.
    With thousands=False (percent, G, durations, ages) a single "," or "." is always decimal."""
    t = token.replace(" ", " ").replace(" ", " ")
    seps = [c for c in t if c in " .,"]
    if not seps:
        return float(t)
    if " " in seps:
        t = t.replace(" ", "")
        seps = [c for c in seps if c != " "]
        if not seps:
            return float(t)
    if len(set(seps)) == 2:  # "1.234,50" or "1,234.50": the last one is the decimal
        dec = t[max(t.rfind("."), t.rfind(","))]
        thou = "," if dec == "." else "."
        return float(t.replace(thou, "").replace(dec, "."))
    sep = seps[0]
    groups = t.split(sep)
    if len(groups) == 2 and not thousands:
        return float(groups[0] + "." + groups[1])
    if len(groups) > 2 or (len(groups[-1]) == 3 and groups[0] not in ("0", "")):
        if all(len(g) == 3 for g in groups[1:]):
            return float("".join(groups))
    if len(groups) == 2:
        return float(groups[0] + "." + groups[1])
    raise ValueError(token)


def read(answer: str, kind: str) -> tuple[float, str | None] | None:
    """(number, unit) from one answer, or None if it cannot be read unambiguously."""
    text = " " + answer.lower().strip().rstrip(".!") + " "
    unit = None
    if kind in ("frist", "alder"):
        found = [TIME_UNITS[w] for w in re.findall(r"[^\W\d_]+", text) if w in TIME_UNITS]
        if len(set(found)) > 1:
            return None
        unit = found[0] if found else None
        text = re.sub(r"[^\W\d_]+", lambda m: "" if m.group(0) in TIME_UNITS else m.group(0), text)
    else:
        text = NOISE.sub(" ", text)
    nums = NUM.findall(text)
    words = [w for w in re.findall(r"[^\W\d_]+", text) if w in WORDS]
    rest = NUM.sub(" ", text)
    rest = re.sub(r"[^\W\d_]+", lambda m: "" if m.group(0) in WORDS else m.group(0), rest)
    if re.search(r"[^\W_]", rest):  # leftover words or digits: not a plain value
        return None
    if len(nums) + len(words) != 1:
        return None
    try:
        n = to_float(nums[0], thousands=kind == "belop") if nums else float(WORDS[words[0]])
    except ValueError:
        return None
    return n, unit


def same(a: float, b: float) -> bool:
    return abs(a - b) < TOL


def score(completion: str, item: dict) -> Result:
    """item: fasitverdi, enhet, type (belop|prosent|g|frist|alder), år, verdihistorikk."""
    line = answer_line(completion)
    if line is None:
        return Result("utolket")
    kind = item["type"]
    got = read(line, kind)
    if got is None:
        return Result("utolket")
    n, unit = got
    if kind == "frist" and unit is None:
        return Result("utolket", n)
    if kind == "alder" and unit not in (None, "år"):
        return Result("feil", n, unit)

    def match(value, value_unit):
        return same(n, value) and (kind != "frist" or unit == TIME_UNITS.get(value_unit, value_unit))

    if match(item["fasitverdi"], item["enhet"]):
        return Result("korrekt", n, unit)
    years = sorted({h["år"] for h in item["verdihistorikk"]
                    if h["gyldig_fra"] != item["gyldig_fra"] and match(h["verdi"], h["enhet"])})
    if years:
        return Result("utdatert", n, unit, years)
    return Result("feil", n, unit)
