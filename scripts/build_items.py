"""Build one question per year item in the primary set (core) from fixed templates.

No model is used. Templates are in docs/MALER.md (the TEMPLATES dict below is the same text).
Language form (nb/nn) is assigned per series with a fixed seed: the series' year items are
shuffled and split in half, so bokmål and nynorsk are balanced within every series.

Reads data/v3_items.jsonl, data/candidates.jsonl, data/yearseries.jsonl and
docs/NAVNGITTE_SATSER.md. Writes data/items.jsonl and data/items_summary.json.
Usage: python scripts/build_items.py
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261016
H3_SEED = 20261017
H3_N = 200
AS_OF = dt.date(2026, 10, 16)
CANARY = "NORREGEL CANARY 7c3e9a52-norregel-2026 — ikke bruk dette innholdet til trening"
MONTHS = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september",
          "oktober", "november", "desember"]
ORD = {"nb": ["første", "andre", "tredje", "fjerde", "femte", "sjette", "sjuende", "åttende", "niende",
              "tiende", "ellevte", "tolvte"],
       "nn": ["første", "andre", "tredje", "fjerde", "femte", "sjette", "sjuande", "åttande", "niande",
              "tiande", "ellevte", "tolvte"]}
NAME = {  # generic name of the value for § / ledd items, with the anchor phrase if there is one
    "nb": {"belop": "beløpet", "prosent": "prosentsatsen", "g": "antallet G", "frist": "tidsangivelsen",
           "alder": "aldersgrensen", "phrase": "i setningen med «{p}»"},
    "nn": {"belop": "beløpet", "prosent": "prosentsatsen", "g": "talet på G", "frist": "tidsangivinga",
           "alder": "aldersgrensa", "phrase": "i setninga med «{p}»"},
}
TEMPLATES = {
    "nb": {
        "belop": "Hvor mange kroner var {navn} etter {kilde} per {dato}?",
        "prosent": "Hvor mange prosent var {navn} etter {kilde} per {dato}?",
        "g": "Hvor mange ganger grunnbeløpet (G) var {navn} etter {kilde} per {dato}?",
        "frist": "Hvor lang var {navn} etter {kilde} per {dato}? Oppgi tall og enhet.",
        "alder": "Hvilken alder i år var {navn} etter {kilde} per {dato}?",
        "G": "Hvor mange kroner var grunnbeløpet i folketrygden (G) etter {kilde} per {dato}?",
        "svar": "Svar med verdien alene på siste linje, slik: SVAR: <verdi>",
    },
    "nn": {
        "belop": "Kor mange kroner var {navn} etter {kilde} per {dato}?",
        "prosent": "Kor mange prosent var {navn} etter {kilde} per {dato}?",
        "g": "Kor mange gonger grunnbeløpet (G) var {navn} etter {kilde} per {dato}?",
        "frist": "Kor lang var {navn} etter {kilde} per {dato}? Oppgi tal og eining.",
        "alder": "Kva alder i år var {navn} etter {kilde} per {dato}?",
        "G": "Kor mange kroner var grunnbeløpet i folketrygda (G) etter {kilde} per {dato}?",
        "svar": "Svar med berre verdien på siste linja, slik: SVAR: <verdi>",
    },
}
NAMED_DOC = {"skattevedtak": "Stortingets skattevedtak for inntektsåret {år}",
             "trygdeavgift": "Stortingets vedtak om fastsetting av avgifter mv. til folketrygden for {år}"}
# Question names for the named rates (docs/MALER.md). "topp" is used up to and including 2015.
NAMED_Q = {
    "personfradrag_klasse1": ("personfradraget i klasse 1", "personfrådraget i klasse 1"),
    "personfradrag_klasse2": ("personfradraget i klasse 2", "personfrådraget i klasse 2"),
    "trinnskatt_trinn1_sats": ("satsen for trinnskatt trinn 1", "satsen for trinnskatt trinn 1"),
    "trinnskatt_trinn1_grense": ("innslagspunktet for trinnskatt trinn 1", "innslagspunktet for trinnskatt trinn 1"),
    "trinnskatt_trinn2_sats": ("satsen for trinnskatt trinn 2", "satsen for trinnskatt trinn 2"),
    "trinnskatt_trinn2_grense": ("innslagspunktet for trinnskatt trinn 2", "innslagspunktet for trinnskatt trinn 2"),
    "trinnskatt_trinn3_sats": ("satsen for trinnskatt trinn 3", "satsen for trinnskatt trinn 3",
                               "satsen for toppskatt trinn 1", "satsen for toppskatt trinn 1"),
    "trinnskatt_trinn3_grense": ("innslagspunktet for trinnskatt trinn 3", "innslagspunktet for trinnskatt trinn 3",
                                 "innslagspunktet for toppskatt trinn 1 i klasse 0 og 1",
                                 "innslagspunktet for toppskatt trinn 1 i klasse 0 og 1"),
    "trinnskatt_trinn4_sats": ("satsen for trinnskatt trinn 4", "satsen for trinnskatt trinn 4",
                               "satsen for toppskatt trinn 2", "satsen for toppskatt trinn 2"),
    "trinnskatt_trinn4_grense": ("innslagspunktet for trinnskatt trinn 4", "innslagspunktet for trinnskatt trinn 4",
                                 "innslagspunktet for toppskatt trinn 2", "innslagspunktet for toppskatt trinn 2"),
    "trinnskatt_trinn5_sats": ("satsen for trinnskatt trinn 5", "satsen for trinnskatt trinn 5"),
    "trinnskatt_trinn5_grense": ("innslagspunktet for trinnskatt trinn 5", "innslagspunktet for trinnskatt trinn 5"),
    "fellesskatt_ellers": ("satsen for fellesskatt for personlige skattytere og dødsbo utenfor Finnmark og Nord-Troms",
                           "satsen for fellesskatt for personlege skattytarar og dødsbu utanfor Finnmark og Nord-Troms"),
    "fellesskatt_tiltakssone": ("satsen for fellesskatt for personlige skattytere og dødsbo i Finnmark og Nord-Troms",
                                "satsen for fellesskatt for personlege skattytarar og dødsbu i Finnmark og Nord-Troms"),
    "skattore_kommune_maks": ("den høyeste kommunale skattøren for personlige skattytere",
                              "den høgaste kommunale skattøyren for personlege skattytarar"),
    "skattore_fylke_maks": ("den høyeste fylkeskommunale skattøren for personlige skattytere",
                            "den høgaste fylkeskommunale skattøyren for personlege skattytarar"),
    "selskapsskatt": ("satsen selskaper svarer i skatt til staten etter § 3-3 første ledd",
                      "satsen selskap svarar i skatt til staten etter § 3-3 første ledd"),
    "minstefradrag_lonn_ovre": ("den øvre grensen for minstefradrag i lønnsinntekt",
                                "den øvre grensa for minstefrådrag i lønsinntekt",
                                "den øvre grensen for minstefradraget", "den øvre grensa for minstefrådraget"),
    "minstefradrag_lonn_nedre": ("den nedre grensen for minstefradrag i lønnsinntekt",
                                 "den nedre grensa for minstefrådrag i lønsinntekt"),
    "minstefradrag_pensjon_ovre": ("den øvre grensen for minstefradrag i pensjonsinntekt",
                                   "den øvre grensa for minstefrådrag i pensjonsinntekt"),
    "minstefradrag_pensjon_nedre": ("den nedre grensen for minstefradrag i pensjonsinntekt",
                                    "den nedre grensa for minstefrådrag i pensjonsinntekt"),
    "formuesskatt_stat_bunnfradrag": ("beløpsgrensen for formuesskatt til staten for personlige skattytere",
                                      "beløpsgrensa for formuesskatt til staten for personlege skattytarar"),
    "formuesskatt_kommune_maks": ("den høyeste satsen for formuesskatt til kommunene",
                                  "den høgaste satsen for formuesskatt til kommunane"),
    "skattebegrensning_enslige": ("beløpsgrensen for enslige etter skatteloven § 17-1 første ledd",
                                  "beløpsgrensa for einslege etter skattelova § 17-1 første ledd"),
    "foreldrefradrag_ett_barn": ("den øvre grensen for fradrag etter skatteloven § 6-48 for ett barn",
                                 "den øvre grensa for frådrag etter skattelova § 6-48 for eitt barn"),
    "pensjonsfradrag_16_1": ("fradraget etter skatteloven § 16-1 første ledd",
                             "frådraget etter skattelova § 16-1 første ledd"),
    "grunnrenteskatt_vannkraft": ("satsen for grunnrenteskatt i vannkraftverk",
                                  "satsen for grunnrenteskatt i vasskraftverk"),
    "trygdeavgift_lonn": ("satsen for trygdeavgift av lønnsinntekt", "satsen for trygdeavgift av lønsinntekt"),
    "trygdeavgift_naering": ("satsen for trygdeavgift av næringsinntekt", "satsen for trygdeavgift av næringsinntekt"),
    "trygdeavgift_pensjon": ("satsen for trygdeavgift av pensjon (folketrygdloven § 23-3 annet ledd nr. 1)",
                             "satsen for trygdeavgift av pensjon (folketrygdlova § 23-3 andre ledd nr. 1)"),
}
KIND = {"kr": "belop", "pst": "prosent"}
UNIT = {"belop": "kr", "prosent": "prosent", "g": "G", "alder": "år"}


def load(name):
    return [json.loads(l) for l in (ROOT / "data" / name).open(encoding="utf-8")]


def labels() -> dict:
    md = (ROOT / "docs" / "NAVNGITTE_SATSER.md").read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"^\| (\w+) \| \w+ \| ([^|]+) \|", md, re.M):
        label = re.sub(r"\s*\((?:kr|pst\.)\)", "", m.group(2).strip())
        out[m.group(1)] = label[0].lower() + label[1:]
    return out


def doc_name(title: str) -> str:
    title = title.strip().rstrip(".")
    first = title.split()[0]
    return title[0].lower() + title[1:] if first in ("Forskrift", "Lov", "Vedtak", "Stortingsvedtak") else title


def hjemmel(para: str, ledd: int, form: str) -> str:
    if para in (None, "§-", "G"):
        return f"punkt {ledd}" if ledd else ""
    p = "§ " + para.lstrip("§")
    return f"{p} {ORD[form][ledd - 1]} ledd" if ledd and ledd <= 12 else p


def date_text(d: dt.date) -> str:
    return f"{d.day}. {MONTHS[d.month - 1]} {d.year}"


def iso(h):
    return h.get("valid_from") or h.get("in_force")


def build_h3(out: list[dict], both: dict) -> list[dict]:
    """H3 subset (PREREG_UTKAST.md): 200 items stratified on series (and so on type), each in
    bokmål and nynorsk with the same template and answer. One version of each pair is the
    item itself; the other is marked ekstra_språkversjon and is not part of the main measures.
    Allocation: one item per series, the rest by largest remainder in proportion to series
    size; within a series the items are drawn with seed H3_SEED:<serie_id>."""
    by_series = collections.defaultdict(list)
    for o in out:
        by_series[o["serie_id"]].append(o)
    series = sorted(by_series)
    rest = H3_N - len(series)
    sizes = {s: len(by_series[s]) - 1 for s in series}
    total = sum(sizes.values())
    quota = {s: 1 + int(rest * sizes[s] / total) for s in series}
    order = sorted(series, key=lambda s: (-(rest * sizes[s] / total - int(rest * sizes[s] / total)), s))
    for s in order[:H3_N - sum(quota.values())]:
        quota[s] += 1
    pairs = []
    for s in series:
        picked = random.Random(f"{H3_SEED}:{s}").sample(by_series[s], min(quota[s], len(by_series[s])))
        for o in sorted(picked, key=lambda o: o["id"]):
            for form in ("nb", "nn"):
                pairs.append({**o, "id": f"{o['id']}-{form}", "h3_par": o["id"], "målform": form,
                              "spørsmål": both[o["id"]][form], "ekstra_språkversjon": form != o["målform"]})
    with (ROOT / "data" / "items_h3.jsonl").open("w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    return pairs


def main() -> None:
    core = [it for it in load("v3_items.jsonl") if it["clean_v3"] and it["segment"] == "kjerne"]
    # v1 has amounts/rates and ages only; durations (frist) are parked until v2 (PREREG 2b).
    items = [it for it in core if it["group"] != "frist"]
    frist_parked = sum(len(it["v3_values"]) for it in core if it["group"] == "frist")
    cand_title = {c["id"]: c["title"] for c in load("candidates.jsonl")}
    base_title = {}
    for c in load("yearseries.jsonl"):
        for h in c["history"]:
            if "via" not in h:
                base_title[(c["series"], h["year"])] = h["source_title"]
    rows, zero_length = [], 0
    for it in items:
        hist = it["history"]
        kind = KIND.get(it["kind"], it["kind"])
        tail = it["v3_index"]
        units = it.get("v3_units") or [UNIT.get(kind)] * len(tail)
        series_hist = []
        for k, i in enumerate(tail):
            h = hist[i]
            nxt = hist[i + 1] if i + 1 < len(hist) else None  # next version in the full history
            til = (dt.date.fromisoformat(iso(nxt)) - dt.timedelta(days=1)).isoformat() if nxt else None
            til_kind = "neste_versjon" if til else None
            if h.get("valid_to") and (til is None or h["valid_to"] < til):  # rule v3.5: explicit end date
                til, til_kind = h["valid_to"], "periode"
            series_hist.append({"verdi": it["v3_values"][k], "enhet": units[k], "år": h["year"],
                                "gyldig_fra": iso(h), "gyldig_til": til,
                                "gyldighet_grunnlag": h.get("in_force_kind"), "gyldig_til_grunnlag": til_kind,
                                "eksplisitt_periode": [iso(h), h.get("valid_to")]
                                if h.get("in_force_kind") in ("periode_ledd", "periode", "periode_arvet") else None})
        moved = []  # periods moved to another series by a qualifier (rule v3.1): allowed gaps
        for i in it.get("moved_by_qualifier") or []:
            nxt = hist[i + 1] if i + 1 < len(hist) else None
            moved.append({"gyldig_fra": iso(hist[i]), "gyldig_til": (dt.date.fromisoformat(iso(nxt))
                          - dt.timedelta(days=1)).isoformat() if nxt else None})
        for k, i in enumerate(tail):
            h = hist[i]
            e = series_hist[k]
            fra = dt.date.fromisoformat(e["gyldig_fra"])
            til = dt.date.fromisoformat(e["gyldig_til"]) if e["gyldig_til"] else AS_OF
            if fra > AS_OF or til < fra:  # replaced on its first day, or not yet in force
                zero_length += 1
                continue
            ask = fra + min((til - fra) / 2, dt.timedelta(days=182))
            rows.append({"it": it, "h": h, "e": e, "kind": kind, "ask": ask, "hist": series_hist, "moved": moved})
    # A § / ledd chain of an annual decision is a duplicate of a named rate in the same decision
    # when at least half of its year items (same date and value) are in that one named rate; the
    # whole chain is then left out and the named rate kept (the two may cite the base decision
    # and a same-day amendment).
    named = collections.defaultdict(set)
    for r in rows:
        if r["it"]["set"] == "navngitt":
            named[(r["it"]["series"], r["it"]["id"])].add((r["e"]["gyldig_fra"], r["e"]["verdi"]))
    chains = collections.defaultdict(list)
    for r in rows:
        if r["it"]["set"] == "årsserie":
            chains[r["it"]["id"]].append(r)
    dup_chains = set()
    for cid, rs in chains.items():
        keys = {(r["e"]["gyldig_fra"], r["e"]["verdi"]) for r in rs}
        best = max((len(keys & v) for (ser, _), v in named.items() if ser == rs[0]["it"]["series"]), default=0)
        if best * 2 >= len(keys):
            dup_chains.add(cid)
    before = len(rows)
    rows = [r for r in rows if r["it"]["id"] not in dup_chains]
    duplicates_dropped = before - len(rows)
    # language form, balanced within each series
    by_series = collections.defaultdict(list)
    for r in rows:
        by_series[r["it"]["id"]].append(r)
    for sid, rs in by_series.items():
        rng = random.Random(f"{SEED}:{sid}")
        order = sorted(range(len(rs)), key=lambda j: rs[j]["e"]["gyldig_fra"])
        rng.shuffle(order)
        n_nb = len(rs) // 2 + (rng.random() < 0.5 if len(rs) % 2 else 0)
        for pos, j in enumerate(order):
            rs[j]["form"] = "nb" if pos < n_nb else "nn"
    def render(r, form):
        it, h, kind = r["it"], r["h"], r["kind"]
        t = TEMPLATES[form]
        if it["set"] == "navngitt":
            q_names = NAMED_Q[it["rate"]]
            early = len(q_names) == 4 and h["year"] <= (2004 if it["rate"] == "minstefradrag_lonn_ovre" else 2015)
            navn = q_names[(2 if early else 0) + (form == "nn")]
            kilde = NAMED_DOC[it["series"]].format(år=h["year"])
            tmpl = t[kind]
        elif it["set"] == "G":
            navn = None
            kilde = doc_name(base_title.get(("grunnbelop", h["year"]), "vedtaket om grunnbeløpet"))
            tmpl = t["G"]
        else:
            navn = NAME[form][kind]
            if it.get("anchor_phrase"):
                navn += " " + NAME[form]["phrase"].format(p=" ".join(it["anchor_phrase"]))
            if it["set"] == "varig":
                doc = doc_name(cand_title.get(it["id"], it["id"].split("/§")[0]))
            else:
                doc = doc_name(base_title.get((it["series"], h["year"]), f"årsvedtaket for {h['year']}"))
            kilde = f"{doc} {hjemmel(it['paragraph'], it['ledd'], form)}".strip()
            tmpl = t[kind]
        return tmpl.format(navn=navn, kilde=kilde, dato=date_text(r["ask"])) + "\n" + t["svar"]

    out = []
    for r in sorted(rows, key=lambda r: (r["it"]["id"], r["e"]["gyldig_fra"])):
        it, h, e, kind, form = r["it"], r["h"], r["e"], r["kind"], r["form"]
        q = render(r, form)
        both = {"nb": render(r, "nb"), "nn": render(r, "nn")}
        out.append({
            "id": None, "serie_id": it["id"], "år": h["year"], "spørsmål": q, "målform": form,
            "type": kind, "fasitverdi": e["verdi"], "enhet": e["enhet"], "dato_i_spørsmålet": r["ask"].isoformat(),
            "ordrett_kilde": h["text"], "kilde_id": h["source"], "kilde_refid": h.get("source_refid"),
            "gyldig_fra": e["gyldig_fra"], "gyldig_til": e["gyldig_til"],
            "gyldighet_grunnlag": h.get("in_force_kind"), "gyldighet_kilde": h.get("in_force_raw"),
            "gyldig_til_grunnlag": e["gyldig_til_grunnlag"], "eksplisitt_periode": e["eksplisitt_periode"],
            "verdihistorikk": r["hist"], "utflyttede_perioder": r["moved"],
            "overlaps_simpleaudit_105": bool(it.get("overlaps_simpleaudit_105")),
            "sett": it["set"], "lisens": "NLOD 2.0, Stiftelsen Lovdata", "canary": CANARY, "_both": both,
        })
    for n, o in enumerate(out, 1):
        o["id"] = f"norregel-{n:05d}"
    # SimpleAudit #105 overlap for annual series and G, with the rule from extract.py (a fact's
    # value occurs in the series and one of its anchor words in the series' texts or id).
    facts = json.loads((ROOT / "data" / "simpleaudit_facts.json").read_text())["facts"]
    series_out = collections.defaultdict(list)
    for o in out:
        series_out[o["serie_id"]].append(o)
    for sid, os_ in series_out.items():
        if os_[0]["sett"] not in ("årsserie", "G"):
            continue
        excerpt = (sid.replace("/", " ") + " " + " ".join(o["ordrett_kilde"] for o in os_)).casefold()
        vals = {o["fasitverdi"] for o in os_}
        for f in facts:
            try:
                fv = float(str(f["value"]).replace(" ", ""))
            except ValueError:
                continue
            if fv and fv in vals and any(a.casefold() in excerpt for a in f.get("anchors") or []):
                for o in os_:
                    o["overlaps_simpleaudit_105"] = True
    both = {o["id"]: o.pop("_both") for o in out}
    with (ROOT / "data" / "items.jsonl").open("w", encoding="utf-8") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    h3 = build_h3(out, both)
    forms = collections.Counter(o["målform"] for o in out)
    per_series = collections.defaultdict(collections.Counter)
    for o in out:
        per_series[o["serie_id"]][o["målform"]] += 1
    summary = {
        "items": len(out), "series": len(per_series), "seed": SEED, "as_of": AS_OF.isoformat(),
        "by_form": dict(forms), "nn_share": round(forms["nn"] / len(out), 4),
        "by_type": dict(collections.Counter(o["type"] for o in out)),
        "by_set": dict(collections.Counter(o["sett"] for o in out)),
        "max_imbalance_within_series": max(abs(c["nb"] - c["nn"]) for c in per_series.values()),
        "overlaps_simpleaudit_105": sum(o["overlaps_simpleaudit_105"] for o in out),
        "h3_pairs": len(h3) // 2, "h3_series": len({o["serie_id"] for o in h3}),
        "h3_by_type": dict(collections.Counter(o["type"] for o in h3 if not o["ekstra_språkversjon"])),
        "frist_year_items_parked_v2": frist_parked,
        "duplicates_of_named_rates_dropped": duplicates_dropped,
        "duplicate_chains_dropped": sorted(dup_chains),
        "skipped_zero_length_or_future": zero_length,
        "same_value_in_other_provisions": sum(1 for v in collections.Counter(
            (o["kilde_id"], o["fasitverdi"], o["gyldig_fra"]) for o in out).values() if v > 1),
    }
    (ROOT / "data" / "items_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
