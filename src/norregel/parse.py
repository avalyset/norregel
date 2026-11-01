"""Parse Lovdata HTML/XML documents into blocks, and Norwegian rule values out of text.

Pure standard library. No model is involved anywhere.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

ORDINALS = {
    "første": 1, "andre": 2, "annet": 2, "tredje": 3, "fjerde": 4, "femte": 5,
    "sjette": 6, "sjuende": 7, "syvende": 7, "åttende": 8, "niende": 9, "tiende": 10,
    "ellevte": 11, "tolvte": 12,
}
NUMBER_WORDS = {
    "en": 1, "ett": 1, "én": 1, "to": 2, "tre": 3, "fire": 4, "fem": 5, "seks": 6,
    "sju": 7, "syv": 7, "åtte": 8, "ni": 9, "ti": 10, "elleve": 11, "tolv": 12,
    "tretten": 13, "fjorten": 14, "femten": 15, "seksten": 16, "sytten": 17,
    "atten": 18, "nitten": 19, "tjue": 20, "tjuefire": 24, "tretti": 30,
    "førti": 40, "femti": 50, "seksti": 60, "halvt": 0.5, "halv": 0.5,
}
MONTHS = {
    "januar": 1, "februar": 2, "mars": 3, "april": 4, "mai": 5, "juni": 6, "juli": 7,
    "august": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
}
CONTENT = {"legalP", "defaultP"}


@dataclass
class Block:
    """One outermost content article (legalP / defaultP) with its full text."""

    order: int
    cls: str
    id: str
    text: str
    paragraph: str | None  # data-name of the enclosing legalArticle, e.g. "§8-10"
    section: str | None  # data-name of the enclosing section, e.g. "kapI"


@dataclass
class _Open:
    tag: str
    cls: str
    id: str
    name: str | None
    order: int
    parts: list[str] = field(default_factory=list)


class _BlockParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[_Open] = []
        self.blocks: list[Block] = []
        self.header: dict[str, str] = {}
        self._dd: str | None = None
        self._dd_parts: list[str] = []
        self._order = 0
        self._in_main = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "dd" and not self._in_main:
            self._dd, self._dd_parts = (a.get("class") or ""), []
        if tag == "main":
            self._in_main = True
        if not self._in_main or tag not in ("article", "section"):
            return
        self._order += 1
        self.stack.append(
            _Open(tag, a.get("class") or "", a.get("id") or "", a.get("data-name"), self._order)
        )

    def handle_endtag(self, tag):
        if tag == "dd" and self._dd is not None:
            self.header[self._dd] = " ".join("".join(self._dd_parts).split())
            self._dd = None
            return
        if not self._in_main or tag not in ("article", "section") or not self.stack:
            return
        node = self.stack.pop()
        text = "".join(node.parts)
        if self.stack:  # the parent passes it on when it closes, so every ancestor gets it once;
            self.stack[-1].parts.append(f" {text} ")  # spaces keep words of adjacent elements apart
        if node.cls in CONTENT and not any(p.cls in CONTENT for p in self.stack):
            paragraph = next((p.name for p in reversed(self.stack) if p.cls == "legalArticle"), None)
            section = next((p.name for p in reversed(self.stack) if p.tag == "section"), None)
            self.blocks.append(
                Block(node.order, node.cls, node.id, " ".join(text.split()), paragraph, section)
            )

    def handle_data(self, data):
        if self._dd is not None:
            self._dd_parts.append(data)
        elif self.stack:
            self.stack[-1].parts.append(data)


def parse_document(html: str) -> tuple[dict[str, str], list[Block]]:
    parser = _BlockParser()
    parser.feed(html)
    blocks = sorted(parser.blocks, key=lambda b: b.order)
    header = dict(parser.header)
    header["_changes"] = " ".join(re.findall(r"(?:lov|forskrift)/\d{4}-\d{2}-\d{2}-\d+", _section(html, "changesToDocuments")))
    return header, blocks


def _section(html: str, cls: str) -> str:
    m = re.search(rf'<dd class="{cls}">(.*?)</dd>', html, re.S)
    return m.group(1) if m else ""


def ledd_from_id(element_id: str) -> int | None:
    m = re.search(r"paragraf-[^-]+(?:-[^-]+)*?-ledd-(\d+)$", element_id)
    return int(m.group(1)) if m and "punkt" not in element_id else None


def iso_in_force(raw: str) -> tuple[str | None, str]:
    """Leading ISO date of a dateInForce field, and its kind."""
    raw = (raw or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return raw, "iso"
    m = re.match(r"(\d{4}-\d{2}-\d{2})", raw)
    if m:
        return m.group(1), "iso_lead"
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.?\s+(\d{4})", raw)  # e.g. "12.02 2026"
    if m:
        day, month, year = (int(g) for g in m.groups())
        return f"{year}-{month:02d}-{day:02d}", "dmy"
    return None, "none"


def effective_date(raw: str) -> tuple[str | None, str]:
    """The date a version takes effect, from a dateInForce field.

    "med virkning fra (og med) <ISO date>" wins over the in-force date; "med virkning fra og
    med / for inntektsåret YYYY" gives 1 January YYYY. Otherwise the leading in-force date
    (iso_in_force). An academic year without a date ("Undervisningsåret 2012–2013") has no
    date and is reported as kind "undervisningsår".
    """
    raw = raw or ""
    m = re.search(r"virkning fra (?:og med )?(\d{4}-\d{2}-\d{2})", raw)
    if m:
        return m.group(1), "virkning"
    m = re.search(r"virkning (?:fra og med|for) inntektsåret (\d{4})", raw)
    if m:
        return f"{m.group(1)}-01-01", "virkning_inntektsår"
    date, kind = iso_in_force(raw)
    if date:
        return date, kind
    if re.match(r"\s*(?:Undervisningsåret|Utdanningsåret|Studieåret)\b", raw):
        return None, "undervisningsår"
    return None, kind


_DATE = r"(?:\d{1,2}\.\s*(?:" + "|".join(MONTHS) + r")\s+\d{4}|\d{4}-\d{2}-\d{2})"
_SPAN = rf"({_DATE})\s*(?:–|-|til(?:\s+og\s+med)?)\s*({_DATE})"
LEDD_PERIOD = re.compile(rf"(?:for\s+perioden|i\s+tidsrommet)\s+(?:fra\s+(?:og\s+med\s+)?)?{_SPAN}", re.I)
DOC_PERIOD = re.compile(rf"(?:^|\.\s+)Satse(?:ne|ne og vilkårene|ne og vilkåra)\b[^.]*?\bgjeld(?:er)?\s+for\s+perioden\s+{_SPAN}", re.I)
PART_START = re.compile(
    rf"Endring(?:ene|ane)\s+under\s+([IVXL]+)(?:\s+og\s+([IVXL]+))?\s+"
    rf"(?:gjelder fra|gjeld frå|tek til å gjelde|tar til å gjelde|trer i kraft|trer i kraft fra)\s+({_DATE})", re.I)
LAW_START = re.compile(rf"^\s*Loven\s+(?:gjelder fra|trer i kraft)\s+({_DATE})", re.I)
# v3.6 (1b): a date for one paragraph, (1c) "For (inntekts)året ÅÅÅÅ svares …", (1e) the whole document
PARA_START = re.compile(
    rf"Endring(?:en|ene|a|ane)\s+i\s+§\s*(\d+[a-z]?(?:\s*-\s*\d+[a-z]?)?)\b[^.]*?"
    rf"(?:gis virkning fra|gjelder fra|har virkning fra|tek til å gjelde|gjeld frå)\s+({_DATE})", re.I)
YEAR_PERIOD = re.compile(r"(?:^|\.\s+)For\s+(?:inntekts)?året\s+(\d{4})\s+(?:svares|skal|gjelder|betales|fastsettes)", re.I)
DOC_START = re.compile(rf"(?:^|\.\s+)(?:Forskriften|Vedtaket|Endringene|Endringane)\s+"
                       rf"(?:gjelder fra|gis virkning fra|har virkning fra)\s+({_DATE})", re.I)


def to_iso(text: str) -> str:
    m = re.fullmatch(r"(\d{1,2})\.\s*(\w+)\s+(\d{4})", text.strip())
    if m:
        return f"{m.group(3)}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    return text.strip()


def doc_dates(blocks) -> dict:
    """Explicit dates stated for a whole source document (rule v3.5): the period of its rates
    ("Satsene … gjelder for perioden D1–D2"), start dates per part of an amending act
    ("Endringene under III gjelder fra D", keyed by section "kapIII") and for a whole act."""
    out = {"period": None, "parts": {}, "law": None, "paras": {}}
    for b in blocks:
        m = DOC_PERIOD.search(b.text)
        if m and not out["period"]:
            out["period"] = (to_iso(m.group(1)), to_iso(m.group(2)))
        m = YEAR_PERIOD.search(b.text)
        if m and not out["period"]:
            out["period"] = (f"{m.group(1)}-01-01", f"{m.group(1)}-12-31")
        for m in PARA_START.finditer(b.text):
            out["paras"].setdefault("§" + re.sub(r"\s+", "", m.group(1)), to_iso(m.group(2)))
        m = DOC_START.search(b.text)
        if m and not out["law"]:
            out["law"] = to_iso(m.group(1))
        for m in PART_START.finditer(b.text):
            for part in (m.group(1), m.group(2)):
                if part:
                    out["parts"][f"kap{part.upper()}"] = to_iso(m.group(3))
        m = LAW_START.search(b.text)
        if m and not out["law"]:
            out["law"] = to_iso(m.group(1))
    return out


def explicit_date(text: str, section: str | None, docd: dict,
                  paragraph: str | None = None) -> tuple[str | None, str | None, str | None]:
    """(gyldig_fra, explicit gyldig_til, kind) from the text itself, in the order of rule v3.6:
    a period in the version's own ledd, a date for its paragraph, the document's rate period
    (or "For året ÅÅÅÅ"), the start of its part of an amending act, the start of the whole
    document. (None, None, None) if the text states none."""
    m = LEDD_PERIOD.search(text or "")
    if m:
        return to_iso(m.group(1)), to_iso(m.group(2)), "periode_ledd"
    key = "§" + paragraph.lstrip("§").replace(" ", "") if paragraph else None
    if key and key in docd.get("paras", {}):
        return docd["paras"][key], None, "paragraf"
    if docd.get("period"):
        return docd["period"][0], docd["period"][1], "periode"
    if section and section in docd.get("parts", {}):
        return docd["parts"][section], None, "del"
    if docd.get("law"):
        return docd["law"], None, "lov"
    return None, None, None


LAW_REF = re.compile(
    r"(lov|forskrift) (\d{1,2})\.\s*(" + "|".join(MONTHS) + r") (\d{4}) nr\.\s*(\d+)", re.I
)


def law_ref(text: str) -> str | None:
    """First 'lov 12. juni 2026 nr. 25' style reference in a text, as a refid."""
    m = LAW_REF.search(text)
    if not m:
        return None
    kind, day, month, year, nr = m.groups()
    return f"{kind.lower()}/{year}-{MONTHS[month.lower()]:02d}-{int(day):02d}-{int(nr)}"


REPLACE_HEAD = re.compile(
    r"^I (?:ny |nytt )?§\s*(\d+(?:\s?[a-zA-Z](?![a-zA-ZæøåÆØÅ]))?(?:-\d+(?:\s?[a-zA-Z](?![a-zA-ZæøåÆØÅ]))?)?)"
    r"((?:\s+(?:nytt\s+)?(?:" + "|".join(ORDINALS) + r")\s+ledd)?)(.*)$",
    re.I,
)
_VERB = r"(?:skal\s+)?(?:endres til|erstattes med|erstattes av|byttes ut med|skal lyde|lyde)"


def parse_replacement(text: str) -> tuple[str, int | None, bool, list[tuple[str, str]]] | None:
    """(paragraph, ledd, sub-ledd, [(old, new)]) for 'I § N … «old» endres til «new»'."""
    m = REPLACE_HEAD.match(text)
    if not m or not re.search(_VERB + r"|endres\s*«|erstattes\s*«", text, re.I):
        return None
    para = "§" + re.sub(r"\s+", "", m.group(1))
    lm = re.search(r"(" + "|".join(ORDINALS) + r")\s+ledd", m.group(2) or "", re.I)
    ledd = ORDINALS[lm.group(1).lower()] if lm else None
    rest = m.group(3) or ""
    sub = bool(re.search(r"punktum|bokstav|nr\.|tabell", rest.split("«")[0], re.I))
    pairs = re.findall(r"«([^»]+)»\s*" + _VERB + r"\s*«([^»]+)»", rest, re.I)
    pairs += re.findall(r"(?:endres|erstattes|byttes ut)\s*«([^»]+)»\s*(?:til|med)\s*«([^»]+)»", rest, re.I)
    if not pairs and re.search(r"henholdsvis", rest, re.I):
        verb = re.search(_VERB, rest, re.I)
        if verb is None:
            return None
        olds = re.findall(r"«([^»]+)»", rest[: verb.start()])
        news = re.findall(r"«([^»]+)»", rest[verb.end():])
        if olds and len(olds) == len(news):
            pairs = list(zip(olds, news))
    return (para, ledd, sub, pairs) if pairs else None


TARGET = re.compile(
    r"^I (lov|forskrift) (\d{1,2})\.\s*(" + "|".join(MONTHS) + r") (\d{4}) nr\.\s*(\d+)\b", re.I
)
INSTRUCTION = re.compile(
    r"^(?:Ny |Nytt )?§\s*(\d+(?:\s?[a-zA-Z](?![a-zA-ZæøåÆØÅ]))?(?:-\d+(?:\s?[a-zA-Z](?![a-zA-ZæøåÆØÅ]))?)?)"
    r"((?:\s+(?:nytt\s+)?(?:" + "|".join(ORDINALS) + r")(?:\s*(?:,|og)\s*(?:nytt\s+)?(?:" + "|".join(ORDINALS) + r"))*\s+ledd)?)"
    r"(.*?)\s+(?:\(endret\)\s+)?(skal lyde|oppheves)",
    re.I,
)


def target_of(text: str) -> str | None:
    m = TARGET.match(text)
    if not m:
        return None
    kind, day, month, year, nr = m.groups()
    return f"{kind.lower()}/{year}-{MONTHS[month.lower()]:02d}-{int(day):02d}-{int(nr)}"


def parse_instruction(text: str) -> tuple[str, int | None, bool, bool] | None:
    """(paragraph, ledd or None, sub-ledd granularity, repealed) for an amendment line."""
    m = INSTRUCTION.match(text)
    if not m:
        return None
    para = "§" + re.sub(r"\s+", "", m.group(1))
    ledds = [ORDINALS[w.lower()] for w in re.findall(r"(" + "|".join(ORDINALS) + r")", m.group(2) or "", re.I)]
    sub = bool(re.search(r"punktum|bokstav|nr\.|tabell", m.group(3) or "", re.I))
    # A list when several ledd are replaced at once ("andre og tredje ledd"), else int or None.
    ledd = (ledds[0] if len(ledds) == 1 else ledds) if ledds else None
    return para, ledd, sub, m.group(4).lower() == "oppheves"


# ---------------------------------------------------------------- values

_NUM = r"\d{1,3}(?:[   .]\d{3})+(?:,\d+)?|\d+(?:,\d+)?"
_WORD = "|".join(sorted(NUMBER_WORDS, key=len, reverse=True))

AMOUNT = re.compile(rf"(?:\bkr\.?\s*({_NUM})(?!\s*(?:prosent|%))|\b({_NUM})\s*(?:kroner|kr\b))", re.I)
G_MULT = re.compile(
    rf"\b({_NUM}|{_WORD}|1/\d+)\s+(?:ganger\s+)?(?:folketrygdens\s+)?grunnbeløp(?:et|ene)?\b"
    rf"|\b({_NUM})\s*G\b",
    re.I,
)
PERCENT = re.compile(rf"\b({_NUM})\s*(?:prosent|%)", re.I)
DURATION = re.compile(
    rf"\b({_NUM}|{_WORD})\s+(virkedager|kalenderdager|dager|døgn|uker|måneder|år)\b", re.I
)
AGE_CUE = re.compile(
    rf"(?:under|over|fylt|fylte|fyller|fylle|eldre enn|yngre enn|alder(?:en)? på|i alderen|før|mellom"
    rf"|mellom\s+(?:{_NUM}|{_WORD})\s+og|alderen\s+(?:{_NUM}|{_WORD})\s+(?:til|og))\s+$",
    re.I,
)
AGE_AFTER = re.compile(r"^\s*(?:gammel|gamle|eller eldre|og eldre|eller yngre|og yngre)\b", re.I)


def to_number(token: str) -> float | None:
    token = token.strip().lower()
    if token in NUMBER_WORDS:
        return float(NUMBER_WORDS[token])
    if re.fullmatch(r"1/\d+", token):
        return 1 / int(token[2:])
    token = re.sub(r"[   .]", "", token).replace(",", ".")
    try:
        return float(token)
    except ValueError:
        return None


def values(text: str) -> list[tuple[str, float, str]]:
    """(type, number, matched text) in order of appearance.

    Types: belop (kroner), g (multiples of the base amount), prosent, frist (a duration
    in days/weeks/months/years) and alder (years preceded by an age cue such as
    "under" or "fylt").
    """
    found: list[tuple[int, str, float, str]] = []
    for m in AMOUNT.finditer(text):
        n = to_number(m.group(1) or m.group(2))
        if n is not None:
            found.append((m.start(), "belop", n, m.group(0)))
    for m in G_MULT.finditer(text):
        n = to_number(m.group(1) or m.group(2))
        if n is not None:
            found.append((m.start(), "g", n, m.group(0)))
    for m in PERCENT.finditer(text):
        n = to_number(m.group(1))
        if n is not None:
            found.append((m.start(), "prosent", n, m.group(0)))
    for m in DURATION.finditer(text):
        n = to_number(m.group(1))
        if n is None:
            continue
        unit = m.group(2).lower()
        age = AGE_CUE.search(text[max(0, m.start() - 30): m.start()]) or AGE_AFTER.match(text[m.end():])
        kind = "alder" if unit == "år" and age else "frist"
        found.append((m.start(), kind, n, m.group(0)))
    found.sort(key=lambda f: f[0])
    return [(kind, n, raw) for _, kind, n, raw in found]
