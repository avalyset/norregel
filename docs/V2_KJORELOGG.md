# Kjørelogg v2

Ført under kjøringen etter `docs/PREREG_V2.md`. Låsen er commit `ef205af` (Zenodo 10.5281/zenodo.23437444) for piloten og
hovedoppgavene, og `d68ce0d` for H3 (A-V2-6 og A-V2-7 i `docs/AVVIK_V2.md`). Tider i UTC er fra logghodene.

## Pilot, 2026-10-17

`scripts/run_v2.sh pilot` startet 13:54:47 og avsluttet 14:33 med exit 0. Alle elleve loggene har status `success` og
20 samples.

| Modell | Start–slutt | Feil | Tenketokens |
|---|---|---|---|
| `anthropic/claude-haiku-4-5-20251001` | 13:54:50–13:54:56 | 0 | 0 |
| `anthropic/claude-opus-4-5-20251101` | 13:54:59–13:55:07 | 0 | 0 |
| `anthropic/claude-opus-4-6` | 13:55:10–13:55:26 | 0 | 0 |
| `anthropic/claude-sonnet-4-6` | 13:55:29–13:55:39 | 0 | 0 |
| `google/gemini-2.5-flash` | 13:55:42–13:58:10 | 0 | 15 877 |
| `google/gemini-2.5-flash-lite` | 13:58:13–14:03:19 | **20** | 0 |
| `google/gemini-2.5-pro` | 14:03:23–14:08:27 | **20** | 0 |
| `google/gemma-4-26b-a4b-it` | 14:08:31–14:16:07 | 0 | 170 567 |
| `google/gemma-4-31b-it` | 14:16:11–14:24:03 | 0 | 26 924 |
| `ollama/nb-llama-3.1-8b-instruct-cardtmpl:latest` | 14:24:17–14:30:51 | 0 | 0 |
| `ollama/normistral-7b-warm-instruct-cardtmpl:latest` | 14:31:03–14:33:12 | 0 | 0 |

- **Forhåndssjekkene** for de lokale modellene passerte (A2 og A3).
- **Gemini 2.5 Flash-Lite og Gemini 2.5 Pro:** alle 20 samples endte i feil etter forsøkene. Feilmeldingen er for begge
  «This model models/gemini-2.5-… is no longer available to new users». Ingen av modellene ga et eneste svar.
- **Pilotreglene** (`scripts/run_v2.sh regler`, `logs/run_v2/pilot_utfall.json`):
  - Pilotkostnaden er 0,25 USD etter prislista, og fremskrevet kostnad 57,17 USD (tak 400). K6 tar ingen modell ut.
  - Tenkeregelen (`PREREG_V2.md`, linje 177) ble utløst: Gemma 4 26B og Gemma 4 31B talte tenketokens i piloten (170 567 og
    26 924) og fikk R = 3 (`logs/run_v2/pilot_utfall.json`, feltene `reasoning_tokens` og `avvik`). Etter `PREREG_V2.md`,
    linje 181, føres utløste regler som avvik. Dette er ført som A-V2-9 i `docs/AVVIK_V2.md`.
  - `fortsett` er sann. Grunnen er at de to Gemini-loggene har status `success` med alle 20 id-er, og derfor teller som
    komplette etter definisjonen.

## Stopp før full kjøring

Kjøringen er stoppet her for forfatterens beslutning, etter instruksen om å stoppe ved en feil som protokollen ikke dekker.
Ingen hovedkjøring er startet.

- **Hvorfor protokollen ikke dekker tilfellet:** at en modell ikke lenger er tilgjengelig for nøkkelen, gir etter den låste
  definisjonen (v1-protokollen 3.4, `svar_v2.py`) «komplette» kjøringer der hvert svar er endelig feil. Modellene ville da
  vært med i analysene med 0 tolkbare svar.
- **Det PREREG_V2 sier om bortfall** (avsnitt 5): en modell som ikke kan fullføres, er ute av alle analyser.
- **Uten de to modellene** er det seks H1-modeller (Haiku 4.5, Opus 4.5, Opus 4.6, Gemini 2.5 Flash, Gemma 4 26B og
  Gemma 4 31B), fortsatt fra to leverandører. K3 er da 92,1 % ved 87,6 % tolkbarhet (`pilot_regler_v2.k3`).

## Avgjørelse etter stoppet (17.10.2026, forfatteren)

Forfatteren godtok forslaget om å ta de to Gemini-modellene ut som bortfall. Det er ført som avvik A-V2-3 og A-V2-4 i
`docs/AVVIK_V2.md` før første hovedkall. Feil i den publiserte teksten står i `docs/ERRATA_V2.md`: to da, tre etter A-V2-6.

## Google-kvoten (lest 2026-10-17 ca. 14:47 UTC)

Grensene står i AI Studio under Rate Limit for prosjektet «Gemini Project», nivå «Free tier». Siden viser grensen og den
høyeste bruken de siste 28 dagene.

| Modell | RPM | TPM (inn) | RPD | Høyeste bruk (RPM / TPM / RPD) |
|---|---|---|---|---|
| Gemini 2.5 Flash | 5 | 250K | 20 | 7 / 487 / 20 |
| Gemma 4 26B | 30 | 16K | 14.4K | 17 / 677 / 22 |
| Gemma 4 31B | 30 | 16K | 14.4K | 15 / 1.15K / 58 |

Behovet er regnet med R fra pilotreglene og tokens og tid fra piloten (`logs/run_v2/pilot_utfall.json` og pilotloggene).
Alle tre modellene har R = 3, så hver trenger 3 × (916 + 1 760) = 8 028 kall.

- **Gemini 2.5 Flash rekker ikke på gratisnivået.**
  - Ved 20 kall per døgn tar 8 028 kall 402 døgn.
  - Ingen enkeltkjøring, verken 916 eller 1 760 kall, kan fullføres innen ett døgn. Etter omstartsregelen (v1-protokollen
    3.4: ett `eval-retry`, ikke flere) kan en kjøring heller ikke fortsettes over flere døgn.
  - Dagens 20 kall er allerede brukt av piloten.
  - På betalt nivå er fremskrevet kostnad 20,34 USD (pilotreglene: pilotkostnad per sample × 8 028 × 1,25).
- **Gemma 4 rekker på gratisnivået.**
  - Begge modellene ligger under RPM, TPM og RPD. Det er omtrent 73 inntokens per kall, og i piloten gikk det om lag 2,6
    kall per minutt.
  - Etter pilottiden tar det omtrent 51 timer (26B) og 53 timer (31B). API-modellene kjøres én om gangen, så til sammen
    er det omtrent 4,3 døgn.
  - Gemma 4 har ikke noe betalt nivå (`docs/v2_kandidater.json`).

**Beslutning etter forfatterens instruks 17.10.2026** (ført første gang i commit `1f33fd6`): rekker kvoten ikke, kjøres Anthropic- og lokalmodellene ferdig,
Google-modellene startes ikke, og kjøringen stopper for forfatterens beslutning. Kvoten rakk ikke for alle Google-modellene,
og Google-modellene ble da ikke startet. Forfatterens avgjørelse står nedenfor (A-V2-5).

## Avgjørelse om Google (17.10.2026, forfatteren)

Gemini 2.5 Flash faller bort (A-V2-5). Gemma 4 kjøres over flere døgn innenfor gratiskvoten.

**Trengs det endringer i skriptet? Nei.**
- Hver enkeltkjøring er på høyst 1 760 kall. I piloten gikk det om lag 2,6 kall per minutt, altså rundt 3 700 kall per
  døgn, godt under grensen på 14 400 kall per døgn og 30 per minutt.
- En kjøring trenger derfor ikke å deles over et døgnskifte for å holde seg innenfor kvoten, og omstartsregelen trengs ikke.

**Rekkefølgen følger `PREREG_V2.md`, avsnitt 6.10.**
- API-modellene kjøres én om gangen, så Gemma 4 startes med `run_v2.sh api google/gemma-4-26b-a4b-it
  google/gemma-4-31b-it` når Anthropic-kjøringen er ferdig.
- Gemma-kjøringen går parallelt med de lokale modellene, slik avsnitt 6.10 tillater.

## H3-feilen og rettingen (17.10.2026)

- **Anthropic-kjøringen** (`run_v2.sh api` med fire modeller, 14:45:34–15:09 UTC) fullførte hovedoppgaven og
  kontrollkjøringen for alle fire. H3 feilet med `FileNotFoundError` før noe kall, og ingen H3-logg ble skrevet.
- **Rettingen** står under avvik A-V2-6. De kjørende løkkene for Gemma 4 og de lokale modellene fortsatte med
  hovedoppgavene, og deres H3-forsøk feilet før noe kall. Deretter ble H3 kjørt med `ONLY_H3=1`:
  - `run_v2.sh api` for de fire Anthropic-modellene og de to Gemma 4-modellene etter API-køen;
  - `run_v2.sh lokal` for de to lokale modellene etter lokalkøen.

  Tidene står i tabellen nedenfor.

## Hovedkjøringen og H3 (17.–20.10.2026)

Status fra `scripts/svar_v2.py` (T1). Alle loggene har status `success`, og alle kjøringene ble fullført i første forsøk.
Ingen kjøring er forkastet eller avbrutt. Ingen logg består av bare feil, så A-V2-4 ble ikke utløst.

T2 er tom, fordi hovedmappene `logs/run_v2/<modell>/k<r>/` ikke har noen ikke-primær logg. De 11 pilotloggene står ikke i T2
(A-V2-8), men i pilottabellen over. De mislykkede H3-forsøkene (A-V2-6) stoppet før noe kall og skrev ingen logg.

| Modell | Oppgave | k | Samples | Endelige feil | Avkortet | Start–slutt (UTC) |
|---|---|---|---|---|---|---|
| `claude-haiku-4-5-20251001` | items | 1 | 916 | 0 | 0 | 2026-10-17 14:45:38–2026-10-17 14:48:47 |
| `claude-haiku-4-5-20251001` | items_h3_v2 | 1 | 1760 | 0 | 0 | 2026-10-18 15:57:25–2026-10-18 16:03:31 |
| `claude-haiku-4-5-20251001` | items (kontroll) | 2 | 100 | 0 | 0 | 2026-10-17 14:48:53–2026-10-17 14:49:16 |
| `claude-opus-4-5-20251101` | items | 1 | 916 | 0 | 0 | 2026-10-17 14:49:19–2026-10-17 14:53:42 |
| `claude-opus-4-5-20251101` | items_h3_v2 | 1 | 1760 | 0 | 0 | 2026-10-18 16:03:34–2026-10-18 16:11:52 |
| `claude-opus-4-5-20251101` | items (kontroll) | 2 | 100 | 0 | 0 | 2026-10-17 14:53:51–2026-10-17 14:54:25 |
| `claude-opus-4-6` | items | 1 | 916 | 0 | 0 | 2026-10-17 14:54:28–2026-10-17 15:01:58 |
| `claude-opus-4-6` | items_h3_v2 | 1 | 1760 | 0 | 0 | 2026-10-18 16:11:55–2026-10-18 16:26:25 |
| `claude-opus-4-6` | items (kontroll) | 2 | 100 | 0 | 0 | 2026-10-17 15:02:04–2026-10-17 15:02:58 |
| `claude-sonnet-4-6` | items | 1 | 916 | 0 | 0 | 2026-10-17 15:03:02–2026-10-17 15:08:09 |
| `claude-sonnet-4-6` | items_h3_v2 | 1 | 1760 | 0 | 0 | 2026-10-18 16:26:28–2026-10-18 16:35:54 |
| `claude-sonnet-4-6` | items (kontroll) | 2 | 100 | 0 | 0 | 2026-10-17 15:08:14–2026-10-17 15:08:51 |
| `gemma-4-26b-a4b-it` | items | 1 | 916 | 0 | 349 | 2026-10-17 15:09:20–2026-10-17 19:32:23 |
| `gemma-4-26b-a4b-it` | items_h3_v2 | 1 | 1760 | 0 | 634 | 2026-10-18 16:35:57–2026-10-19 00:30:40 |
| `gemma-4-26b-a4b-it` | items | 2 | 916 | 0 | 349 | 2026-10-17 19:32:29–2026-10-17 23:49:38 |
| `gemma-4-26b-a4b-it` | items_h3_v2 | 2 | 1760 | 0 | 634 | 2026-10-19 00:30:42–2026-10-19 08:21:29 |
| `gemma-4-26b-a4b-it` | items | 3 | 916 | 0 | 349 | 2026-10-17 23:49:43–2026-10-18 04:13:01 |
| `gemma-4-26b-a4b-it` | items_h3_v2 | 3 | 1760 | 0 | 634 | 2026-10-19 08:21:32–2026-10-19 16:45:43 |
| `gemma-4-31b-it` | items | 1 | 916 | 0 | 8 | 2026-10-18 04:13:06–2026-10-18 07:56:21 |
| `gemma-4-31b-it` | items_h3_v2 | 1 | 1760 | 0 | 15 | 2026-10-19 16:45:46–2026-10-20 00:16:44 |
| `gemma-4-31b-it` | items | 2 | 916 | 0 | 9 | 2026-10-18 07:56:26–2026-10-18 11:36:09 |
| `gemma-4-31b-it` | items_h3_v2 | 2 | 1760 | 0 | 14 | 2026-10-20 00:16:47–2026-10-20 07:45:41 |
| `gemma-4-31b-it` | items | 3 | 916 | 0 | 8 | 2026-10-18 11:36:14–2026-10-18 15:56:58 |
| `gemma-4-31b-it` | items_h3_v2 | 3 | 1760 | 0 | 14 | 2026-10-20 07:45:44–2026-10-20 13:08:34 |
| `nb-llama-3.1-8b-instruct-cardtmpl:latest` | items | 1 | 916 | 0 | 297 | 2026-10-17 14:45:41–2026-10-17 19:48:52 |
| `nb-llama-3.1-8b-instruct-cardtmpl:latest` | items_h3_v2 | 1 | 1760 | 0 | 553 | 2026-10-17 22:43:30–2026-10-18 07:33:27 |
| `nb-llama-3.1-8b-instruct-cardtmpl:latest` | items (kontroll) | 2 | 100 | 0 | 31 | 2026-10-17 19:48:57–2026-10-17 20:19:47 |
| `normistral-7b-warm-instruct-cardtmpl:latest` | items | 1 | 916 | 3 | 10 | 2026-10-17 20:20:01–2026-10-17 22:26:43 |
| `normistral-7b-warm-instruct-cardtmpl:latest` | items_h3_v2 | 1 | 1760 | 4 | 25 | 2026-10-18 07:33:41–2026-10-18 11:35:52 |
| `normistral-7b-warm-instruct-cardtmpl:latest` | items (kontroll) | 2 | 100 | 1 | 1 | 2026-10-17 22:26:48–2026-10-17 22:41:27 |

Uten logger, og ute av analysen etter A-V2-3 og A-V2-5: Gemini 2.5 Pro, Gemini 2.5 Flash-Lite og Gemini 2.5 Flash.

Kostnaden etter prislista i T18 er 30,10 USD for hovedkjøringen, H3 og kontrollkjøringene (alle loggene i
`logs/run_v2/<modell>/k<r>/`, `scripts/svar_v2.py`, linje 90). Medregnet piloten
viser kostnadsvakta (`scripts/kostnad_v2.py`) 30,35 USD. Gemma 4 og de lokale modellene koster 0.

## Merknader til RESULTS_V2.md (20.10.2026)

- **T1, kolonnen «Tatt ut»:** den viser bare uttak etter pilotreglene (`scripts/svar_v2.py`, linje 70–77 og 143–145;
  `scripts/rapport_v2.py`, linje 48). De tre Gemini 2.5-modellene som falt bort under A-V2-3 og A-V2-5, står med «nei» og
  som ikke komplette uten forsøk.
- **Linje 3, SHA-256 for «modeller»** (`9e98c4789ef27d4e…`): den gjelder modellista analysen ble kjørt med, altså
  `v2_modeller_komplette.json` fra `scripts/svar_v2.py` (`scripts/analysis_v2.py`, linje 625). Den gjelder ikke
  `docs/v2_modeller.json` i låsen (`6fcf8a650d09e3d5…`). Lista er ikke publisert. Den har de åtte komplette modellene.
- **T16, S6:** S6 omfatter bare modellene med R = 3 som er komplette i kjøringen, altså Gemma 4 26B og Gemma 4 31B
  (`logs/run_v2/_analyse/report_v2.json`, `S6_kjøring_2` og `S6_kjøring_3`; `scripts/analysis_v2.py`, linje 638–642).
  Lista over utelatte er tom, fordi ingen modell med R = 3 manglet en kjøring.
- **T16, det som ikke vises:** tilstandene per modell og H2 i sensitivitetsanalysene står i `report_v2.json`, men den låste
  `scripts/rapport_v2.py` (funksjonen `t16`) rendrer bare H1 og H3 samlet.
- **`data/errata_v2.txt` ved analysen:** SHA-256 `1015ee1d83bcacc8d985faeb44525c07263009e89a93d3ba42d77590ca63e03a`, lik
  låsen (`docs/LOCK_V2.md`, linje 54). Ingen erratum er ført, og S7 er derfor lik primæranalysen.
  - `PREREG_V2.md` (linje 80–81) og `docs/LOCK_V2.md` (linje 5) sier at versjonen som brukes i S7, publiseres med egen
    SHA-256.
  - Versjonen er identifisert ved SHA-256-en over, som også står i den publiserte låsen.
  - Fila er med i Zenodo 2.1 som `errata_v2.txt` (fillista `SHA256SUMS_v2_1`).
