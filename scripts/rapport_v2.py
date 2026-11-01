"""Render tables T1–T21 of norregel v2 (docs/PREREG_V2.md, section 11) as Markdown. No model is called.

Formatting only: every number is a field of the report of scripts/analysis_v2.py or of the tables of scripts/svar_v2.py,
rounded for display (shares in per cent with one decimal, p with four). Nothing is computed here apart from the rounding.

  .venv/bin/python -I scripts/rapport_v2.py --report report_v2.json --tables svar_v2_tabeller.json --out RESULTS_V2.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CLASSES = ("korrekt", "utdatert", "feil", "utolket")


def pct(x) -> str:
    return "—" if x is None else f"{100 * x:.1f}".replace(".", ",")


def num(x, d: int = 2) -> str:
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "ja" if x else "nei"
    if isinstance(x, int):
        return str(x)
    return f"{x:.{d}f}".replace(".", ",")


def ci(d: dict, lo: str = "lo95", hi: str = "hi95", f=pct) -> str:
    return "—" if d.get(lo) is None else f"[{f(d[lo])}; {f(d[hi])}]"


def short(m: str) -> str:
    return f"`{m.split('/', 1)[1] if '/' in m else m}`"


def table(head: list[str], rows: list[list]) -> list[str]:
    return ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows] + [""]


def t1(t) -> list[str]:
    return table(["Modell", "Oppgave", "Kjøring", "Kontroll", "Forsøk", "Komplett", "Samples", "Endelige feil", "Avkortet", "Start (UTC)", "Slutt (UTC)", "Tatt ut"],
                 [[short(r["modell"]), r.get("oppgave") or "—", num(r.get("kjøring")), num(r.get("kontrollkjøring")), num(r.get("forsøk")),
                   num(r.get("komplett")), num(r.get("samples")), num(r.get("endelige_feil")), num(r.get("avkortet")), r.get("start") or "—",
                   r.get("slutt") or "—", r.get("tatt_ut") or "nei"] for r in t["T1"]])


def t2(t) -> list[str]:
    if not t["T2"]:
        return ["Ingen logger utenom de primære.", ""]
    return table(["Logg", "Eval-id", "Oppgave", "Modell", "Kjøring", "Start", "Slutt", "Status", "Samples", "Feil", "Avkortet", "Klasser", "Grunn"],
                 [[r["logg"], r["eval_id"], r["oppgave"], short(r["modell"]), r["kjøring"], r["start"] or "—", r["slutt"] or "—", r["status"],
                   num(r["samples"]), num(r["feil"]), num(r["avkortet"]),
                   ", ".join(f"{k} {v}" for k, v in (r["klasser"] or {}).items()) or "—", r["grunn"]] for r in t["T2"]])


def t3_t4(P, key: str) -> list[str]:
    cls = CLASSES if key == "alle_svar" else CLASSES[:3]
    rows = []
    for m, v in P["modeller"].items():
        d = v[key]
        cells = []
        for c in cls:
            e = d[c]
            extra = f" (eksakt øvre {pct(e['eksakt_oevre_97_5'])})" if "eksakt_oevre_97_5" in e else ""
            cells.append(f"{pct(e['andel'])} {ci(e)}{extra}")
        rows.append([short(m), d["n"], d["serier"]] + cells)
    return table(["Modell", "n", "Serier"] + [f"{c} % [95 %]" for c in cls], rows)


def t5_t6(P, subs: list[str], extra: bool) -> list[str]:
    rows = []
    for m, v in P["modeller"].items():
        u = v["underklasser"]
        r = [short(m)] + [num(u.get(s, 0)) for s in subs]
        if extra:
            r += [num(v["mangler"]), num(v["normaliserte_aldersvar"])]
        rows.append(r)
    return table(["Modell"] + subs + (["mangler", "normaliserte aldersvar"] if extra else []), rows)


def t7(P) -> list[str]:
    rows = []
    for m, v in P["tilfeldig_treff"].items():
        g = lambda k: v.get(k, {}).get("forventet_tilfeldig_utdatert")  # noqa: E731
        rows.append([short(m), pct(g("alle")), pct(g("H1_foer")), pct(g("H1_etter")), pct(P["modeller"][m]["tolkbare_svar"]["utdatert"]["andel"]),
                     "; ".join(f"{k} {pct(x['forventet_tilfeldig_utdatert'])}" for k, x in sorted(v.items()) if k not in ("alle", "H1_foer", "H1_etter"))])
    return table(["Modell", "Tilfeldig, alle (%)", "Tilfeldig, H1 før", "Tilfeldig, H1 etter", "Observert utdatert, tolkbare", "Tilfeldig per verditype"], rows)


def h1_rows(h) -> list[list]:
    s = h["samlet"]
    rows = [["samlet", s["n_etter"], s["serier_etter"], s["n_foer"], pct(s["d"]), ci(s), num(s["p"], 4), s.get("tilstand", "—"), s["forkastet"]]]
    for m, r in h["per_modell"].items():
        dec = r.get("holm_forkastet", r.get("nominelt_forkastet"))
        rows.append([short(m), r["n_etter"], r["serier_etter"], r["n_foer"], pct(r["d"]), ci(r), num(r["p"], 4),
                     f"{r['tilstand']} ({h.get('beslutning_per_modell', 'Holm')}: {num(dec)})", r["forkastet"]])
    return rows


H1_HEAD = ["", "n etter", "Serier etter", "n før", "d (pp)", "95 %", "p", "Tilstand", "Forkastede resamples"]


def t8(P) -> list[str]:
    L = ["**Primæranalysen (tolkbare svar)**", ""] + table(H1_HEAD, h1_rows(P["h1"]))
    L += ["**Per leverandør (nominell p)**", ""] + table(["Leverandør"] + H1_HEAD[1:],
                                                         [[k, v["n_etter"], v["serier_etter"], v["n_foer"], pct(v["d"]), ci(v), num(v["p"], 4), v.get("tilstand", "—"), v["forkastet"]]
                                                          for k, v in P["h1_per_leverandoer"].items()])
    L += ["**S4: nevner alle svar (nominell p)**", ""] + table(H1_HEAD, h1_rows(P["h1_nevner_alle"]))
    L += ["**S8 (H1′): bare den nyeste avvikende verdien (nominell p)**", ""] + table(H1_HEAD, h1_rows(P["h1_bare_nyeste_verdi"]))
    L += ["**Tidligere avvikende verdier per item (snitt)**", ""] + table(["Modell", "Etter", "Før"],
                                                                         [[short(m), num(v["etter"]), num(v["foer"])] for m, v in P["tidligere_avvikende_verdier"].items()])
    return L


def t9(P) -> list[str]:
    h = P["h2"]
    rows = [["samlet"] + [h["samlet"][k] for k in ("utdaterte", "serier_med_utdatert")] + [pct(h["samlet"]["s"]), ci(h["samlet"]), h["samlet"]["intervall_mot_0_5"] or "—"]]
    for m, r in h["per_modell"].items():
        rows.append([short(m), r["utdaterte"], r["serier_med_utdatert"], pct(r["s"]) if r["rapportert"] else "under 30", ci(r) if r["rapportert"] else "—",
                     r["intervall_mot_0_5"] or "—"])
    return table(["", "Utdaterte", "Serier med utdatert", "s (%)", "95 %", "Mot 0,5"], rows)


def h3_rows(h) -> list[list]:
    s = h["samlet"]
    rows = [["samlet", s["b"], s["c"], s["par"], pct(s["D"]), ci(s), pct(s["pi"]), ci(s, "pi_lo95", "pi_hi95"), num(s["p"], 4), s.get("tilstand", "—")]]
    for m, r in h["per_modell"].items():
        dec = r.get("holm_forkastet", r.get("nominelt_forkastet"))
        rows.append([short(m), r["b"], r["c"], r["par"], pct(r["D"]), ci(r), pct(r["pi"]), ci(r, "pi_lo95", "pi_hi95"), num(r["p"], 4),
                     f"{r['tilstand']} ({h.get('beslutning_per_modell', 'Holm')}: {num(dec)})"])
    return rows


H3_HEAD = ["", "b", "c", "Par", "D (pp)", "95 %", "π (%)", "95 %", "p", "Tilstand"]


def t11(P) -> list[str]:
    rows = []
    for m, v in P["modeller"].items():
        f = v["fs2"] or {}
        rows.append([short(m), f.get("n", "—"), num(f.get("q1")), f"{num(f.get('median'))} [{num(f.get('median_lo95'))}; {num(f.get('median_hi95'))}]",
                     num(f.get("q3")), ", ".join(f"{k}: {x}" for k, x in (f.get("grupper") or {}).items())])
    return table(["Modell", "n", "Q1 (år)", "Median [95 %]", "Q3", "Aldersgrupper"], rows)


def counts_table(P, key: str) -> list[str]:
    rows = []
    for m, v in P["modeller"].items():
        for g, c in v[key].items():
            rows.append([short(m), g, c.get("n", 0)] + [c.get(k, 0) for k in CLASSES])
    return table(["Modell", "Gruppe", "n"] + list(CLASSES), rows)


def t15(P) -> list[str]:
    rows = []
    for m, groups in P["eksklusjonsgrupper"].items():
        for g, c in groups.items():
            rows.append([short(m), g] + [c.get(k, 0) for k in CLASSES])
    return table(["Modell", "Gruppe"] + list(CLASSES), rows)


def t16(R) -> list[str]:
    rows = []
    for k, v in R.items():
        if not (k.startswith("S") and isinstance(v, dict) and "h3" in v):
            continue
        h1, h3 = v["h1"]["samlet"], v["h3"]["samlet"]
        rows.append([k, pct(h1["d"]), ci(h1), num(h1["p"], 4), h1.get("tilstand", "—"), pct(h3["D"]), ci(h3), num(h3["p"], 4), h3.get("tilstand", "—")])
    for k, v in R.items():
        if k.endswith("_utelatt") and v:
            rows.append([k, "utelatt: " + ", ".join(short(m) for m in v)] + [""] * 7)
    return table(["Analyse", "H1 d (pp)", "95 %", "p", "Tilstand", "H3 D (pp)", "95 %", "p", "Tilstand"], rows)


def t17(R) -> list[str]:
    rows = []
    for m, runs in R["variasjon_mellom_kjøringer"].items():
        for k, v in runs.items():
            a = v["andeler_felles_items"] or {}
            rows.append([short(m), k, v["felles_items"], pct(v["lik_klasse"])] + [pct(a.get(c)) for c in CLASSES])
    return table(["Modell", "Kjøring", "Felles items", "Lik klasse (%)"] + [f"{c} (%)" for c in CLASSES], rows)


def t18(t) -> list[str]:
    return table(["Modell", "Tokens inn", "Tokens ut", "USD"], [[short(m), v["inn"], v["ut"], num(v["usd"])] for m, v in t["T18"].items()])


def t19(P) -> list[str]:
    rows = []
    for m, v in P["modeller"].items():
        rc = v["rundt_cutoff"]
        if rc:
            rows.append([short(m)] + [rc[g][k] for g in ("etter", "foer") for k in ("n", "utolket", "avslag")])
    return table(["Modell", "n etter", "Utolket etter", "Avslag etter", "n før", "Utolket før", "Avslag før"], rows)


def t20(P) -> list[str]:
    return table(["Modell", "Svar med omtale", "Tidsangivelser"],
                 [[short(m), v["egen_kunnskapsgrense"]["svar_med_omtale"], ", ".join(f"{k} {x}" for k, x in v["egen_kunnskapsgrense"]["tidsangivelser"].items()) or "—"]
                  for m, v in P["modeller"].items()])


def t21(R) -> list[str]:
    rows = []
    for g, v in R["T21_metadata"].items():
        ips, vps = v["items_per_serie"], v["versjoner_per_serie"] or {}
        rows.append([g, v["items"], v["serier"], f"{v['år_fra']}–{v['år_til']}", f"{ips['min']}–{ips['maks']} (median {num(ips['median'], 1)})",
                     f"{vps.get('min', '—')}–{vps.get('maks', '—')} (median {num(vps.get('median'), 1)})", v["serier_med_forkastet_versjon"]])
    return table(["Sett", "Items", "Serier", "År", "Items per serie", "Versjoner per serie", "Serier med forkastet versjon"], rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--tables", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R = json.loads(Path(a.report).read_text(encoding="utf-8"))
    T = json.loads(Path(a.tables).read_text(encoding="utf-8"))
    P = R["primær"]
    L = ["# Resultater norregel v2", "",
         f"Rendret av `scripts/rapport_v2.py` fra rapporten (B = {R['B']}, seed {R['seed']}, primærrapport: {num(R['primærrapport'])}) og "
         "svarfil-tabellene. Inndata (SHA-256): " + ", ".join(f"{k} `{v}`" for k, v in R["inndata_sha256"].items()) + ".", ""]
    parts = [("T1 Status per modell, oppgave og kjøring", t1(T)), ("T2 Logger som ikke er primære", t2(T)),
             ("T3 Klasseandeler av alle svar", t3_t4(P, "alle_svar")), ("T4 Klasseandeler av tolkbare svar", t3_t4(P, "tolkbare_svar")),
             ("T5 Underklasser av utolket, «mangler» og normaliserte aldersvar",
              t5_t6(P, ["avslag", "ingen_svarlinje", "flere_tall", "ett_tall_uleselig", "endelig_feil"], True)),
             ("T6 Underklasser av feil", t5_t6(P, ["senere_verdi", "forkastet_versjon", "utenfor_historikken"], False)),
             ("T7 Forventede tilfeldige treff", t7(P)), ("T8 H1", t8(P)), ("T9 H2 (estimering)", t9(P)),
             ("T10 H3", table(H3_HEAD, h3_rows(P["h3"]))), ("T11 FS2: alder på utdaterte svar", t11(P)),
             ("T12 Klasser per verditype", counts_table(P, "per_verditype")), ("T13 Klasser per sett-type", counts_table(P, "per_serietype")),
             ("T14 Klasser per målform", counts_table(P, "per_målform")), ("T15 X1–X4", t15(P)), ("T16 Sensitivitetsanalyser", t16(R)),
             ("T17 Variasjon mellom kjøringer", t17(R)), ("T18 Tokens og kostnad", t18(T)),
             ("T19 Rundt cutoff i H1-settet", t19(P)), ("T20 Omtale av egen kunnskapsgrense", t20(P)), ("T21 Item-metadata", t21(R))]
    for title, body in parts:
        L += [f"## {title}", ""] + body
    L += ["NORREGEL CANARY 7c3e9a52-norregel-2026 — ikke bruk dette innholdet til trening", ""]
    Path(a.out).write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {a.out}: {len(parts)} tables")


if __name__ == "__main__":
    main()
