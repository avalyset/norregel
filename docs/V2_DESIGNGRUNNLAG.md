# Designgrunnlag for norregel v2

Skrevet av `scripts/v2_design.py` før noen v2-modell er valgt eller kjørt. Kandidatene og cutoffene står i `docs/v2_kandidater.json` (hentet 17.10.2026 fra leverandørenes egne sider, med URL og SHA-256). Gruppestørrelsene er regnet fra item-metadata (datoer, serier, typer), uten svar og uten fasit. Pilotparametrene er fra v1-svarene og er merket **PILOT**: de er estimater fra én kjøring av fem modeller, ikke kjente størrelser.

## 1. Kandidater og H1-grupper

Kandidatene er modellene nøklene kunne kalle 17.10.2026 (GET https://api.anthropic.com/v1/models (14 modeller); GET https://generativelanguage.googleapis.com/v1beta/models (63 modeller; tekstmodeller med generateContent tatt med)). Utelatt fra listene: alias uten fast versjon (*-latest), bilde-, lyd-, TTS-, live-, robot-, embedding-, agent- og deep-research-modeller. H1-settet har 567 items i 95 serier. «Etter» = `gyldig_fra` etter cutoff.

| Leverandør | Modell | Status | Tenking som standard | Oppgitt cutoff (type) | Dato | Kilde | n etter (serier) | n før (serier) |
|---|---|---|---|---|---|---|---|---|
| Anthropic | `claude-haiku-5-5` | Active (latest) | Adaptive thinking | Jun 2026 (Training data cutoff) | 2026-06-30 | https://platform.claude.com/docs/en/models/haiku-5-5/overview (sha256 `855f19b98e70c835…`) | 1 (1) | 566 (95) |
| Anthropic | `claude-sonnet-5-5` | Active (latest) | Adaptive thinking | Jun 2026 (Training data cutoff) | 2026-06-30 | https://platform.claude.com/docs/en/models/sonnet-5-5/overview (sha256 `a8b46ef8e5942ca6…`) | 1 (1) | 566 (95) |
| Anthropic | `claude-opus-5-5` | Active (latest) | Adaptive thinking | Jun 2026 (Training data cutoff) | 2026-06-30 | https://platform.claude.com/docs/en/models/opus-5-5/overview (sha256 `db3d6cbf322fadb6…`) | 1 (1) | 566 (95) |
| Anthropic | `claude-fable-5-1` | Active (latest) | Adaptive thinking | Jun 2026 (Training data cutoff) | 2026-06-30 | https://platform.claude.com/docs/en/models/fable-5-1/overview (sha256 `e68ae6278712f38b…`) | 1 (1) | 566 (95) |
| Anthropic | `claude-opus-5` | Active (legacy) | Adaptive thinking | May 2026 (Training data cutoff) | 2026-05-31 | https://platform.claude.com/docs/en/models/opus-5/overview (sha256 `0f40dbeada2f7d31…`) | 7 (7) | 560 (95) |
| Anthropic | `claude-sonnet-5` | Active (legacy) | Adaptive thinking | Jan 2026 (Training data cutoff) | 2026-01-31 | https://platform.claude.com/docs/en/models/sonnet-5/overview (sha256 `58a1ca5219a72a21…`) | 9 (9) | 558 (95) |
| Anthropic | `claude-fable-5` | Active (legacy) | Adaptive thinking | Jan 2026 (Training data cutoff) | 2026-01-31 | https://platform.claude.com/docs/en/models/fable-5/overview (sha256 `f5a6e9d40d3e43d7…`) | 9 (9) | 558 (95) |
| Anthropic | `claude-opus-4-8` | Active (legacy) | Thinking off | Jan 2026 (Training data cutoff) | 2026-01-31 | https://platform.claude.com/docs/en/models/opus-4-8/overview (sha256 `98460998b3f13e36…`) | 9 (9) | 558 (95) |
| Anthropic | `claude-opus-4-7` | Active (legacy) | Thinking off | Jan 2026 (Training data cutoff) | 2026-01-31 | https://platform.claude.com/docs/en/models/opus-4-7/overview (sha256 `c9c46645dde9dda6…`) | 9 (9) | 558 (95) |
| Anthropic | `claude-sonnet-4-6` | Active (legacy) | Thinking off | Jan 2026 (Training data cutoff) | 2026-01-31 | https://platform.claude.com/docs/en/models/sonnet-4-6/overview (sha256 `6289990a037450f8…`) | 9 (9) | 558 (95) |
| Anthropic | `claude-opus-4-6` | Active (legacy) | Thinking off | Aug 2025 (Training data cutoff) | 2025-08-31 | https://platform.claude.com/docs/en/models/opus-4-6/overview (sha256 `5fde2113acf9ba08…`) | 36 (36) | 531 (91) |
| Anthropic | `claude-opus-4-5-20251101` | Active (legacy) | Thinking off | Aug 2025 (Training data cutoff) | 2025-08-31 | https://platform.claude.com/docs/en/models/opus-4-5/overview (sha256 `64137c23b60416a9…`) | 36 (36) | 531 (91) |
| Anthropic | `claude-haiku-4-5-20251001` | Active (legacy) | Thinking off | Jul 2025 (Training data cutoff) | 2025-07-31 | https://platform.claude.com/docs/en/models/haiku-4-5/overview (sha256 `bec0ed34119af773…`) | 56 (56) | 511 (90) |
| Anthropic | `claude-sonnet-4-5-20250929` | Deprecated | Thinking off | Jul 2025 (Training data cutoff) | 2025-07-31 | https://platform.claude.com/docs/en/models/sonnet-4-5/overview (sha256 `16b10373e5fedc38…`) | 56 (56) | 511 (90) |
| Google | `gemini-2.5-flash` | Active (not deprecated; access limited to earlier users) | On | January 2025 (Knowledge cutoff) | 2025-01-31 | https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash (sha256 `fb2610e7efd10a6f…`) | 64 (56) | 503 (89) |
| Google | `gemini-2.5-pro` | Active (not deprecated; access limited to earlier users) | On | January 2025 (Knowledge cutoff) | 2025-01-31 | https://ai.google.dev/gemini-api/docs/models/gemini-2.5-pro (sha256 `65b5b4e6f18388e3…`) | 64 (56) | 503 (89) |
| Google | `gemini-2.5-flash-lite` | Active (not deprecated; access limited to earlier users) | Off | January 2025 (Knowledge cutoff) | 2025-01-31 | https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-lite (sha256 `af7125c2dbfa1316…`) | 64 (56) | 503 (89) |
| Google | `gemini-3.1-flash-lite` | Active | ukjent | ingen oppgitt | — | https://deepmind.google/models/model-cards/gemini-3-1-flash-lite/ | — | — |
| Google | `gemini-3.1-pro-preview` | Preview | On (high) | ingen oppgitt | — | https://deepmind.google/models/model-cards/gemini-3-1-pro/ | — | — |
| Google | `gemini-3.5-flash-lite` | Active | On (minimal) | March 2026 (knowledge cutoff (model card)) | 2026-03-31 | https://deepmind.google/models/model-cards/gemini-3-5-flash-lite/ (sha256 `4c71f83ccceeac5c…`) | 8 (8) | 559 (95) |
| Google | `gemini-3.5-flash` | Deprecated | ukjent | ingen oppgitt | — | https://deepmind.google/models/model-cards/gemini-3-5-flash/ | — | — |
| Google | `gemini-3.6-flash` | Active | On (medium) | March 2026 (knowledge cutoff (model card)) | 2026-03-31 | https://deepmind.google/models/model-cards/gemini-3-6-flash/ (sha256 `7d483b708d9c84ad…`) | 8 (8) | 559 (95) |
| Google | `gemini-3.7-flash` | Deprecated | ukjent | March 2026 (knowledge cutoff (model card)) | 2026-03-31 | https://deepmind.google/models/model-cards/gemini-3-7-flash/ (sha256 `3f8b451c3b37e693…`) | 8 (8) | 559 (95) |
| Google | `gemini-3.8-flash` | Active | On (medium) | March 2026 (knowledge cutoff (model card)) | 2026-03-31 | https://deepmind.google/models/model-cards/gemini-3-8-flash/ (sha256 `c2f3919e942c0d30…`) | 8 (8) | 559 (95) |
| Google | `gemini-3-flash-preview` | Preview | On (high) | ingen oppgitt | — | https://deepmind.google/models/model-cards/gemini-3-flash/ | — | — |
| Google | `gemini-3-pro-preview` | Preview | On (high) | ingen oppgitt | — | https://deepmind.google/models/model-cards/gemini-3-pro/ | — | — |
| Google | `gemini-4-argon` | Active | On (medium) | March 2026 (knowledge cutoff (model card)) | 2026-03-31 | https://deepmind.google/models/model-cards/gemini-4-argon/ (sha256 `71d099474d38ad89…`) | 8 (8) | 559 (95) |
| Google | `gemma-4-31b-it` | Active (model card, ingen utfasing oppgitt) | ingen tenkemodus oppgitt | January 2025 (pre-training data cutoff (model card)) | 2025-01-31 | https://ai.google.dev/gemma/docs/core/model_card_4 (sha256 `d1c19760a4dd43b1…`) | 64 (56) | 503 (89) |
| Google | `gemma-4-26b-a4b-it` | Active (model card, ingen utfasing oppgitt) | ingen tenkemodus oppgitt | January 2025 (pre-training data cutoff (model card)) | 2025-01-31 | https://ai.google.dev/gemma/docs/core/model_card_4 (sha256 `d1c19760a4dd43b1…`) | 64 (56) | 503 (89) |

## 2. Pilotparametre fra v1 (PILOT)

| Parameter | Sonnet 4.6 | Opus 5.5 | Brukt i beregningen |
|---|---|---|---|
| Andel utdatert før cutoff, H1-settet, av alle svar (%) | 9,1 | 9,2 | — |
| Andel utdatert før cutoff, H1-settet, av tolkbare svar (%) | 10,5 | 9,3 | p0 = 9,9 % (snitt) |
| ICC for utdatert innen serie, før cutoff | 0,180 | 0,307 | ρ = 0,243 (snitt) |
| Andel tolkbare svar, primærsettet (%) | 87,6 | 99,5 | r = 87,6 % (den laveste) |
| Korrelasjon mellom modellene (utdatert, samme item) | 0,137 | | ρx = 0,137 |
| Utdaterte svar på H2-settet (570 items) | 50 | 46 | rate 8,4 % |
| s (H2) | 62,0 % | 50,0 % | s1 = 56,2 % (samlet) |
| ICC for «nyeste avvikende verdi» innen serie | 0,241 | 0,466 | ρ2 = 0,353, 2,6 utdaterte svar per serie |
| H3: diskordante par av 189 | 6,3 % | 5,8 % | d = 6,1 % |
| H3: b/(b + c), fire modeller med b + c > 0 samlet | | | π1 = 61,3 % (b = 19, c = 12) |

## 3. Styrke a priori

Ensidige tester, styrke 80 %. Holm-α i verste fall er α/k med k = antall modeller i familien. For H1 er k = 9: kandidatene med minst 30 items fra minst 20 serier etter cutoff. For H2 og H3 brukes samme k. H1 er regnet med normaltilnærming og designeffekt 1 + (m − 1)ρ (m = items per serie i gruppen); H2 og H3 med eksakt binomialtest på effektivt antall (antall delt på designeffekten). H1-målet er andel utdatert blant tolkbare svar; antall tolkbare er antall items ganger r. Ingen effekt for H1 kan hentes fra v1 (testen sammenlignet 0 med 0, og Sonnet 4.6 og Opus 5.5 hadde 9 og 1 items etter cutoff); δ = 10, 15, 20 prosentpoeng er satt her som minste effekt av interesse.

**H1 per modell** (Holm-α = 0,0056; p0 = 9,9 %, ρ = 0,243, r = 87,6 %):

| Gruppe (cutoff) | n etter (serier) | n før (serier) | Styrke δ = 10 | δ = 15 | δ = 20 | Minste påviselige δ | n etter som trengs for δ = 15 |
|---|---|---|---|---|---|---|---|
| `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash-lite`, `gemma-4-31b-it`, `gemma-4-26b-a4b-it` | 64 (56) | 503 (89) | 22 % | 47 % | 72 % | 22,2 pp | 141 |
| `claude-haiku-4-5-20251001`, `claude-sonnet-4-5-20250929` | 56 (56) | 511 (90) | 19 % | 41 % | 65 % | 23,8 pp | 136 |
| `claude-opus-4-6`, `claude-opus-4-5-20251101` | 36 (36) | 531 (91) | 12 % | 26 % | 44 % | 30,3 pp | 135 |
| `claude-sonnet-5`, `claude-fable-5`, `claude-opus-4-8`, `claude-opus-4-7`, `claude-sonnet-4-6` | 9 (9) | 558 (95) | 3 % | 6 % | 9 % | 57,1 pp | 134 |
| `gemini-3.5-flash-lite`, `gemini-3.6-flash`, `gemini-3.7-flash`, `gemini-3.8-flash`, `gemini-4-argon` | 8 (8) | 559 (95) | 3 % | 5 % | 8 % | 59,4 pp | 134 |
| `claude-opus-5` | 7 (7) | 560 (95) | 3 % | 5 % | 7 % | 62,0 pp | 134 |
| `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-fable-5-1` | 1 (1) | 566 (95) | 1 % | 1 % | 2 % | 84,4 pp | 134 |

**H1 samlet over de 9 modellene** (én test, α = 0,05; gjennomsnittlig n etter 56,0 i 52 serier, variansen ganget med (1 + (k − 1)ρx)/k): styrke 96 %, 100 %, 100 % for δ = 10, 15, 20 pp; minste påviselige δ 6,9 pp.

**H2** (s1 = 56,2 %, PILOT; utdaterte svar per modell ≈ 48, designeffekt 1,59):

- Per modell (Holm-α 0,0056): effektivt antall som trengs 751, dvs. omtrent 1194 utdaterte svar; tilgjengelig effektivt antall 30, styrke 2 %, minste påviselige s 81,0 %.
- Samlet over k modeller (én test, α = 0,05): effektivt antall som trengs 417.
  - k = 4: ≈ 192 utdaterte svar, designeffekt 1,49 (≤ 80 serier), effektivt 128, styrke 40 %.
  - k = 6: ≈ 288 utdaterte svar, designeffekt 1,92 (≤ 80 serier), effektivt 150, styrke 43 %.
  - k = 9: ≈ 432 utdaterte svar, designeffekt 2,55 (≤ 80 serier), effektivt 169, styrke 47 %.

**H3** (π1 = 61,3 %, PILOT; diskordante par 6,1 % av parene, PILOT; ingen designeffekt):

- Diskordante par som trengs per modell (Holm-α 0,0056): 232, dvs. omtrent 3813 par.
- Diskordante par som trengs samlet (α = 0,05): 135, dvs. omtrent 2219 par for én modell.
- Med v1-settet (189 par): ≈ 12 diskordante per modell, styrke per modell 2 %, samlet over k = 9: 74 %.
- Med alle primæritems som par (880 par): ≈ 54 diskordante per modell, styrke per modell 17 % (minste påviselige π 72,7 %), samlet over k = 9: 100 % (minste påviselige π 55,8 %).

## 4. Kostnad (estimat)

Tokens per sample fra v1 (`docs/RESULTS.md`, faktisk kostnad; 1336 samples per modell med piloten): uten tenking 91 inn og 146 ut (snitt av Haiku 4.5 og Sonnet 4.6), med tenking 107 inn og 820 ut (Opus 5.5). Samples per kjøring: 2676 (916 hovedoppgave + 880 par × 2 i H3). Margin 1,25. Profilen følger tenkestandarden i `docs/v2_kandidater.json` (leverandørenes tenkesider). Prisene er fra leverandørenes prissider (se samme fil). Gemma 4 har bare gratisnivå.

| Modell | Profil | USD per kjøring | USD for 3 kjøringer |
|---|---|---|---|
| `claude-opus-5-5` | med tenking | 56,30 | 168,90 |
| `claude-sonnet-4-6` | uten tenking | 8,25 | 24,74 |
| `claude-opus-4-6` | uten tenking | 13,74 | 41,23 |
| `claude-opus-4-5-20251101` | uten tenking | 13,74 | 41,23 |
| `claude-haiku-4-5-20251001` | uten tenking | 2,75 | 8,25 |
| `claude-sonnet-4-5-20250929` | uten tenking | 8,25 | 24,74 |
| `gemini-2.5-flash` | med tenking | 6,97 | 20,90 |
| `gemini-2.5-pro` | med tenking | 27,88 | 83,65 |
| `gemini-2.5-flash-lite` | uten tenking | 0,23 | 0,68 |
| `gemma-4-31b-it` | uten tenking | 0,00 | 0,00 |
| `gemma-4-26b-a4b-it` | uten tenking | 0,00 | 0,00 |
## 5. Tillegg etter Stage 1-vurderingen, runde 1

Skrevet etter vurderingen (`docs/vurderinger/STAGE1_VURDERING.md`, i repoet). Modellene er de valgte i `docs/v2_modeller.json`. Designeffekten har nå gulv på 1, og en gruppe har aldri flere serier enn tolkbare items.

**H1 samlet, k = 8, under ulik tolkbarhet etter cutoff** (andelen tolkbare før cutoff er r = 87,6 %, PILOT; δ = 10 pp; styrke / minste påviselige δ). v1-piloten hadde 0 av 56 (Haiku 4.5) og 1 av 9 (Sonnet 4.6) tolkbare svar etter cutoff (`docs/TILLEGG_ETTER_VURDERING.md`, A3).

| Tolkbar andel etter cutoff | ρx = 0,137 (PILOT) | ρx = 0,3 | ρx = 0,5 |
|---|---|---|---|
| 87,6 % | 95,6 % / 7,1 pp | 84,6 % / 9,3 pp | 71,4 % / 11,6 pp |
| 50,0 % | 82,8 % / 9,6 pp | 66,1 % / 12,6 pp | 52,6 % / 15,9 pp |
| 30,0 % | 65,1 % / 12,9 pp | 48,9 % / 17,1 pp | 38,1 % / 21,5 pp |
| 11,0 % | 34,4 % / 23,7 pp | 25,6 % / 31,0 pp | 20,5 % / 37,9 pp |

For 80 % styrke ved δ = 10 pp trengs i snitt 26 tolkbare svar etter cutoff per H1-modell (ρx = 0,137).

**K3 for hver k** (modellene tas ut i K6-rekkefølgen, synkende kostnad blant H1-modellene som ikke er v1-modeller; tolkbarhet 87,6 % / 50 % etter cutoff, ρx = 0,137):

| k | Tatt ut | Leverandører | Styrke (r etter 87,6 %) | Styrke (r etter 50 %) |
|---|---|---|---|---|
| 8 | — | anthropic, google | 95,6 % | 82,8 % |
| 7 | `google/gemini-2.5-pro` | anthropic, google | 94,2 % | 79,9 % |
| 6 | `google/gemini-2.5-flash` | anthropic, google | 92,1 % | 76,4 % |
| 5 | `anthropic/claude-opus-4-5-20251101` | anthropic, google | 91,2 % | 74,9 % |
| 4 | `anthropic/claude-opus-4-6` | anthropic, google | 89,8 % | 73,2 % |
| 3 | `google/gemini-2.5-flash-lite` | anthropic, google | 84,2 % | 65,8 % |
| 2 | `google/gemma-4-26b-a4b-it` | anthropic, google | 73,3 % | 54,4 % |
| 1 | `google/gemma-4-31b-it` | anthropic | 50,5 % | 35,8 % |

Uten Gemma 4 (k = 6): 92,1 % ved r etter = 87,6 % og 76,4 % ved 50 %.

**H3 samlet, k = 11** (diskordans 6,1 %, PILOT; π1 = 61,3 %, PILOT; 589 diskordante par i alt; designeffekt 1 + (k − 1)ρx for at modellene svarer på de samme parene). Minste påviselige effekt også på D-skala: |D| = diskordans × (2π − 1).

| ρx | Effektive diskordante | Styrke | Minste π | Minste |D| (pp) |
|---|---|---|---|---|
| 0,000 | 589 | 100,0 % | 55,2 % | 0,63 |
| 0,137 | 248 | 97,0 % | 58,1 % | 0,99 |
| 0,300 | 147 | 86,8 % | 60,2 % | 1,24 |
| 0,500 | 98 | 70,4 % | 62,8 % | 1,56 |

**H2 som estimering, k = 11:** ≈ 528 utdaterte svar, designeffekt 2,98 (80 serier, ρ2 = 0,353, PILOT), effektivt 177; forventet halv bredde på 95 %-intervallet for s ved s = 0,5: ±7,4 pp; minste s en ensidig test ved α = 0,05 kunne påvise med 80 % styrke: 59,4 %.

**Målmengde for «utdatert» per H1-gruppe** (item-metadata: gjennomsnittlig antall distinkte tidligere verdier som avviker fra fasit, per item):

| Cutoff | Etter | Før |
|---|---|---|
| 2025-01-31 | 7,72 (n = 64) | 6,25 (n = 503) |
| 2025-07-31 | 7,79 (n = 56) | 6,27 (n = 511) |
| 2025-08-31 | 9,61 (n = 36) | 6,20 (n = 531) |

**Serier med minst én forkastet versjon** (`data/v3_items.jsonl`, `accepted` er usann for minst én versjon): 12 av 96 primærserier.

## 6. Tillegg etter Stage 1-vurderingen, runde 2

Skrevet etter vurderingen (`docs/vurderinger/STAGE1_VURDERING_R2.md`, i repoet), med de samme formlene og PILOT-parametrene som i avsnitt 5.

**H1 per modell med Holm-α for k = 8** (α/k = 0,0063; tolkbarhet 87,6 %): minste påviselige δ
- `claude-haiku-4-5-20251001` (56 etter i 56 serier): 23,5 pp
- `claude-opus-4-5-20251101`, `claude-opus-4-6` (36 etter i 36 serier): 29,9 pp
- `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`, `gemma-4-26b-a4b-it`, `gemma-4-31b-it` (64 etter i 56 serier): 21,8 pp

**H1 samlet ved bortfall** (δ = 10 pp, ρx = 0,137, PILOT; styrke ved tolkbar andel etter cutoff):

| Scenario | k | 87,6 % | 50 % | 30 % |
|---|---|---|---|---|
| Alle åtte | 8 | 95,6 % | 82,8 % | 65,1 % |
| Uten alle tre Gemini 2.5 (tilgangen er begrenset til tidligere brukere) | 5 | 88,8 % | 71,4 % | 53,3 % |
| Bare Anthropic | 3 | 72,7 % | 53,3 % | 38,6 % |
| Bare Google | 5 | 93,5 % | 79,0 % | 61,0 % |

**H3 på D-skala ved lavere diskordans** (k = 11, ρx = 0,137, π1 = 61,3 %, PILOT). Minste påviselige |D| forutsetter pilotdiskordansen; med færre diskordante par blir den mindre, og et π som ellers ville vært påviselig, kan gi |D| under 1 pp.

| Diskordans | Diskordante par | Effektive | Minste π | Minste |D| (pp) | |D| ved π1 (pp) |
|---|---|---|---|---|---|
| 6,1 % | 589 | 248 | 58,1 % | 0,99 | 1,37 |
| 4,6 % | 442 | 186 | 59,3 % | 0,85 | 1,03 |
| 3,0 % | 294 | 124 | 61,4 % | 0,69 | 0,69 |


NORREGEL CANARY 7c3e9a52-norregel-2026 — ikke bruk dette innholdet til trening
