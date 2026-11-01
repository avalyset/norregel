# Tillegg etter fagfellevurdering

**Skrevet etter fagfellevurderingen 17.10.2026. Ikke preregistrert. Alt i dette dokumentet er deskriptivt eller utforskende.** Tallene er regnet av `scripts/tillegg_vurdering.py` fra eksisterende svar og metadata; ingen modell er kjørt, ingen ny test er gjort, og ingen tall her erstatter `docs/RESULTS.md`.

Stier som `logs/`, `data/`, `docs/` og `scripts/` viser til det lokale repoet. Logg- og datafilene publiseres ikke.

## A0. Tidslinje før første modellkall

- **Zenodo v1** ble publisert 2026-10-16 16:18:04 UTC (`docs/ZENODO_DOI.md:87`), med fire filer: `PREREG.md`, `PREREG_TILLEGG.md`, `LOCK_MANIFEST.md` og `exclusions_tillegg.json`. Kjøreprotokollen og modellista var ikke med.
- **Kjøreprotokollen og modellista** ble committet lokalt i `3c554cff` 2026-10-16 16:30:44 UTC (`git log`); de ble publisert i v1.1.
- **Første logg med benchmark-items:** 2026-10-16 16:30:54 UTC (pilotforsøket med Haiku som feilet lokalt, A1). Første pilotlogg med besvarte samples: 2026-10-16 16:31:39 UTC. Første logg i hovedkjøringen: 2026-10-16 16:45:40 UTC.

## A1. Kjøringer som ikke er med i analysen

Tillegget sier «Every run is reported» (`docs/PREREG_TILLEGG.md:202`). Tabellen viser hver Inspect-logg i `logs/` som ikke er en primærlogg i `docs/RESULTS.md` avsnitt 1. For hver logg står eval-id, oppgave, modell, tid fra logghodet, status, antall samples i loggen, samples med feil, avkortede svar (`max_tokens`), og klassene etter scorer v2 for de samplene som finnes (korrekt / utdatert / feil / utolket; et sample med feil er utolket). Klassene er regnet her og teller ikke i resultatene.

Antall logger: 11.

| Logg | Eval-id | Oppgave | Modell | Start – slutt (UTC) | Status | Samples | Feil | Avkortet | Klasser (scorer v2) | Grunn (kilde) |
|---|---|---|---|---|---|---|---|---|---|---|
| `2026-10-16T16-30-54-00-00_norregel-v2_kYaVmvMoyEWbbpUSefWNzP.eval` | `LNg22yzgL6tnmcVALknvbu` | `norregel_v2` | `anthropic/claude-haiku-4-5-20251001` | 2026-10-16 16:30:54 – 2026-10-16 16:31:07 | `success` | 20 | 20 | 0 | 0 / 0 / 0 / 20 | pilotforsøk med `anthropic` 1.15.0, feilet lokalt (A1) (`docs/RUN_PROTOCOL.md:216`) |
| `2026-10-16T16-31-39-00-00_norregel-v2_hc5SKLaC8Fj2egXmqeJ5r9.eval` | `Yg6XHRqbnhBDvKXYYfGMLx` | `norregel_v2` | `anthropic/claude-haiku-4-5-20251001` | 2026-10-16 16:31:39 – 2026-10-16 16:31:45 | `success` | 20 | 0 | 0 | 0 / 0 / 1 / 19 | pilot, teller ikke i resultatene (`docs/RUN_PROTOCOL.md:165`) |
| `2026-10-16T16-32-18-00-00_norregel-v2_XvwLyTPbrgBUriu2QePBhM.eval` | `ZH2z4oQ7cferBFqEr5Divd` | `norregel_v2` | `anthropic/claude-opus-5-5` | 2026-10-16 16:32:18 – 2026-10-16 16:32:46 | `success` | 20 | 0 | 0 | 10 / 1 / 9 / 0 | pilot, teller ikke i resultatene (`docs/RUN_PROTOCOL.md:165`) |
| `2026-10-16T16-32-01-00-00_norregel-v2_SJRZPZXbbMjeAiv48gBst2.eval` | `YLSWFUWZQpPXXfJrYeA7WY` | `norregel_v2` | `anthropic/claude-sonnet-4-6` | 2026-10-16 16:32:01 – 2026-10-16 16:32:15 | `success` | 20 | 0 | 0 | 9 / 1 / 8 / 2 | pilot, teller ikke i resultatene (`docs/RUN_PROTOCOL.md:165`) |
| `2026-10-16T16-41-54-00-00_norregel-v2_GhQyFnkokYs6kVVQYezs9T.eval` | `hNtVWXSFpZ4YWGLdhwP5QC` | `norregel_v2` | `ollama/hf.co/ltg/normistral-7b-warm-instruct:Q4_K_M` | 2026-10-16 16:41:54 – 2026-10-16 16:45:09 | `success` | 20 | 0 | 1 | 0 / 0 / 0 / 20 | pilot, teller ikke i resultatene (`docs/RUN_PROTOCOL.md:165`) |
| `2026-10-16T17-52-39-00-00_norregel-v2_ZsTiPRBxiCuZuRPYcnPFNA.eval` | `WnowVs8hdsRzqxtGGZifnr` | `norregel_v2` | `ollama/nb-llama-3.1-8b-instruct-cardtmpl:latest` | 2026-10-16 17:52:39 – 2026-10-16 17:59:29 | `success` | 20 | 0 | 7 | 1 / 1 / 4 / 14 | pilot, teller ikke i resultatene (`docs/RUN_PROTOCOL.md:165`) |
| `2026-10-16T16-33-05-00-00_norregel-v2_8aGN8uLonM6ovCGBbXbcRo.eval` | `XzMgw3NsGoC836HF6eS5ma` | `norregel_v2` | `ollama/nb-llama-3.1-8b:latest` | 2026-10-16 16:33:05 – 2026-10-16 16:41:29 | `success` | 20 | 0 | 9 | 1 / 0 / 4 / 15 | pilot, teller ikke i resultatene (`docs/RUN_PROTOCOL.md:165`) |
| `2026-10-16T17-49-17-00-00_norregel-v2_VHYcxG67KpuTWcqTzcCcNW.eval` | `d8YzCK6eFeBQgv3a5H7uVH` | `norregel_v2` | `ollama/normistral-7b-warm-instruct-cardtmpl:latest` | 2026-10-16 17:49:17 – 2026-10-16 17:51:29 | `success` | 20 | 0 | 0 | 0 / 0 / 0 / 20 | pilot, teller ikke i resultatene (`docs/RUN_PROTOCOL.md:165`) |
| `2026-10-16T17-51-32-00-00_norregel-v2_2E4TXpawmMRjruvwXKEGwQ.eval` | `fAMGZTfxKbBwFTBvw8x8Y9` | `norregel_v2` | `ollama/normistral-7b-warm-instruct-cardtmpl:latest` | 2026-10-16 17:51:32 – 2026-10-16 17:51:58 | `cancelled` | 5 | 1 | 0 | 0 / 0 / 0 / 5 | avbrutt etter regelen i A4, som A5 opphevet (`AVBRUTT.md` i mappa) (`docs/RUN_PROTOCOL.md:244`) |
| `2026-10-16T16-45-40-00-00_norregel-v2_S6uZR4AUjc4XjUJNhqBz5D.eval` | `C83ajW9hV6EXBWPRk5kHFb` | `norregel_v2` | `ollama/nb-llama-3.1-8b:latest` | 2026-10-16 16:45:40 – 2026-10-16 17:42:24 | `cancelled` | 109 | 1 | 50 | 6 / 3 / 19 / 81 | forkastet før analyse, se A3 (`FORKASTET.md` i mappa) (`docs/RUN_PROTOCOL.md:236`) |
| `2026-10-17T01-12-43-00-00_norregel-v2_JXFZRTwEtxMsDPJ7XoMkKM.eval` | `9GdNHJi6vrVGaApHzLd9eX` | `norregel_v2` | `ollama/normistral-7b-warm-instruct-cardtmpl:latest` | 2026-10-17 01:12:43 – 2026-10-17 02:16:00 | `cancelled` | 92 | 1 | 3 | 0 / 0 / 0 / 92 | forsøk 1, stoppet og tatt opp igjen med `inspect eval-retry` (A6); forsøk 2 er primærloggen (`docs/RUN_PROTOCOL.md:258`) |

## A2. Serietyper, tidsspenn og serielengder

`PREREG.md` lover antall items per sett (`docs/PREREG.md:181`). Feltet `sett` i hvert item gir typen: varig (varige bestemmelser), årsserie (årsforskrifter kjedet etter tittel), G (grunnbeløpet) og navngitt (navngitte satser i skatte- og trygdeavgiftsvedtaket).

| Sett | Items (alle 916) | Items (primærsettet) | Serier (primærsettet) |
|---|---|---|---|
| varig | 265 | 235 | 48 |
| årsserie | 92 | 92 | 21 |
| G | 26 | 26 | 1 |
| navngitt | 533 | 527 | 26 |
| sum | 916 | 880 | 96 |

- **Tidsspenn, primærsettet:** gyldighetsår fra 2001 til 2026; datoene i spørsmålene fra 2001-10-30 til 2026-09-08.
- **Serielengde, primærsettet:** items per serie er minst 1, median 6,0 og høyst 26 (96 serier).
- **Versjoner i historikken:** antall daterte versjoner i seriens historikk er minst 2, median 7,0 og høyst 27.
- Historikken er den rene serien etter renhetsregel v3. Om en serie er avkortet i forhold til bestemmelsens første verdi, står ikke i item-metadataene og er ikke talt her.

## A3. Andel korrekt blant tolkbare svar, og utolket før og etter cutoff

Tolkbare svar er svar i klassene korrekt, utdatert og feil (ikke utolket). Andelene under er av de tolkbare svarene i primærsettet (880 items). Hovedmålet i `docs/RESULTS.md` er andel av alle svar.

| Modell | Tolkbare svar | Korrekt av tolkbare | Utdatert av tolkbare | Feil av tolkbare |
|---|---|---|---|---|
| Haiku 4.5 | 53 av 880 | 7,5 % | 1,9 % | 90,6 % |
| Sonnet 4.6 | 771 av 880 | 45,9 % | 7,4 % | 46,7 % |
| Opus 5.5 | 876 av 880 | 46,9 % | 6,5 % | 46,6 % |
| NB-Llama 8B | 276 av 880 | 27,2 % | 4,0 % | 68,8 % |
| NorMistral 7B | 2 av 880 | 0,0 % | 0,0 % | 100,0 % |

**H1-settet (567 items), API-modellene.** «Etter» er items med `gyldig_fra` etter modellens cutoff, som i H1. Andel utolket er av alle svar i gruppen; klassene i «etter» er tall.

| Modell | Cutoff | n etter / før | Utolket etter | Utolket før | Klasser etter (korrekt / utdatert / feil / utolket) |
|---|---|---|---|---|---|
| Haiku 4.5 | 2025-07-31 | 56 / 511 | 56 av 56 (100,0 %) | 475 av 511 (93,0 %) | 0 / 0 / 0 / 56 |
| Sonnet 4.6 | 2026-01-31 | 9 / 558 | 8 av 9 (88,9 %) | 74 av 558 (13,3 %) | 0 / 0 / 1 / 8 |
| Opus 5.5 | 2026-06-30 | 1 / 566 | 0 av 1 (0,0 %) | 4 av 566 (0,7 %) | 1 / 0 / 0 / 0 |

**Grupper under leverandørens «reliable knowledge cutoff»** (bare antall items; ingen test). Datoen er siste dag i måneden som `docs/MODELLER.md` oppgir.

| Modell | Reliable knowledge cutoff | n etter / før |
|---|---|---|
| Haiku 4.5 | 2025-02-28 (Feb 2025, `docs/MODELLER.md:26`) | 64 / 503 |
| Sonnet 4.6 | 2025-08-31 (Aug 2025, `docs/MODELLER.md:36`) | 36 / 531 |
| Opus 5.5 | 2026-06-30 (Jun 2026, `docs/MODELLER.md:45`) | 1 / 566 |

## A4. Hva intervallene utelukker

Intervallene er de tosidige 95 %-intervallene i `docs/RESULTS.md` (klyngebootstrap over serier), bortsett fra H3-intervallet fra b og c, som er nytt her. Verdier utenfor et intervall er ikke forenlige med dataene på 95 %-nivå. Det er ikke regnet noen styrke i etterkant.

**H1** (d = andel utdatert etter minus før cutoff, prosentpoeng):

- Haiku 4.5: d = 0,0 [0,0; 0,0], 56 items etter i 56 serier og 511 før; utdaterte svar: 0 etter og 0 før. Begge gruppene har null utdaterte svar, så d er 0 i hver resample; testen sammenligner 0 med 0 og sier ikke noe om H1.
- Sonnet 4.6: d = -9,1 [-13,6; -5,1], 9 items etter i 9 serier og 558 før; utdaterte svar: 0 etter og 51 før. Gruppen «etter» er under minimum (30 items fra 5 serier), og d er rapportert uten test. Med 0 utdaterte svar etter cutoff er andelen etter 0 i hver resample der gruppen finnes, så intervallet er intervallet for minus andelen utdatert før, i de resamplene der en serie med et item etter cutoff er trukket (9 998 av 10 000). Det er ikke evidens mot H1.
- Opus 5.5: d = -9,2 [-13,5; -5,6], 1 item etter i 1 serie og 566 før; utdaterte svar: 0 etter og 52 før. Gruppen «etter» er under minimum (30 items fra 5 serier), og d er rapportert uten test. Med 0 utdaterte svar etter cutoff er andelen etter 0 i hver resample der gruppen finnes, så intervallet er intervallet for minus andelen utdatert før, i de resamplene der en serie med et item etter cutoff er trukket (6 304 av 10 000). Det er ikke evidens mot H1.

**H2** (s = andel av de utdaterte svarene som er den nyeste avvikende verdien):

- Haiku 4.5: 0 utdaterte svar, under minimum (30); ingen test.
- Sonnet 4.6: s = 62,0 % [45,8; 81,4] av 50 utdaterte svar i 18 serier. Intervallet utelukker s under 45,8 % og over 81,4 %; den ensidige nedre 95 %-grensen er 48,1 %. H2 påstår s > 50 %, og 50 % ligger inne i intervallet.
- Opus 5.5: s = 50,0 % [31,4; 73,0] av 46 utdaterte svar i 19 serier. Intervallet utelukker s under 31,4 % og over 73,0 %; den ensidige nedre 95 %-grensen er 34,0 %. H2 påstår s > 50 %, og 50 % ligger inne i intervallet.

**H3** (nynorsk minus bokmål, andel korrekt, prosentpoeng; 189 par):

Det nye intervallet bruker bare b og c: et eksakt Clopper–Pearson-intervall [πL; πU] for c/(b + c), omregnet til differansen (c − b)/n = (b + c)(2π − 1)/n med n = 189, betinget på b + c. Det tar ikke hensyn til variasjon i b + c eller til at parene klynger seg i serier, og er derfor smalere enn bootstrap-intervallet fra `docs/RESULTS.md`, som står ved siden av.

| Modell | b | c | Differanse | Intervall fra b og c | Bootstrap-intervall (RESULTS) |
|---|---|---|---|---|---|
| Haiku 4.5 | 1 | 0 | -0,5 | [-0,5; 0,5] | [-1,6; 0,0] |
| Sonnet 4.6 | 9 | 3 | -3,2 | [-5,7; 0,9] | [-8,6; 1,1] |
| Opus 5.5 | 3 | 8 | 2,6 | [-1,3; 5,1] | [-1,0; 6,6] |
| NB-Llama 8B | 6 | 1 | -2,6 | [-3,7; 0,6] | [-6,7; 0,5] |
| NorMistral 7B | 0 | 0 | 0,0 | ikke definert (b + c = 0) | [0,0; 0,0] |

- Haiku 4.5: intervallet fra b og c utelukker en nynorsk-ulempe større enn 0,5 pp og en nynorsk-fordel større enn 0,5 pp.
- Sonnet 4.6: intervallet fra b og c utelukker en nynorsk-ulempe større enn 5,7 pp og en nynorsk-fordel større enn 0,9 pp.
- Opus 5.5: intervallet fra b og c utelukker en nynorsk-ulempe større enn 1,3 pp og en nynorsk-fordel større enn 5,1 pp.
- NB-Llama 8B: intervallet fra b og c utelukker en nynorsk-ulempe større enn 3,7 pp og en nynorsk-fordel større enn 0,6 pp.

## A5. Restfeilrate i fasit

- **Verdikontroller:** 360 kontroller av enkeltitems i ni blinde runder à 40 (fem runder før alder-rettelsen og sluttkontrollene på de fire låsene); verdien stemte i 359. Avviket var i runde 1 og var vår feil, rettet før låsing (`docs/KRYSSKONTROLL_V3.md:9`).
- **Sluttkontrollen på lås 4** (40 items, seed 20261024) er den eneste som trekker fra det endelige settet: feil fasit for spørsmålsdatoen i 1 av 40, 95 % Clopper–Pearson-intervall [0,001; 0,132] (`docs/ERRATA.md:74`). Det itemet er i X1 og ekskludert.
- **Primærsettet:** 37 av de 40 er i primærsettet. Blant dem har 0 feil fasit for spørsmålsdatoen og 0 feil verdi; 1 har en annen gyldig-fra-dato enn underagenten; det er flagget (E1) og har riktig fasit.
- **Øvre grense:** 0 av 37 gir et 95 % Clopper–Pearson-intervall [0,000; 0,095] (øvre grense 9,5 %) for andelen items i primærsettet med feil fasit. Primærsettet har 843 items som ikke er kontrollert i sluttkontrollen; den øvre grensen tilsvarer omtrent 80 av dem. For feil verdi i kilden er intervallet det samme ([0,000; 0,095]).
- Grensen gjelder feil som en blind gjenuttrekking kan finne. Sensitivitetsanalyse S3 tar bare ut de 7 kjente flaggede itemene og dekker ikke ukjente feil.

## A6. Modellenes omtale av egen kunnskapsgrense

Svar på hovedoppgaven (alle 916 items) som inneholder «kunnskapsgrens», «treningsdata» eller «kunnskapsbase» (uavhengig av store og små bokstaver). Tidsangivelsen er den første måned eller periode med årstall i de 40 tegnene etter nøkkelordet, innen samme setning; ett tall per svar. Ingen svar er sitert.

| Modell | Svar med omtale | Av dem i primærsettet | Av dem utolket | Tidsangivelser i svarene |
|---|---|---|---|---|
| Haiku 4.5 | 117 | 105 | 117 | «april 2024» 69, «mai 2026» 1, «uten tidsangivelse» 47 |
| Sonnet 4.6 | 12 | 11 | 10 | «juli 2025» 1, «tidlig 2025» 2, «uten tidsangivelse» 9 |
| Opus 5.5 | 2 | 2 | 0 | «uten tidsangivelse» 2 |

Leverandørens datoer er «Jul 2025» (treningsdata) og «Feb 2025» (reliable knowledge) for Haiku 4.5 (`docs/MODELLER.md:26`), og «Jan 2026» og «Aug 2025» for Sonnet 4.6 (`docs/MODELLER.md:36`).

## A7. Avkortede svar og repetisjonsløkker

Avkortet = `stop_reason` `max_tokens` i primærloggen. Løkke = et avkortet svar der den hyppigste ikke-tomme linjen (uten mellomrom i endene) forekommer minst 3 ganger. Definisjonen er satt her, etter kjøringene.

| Modell | Oppgave | Svar | Avkortet | Av dem løkker |
|---|---|---|---|---|
| Haiku 4.5 | hovedoppgave | 916 | 0 | 0 |
| Haiku 4.5 | H3 | 400 | 0 | 0 |
| Sonnet 4.6 | hovedoppgave | 916 | 0 | 0 |
| Sonnet 4.6 | H3 | 400 | 0 | 0 |
| Opus 5.5 | hovedoppgave | 916 | 0 | 0 |
| Opus 5.5 | H3 | 400 | 0 | 0 |
| NB-Llama 8B | hovedoppgave | 916 | 297 | 292 |
| NB-Llama 8B | H3 | 400 | 138 | 133 |
| NorMistral 7B | hovedoppgave | 916 | 10 | 6 |
| NorMistral 7B | H3 | 400 | 11 | 7 |

NORREGEL CANARY 7c3e9a52-norregel-2026 — ikke bruk dette innholdet til trening
