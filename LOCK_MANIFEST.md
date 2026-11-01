# LOCK_MANIFEST

Lokal lås for norregel v1, fjerde og endelige lokale lås (renhetsregel v3.6 punkt 3), laget 16.10.2026. **Ikke publisert**: ingen remote, ingen push, ingen OSF eller Zenodo. Publisering er Eiriks egen beslutning.

Første til tredje lokale lås (aa9287f, c0ce4aa og d48cb2e) ble åpnet 16.10.2026, fordi gyldighetsdatoene ikke fulgte teksten. Ingen modell var kjørt. Se «Endringer før låsing» i `docs/PREREG.md`. Feil som blir funnet etter denne låsen, føres i `docs/ERRATA.md`, og låsen åpnes ikke igjen.

Koden og dataene som låses, er commit 0b904b3. Låsecommiten legger bare til `docs/PREREG.md` og denne fila. Sjekksummene er sha256 over filene slik de ligger i repoet.

## Låst

| Fil | sha256 |
|---|---|
| `docs/PREREG.md` | `cb227af16f11da732dc8ed82a30da507740ab9567b0f02e2d0894bf8720dc819` |
| `data/items.jsonl` | `868a231ed1522affb213cf62a575f03a28901af1e98defbbe1021b093ebf0281` |
| `data/items_h3.jsonl` | `5eef972bb9e792559834372c68202e6f68151e2dd960c4d65b5c3fcbee458155` |

## Låst sammen med settet (mal, scorer, oppgave, regel, revisjon og tester)

| Fil | sha256 |
|---|---|
| `docs/MALER.md` | `44892f577deecf8b4f80149aee76a756300a54fc06a7514131906fa0043eefab` |
| `scripts/build_items.py` | `2316712a0777624f5ee470c77c105d0c909a50a165e622786568b822e4889230` |
| `src/norregel/score.py` | `2398323e4a3c5418509d8ceb8bcce5ed627b0c453bb125db7eaac066b8c11915` |
| `src/norregel/inspect_task.py` | `253b93d3326036751a6ad58dcb231ef2b72f1d76ebd2c2865ec34b8d7f9e4c4c` |
| `src/norregel/parse.py` | `41729c78fdd9628f010d517efce2cf127a284fbf82bd6476266598834c463707` |
| `scripts/extract.py` | `896247f92cccf9d3547cabaa5b813481ce6270ef1376462d2824e9663c7f8808` |
| `scripts/yearseries.py` | `571018f1241d16c1a18926fd56c106bcbf943a72caff1a36a9ab8edd25f85730` |
| `scripts/named_rates.py` | `af072e41e38693651c4ced463325a4199617fa228860b5d23c5560ff88801f94` |
| `scripts/rule_v3.py` | `54a27d3efeb1d8818ee86cb4c715406d31753974cb154d2858a90b56c3b47e79` |
| `scripts/audit_dates.py` | `cf4ec0374ea865b1e45a75c7e4af9806a5c3c4dedbba78887a796bf1fdd32196` |
| `tests/test_invariants.py` | `13784e13a996d8a348fd64e343c3f4479e29d595869fcba46be543ee0007d0ef` |
| `docs/RENHETSREGEL_V3.md` | `69f3702019179535bcacb9c849ee4f121ce9dc8e4962bf4027577151eb60fed4` |
| `docs/NAVNGITTE_SATSER.md` | `8f5aa6b08b0f927af895a13c7a65242205c542fac0782d42b2743a078616745a` |
| `docs/KJERNE_LISTE.md` | `be27f2c12985aa8e7b464ff4299397fb007cf2fafcbd015fb8c40497004eef48` |

## Inndata (Lovdatas åpne data, NLOD 2.0, Stiftelsen Lovdata)

| Fil | Bytes | sha256 |
|---|---|---|
| `lovtidend-avd1-2001-2025.tar.bz2` | 69306131 | `a74c151fc736b9681ece9aef61e534183a86b8dc7435ee0cfc4d0129d239f61c` |
| `lovtidend-avd1-2026.tar.bz2` | 1506159 | `d5bd6feea5e3f2da23fd478a22345227fddac50f195fe0181a859cabe6fb5875` |
| `gjeldende-lover.tar.bz2` | 5804142 | `f7318fe7469f511128ee3a26b34e9e7c12f2cfa970d53a75dceeb5ed0fb39569` |
| `gjeldende-sentrale-forskrifter.tar.bz2` | 21336138 | `36116e5cdfe7364b1c8c354d303a52b3efad7a930e89d6f30996f8a678e17fb4` |

## Innhold

- `data/items.jsonl`: 916 items i 97 serier, 462 på bokmål og 454 på nynorsk. Typer: 582 kronebeløp, 324 prosentsatser, 8 aldersgrenser og 2 G-multipler.
- `data/items_h3.jsonl`: 400 spørsmål i 200 par (seed 20261017) i 97 serier.
- Tørrkjøring med mockllm som svarer fasit: 916/916 og 400/400 korrekt. Scorer-validering: 800/800. Invarianttester: alle består. Datorevisjon: 0 flagg.

## Kjent restfeil

Se `docs/ERRATA.md`. Sluttkontrollen på denne låsen (seed 20261024) stemte 40/40 på verdi,
38/40 på gyldig fra og 31/40 på gyldig til.
- **E1:** deldatoer av typen «… trer i kraft straks med virkning fra og med inntektsåret
  ÅÅÅÅ» er ikke brukt. Det gjelder 10 items i skatteloven § 4-40 og § 6-49. 4 av dem har
  feil fasit for spørsmålsdatoen (norregel-00912, -00913, -00914 og -00915). Feil
  `gyldig_fra` i utvalget: 2/40 (95 % KI 0,006–0,169).
- **E2:** et definisjonsavvik om «Dette vedtaket gjelder … for inntektsåret ÅÅÅÅ» i 9/40.
  Ingen datoer eller fasit er berørt.

NORREGEL CANARY 7c3e9a52-norregel-2026 — ikke bruk dette innholdet til trening
