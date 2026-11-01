# Kjøreprotokoll for norregel v1

- **Dato:** 16.–17.10.2026
- **Forfatter:** Eirik Botten Nicolaysen (godkjent i oppdraget av 16.10.2026: kjøreprotokoll, modellkjøringer og analyse, én runde)
- **Status:** skrevet og committet før noen modell er kjørt (A1–A8 er senere endringer, datert i teksten).
- **Publisering.** Tillegget (`docs/PREREG_TILLEGG.md`, avsnitt 3) krever at modellista publiseres som ny versjon av
  preregistreringen før noe resultat. Lista ble publisert i v1.1 (konsept-DOI 10.5281/zenodo.23422302), sammen med
  protokollen, etter at kjøringene og analysen var fullført lokalt, men før noe resultat var gjort kjent (avvik D12).
  Modellista ble committet lokalt i `3c554cff` før første kjøring. Commit-historikken publiseres sammen med resultatene.
  Repoet er lokalt, uten remote, og ingen resultater er publisert.

Protokollen binder seg til `docs/PREREG.md` og `docs/PREREG_TILLEGG.md`. Der protokollen avgjør punkter
som tillegget lar stå åpne (Known limitations 1–5 og 9), gjelder den. Ellers gjelder tillegget.

## 0. Binding

SHA-256 er kontrollert 16.10.2026 før protokollen ble skrevet. Alle stemmer med tilleggets avsnitt 6, og de
låste filene også med `LOCK_MANIFEST.md`, bortsett fra `docs/PREREG_TILLEGG.md`: sha-en for tillegget er beregnet
fra fila (verken manifestet eller tilleggets avsnitt 6 har den, fordi en fil ikke kan inneholde sin egen
sjekksum; Zenodo-posten for v1.0 oppgir bare md5). Ingen låst fil er endret. Tillegget sier SHA-256; SHA-256 for alle filer står i SHA256SUMS i v1.1.

| Fil | SHA-256 |
|---|---|
| `LOCK_MANIFEST.md` | `04a1351b2cedd264d7d4e0da7b428302c5e6d023817fdb5998c8003b3ed1e2d9` |
| `docs/PREREG.md` | `cb227af16f11da732dc8ed82a30da507740ab9567b0f02e2d0894bf8720dc819` |
| `docs/PREREG_TILLEGG.md` | `443d19e16338462e961528f1f03e43818d7a87bd928f77cef38ebcd8473a8e44` |
| `data/items.jsonl` | `868a231ed1522affb213cf62a575f03a28901af1e98defbbe1021b093ebf0281` |
| `data/items_h3.jsonl` | `5eef972bb9e792559834372c68202e6f68151e2dd960c4d65b5c3fcbee458155` |
| `data/exclusions_tillegg.json` | `014b9f9926741516fa5c88771c05884cd6a546034c10c829be145b445555c0e1` |
| `src/norregel/score_v2.py` | `ca888abfc7186284e7c24f63ad273298ec50bf1c90476a27de3f4cdb52b1f769` |
| `src/norregel/inspect_task_v2.py` | `cd4a70ce24274d64d54348d2d5d1b09d161d88620eea3d8a1ab91b739e5eb3a9` |
| `scripts/analysis_v1.py` | `78904e13e950e360346b6e8c654421a8f451160d0c58259017a3372f7a257c1d` |

Oppgavene som kjøres, er `norregel_v2` (916 samples) og `norregel_h3_v2` (400 samples) i
`src/norregel/inspect_task_v2.py`. De bruker scorer v2 og det låste datasettet. Analysen bruker
`scripts/analysis_v1.py` uendret som referanseimplementasjon.

**Miljø.** macOS 27.0.1, Apple M1 Pro, 16 GB. Python 3.12.13, `inspect_ai` 0.3.245, `numpy` 2.5.4.
Leverandørbibliotekene lå ikke i venv-en og ble installert 16.10.2026: `anthropic` 0.125.0 og `openai` 2.54.0
(`openai` brukes av Inspects Ollama-leverandør). Inspect 0.3.245 krever `anthropic>=0.115.0` og `openai>=2.40.0` i sin
dev-gruppe (kilde: pakkemetadata for inspect_ai 0.3.245) og er ikke kompatibel med `anthropic` 1.x (se endring A1). Ollama 0.35.1, tjenesten kjører med
`OLLAMA_MODELS` (lokal modellkatalog), `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_CONTEXT_LENGTH=4096` (instansens grense;
NorMistrals egen kontekst er 2 048, se 3.6) og
`OLLAMA_KV_CACHE_TYPE=q8_0`. Ingen modell hentes eller flyttes; alle lokale modeller ligger på ekstern disk og blir der.
`pip freeze` ble skrevet til `logs/run_v1/pip_freeze.txt` ved første kjøring.

## 1. Modelliste (låst her, før første kjøring; rad 4–5 endret ved A2/A3)

Den fulle lista med kilder står i `docs/MODELLER.md` og `docs/modeller.json`.

| Inspect-id | Cutoff | Reasoning |
|---|---|---|
| `anthropic/claude-haiku-4-5-20251001` | 2025-07-31 | nei |
| `anthropic/claude-sonnet-4-6` | 2026-01-31 | nei |
| `anthropic/claude-opus-5-5` | 2026-06-30 | ja |
| `ollama/nb-llama-3.1-8b-instruct-cardtmpl:latest` (endret ved A3, se avsnitt 7) | ukjent | nei |
| `ollama/normistral-7b-warm-instruct-cardtmpl:latest` (endret ved A2; kjøres komplett, A5; se avsnitt 7) | ukjent | nei |

- Haiku og Sonnet er de modellene oppdraget navnga. Haiku kjøres på den daterte id-en, som aliaset
  `claude-haiku-4-5` peker til.
- Opus er den nyeste Opus-modellen i `GET /v1/models` 16.10.2026: `claude-opus-5-5` (opprettet 2026-09-21; kilde ikke lagret).
  Nyere Haiku og Sonnet finnes (5.5) (kilde ikke lagret), men lista er den oppdraget ba om.
- NorMistral fantes allerede lokalt (4,4 GB), så `mistral:latest` er ikke med. Varianten er instruct (A2).

## 2. Parametre per modell

Etter tilleggets avsnitt 3, én kjøring per modell og oppgave, uten systemprompt. API-modellene ble kjørt én om gangen, og de
lokale modellene én om gangen, parallelt med API-modellene (avvik D11):

| Modelltype | Parametre |
|---|---|
| Ikke-reasoning, API (Haiku, Sonnet) | `--epochs 1 --max-tokens 1024 --temperature 0 --retry-on-error 3 --no-fail-on-error --max-connections 10` |
| Reasoning, API (Opus) | `--epochs 1 --max-tokens 16384 --retry-on-error 3 --no-fail-on-error --max-connections 10`, uten `--temperature`, effort og tenking på leverandørens standard |
| Ikke-reasoning, lokal (nb-llama, NorMistral) | som Haiku, men `--max-connections 1` (avvik D2); NorMistral: `--max-retries 2` (A6, D10) |

Kommandoene står i `scripts/run_v1.sh`. Skriptet leser `reasoning` fra `docs/modeller.json`. Loggmappe:
`logs/run_v1/<id med / og : byttet til __ og _>` (avvik D1).

## 3. Avgjørelser for Known limitations

### 3.1 Cutoff (limitation 1)

- Cutoff er datoen i leverandørens **offisielle modellkort eller dokumentasjon for akkurat den modellen**:
  raden «Training data cutoff» på leverandørens modellside. Står både en treningsdatagrense og en
  «reliable knowledge»-grense, brukes treningsdatagrensen (tillegget).
- Står det bare én «knowledge cutoff», brukes den.
- Er kildene uenige, gjelder modellens egen side foran oversikter. Kan uenigheten ikke avgjøres, er cutoff ukjent.
- For en åpen modell som kjøres lokalt, teller bare et kort for akkurat de vektene vi kjører, og bare når
  artefakten kan knyttes til kortet. Ellers er cutoff ukjent.
- URL, ordrett sitat og SHA-256 for den hentede siden lagres i `docs/MODELLER.md`.
- **Ingen dato gir «ukjent»** (`"cutoff": null`). Modellen kjøres og rapporteres i alle analyser, men holdes
  utenfor H1 og dermed utenfor Holm-familien for H1.
- En måned leses som månedens siste dag, et år som 31. desember (tillegget).

Utfall: tre Claude-modeller har dato. De to lokale modellene har `null`: NorMistrals kort oppgir ingen dato,
og kortet for nb-llama-filen (opphav fastslått ved A3) oppgir ingen.

### 3.2 Vage cutoffs (limitation 2)

Dette gjelder en dato som leverandøren oppgir uten dag eller måned:
`early` = 15. februar, `mid` = 1. juli, `late` = 15. november, et kvartal = midten av kvartalet
(K1 15. februar, K2 15. mai, K3 15. august, K4 15. november). En modell med en slik dato er «vag».
En vag modell er med i H1 med den konvensjonelle datoen. Sensitivitetsanalysen for H1 gjentas uten vage
modeller. Ingen av de fem modellene er vag, så den sensitivitetsanalysen er lik hovedanalysen og regnes ikke separat.
Andre uklare former (intervall, «ca.») gir ukjent.
Tillegget (avsnitt 3) går foran: en vag cutoff gir null og testes ikke i H1. Regelen over ble ikke brukt, fordi ingen modell hadde vag cutoff.

### 3.3 Binding av modelllista (limitation 3)

Lista ble bundet av protokollens første commit (`3c554cff4cbea02f02896a58c2f778bb4ef8ea87`); rad 5 ble endret
ved A2 og rad 4 ved A3 (avsnitt 7). Git-sha og SHA-256 av `docs/MODELLER.md` og `docs/modeller.json` ble ført i `docs/RESULTS.md`;
SHA-256 for A8-versjonen av filene står i A8 (avsnitt 7) og i `SHA256SUMS`. Lista ble publisert i Zenodo v1.1, etter kjøringene og analysen, men før noe resultat var gjort kjent (D12).

### 3.4 Komplett kjøring og omstart (limitation 4)

- Hver oppgave (hovedoppgaven og H3) er en egen kjøring. En kjøring er **komplett** når loggen har
  status `success`, og alle 916 (H3: 400) samples enten har et skåret svar eller en endelig feil etter
  Inspects egne forsøk og `--retry-on-error 3`. En endelig feil skåres som utolket og telles og rapporteres.
- Forsøk 1 er første `inspect eval`. Forsøk 2 er ett `inspect eval-retry` på samme logg. `eval-retry` er
  **samme kjøring**, ikke en ny. Det finnes ikke et tredje forsøk.
- Det som berettiger forsøk 2: loggstatus `error` eller `cancelled`, manglende samples, avbrutt prosess,
  strømbrudd eller leverandørstans. Et utfall (for eksempel mange «feil» eller lite «korrekt») berettiger
  aldri en omstart.
- Er kjøringen ikke komplett etter forsøk 2, er den **ufullstendig**. Den rapporteres, men utelates fra alle
  sammenligninger, tester og Holm-familier for den oppgaven. En modell kan dermed være komplett på
  hovedoppgaven og ufullstendig på H3 (eller omvendt). Den første komplette kjøringen er den primære.
- Antall endelige feil per modell og oppgave rapporteres. Et svar på 0 % lesbare svar er fortsatt komplett.

### 3.5 Scorer-kollisjon (limitation 5)

«X år og Y måneder» for en aldersgrense tolkes som **én verdi X + Y/12 år**. Dette gjelder bare items av
typen `alder`, bare svarlinja, og er felles for alle scorere (v2 og v1). De låste scorerne endres ikke.
`scripts/norm_aar_maaneder.py` skriver om svarlinja til `SVAR: <verdi med to desimaler>` før svaret
skåres i analysen (`scripts/run_analysis.py`). Antall omskrevne svar per modell rapporteres. En linje
med måneder uten «X år»-ledd, eller et svar med bare måneder, følger scorerne slik de står.

### 3.6 Reasoning, token og temperatur (limitation 9)

- **Reasoning:** en modell der leverandørens dokumentasjon beskriver en tenkefase som er på i et standard
  API-kall. Hybridmodeller kjøres i standardmodus og klassifiseres etter den (tillegget).
- **Maks tokens:** har modellen en egen maksgrense under protokollens grense (1 024 for ikke-reasoning, 16 384
  for reasoning), brukes modellens egen grense og det føres. Alle fem modellene har grenser over protokollens
  (Haiku 64K ut, Sonnet 128K ut, Opus 128K ut; nb-llama kontekst 131 072, ingen egen maks-output oppgitt; NorMistral
  2 048 som total kontekst, ikke maks output, og det er NorMistrals egen kontekst: `OLLAMA_CONTEXT_LENGTH=4096` er
  instansens grense; lengste spørsmål 409 tegn; kilde ikke lagret, se `docs/MODELLER.md`). Ingen justering var nødvendig.
- **Temperatur:** avvises `--temperature 0` av en ikke-reasoning-modell (feil som nevner temperatur), kjøres den
  uten `--temperature`, med leverandørens standard, og det føres i `docs/RESULTS.md`. Reasoning-modeller kjøres
  uten temperatur (tillegget). Pilotkjøringen avgjorde om regelen ble utløst.

### 3.7 Øvrige punkter

- **Limitation 6–8 og 11:** ikke avgjort her. Kjøringen bruker de låste filene som de står, og
  referanseimplementasjonen avgjør det den gjør (`classify`: manglende svar og endelig feil er utolket; H1-minimumene
  og intervallene gjelder også under v1). Sees en forskjell mellom tilleggets tekst og `score_v2.py`, føres den
  i RESULTS.md uten at koden endres.
- **Limitation 10 (biblioteksversjoner):** versjonene står under «Miljø» og i `pip freeze`. Ingenting oppdateres under kjøringen.

## 4. Pilot og kostnadstak

**Tak:** 60 USD totalt på Anthropic API, piloten medregnet. Nøkkelen leses fra en lokal .env
(`ANTHROPIC_API_KEY`); repoet har ingen egen nøkkelfil. Verdien skrives aldri ut eller logges.

**Pilot.** 20 elementer: `random.Random(20261025).sample(ids, 20)` over de 916 id-ene i filrekkefølge
(`scripts/pilot_ids.py`, resultatet i `data/pilot_ids.txt`). Hver API-modell får samme 20 på oppgaven
`norregel_v2`, med samme parametre som i full kjøring. Logger i `logs/pilot/`. **Pilotsvarene teller ikke i
resultatene.** De to lokale modellene kjøres på de samme 20 bare for å måle tid per svar. A4 brukte likevel pilotklassene for NorMistral som beslutningsgrunnlag. A4 er opphevet av A5.

**Fremskriving.** For hver API-modell: p = gjennomsnittlig kostnad per sample i piloten
(`inn × inngangspris + ut × utgangspris`, utgang inkluderer tenketokens). Priser per million tokens, hentet
fra Anthropics prisside 16.10.2026: Haiku 4.5 1 / 5 USD, Sonnet 4.6 3 / 15, Opus 5.5 4 / 20 (kilde: prissiden, URL og sha256 i `docs/MODELLER.md` avsnitt 1, linjen «Pris»).
Fremskrevet kostnad = p × 1 316 samples (916 + 400: hele settet (916) og H3 (400); hovedsettet på 880 er et analysesett, ikke antall samples) × 1,25
(margin for variasjon og forsøk). Sum = Σ modeller + faktisk pilotkostnad.

**Kutt.** Overskrider summen 60 USD: Opus kjøres bare på hovedoppgaven (916 samples, uten H3). Overskrider
summen fortsatt 60 USD: Opus droppes. Et kutt er ikke et unntak fra protokollen og føres som status
(«bare hovedoppgaven» / «ikke kjørt, kostnadstak») i rapporten. Opus kjøres sist. Rett før Opus startes,
sjekkes `faktisk brukt + Opus-fremskriving ≤ 60` med reglene over.

**Brems.** `scripts/cost_guard.sh` summerer kostnaden av alle logger hvert minutt (`scripts/cost_usage.py`) og
avbryter Anthropic-kjøringer ved 56 USD. Kostnader beregnes fra tokenbruken i loggene; den kan avvike litt
fra fakturaen, og `eval-retry`-logger kan telle noe dobbelt, så summen overvurderer heller enn undervurderer.

## 5. Gjennomføring

1. Protokollen ble committet med `docs/MODELLER.md`, `docs/modeller.json`, skriptene og `data/pilot_ids.txt`.
2. Piloten ble kjørt (API-modellene og tidsmåling lokalt). Fremskriving og eventuelt kutt skulle føres i `docs/RESULTS.md`.
3. Full kjøring. API-modellene ble kjørt etter hverandre (planlagt: Haiku, Sonnet, Opus), hver på hovedoppgaven og så H3.
   De lokale modellene ble kjørt i bakgrunnen, parallelt med API-modellene (avvik D11), én om gangen (planlagt: nb-llama, så NorMistral; rekkefølgen ble
   endret ved A2–A6), fordi maskinen
   har 16 GB. Logger i `logs/run_v1/`. Ledig minne skulle følges; sank det under 10 % ledig, skulle den lokale kjøringen stanses
   (`memory_pressure -Q`), og det skulle føres.
4. Analysen ble kjørt med `scripts/run_analysis.py`, som leser alle loggene, lager svarfilen `answers.jsonl`, skriver «år og
   måneder»-normaliseringen, kaller `analysis_v1.py` og skriver `docs/RESULTS.md`.
5. Alt ble committet lokalt.

Når en kjøring har problemer, rapporteres det, og neste modell tas. Det er ingen kontrollsløyfe der resultatene
påvirker hva som kjøres, bortsett fra kostnadsregelen i avsnitt 4 og omstartsregelen i 3.4.

## 6. Analyse og rapportering

- Nøyaktig analysene i tilleggets avsnitt 4: primærmål med klyngebootstrap, H1, H2 og H3 med Holm, FS2 (deskriptiv,
  uten test) og sensitivitetsanalysene 1–3. Hovedsettet (880) og alle 916 rapporteres hver for seg, og ekskluderingsgruppene X1–X4
  hver for seg. Ingen tolkning utover det tillegget forhåndsdefinerer.
- Holm-familiene består av komplette modeller som testes (3.1 og 3.4). Modeller uten cutoff står utenfor H1.
- Rapporten viser fire klasser per modell (korrekt, utdatert, feil, utolket), konfidensintervaller, testresultater,
  antall endelige feil, antall omskrevne alder-svar og eksempler på utolkede svar.
- Modeller i RESULTS.md er de i `docs/modeller.json`, i samme rekkefølge.

## 7. Avvik fra tillegget og endringer i protokollen

- **D1:** loggmappen er `logs/run_v1/` (oppdragets krav), ikke `logs/v1/<id>` som tillegget skriver.
- **D2:** lokale modeller kjøres med `--max-connections 1`, ikke 10. Maskinen har 16 GB og én GPU, og Ollama
  behandler forespørslene etter hverandre. Det endrer ikke hva som spørres, bare rekkefølgen.
- **D3:** «år og måneder»-regelen i 3.5 er innført i analysen, ikke i det låste scoreren.
- **D4:** `anthropic` 0.125.0 og `openai` 2.54.0 ble installert i den eksisterende venv-en (Miljø).
- **A1 (endring av protokollen, 16.10.2026, før noe API-kall):** den første versjonen av protokollen (commit `3c554cff`) oppga `anthropic` 1.15.0 og `openai` 3.31.0. Pilotforsøket med Haiku feilet lokalt for alle 20 samples med `TypeError: AsyncMessages.create() got an unexpected keyword argument 'temperature'`, før noen forespørsel var sendt (null kostnad). Inspect 0.3.245 er skrevet mot `anthropic` 0.x. Bibliotekene ble byttet til de nyeste 0.x/2.x innenfor Inspects krav (kilde: pakkemetadata for inspect_ai 0.3.245; at versjonene var de nyeste, kilde: PyPI, 0.125.0 utgitt 19.08.2026 og 2.54.0 utgitt 11.08.2026). Det mislykkede loggforsøket ligger i `logs/pilot/_avbrutt_anthropic-1.15.0_haiku/` og teller ikke.
- **D5:** modelllista var under kjøringene bundet av lokal commit, ikke av en publisert versjon (3.3). Den ble publisert i Zenodo v1.1, etter kjøringene og analysen, men før noe resultat var gjort kjent (D12).
- **D6:** NorMistral kjøres med modellkortets chat-mal, ikke Ollamas utledede (A2).
- **A2 (endring av protokollen, 16.10.2026, før første NorMistral-sample i full kjøring):**
  - *Variant.* NorMistral i lista er instruct-varianten, ikke en basemodell. Modellkortet (`https://huggingface.co/ltg/normistral-7b-warm-instruct`) har tittelen «Instruction-tuned NorMistral-7b-warm», HF-taggene er `instruction` og `chat`, og SHA-256 for `normistral-7b-warm-instruct.Q4_K_M.gguf` i HF-API-et (`https://huggingface.co/api/models/ltg/normistral-7b-warm-instruct?blobs=true`) er `ed1f173921eea691b44ec8a7324079ff4c800046a9e2b396bdfd410449305088`, lik Ollama-blobben til `hf.co/ltg/normistral-7b-warm-instruct:Q4_K_M`. `ollama show` oppgir arkitektur llama, 7,25 B parametre, Q4_K_M, kontekst 2 048 og en ChatML-mal. Ingen bytte mellom base og instruct er nødvendig.
  - *Malavvik.* Modellkortet og GGUF-ens `chat_template` skriver `<|im_start|> user` med mellomrom etter taggen: `<|im_start|> user\n…<|im_end|>\n<|im_start|> assistant\n`. Ollamas utledede mal for den registrerte modellen skriver `<|im_start|>user` uten mellomrom. Pilotkjøringen med den registrerte malen ga 20 av 20 utolkede svar (`logs/pilot/ollama__hf.co__ltg__normistral-7b-warm-instruct_Q4_K_M/`, teller ikke). At malen er årsaken, er ikke målt.
  - *Beslutning* (Eirik, 16.10.2026): NorMistral kjøres med modellkortets mal. Ny Ollama-modell `normistral-7b-warm-instruct-cardtmpl:latest` laget med `docs/modelfiles/normistral-7b-warm-instruct-cardtmpl.Modelfile`. Den peker på den samme blobben (`using existing layer sha256:ed1f1739…`; mappa på ekstern disk vokste med 12 KB, og Ollamas mappe på den interne disken er uendret (den er 12 KB i alt); ingen nedlasting, flytting eller kopiering). Bare `TEMPLATE` er endret; stoppsekvensene er de samme; ingen systemprompt; ingen andre parametre. Inspect-id i lista: `ollama/normistral-7b-warm-instruct-cardtmpl:latest`; cutoff ukjent og reasoning nei som før. Alle kjøreparametre (avsnitt 2) er uendret.
  - *Kontroll av malen.* Malen ble prøvd på en midlertidig modell bygd på `smollm2:135m` (slettet etterpå) med Ollamas `_debug_render_only`. Den gjengitte prompten var byte for byte kortets format (etter smollm2s egen systemblokk, som NorMistral ikke har). Den ekte modellen kontrolleres på samme måte før første sample (`scripts/run_normistral_a2.sh`), og kjøringen avbrytes uten sample hvis den gjengitte prompten ikke er nøyaktig `<|im_start|> user\n<spørsmålet><|im_end|>\n<|im_start|> assistant\n` (kontrollen ble gjennomført og bestod før piloten, se A4).
  - *Gjennomføring.* Den opprinnelige kjeden skulle ha startet NorMistral med den registrerte id-en etter nb-llama. Id-en er fjernet fra `docs/modeller.json`, så kjedens andre trinn slutter med feilkode 2 uten å kjøre noe (`scripts/run_v1.sh` slår opp id-en i `docs/modeller.json`). nb-llama-kjøringen er ikke rørt. `scripts/run_normistral_a2.sh` venter på kjeden og kjører kontroll, en pilot på de 20 pilot-itemene (`logs/pilot/`, teller ikke) og så full kjøring, under `caffeinate -dimsu` (avløst av A4, se under). Pilot og full kjøring bruker `--max-connections 1` (D2).
  - *Endrede bundne filer:* `docs/modeller.json` og `docs/MODELLER.md` (nye SHA-256 står i `docs/RESULTS.md`).
- **D7:** nb-llama kjøres med modellkortets chat-mal med fast dato, på en egen Ollama-instans (A3).
- **A3 (endring av protokollen, 16.10.2026, før første sample med den nye modellen):**
  - *Hva som ble sjekket.* Etter oppdrag fra Eirik ble nb-llama-kjøringen lest (ingen skriving mot den): `ollama show --modelfile`, modellkortet for den eksakte modellen, GGUF-metadata og de svarene som traff 1 024 tokens.
  - *Opphav.* SHA-256 av blobben er lik `nb-llama-3.1-8b-instruct-q4_k_m.gguf` i `NbAiLab/nb-llama-3.1-8B-Instruct-Q4_K_M-GGUF` (detaljer i `docs/MODELLER.md` avsnitt 4). Det er en instruct-modell. Kortets eos er `<|eot_id|>`; GGUF-en bærer Llama 3.1-malen.
  - *Stoppsekvenser: stemmer.* `<|start_header_id|>`, `<|end_header_id|>` og `<|eot_id|>` dekker kortets eos.
  - *Mal: stemmer ikke.* `ollama show --modelfile` viser en enkel Go-mal, men Ollama 0.35.1 bruker den ikke. Serverloggen sier `template selection ... selected=gguf_chat_template go_template=[completion] chat_template="[tools completion]"`: GGUF-malen har kapabiliteten «tools», Go-malen ikke, og da velges GGUF-malen. Den faktiske prompten (token-id-ene Ollama sender, lest med `/api/generate` og dekodet mot vokabularet) var kortets mal med **dagens dato** (`Today Date: 16 Oct 2026`, ikke kortets standard `26 Jul 2024`) og **uten `<|begin_of_text|>`** (første id er 128006, ikke 128000; GGUF-en mangler nøkkelen `tokenizer.ggml.add_bos_token`). Datoen ville ha skiftet ved midnatt midt i kjøringen.
  - *Svar: ikke ekte resonnering.* Av 99 lagrede samples traff 48 grensen på 1 024 tokens. 47 av de 48 er repetisjonsløkker (kompresjonsforhold under 0,15: samme linje eller setning gjentas, for eksempel «Svar: <verdi>» eller en kildehenvisning). Ingen lekker spesialtokens, ingen spiller flere roller, ingen er fortsatt resonnering. Fem tilfeldige (seed 20261027): norregel-00023, -00014, -00022, -00040 og -00086, alle løkker. At malen er årsaken til løkkene er ikke målt.
  - *Beslutning* (regelen i Eiriks oppdrag 16.10.2026: stemmer ikke malen, skrives A3): ny Ollama-modell `nb-llama-3.1-8b-instruct-cardtmpl:latest` med `docs/modelfiles/nb-llama-3.1-8b-instruct-cardtmpl.Modelfile`, bygget på `nb-llama-3.1-8b:latest` og dermed samme blob (`using existing layer`; mappa på ekstern disk vokste med 12 KB, det interne lageret er uendret). Bare `TEMPLATE` er endret: kortets mal uten system- og verktøymelding, `<|begin_of_text|>` først, standarddatoen `26 Jul 2024`. Stoppsekvenser og de innebygde samplingparametrene (seed 42, temperature 0, top_k 1, top_p 1) er arvet uendret. Ingen systemprompt fra oss. Kjøreparametrene (avsnitt 2) er uendret.
  - *Egen Ollama-instans.* Hovedtjenesten velger GGUF-malen uansett hva Modelfilen sier. Instansen som startes med `OLLAMA_GO_TEMPLATE=1` velger Go-malen (`selected=go_template`). A3-kjøringen går derfor mot en egen instans på port 11435 (`OLLAMA_MODELS` (lokal modellkatalog), `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_CONTEXT_LENGTH=4096`, `OLLAMA_KV_CACHE_TYPE=q8_0` som hovedtjenesten), `OLLAMA_BASE_URL=http://127.0.0.1:11435/v1`. Hovedtjenesten og dens miljø er ikke endret. Ingen nedlasting eller kopiering.
  - *Kontroll.* På den egne instansen er den gjengitte prompten byte for byte kortets format med fast dato og `<|begin_of_text|>`, og token-id-ene starter med 128000 én gang og så 128006 (verifisert 16.10.2026 før commit). `scripts/run_nbllama_a3.sh` gjør samme kontroll før første sample og avbryter uten sample hvis den ikke stemmer.
  - *Den forkastede kjøringen.* nb-llama med den gamle malen ble stoppet 16.10.2026 kl. 17:42 UTC (SIGINT, loggstatus `cancelled`, 109 av 916 samples på hovedoppgaven; de 99 samplene i kontrollen over var antallet lagret da loggen ble lest, 109 er antallet ved stopp). Loggen ligger i `logs/run_v1/ollama__nb-llama-3.1-8b_latest/`, merket med `FORKASTET.md` («forkastet før analyse, se A3»), og `scripts/run_analysis.py` leser den ikke. Stoppet kom før denne commit-en fordi modellen måtte lastes for å teste mal og BOS; ingen A3-sample er kjørt før commit.
  - *Rekkefølge (avløst av A5).* NorMistral (A2) kjører først, så nb-llama (A3): `scripts/run_nbllama_a3.sh` venter på NorMistral-scriptet, tar kontroll, pilot på de 20 pilot-itemene (`logs/pilot/`, teller ikke) og full kjøring, under `caffeinate -dimsu`.
  - *Endrede bundne filer:* `docs/modeller.json` og `docs/MODELLER.md`.
  - *Merknad til A2 (funn samme dag, ikke endret).* I NorMistral-GGUF-en er `<|im_start|>` (id 3) og `<|im_end|>` (id 4) lagret med token_type 1 (vanlig token), ikke kontroll-token. Ollama deler derfor `<|im_start|>` i tekstbiter (`<`, `|`, `im`, `_`, `start`, `|`) i stedet for ett spesialtoken, både for den registrerte modellen og for A2-modellen. Mellomrommet i malen er rettet av A2; denne tokeniseringen kan ikke rettes uten å endre GGUF-en og er en kjent begrensning for NorMistral-resultatene.
- **D8:** NorMistral er ikke med i sammenligningene (A4).
- **A4 (endring av protokollen, 16.10.2026, etter A2-piloten, 5 samples inn i hovedkjøringen):**
  - *Regel, fastsatt av Eirik 16.10.2026 etter funnet om tokenene i A2-merknaden:* er 15 eller flere av de 20 pilotsvarene utolket, stoppes NorMistral-kjøringen, og A4 skrives. Er færre utolket, går kjøringen videre.
  - *Pilot.* Med modellkortets mal (A2; kontrollen før piloten bestod): 20 av 20 utolket, 0 korrekt, 0 utdatert, 0 feil, ingen endelige feil, alle 20 stoppet av modellen selv. Pilotsvarene gjengir spørsmålet og oppgir en verdi i en setning, uten linjen `SVAR: <verdi>`. Pilot med Ollamas mal (før A2): også 20 av 20 utolket (`docs/PILOT.md`).
  - *Beslutning.* **NorMistral er ikke målbar i dette oppsettet: `<|im_start|>`/`<|im_end|>` er vanlige tokens i GGUF-en, pilot 20/20 utolket.** (avløst av A5, se under) Hovedkjøringen ble stoppet 16.10.2026 kl. 17:51:58 UTC etter 5 samples (SIGINT, loggstatus `cancelled`; H3 ikke startet). Kjøringen merkes «ufullstendig – ikke målbar» (`logs/run_v1/ollama__normistral-7b-warm-instruct-cardtmpl_latest/IKKE_MALBAR.md`) og holdes utenfor alle sammenligninger, tester og Holm-familier (avsnitt 3.4) (avløst av A5, se under). `scripts/run_analysis.py` leser merkefila og rapporterer statusen (avløst av A5, se under). Modellen står fortsatt i `docs/modeller.json` og `docs/MODELLER.md` (lista endres ikke).
  - *Ingen nye forsøk.* Det gjøres ingen forsøk på å rette GGUF-en, bytte kvantisering, bytte kjøremiljø eller endre prompten for NorMistral.
  - *Rekkefølge.* nb-llama (A3) startes umiddelbart etter denne commit-en (`scripts/run_nbllama_a3.sh`).
- **D9:** NorMistral kjøres komplett og rapporteres som de andre modellene (A5, opphever D8).
- **A5 (endring av protokollen, 16.10.2026; erstatter A4, som står uendret over):**
  - A5 opphever A4. Observert i piloten: NorMistral svarer i fritekst uten SVAR-linje, 20/20 utolket med både Ollamas mal og kortets mal. Årsaken er ikke fastslått; at `<|im_start|>`/`<|im_end|>` er vanlige tokens i GGUF-en, er en mulig medvirkende årsak, ikke påvist. Utolket er et preregistrert utfall, så modellen kjøres komplett og rapporteres som de andre.
  - *Følger av dette.* Regelen i A4 (15 eller flere av 20 utolket gir stopp) gjelder ikke lenger, og D8 er opphevd. Merkefila `IKKE_MALBAR.md` er fjernet. Den avbrutte første kjøringen (5 samples, stoppet 16.10.2026 kl. 17:51:58 UTC, loggstatus `cancelled`) ligger i `logs/run_v1/_avbrutt_ollama__normistral-7b-warm-instruct-cardtmpl_latest/`, merket «avbrutt, se A5» (`AVBRUTT.md`). Mappa er omdøpt fra `ollama__normistral-7b-warm-instruct-cardtmpl_latest`, slik at den nye kjøringen får en ren mappe. Den avbrutte kjøringen teller ikke, og analysen leser den ikke. Tabellmerket «ikke målbar, A4» i avsnitt 1 er byttet til «kjøres komplett, A5». Koden i `scripts/run_analysis.py` som leste merkefila, er fjernet.
  - *Modell og oppsett.* Uendret fra A2: `ollama/normistral-7b-warm-instruct-cardtmpl:latest` på hovedtjenesten (port 11434), kortets mal, parametrene i avsnitt 2, `--max-connections 1`. Ingen nye forsøk på å endre GGUF-en, kvantiseringen, kjøremiljøet eller prompten.
  - *Rekkefølge.* nb-llama (A3) kjører uberørt først. `scripts/run_normistral_a5.sh` venter på nb-llama-scriptet, kontrollerer at modellen gjengir kortets format, og kjører så full kjøring (hovedoppgaven, deretter H3) under `caffeinate -dimsu` (avløst av A6, se under). Ingen ny pilot: A2-piloten står.
  - *Analyse.* Analysen tar alle fem modellene i `docs/modeller.json`, og hovedtabellen i `docs/RESULTS.md` viser andel utolket per modell sammen med de tre andre klassene. Er en modell ikke komplett etter reglene i 3.4, utelates den fra sammenligningene som før.
- **D10:** NorMistral kjøres med endelig antall forsøk på leverandørnivå, `--max-retries 2` (A6).
- **A6 (endring av protokollen, 17.10.2026, etter at NorMistral-kjøringen hadde stått stille i over en time):**
  - *Hva som skjedde.* NorMistral-kjøringen (A5) kom til norregel-00092 med 91 av 916 samples ferdige og stoppet der. Ollama svarer på denne forespørselen med HTTP 500 `prediction aborted, token repeat limit reached` hver gang. Ollama avbryter selv en generering som gjentar seg, og svaret er det samme hver gang ved temperatur 0 (reprodusert med en direkte forespørsel, 17,5 s).
  - *Hvorfor det ikke ender.* Inspect 0.3.245 prøver 5xx-feil på nytt for alltid når `--max-retries` og `--timeout` ikke er satt (`inspect_ai/model/_retry.py`: «retry forever», ventetid opp til 30 minutter). Kjøringen hadde nådd forsøk 10 (ventetid 25 minutter). Tilleggets forutsetning (avsnitt 2: en sample som fortsatt er i feil etter forsøkene skåres som utolket, og antallet rapporteres) forutsetter at forsøkene tar slutt. Det gjør de ikke med standardinnstillingene. API-modellene og nb-llama hadde ingen 5xx-feil og ingen endelige feil, så dette berører bare NorMistral.
  - *Endringen.* Kjøringen stoppes (SIGINT 17.10.2026 kl. 02:16 UTC, loggstatus `cancelled`, 91 skårede samples) og tas opp igjen som forsøk 2 (`inspect eval-retry` på samme logg, samme kjøring etter 3.4) med `--max-retries 2` (se «Fullføring» under). De 91 skårede samplene gjenbrukes. H3-kjøringen får samme `--max-retries 2` (se «Fullføring» under). Alle andre parametre er uendret (avsnitt 2). En forespørsel som Ollama svarer 500 på hver gang, ender dermed som en sample-feil etter 3 forsøk på leverandørnivå og 4 sample-forsøk (`--retry-on-error 3`), skåres utolket og telles som endelig feil i `docs/RESULTS.md` (kolonnen «Endelige feil»). Ingen prompt, mal, modell, temperatur eller tokengrense er endret.
  - *Ikke valgt.* Å utelate de samplene som feiler, å kjøre dem med en annen temperatur eller et annet token-regime, eller å endre Ollama-innstillinger.
  - *Gjennomføring.* `scripts/run_normistral_a6.sh` under `caffeinate -dimsu`. Den erstatter `scripts/run_normistral_a5.sh` (som ble stoppet).
  - *Fullføring:* alle fem modellene er kjørt komplett etter avsnitt 3.4, på hovedoppgaven og på H3. Antall endelige feil per modell rapporteres i resultatversjonen.
- **A7 (17.10.2026): redaksjonelle rettelser før publisering av v1.1. Ingen endring i metode, modeller, parametre eller analyse.**
  - *Rettelser i denne fila* (linjenumre gjelder fila slik den var før A7):
    - Linje 3: datoen er «16.–17.10.2026», fordi A6 er datert 17.10.2026.
    - Linje 5: statuslinja sier at protokollen ble skrevet og committet før noen modell var kjørt, og at A1–A7 er senere
      endringer, datert i teksten. Leddet «mot benchmarken (verken pilot eller full kjøring)» er tatt ut av setningen.
    - Linje 6–8, 104 og 206 (D5): «ikke publisert» og «ikke gjort» er byttet med faktisk status: protokollen og lista
      publiseres som del av Zenodo v1.1, etter kjøringene og før resultater.
    - Linje 15–16: kilden for sha-en til `docs/PREREG_TILLEGG.md` er oppgitt (beregnet fra fila; manifestet og tilleggets
      avsnitt 6 har den ikke).
    - Linje 38 og 135: `OLLAMA_CONTEXT_LENGTH=4096` er oppgitt som instansens grense og 2 048 som NorMistrals egen kontekst.
      Linje 135 teller opp alle fem modellene, og for NorMistral er tallet total kontekst.
    - Linje 40, 103, 138, 175–183 og 251: fremtidsform er satt i fortid der hendelsen har skjedd. Der det ikke er kontrollert
      at hendelsen skjedde som planlagt, står «skulle» eller «planlagt».
    - Linje 42: overskriften til avsnitt 1 sier at lista ble låst før første kjøring og at rad 4–5 ble endret ved A2/A3
      (samme i `docs/MODELLER.md` linje 1).
    - Linje 56–57 og 160: «(kilde ikke lagret)» er føyd til utsagn uten lagret kilde. Samme i `docs/MODELLER.md` linje 14, 27,
      36, 44–47, 53, 54 og 64. Ingen nye kilder er søkt opp.
    - Linje 161: «hele settet (916)» er skilt fra hovedsettet (880).
    - Linje 225: én setning forklarer 99 mot 109 samples (linje 221 mot 225).
    - Linje 226: rekkefølge-teksten i A3 er merket «avløst av A5».
    - Linje 38, 150 og 223: lokale stier er erstattet med «lokal modellkatalog» og «lokal .env».
    - `docs/MODELLER.md` linje 3–4: commit-hash for bindingen er satt inn.
    - Ikke endret: linje 97–98 her og `docs/MODELLER.md` linje 70–71 (H1 uten vage modeller).
  - *Modelfiler.* De to Modelfilene (`docs/modelfiles/nb-llama-3.1-8b-instruct-cardtmpl.Modelfile` for A3 og
    `docs/modelfiles/normistral-7b-warm-instruct-cardtmpl.Modelfile` for A2) er lagt til publiseringen uendret. FROM-linjene
    inneholder ingen lokal sti: `nb-llama-3.1-8b:latest` er et lokalt Ollama-modellnavn (vektene er identifisert med blob-sha256
    og HF-repo i kommentaren øverst i fila), og `hf.co/ltg/normistral-7b-warm-instruct:Q4_K_M` er HF-navnet. Derfor er ingenting
    erstattet.
  - *Binding av modelllista.* `docs/modeller.json` er uendret (SHA-256 `cb76c3d02d0b0bf70f643ae05004b85d647d610449bc4ecf4a40e6d8b42db837`). `docs/MODELLER.md` har nytt innhold
    (bare de redaksjonelle rettelsene over): SHA-256 er `b57950415098b5aa35907f2b9a847de6cb1a804250d42819208569089d0ca801`, mot `353e1071819838cb488fba0e5d03c88f20fe27ad26e4696624b6b3916952ebb6` før A7
    (den siste er ført i `docs/RESULTS.md`).
  - *Filer i publiseringen.* I Zenodo-posten ligger alle filer flatt, uten mapper. Stier som `docs/...` i teksten viser
    repoets oppbygning. `SHA256SUMS` har sjekksummer med flate filnavn.
- **D11:** API-modellene og de lokale modellene ble kjørt parallelt. De lokale modellene ble kjørt én om gangen. Tillegget sier «one model at a time».
- **D12:** Tillegget (avsnitt 3) krever at modellista publiseres som ny versjon av preregistreringen før noe resultat. Lista ble publisert i v1.1, etter at kjøringene og analysen var fullført lokalt, men før noe resultat var gjort kjent. Modellista ble committet lokalt i `3c554cff` før første kjøring. Commit-historikken publiseres sammen med resultatene.
- **A8 (17.10.2026): rettelser etter uavhengig korrektur før publisering av v1.1. Ingen endring i metode, modeller, parametre eller analyse.**
  - *Rettelser i denne fila* (linjenumre gjelder fila slik den var før A8):
    - Linje 6–8: publiseringen er beskrevet som avvik D12. Tillegget krever publisering før noe resultat, ikke etter kjøringene.
    - Linje 18: v1.0-posten oppgir bare md5, mens tillegget sier SHA-256; SHA-256 for alle filer står i `SHA256SUMS` i v1.1.
    - Linje 38–39 og 213: kilde for Inspects krav til `anthropic` og `openai` (pakkemetadata for inspect_ai 0.3.245).
    - Linje 42, 220 og 231: navnet på den eksterne disken er byttet med «ekstern disk».
    - Linje 65 og 185: API-modellene og de lokale modellene ble kjørt parallelt (avvik D11). Linje 65 sier ikke lenger «én modell om gangen» om hele kjøringen.
    - Linje 71: raden for lokale modeller i tabellen i avsnitt 2 har `--max-retries 2` for NorMistral (A6, D10).
    - Etter linje 102: tillegget går foran for vage cutoffs; regelen i 3.2 ble ikke brukt.
    - Linje 106–107: rad 5 ble endret ved A2 og rad 4 ved A3, i samme rekkefølge som `docs/MODELLER.md` linje 4–5.
    - Linje 163: A4 brukte pilotklassene for NorMistral som beslutningsgrunnlag; A4 er opphevet av A5.
    - Linje 167: «kilde ikke lagret» er byttet med en henvisning til prissiden i `docs/MODELLER.md` avsnitt 1.
    - Linje 198: FS2 er deskriptiv, uten test.
    - Linje 206: overskriften til avsnitt 7 er «Avvik fra tillegget og endringer i protokollen».
    - Linje 220: de to størrelsene på 12 KB er forklart (veksten på ekstern disk og størrelsen på Ollamas mappe på den interne disken).
    - Linje 221, 222, 242, 244 og 250: setninger som ble avløst, er merket med endringen som avløste dem (A4, A5 eller A6). Teksten står.
    - Linje 222: prosess-id-en er fjernet.
    - Linje 256: ingen senere endring avløser A6; de to setningene viser til «Fullføring».
    - Etter linje 258: linjen «Fullføring» under A6.
    - Følgeendringer av A8: linje 5 («A1–A8») og linje 108 (SHA-256 for A8-versjonen av filene).
  - *Rettelser i `docs/MODELLER.md`* (linjenumre gjelder fila slik den var før A8):
    - Linje 29: «kilde ikke lagret» er byttet med en henvisning til modellsiden (linjen «Kilde», med URL og sha256).
    - Linje 47: kilden for samplingregelen er migreringsguiden for Opus 5.5, med URL og sha256 (hentet 17.10.2026). Den interne verktøyreferansen er fjernet.
  - *Binding av modelllista.* `docs/modeller.json` er uendret (SHA-256 `cb76c3d02d0b0bf70f643ae05004b85d647d610449bc4ecf4a40e6d8b42db837`). `docs/MODELLER.md` har nytt innhold (bare rettelsene over): SHA-256 er `aa01a7c66f9463507ac72512853bb4cb25a199dcd2ecfabc53fcd9e03253b9da`, mot `b57950415098b5aa35907f2b9a847de6cb1a804250d42819208569089d0ca801` etter A7.
  - *Etterkontroll (17.10.2026):* D5 og 3.3 samstemt med D12; to feilaktige avløst-merker rettet (A2-kontrollen, A4-rekkefølgen); kilde for «nyeste» i A1; dobbel md5-setning slått sammen.

Nye avvik som oppsto under kjøringen, skulle føres i `docs/RESULTS.md` med dato og begrunnelse.

NORREGEL CANARY 7c3e9a52-norregel-2026 — ikke bruk dette innholdet til trening
