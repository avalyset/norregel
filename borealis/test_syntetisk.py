"""Tester analyse_parvis.py på helt syntetiske items og svar (ingen norregel-items, ingen modellsvar).

Kjøres med:  PYTHONDONTWRITEBYTECODE=1 ~/dev/norregel/.venv/bin/python -B F4/analyse/test_syntetisk.py ~/dev/norregel
Skriver forventet mot faktisk utfall til F4/analyse/test_syntetisk_utfall.md og avslutter med kode 1 hvis en test feiler.
"""
import json
import sys
from pathlib import Path

HER = Path(__file__).parent
sys.path.insert(0, str(HER))
import analyse_parvis as AP  # noqa: E402

rot = Path(sys.argv[1]).expanduser().resolve()
A = AP.last_norregel(rot, json.loads((HER / "LAAST_SHA256.json").read_text()))
rader, feil = [], 0


def sjekk(navn, forventet, faktisk):
    global feil
    ok = forventet == faktisk
    feil += not ok
    rader.append(f"| {navn} | `{forventet}` | `{faktisk}` | {'OK' if ok else 'FEIL'} |")


def hist(*par):
    return [{"år": int(d[:4]), "gyldig_fra": d, "verdi": v} for d, v in par]


H = hist(("2018-01-01", 10.0), ("2020-01-01", 12.0), ("2022-01-01", 15.0))
it_ny = {"id": "syn-ny", "serie_id": "SYN-A", "type": "prosent", "fasitverdi": 15.0, "år": 2022, "gyldig_fra": "2022-01-01", "verdihistorikk": H}
it_mid = {"id": "syn-mid", "serie_id": "SYN-A", "type": "prosent", "fasitverdi": 12.0, "år": 2020, "gyldig_fra": "2020-01-01", "verdihistorikk": H}
svar = lambda t: {"completion": t, "error": False}  # noqa: E731

# 1. Klassifisering (norregels låste classify, uendret)
sjekk("korrekt", ("korrekt", None), tuple(A.classify(svar("SVAR: 15 %"), it_ny, {})[k] for k in ("klasse", "under")))
sjekk("utdatert (nyeste avvikende)", "utdatert", A.classify(svar("SVAR: 12 %"), it_ny, {})["klasse"])
sjekk("utdatert (eldre verdi)", "utdatert", A.classify(svar("SVAR: 10 %"), it_ny, {})["klasse"])
sjekk("senere verdi", ("feil", "senere_verdi"), tuple(A.classify(svar("SVAR: 15 %"), it_mid, {})[k] for k in ("klasse", "under")))
sjekk("utolket: ingen svarlinje", ("utolket", "ingen_svarlinje"), tuple(A.classify(svar("Jeg vet ikke."), it_ny, {})[k] for k in ("klasse", "under")))
sjekk("utolket: avslag", ("utolket", "avslag"), tuple(A.classify(svar("SVAR: vet ikke"), it_ny, {})[k] for k in ("klasse", "under")))
sjekk("S-6: 12 er nyeste avvikende", True, AP.utdatert_nyeste(A, A.classify(svar("SVAR: 12 %"), it_ny, {}), it_ny))
sjekk("S-6: 10 er ikke nyeste avvikende", False, AP.utdatert_nyeste(A, A.classify(svar("SVAR: 10 %"), it_ny, {}), it_ny))

# 2. Testene
sjekk("eksakt McNemar ensidig b10=12, b01=2", round(106 / 16384, 6), round(AP.mcnemar_eksakt(12, 2, "større"), 6))
sjekk("eksakt McNemar tosidig b10=5, b01=5", 1.0, AP.mcnemar_eksakt(5, 5))
sjekk("eksakt McNemar uten diskordante par", None, AP.mcnemar_eksakt(0, 0))
sjekk("Holm: 0,01 og 0,04 av to (0,01 ≤ 0,025; 0,04 ≤ 0,05)", {"x": True, "y": True}, AP.holm({"x": 0.01, "y": 0.04}))
sjekk("Holm: 0,03 og 0,04 av to (0,03 > 0,025 stopper)", {"x": False, "y": False}, AP.holm({"x": 0.03, "y": 0.04}))

# 3. Hele analysen på et syntetisk datasett: 30 items i 6 serier
items, ka, kb, man = {}, [], [], {"primær_a_b": []}
for s in range(6):
    for j in range(5):
        i = f"syn-{s}-{j}"
        items[i] = {**it_ny, "id": i, "serie_id": f"SYN-{s}"}
        man["primær_a_b"].append(i)
ids = man["primær_a_b"]
# A (Borealis) utdatert på 12 items der B er korrekt; B utdatert på 2 der A er korrekt; 2 items utolket hos A; resten korrekt hos begge
a_svar = {i: "SVAR: 15 %" for i in ids}
b_svar = {i: "SVAR: 15 %" for i in ids}
for i in ids[:12]:
    a_svar[i] = "SVAR: 12 %"
for i in ids[12:14]:
    b_svar[i] = "SVAR: 10 %"
for i in ids[14:16]:
    a_svar[i] = "Jeg vet ikke."
post = lambda i, t: {"id": i, "modus": "full", "fullføring": t}  # noqa: E731
r = AP.analyser(A, man, items, {"a": [post(i, a_svar[i]) for i in ids], "b": [post(i, b_svar[i]) for i in ids]}, {}, b=2000)
p = r["primær_H_a"]
sjekk("primær: n (begge tolkbare)", 28, p["n"])
sjekk("primær: b10, b01", (12, 2), (p["b10"], p["b01"]))
sjekk("primær: d", round(10 / 28, 6), round(p["d"], 6))
sjekk("primær: p ensidig", round(106 / 16384, 6), round(p["p_ensidig"], 6))
# Kjøring 1 (2026-11-01) forventet «støttet» her og feilet: effekten ligger i 2–3 av 6 serier, klyngebootstrap gir nedre
# grense 0,0, og regelen krever > 0. Koden følger spesifikasjonen; forventningen var feil (F4/analyse/test_syntetisk_utfall_kjoring1_FEIL-I-FORVENTNING.md).
sjekk("primær: tilstand (effekt samlet i få serier)", "inkonklusiv", p["tilstand"])
sjekk("primær: nedre KI-grense (klynget)", 0.0, round(p["ki95"][0], 6))
sjekk("S-1 (alle svar): n", 30, r["sekundære"]["S-1_utdatert_alle_svar"]["n"])
sjekk("S-4 utolket: b10, b01", (2, 0), (r["sekundære"]["S-4_utolket"]["b10"], r["sekundære"]["S-4_utolket"]["b01"]))
sjekk("beskrivende: A utolket ingen_svarlinje", {"ingen_svarlinje": 2}, r["beskrivende"]["a"]["utolket_under"])

# 3b. Samme antall, men effekten spredt: 2 utdaterte hos A i hver serie, B utdatert på 2 items, 2 utolket hos A
a2 = {i: "SVAR: 15 %" for i in ids}
b2 = {i: "SVAR: 15 %" for i in ids}
for s in range(6):
    for j in (0, 1):
        a2[f"syn-{s}-{j}"] = "SVAR: 12 %"
b2["syn-0-2"] = b2["syn-1-2"] = "SVAR: 10 %"
a2["syn-2-3"] = a2["syn-3-3"] = "Jeg vet ikke."
r2 = AP.analyser(A, man, items, {"a": [post(i, a2[i]) for i in ids], "b": [post(i, b2[i]) for i in ids]}, {}, b=2000)
sjekk("spredt: b10, b01", (12, 2), (r2["primær_H_a"]["b10"], r2["primær_H_a"]["b01"]))
sjekk("spredt: tilstand", "støttet", r2["primær_H_a"]["tilstand"])

# 4. Ingen forskjell: like svar gir «ingen effekt av interesse»
r0 = AP.analyser(A, man, items, {"a": [post(i, "SVAR: 15 %") for i in ids], "b": [post(i, "SVAR: 15 %") for i in ids]}, {}, b=2000)
sjekk("like svar: tilstand", "ingen effekt av interesse", r0["primær_H_a"]["tilstand"])

# 5. Manglende primær-item stopper analysen
try:
    AP.analyser(A, man, items, {"a": [post(i, "SVAR: 15 %") for i in ids[:-1]], "b": [post(i, "SVAR: 15 %") for i in ids]}, {}, b=10)
    sjekk("manglende item stopper", "SystemExit", "ingen stopp")
except SystemExit:
    sjekk("manglende item stopper", "SystemExit", "SystemExit")

ut = ["# Test på syntetiske data: forventet mot faktisk", "", "| test | forventet | faktisk | resultat |", "|---|---|---|---|", *rader, "",
      f"**{len(rader) - feil} av {len(rader)} tester OK, {feil} feil.**"]
(HER / "test_syntetisk_utfall.md").write_text("\n".join(ut) + "\n", encoding="utf-8")
print(f"{len(rader) - feil}/{len(rader)} OK")
sys.exit(1 if feil else 0)
