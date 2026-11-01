# Prøvekjøringer av v2-koden

Skrevet 17.10.2026, etter rettingene fra Stage 1-vurderingen, runde 2, og kjørt på nytt etter at Opus 5.5 ble tatt ut (`PREREG_V2.md`, avvik A-V2-1). Formålet er bare å vise at koden kjører med de
preregistrerte innstillingene. Ingen modell er kalt. Tallene fra de syntetiske svarene sier ingenting om modellene.

## Analysen på syntetiske svar

- **Svar:** `scripts/v2_syntetisk.py` trakk 41 040 syntetiske svar med fast seed (20261117) for de 11 modellene i
  `docs/v2_modeller.json`.
  - Hver modell fikk R kjøringer.
  - Modellene med R = 1 fikk en kontrollkjøring på de 100 kontrollitemene (seed 20261118).
  - H3-svarene gjelder det låste H3-settet `data/items_h3_v2.jsonl` (1 760 spørsmål).
  - Etter cutoff var utdaterte svar og avslag gjort hyppigere, så H1 har en effekt å finne.
  - Svarene ligger utenfor repoet, fordi de er laget av fasiten. SHA-256 for svarfila begynner med `cddc030543f36516`.
- **Kommando:** `.venv/bin/python -I scripts/analysis_v2.py --models docs/v2_modeller.json --answers <syntetiske svar>
  --pairs data/items_h3_v2.jsonl --out <rapport>` med B = 10 000 (standard). Returkode 0. Med 12 modeller tok kjøringen 61 sekunder, med toppminne 230 MB.
- **Deler i rapporten:**
  - B, seed, primærrapport (true) og inndata_sha256;
  - primær, S1_alle_916, S2_scorer_v1, S3_uten_flaggede, S4_nevner_alle_svar, S5_reliable_knowledge_cutoff, S7_uten_errata
    og S9_foer_siste_24_maaneder;
  - variasjon_mellom_kjøringer og T21_metadata;
  - S6_kjøring_2 og S6_kjøring_3, begge uten utelatte modeller.

  S8 ligger i primærdelen som `h1_bare_nyeste_verdi`.
- **H1 samlet (syntetisk):** n_etter = 317, serier_etter = 56, n_foer = 3604, d = 0,3893, intervall [0,3379; 0,4423],
  forkastet = 0, p = 0,0001, tilstand «støttet».
  - Per modell med Holm: Opus 4.5 og Opus 4.6 er «ikke testet», fordi de har færre enn 30 tolkbare svar etter cutoff. De
    seks andre er «støttet».
  - I sensitivitetsanalysene står beslutningen per modell som «nominell p».
- **S9 (syntetisk):** n_foer = 698, d = 0,3864, intervall [0,3287; 0,4454].
- **H2 samlet (syntetisk, estimering):** 621 utdaterte svar i 75 serier, s = 0,7118, intervall [0,6721; 0,7508], «over 0,5».
  Ingen p-verdi.
- **H3 samlet (syntetisk):** b = 2346, c = 2303, 9 680 par, D = −0,0044, intervall [−0,0173; 0,0082], π = 0,5046,
  intervall [0,4915; 0,5181], p = 0,2519, tilstand «inkonklusiv».
- **Resamples forkastet:** 0 for både H1, H2 og H3.
- **Andre kontroller:**
  - S7 er lik primæranalysen, fordi `data/errata_v2.txt` er tom.
  - «Mangler» og normaliserte aldersvar er 0 for alle 11 modellene.
  - T21 gir 880 items i 96 serier, årene 2001–2026, 1–26 items per serie (median 6,0), 2–27 versjoner per serie
    (median 7,0) og 12 serier med forkastet versjon, som i tillegget A2.
- **Rendring:** `scripts/rapport_v2.py` rendret T1–T21 fra rapporten. T1, T2 og T18 ble rendret fra svarfil-tabellene i
  prøven av `svar_v2.py` nedenfor. Returkode 0.
- **SHA-256 for rapporten:** `9cc5f579f7ea6dc3258a3e488ccdc65e2851d4b9440385411b417cd4d2da80bb`.

## Testene

`tests/test_analysis_v2.py` passerte:

- underklassene stemmer med `score_v2.read` på alle 4 315 v1-svar med svarlinje (2 838 lest, 1 454 uten tall, 23 med flere
  tall);
- 12 av alle 97 serier har forkastede versjoner. Det er de samme 12 som blant de 96 primærseriene;
- dubletter og en manglende rad stopper analysen;
- beslutningen per modell er Holm i primæranalysen og nominell p utenfor;
- 24-månedersvinduet i S9 gir 2 av 4 før-items i testtilfellet;
- «67 år og 6 måneder» normaliseres og telles, og tellingen på v1-svarene er 0 for alle fem modellene, som i
  `docs/RESULTS.md`.

## Kjøreskriptet, pilotreglene og svarfila uten modellkall

- **`scripts/run_v2.sh --dry-run`** for `pilot`, `api`, `lokal` og `retry` skrev kommandoene og opprettet ingen filer
  (`logs/run_v2` fantes ikke etterpå).
  - Vaktene ble rapportert: låsen var ikke oppdatert, og forhåndskontrollene og nøklene manglet.
  - `bash -n` ga ingen feil.
- **`scripts/pilot_regler_v2.py`** ble prøvd på v1-pilotloggene (`logs/pilot`), med utfallet skrevet utenfor repoet. Prøven ble gjort med modellista før avvik A-V2-1, da Opus 5.5 var med.
  - Den fant komplette piloter for de tre v1-API-modellene og de to lokale.
  - Den regnet pilotkostnaden (0,37 USD), fremskrivingen for de tre API-modellene og K3 (95,6 %).
  - Den satte «fortsett» til usann, fordi de sju andre API-modellene ikke har noen pilot.
- **`scripts/svar_v2.py`** ble prøvd på v1-loggene lagt i v2-oppsettet, med pilotutfallet over.
  - Den skrev 45 rader i T1.
  - De tre H3-loggene fra v1 (en annen oppgave) kom i T2 med grunnen «ingen forventet oppgave».
  - Ingen modell ble komplett, fordi v1-loggene ikke har H3-oppgaven i v2-form. Det er som ventet.
- **`scripts/build_h3_v2.py`** ble kjørt på nytt og skrev:
  - «lock 4 reproduced (items.jsonl and items_h3.jsonl identical); v1 questions in the new set: 378, identical: 378;
    wrote data/items_h3_v2.jsonl: 880 pairs, 1760 questions»;
  - SHA-256 uendret, `6313775b344a33360d2f250f1731aa9fd54c2fbd460f97ae01f442fd532532ba`.
