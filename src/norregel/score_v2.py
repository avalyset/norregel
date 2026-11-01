"""Deterministic scorer v2 for norregel items (docs/PREREG_TILLEGG.md). No model is involved.

v1 (score.py) is locked and stays unchanged. v2 differs in two ways:

1. Reading. The answer line is the last line labelled "svar" (any case, with markdown such as
   **Svar**:, ### SVAR:, > SVAR:, or "Endelig svar:"). A placeholder line ("<verdi>") is
   skipped, and an empty label line takes the next non-empty line. On that line, text in
   parentheses and markdown are removed. The line must then hold exactly one number (digits
   or, if the line has no digits, Norwegian number words up to 99), times
   "tusen"/"million(er)"/"milliard(er)" if present. Surrounding words ("per år", "av alminnelig inntekt", "fylt", "gammel", "ca.",
   "x G" …) do not stop the reading.
2. Classes, relative to the date in the question:
   - korrekt: the number equals the answer (fasitverdi) exactly (difference below 1e-6;
     v1 allowed 0.005). Always korrekt, also if the same
     value applied in other periods;
   - utdatert: not korrekt, and equals the value of a version in the item's own history that
     started BEFORE the item's period (gyldig_fra earlier than the item's). The years of
     those versions are reported, and the age is the item's year minus the latest of them;
   - feil: read, but neither. A value that only applies after the item's period is feil; the
     years of those later versions are reported in `senere`, so "feil" can be split into
     "later value" and "value not in the history";
   - utolket: no answer line, no number, or more than one number.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

TOL = 1e-6  # exact: answers come from the source text; 0.005 (v1) merged 57.73 and 57.725
ONES = {"null": 0, "en": 1, "ett": 1, "én": 1, "ein": 1, "eitt": 1, "ei": 1, "to": 2, "tre": 3, "fire": 4,
        "fem": 5, "seks": 6, "sju": 7, "syv": 7, "åtte": 8, "ni": 9}
TEENS = {"ti": 10, "elleve": 11, "tolv": 12, "tretten": 13, "fjorten": 14, "femten": 15, "seksten": 16,
         "sytten": 17, "atten": 18, "nitten": 19}
TENS = {"tjue": 20, "tjuge": 20, "tretti": 30, "førti": 40, "femti": 50, "seksti": 60,
        "sytti": 70, "søtti": 70, "åtti": 80, "nitti": 90}
MULT = {"tusen": 1e3, "million": 1e6, "millioner": 1e6, "mill": 1e6, "milliard": 1e9, "milliarder": 1e9, "mrd": 1e9}
LABEL = re.compile(r"(?im)^[\s>#*_`-]*(?:endelig\s+)?svar[\s*_`]*[:：][\s*_`]*(.*)$")
PLACEHOLDER = re.compile(r"<\s*verdi\s*>", re.I)
NUM = re.compile(r"\d{1,3}(?:[   .,'’]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?")


@dataclass
class Result:
    klasse: str  # korrekt | utdatert | feil | utolket
    lest: float | None = None
    år: list[int] = field(default_factory=list)  # utdatert: years of earlier versions with that value
    alder: int | None = None  # utdatert: item year minus the latest such year
    senere: list[int] = field(default_factory=list)  # feil: years of later versions with that value


def number_word(w: str) -> int | None:
    """Norwegian number word 0–99, also compounds like 'sekstisju', 'tjueto'."""
    if w in ONES:
        return ONES[w]
    if w in TEENS:
        return TEENS[w]
    for t, v in TENS.items():
        if w == t:
            return v
        if w.startswith(t) and w[len(t):] in ONES and ONES[w[len(t):]] > 0:
            return v + ONES[w[len(t):]]
    return None


def answer_line(completion: str) -> str | None:
    lines = (completion or "").splitlines()
    found = None
    for k, line in enumerate(lines):
        m = LABEL.match(line)
        if not m:
            continue
        rest = m.group(1).strip()
        if not rest:  # value on the next non-empty line
            rest = next((l.strip() for l in lines[k + 1:] if l.strip()), "")
        if rest and not PLACEHOLDER.search(rest):
            found = rest
    return found


def to_float(token: str, thousands: bool) -> float:
    t = token.replace(" ", " ").replace(" ", " ").replace("'", " ").replace("’", " ")
    t = t.replace(" ", "")
    seps = [c for c in t if c in ".,"]
    if not seps:
        return float(t)
    if len(set(seps)) == 2:
        dec = t[max(t.rfind("."), t.rfind(","))]
        return float(t.replace("," if dec == "." else ".", "").replace(dec, "."))
    sep = seps[0]
    groups = t.split(sep)
    if len(groups) == 2 and not thousands:
        return float(groups[0] + "." + groups[1])
    if (len(groups) > 2 or (len(groups[-1]) == 3 and groups[0] not in ("0", ""))) and all(len(g) == 3 for g in groups[1:]):
        return float("".join(groups))
    if len(groups) == 2:
        return float(groups[0] + "." + groups[1])
    raise ValueError(token)


def read(line: str, kind: str) -> float | None:
    """The one number on an answer line, or None."""
    text = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", line)  # e.g. "(2024)"
    text = re.sub(r"[*_`]", " ", text).lower()
    text = re.sub(r"(?<=\d),[-–]", " ", text)  # "31 350,-"
    text = re.sub(r"(?<=\d)\.[-–]", " ", text)  # "31350.-"
    text = re.sub(r"(?<=\d)-år\w*", " år", text)  # "67-årsalderen"
    nums = [(m.start(), m.group(0)) for m in NUM.finditer(text)]
    words = [(m.start(), number_word(m.group(0))) for m in re.finditer(r"[^\W\d_]+", text)]
    # number words count only when the line has no digits ("en person", "to år" are ordinary words)
    words = [(p, v) for p, v in words if v is not None] if not nums else []
    if kind == "alder" and re.search(r"\bmån(?:e|a)d", text):
        return float("nan")  # an age in months is not an age in years
    if len(nums) + len(words) != 1:
        return None
    try:
        n = to_float(nums[0][1], thousands=kind == "belop") if nums else float(words[0][1])
    except ValueError:
        return None
    after = text[(nums[0][0] + len(nums[0][1])) if nums else words[0][0]:]
    m = re.match(r"\s*(tusen|millioner|million|mill|milliarder|milliard|mrd)\b", after)
    if m:
        n *= MULT[m.group(1)]
    return n


def same(a: float, b: float) -> bool:
    return abs(a - b) < TOL


def score(completion: str, item: dict) -> Result:
    """item: fasitverdi, type (belop|prosent|g|alder), år, gyldig_fra, verdihistorikk."""
    line = answer_line(completion)
    if line is None:
        return Result("utolket")
    n = read(line, item["type"])
    if n is None:
        return Result("utolket")
    if n != n:  # nan: wrong unit for an age
        return Result("feil")
    if same(n, item["fasitverdi"]):
        return Result("korrekt", n)
    earlier = [h for h in item["verdihistorikk"] if h["gyldig_fra"] < item["gyldig_fra"] and same(n, h["verdi"])]
    if earlier:
        years = sorted({h["år"] for h in earlier})
        return Result("utdatert", n, years, item["år"] - years[-1])
    later = sorted({h["år"] for h in item["verdihistorikk"] if h["gyldig_fra"] > item["gyldig_fra"] and same(n, h["verdi"])})
    return Result("feil", n, senere=later)
