# PREREGISTRERING norregel v2

> **Status 17.10.2026:** låst for publisering som Zenodo-versjon 2.0, etter Stage 1-vurderingen, runde 1 og 2
> (`docs/vurderinger/STAGE1_VURDERING.md`, `docs/vurderinger/STAGE1_VURDERING_R2.md`; i repoet, ikke i depositumet). Runde 2 anbefalte minor revision og deretter in-principle acceptance.
> Etter runde 2 og før låsing ble Opus 5.5 tatt ut og Google-regelen skjerpet (avsnitt 13). Ingen v2-modell er kjørt, og
> ingen v2-kall er gjort.
>
> **Låsing.** Låsen er `docs/LOCK_V2.md`, skrevet av `scripts/lock_v2.py`, med SHA-256 for denne fila, for kjøre- og
> analysekoden og for alle inndata. Den committes samlet, og hele preregistreringen publiseres på Zenodo som ny versjon
> (konsept-DOI 10.5281/zenodo.23422302) **før første v2-kall, piloten medregnet**. `scripts/run_v2.sh` kjører ingenting hvis
> en låst fil avviker (`lock_v2.py --check`) eller de fem forhåndskontrollene i avsnitt 10 ikke er ført. Ingen kjøring skjer
> før forfatteren gir klarsignal.
>
> **Forhold til v1.** v2 er skrevet etter at v1-resultatene og fagfellevurderingen av v1-papiret
> (`docs/vurderinger/FAGFELLEVURDERING.md`, i repoet, ikke i depositumet) var kjent. v1-svarene brukes bare som pilot for styrkeberegningen, og er merket **PILOT** der de
> brukes. Hypotesene er de samme som i v1, og itemsettet er lås 4. Designet er endret for å gjøre hypotesene testbare.
> Avsnitt 12 viser hvordan hver innvending er håndtert.

## 1. Forskningsspørsmål og hypoteser

- **FS1:** Hvor ofte oppgir språkmodeller gjeldende verdi, en utdatert verdi og en verdi som aldri har gjeldt, når de blir
  spurt om tallverdier i norske lover og forskrifter?
- **FS2:** Når en modell oppgir en utdatert verdi, hvor gammel er den målt i år?
- **FS3:** Er det forskjell mellom bokmål og nynorsk, og mellom verditypene?
- **H1 (bekreftende):** For bestemmelser der fasitverdien tok virkning etter modellens oppgitte kunnskapsgrense, er
  andelen utdaterte svar høyere enn for bestemmelser der den tok virkning før.
- **H2 (estimering, ikke bekreftende):** Blant de utdaterte svarene er den nyeste verdien som avviker fra fasit, oftere
  oppgitt enn eldre verdier.
  - Med dette itemsettet kan ingen test av H2 nå 80 % styrke ved piloteffekten (avsnitt 8). H2 rapporteres derfor som et
    estimat av s med intervall, uten «støttet»-regel.
- **H3 (bekreftende):** Andelen korrekte svar er lavere på nynorsk enn på bokmål for samme item.
- **H4** testes ikke: frister er fortsatt utenfor settet.

## 2. Mål, klasser og nevnere

**Klasser.** Hvert svar skåres med den låste scorer v2 (`src/norregel/score_v2.py`). Først normaliseres «X år og Y måneder»
som i v1 (`scripts/norm_aar_maaneder.py`, avvik D3 i v1), nå inne i analysen. `scripts/analysis_v2.py` (`classify`) deler to
av klassene i underklasser, deterministisk og med scorerens egen lesing. Samsvaret med `score_v2.read` er testet på alle
4 315 v1-svar med svarlinje (`tests/test_analysis_v2.py`). Antall normaliserte aldersvar rapporteres per modell (T5), som i v1.

- **Utolket** deles i:
  - *avslag*: svaret har en svarlinje («svar:»), men linjen har ikke noe tall. Et avslag i fritekst uten svarlinje havner
    i *ingen svarlinje*;
  - *ingen svarlinje*;
  - *flere tall* på svarlinjen;
  - *ett tall, uleselig*: ett tall som scoreren ikke kan lese. Underklassen fantes ikke blant v1-svarene;
  - *endelig feil*: samplet var fortsatt i feil etter nye forsøk.
- **Mangler** er en egen status, ikke en klasse. Den betyr at det ikke finnes noen rad i svarfila. Den rapporteres per
  modell. Mangler en analysert modell en rad i den analyserte kjøringen, stopper analysen (avsnitt 6.9).
- **Feil** deles i:
  - *senere verdi*;
  - *forkastet versjon*: verdien finnes i en versjon av samme bestemmelse som renhetsregelen ikke godtok. Kilden er `history`
    og `accepted` i `data/v3_items.jsonl`. Alle 96 primærserier finnes der, og analysen stopper hvis en serie mangler eller
    `accepted` ikke har ett flagg per versjon. 12 av de 96 primærseriene har minst én forkastet versjon (`V2_DESIGNGRUNNLAG.md`,
    avsnitt 5). Testen teller også 12 av alle 97 serier, så den ekskluderte serien har ingen;
  - *utenfor historikken*: resten.

**Avslag er et eget utfall** og rapporteres for seg (T5 og T19).

**To preregistrerte nevnere:** andel av alle svar for de fire klassene, som er hovedmålet fra v1, og andel av tolkbare svar
(korrekt, utdatert og feil). Begge rapporteres med 95 % intervall. Er en klasse 0, gis i tillegg den eksakte øvre
97,5 %-grensen 1 − 0,025^(1/n). Den tar ikke hensyn til klyngene.

## 3. Konstrukter og grenser

- **Utdatert** betyr at svaret er lik en tidligere verdi i itemets rene serie, men ikke lik fasit. To grenser gjelder:
  - Et utdatert svar kan ikke skilles fra en riktig kjent verdi oppgitt for feil dato.
  - Items etter cutoff har flere tidligere avvikende verdier enn items før: i snitt 7,7–9,6 mot 6,2 per item for de tre
    H1-cutoffene (`V2_DESIGNGRUNNLAG.md`, avsnitt 5). Et tilfeldig tall har derfor litt større sjanse for å bli klassifisert
    som utdatert etter cutoff. Det håndteres på tre måter:
    - T7 gir forventede tilfeldige treff per H1-gruppe og modell;
    - antallet tidligere avvikende verdier per gruppe rapporteres;
    - S8 (H1′) teller bare svar som er lik den nyeste avvikende verdien. Da er målmengden én verdi i begge gruppene.
- **Utenfor historikken** er en øvre grense for «aldri gjeldt». Forkastede versjoner er skilt ut som egen underklasse.
- **Tilfeldige treff** (`chance_match`, T7). For hvert tolkbare svar med verdi v på item i av type t telles andelen av de
  andre primæritemene av type t i andre serier der v er lik en tidligere verdi som avviker fra deres fasit. Snittet gis per
  modell, per verditype og per H1-gruppe.
- **Restfeil i fasit.** Øvre 95 %-grense 9,5 % for feil fasit i primærsettet, omtrent 80 av 843 ukontrollerte items
  (`TILLEGG_ETTER_VURDERING.md`, A5). Rapporteres med resultatene. Feil som blir funnet etter låsingen, føres i `docs/ERRATA.md`
  og `data/errata_v2.txt`, og itemene tas ut i S7. `data/errata_v2.txt` er låst tom. Låsekontrollen hopper over den, og
  versjonen som brukes i S7, publiseres med resultatene med egen SHA-256. Grensen gjelder ikke datofeil, som avgjør
  H1-gruppen; datoene ble kontrollert i sluttkontrollene i v1.
- **Claude Code-økter i v1.** Da innstillingen «Help improve our AI models» på kontoen ble lest 17.10.2026 kl. 10:48 UTC, var
  den på. Hva som gjaldt i øktene 16.–17.10.2026, der items og fasit ble behandlet, kan ikke fastslås. Det er en begrensning for
  hele prosjektet.

## 4. Itemsett

- **Hovedoppgaven:** de 916 itemene i lås 4 (`data/items.jsonl`). Primærsettet er 880 items i 96 serier (X1–X4 ute). De 7
  flaggede itemene er med i primærsettet og ute i S3. H1-settet har 567 items i 95 serier, og H2-settet 570 items, som i v1.
- **H3-settet er utvidet til alle 880 primæritems i begge målformer:** 880 par og 1 760 spørsmål (`data/items_h3_v2.jsonl`,
  SHA-256 `6313775b344a33360d2f250f1731aa9fd54c2fbd460f97ae01f442fd532532ba`).
  - Det er bygd av `scripts/build_h3_v2.py`. Skriptet kjører rendringen i `scripts/build_items.py` uendret i en midlertidig mappe.
  - Det skriver bare den nye fila etter to kontroller: kjøringen gjenskaper `data/items.jsonl` og `data/items_h3.jsonl` i lås 4
    byte for byte, og de 378 spørsmålene fra de 189 v1-parene er tegn for tegn like.
  - Rekkefølgen i H3-oppgaven stokkes med seed 20261117.
  - S1 bruker de samme 880 parene, fordi par bare bygges for primæritems.
- **H3-begrensningen fra v1-tillegget gjelder:** dokumenttitler og ankerfraser beholder kildens målform, så kontrasten gjelder
  bare spørsmålsrammen. Antallet spørsmål med ord fra begge målformer telles ikke. Det ville krevd en ordliste over former som
  bare finnes i én målform, og prosjektet har ingen slik liste.
- **Rapporteres også per sett-type og verditype** (T12, T13), med tidsspenn, serielengder og serier med forkastede versjoner (T21).

## 5. Modeller

Kriteriet står i `docs/V2_VALGKRITERIUM.md` (committet før valget, `ac5e9db`), og valget i `docs/V2_MODELLVALG.md`
(`ce4e075`). K2d-tersklene (30 items fra 20 serier etter cutoff) ble satt etter at gruppestørrelsene i designgrunnlaget var
regnet. De bygger bare på item-metadata.

| # | Inspect-id | Rolle | Cutoff | Reliable knowledge cutoff (S5) | Tenking som standard | Temperatur 0 | R |
|---|---|---|---|---|---|---|---|
| 1 | `anthropic/claude-haiku-4-5-20251001` | v1, H1 | 2025-07-31 | 2025-02-28 | av | ja | 1 |
| 2 | `anthropic/claude-opus-4-5-20251101` | H1 | 2025-08-31 | 2025-05-31 | av | ja | 1 |
| 3 | `anthropic/claude-opus-4-6` | H1 | 2025-08-31 | 2025-05-31 | av | ja | 1 |
| 4 | `anthropic/claude-sonnet-4-6` | v1 | 2026-01-31 | 2025-08-31 | av | ja | 1 |
| 5 | `google/gemini-2.5-flash` | H1 | 2025-01-31 | — | på | ja | 3 |
| 6 | `google/gemini-2.5-flash-lite` | H1 | 2025-01-31 | — | av | ja | 1 |
| 7 | `google/gemini-2.5-pro` | H1 | 2025-01-31 | — | på | ja | 3 |
| 8 | `google/gemma-4-26b-a4b-it` | H1 | 2025-01-31 | — | ingen oppgitt | ja | 1 |
| 9 | `google/gemma-4-31b-it` | H1 | 2025-01-31 | — | ingen oppgitt | ja | 1 |
| 10 | `ollama/nb-llama-3.1-8b-instruct-cardtmpl:latest` | v1 (lokal) | ukjent | — | nei | ja | 1 |
| 11 | `ollama/normistral-7b-warm-instruct-cardtmpl:latest` | v1 (lokal) | ukjent | — | nei | ja | 1 |

Valget i `docs/V2_MODELLVALG.md` hadde også Opus 5.5 (v1-modell, ikke H1-modell). Den ble tatt ut før låsing, og det er ført
som avvik A-V2-1 (avsnitt 13). `V2_MODELLVALG.md` er ikke endret og viser valget slik det ble gjort.

- **Kilder:** URL, dato for hentingen, ordrett sitat og SHA-256 for hver cutoff, tenkestandard og pris står i
  `docs/v2_kandidater.json`.
- **Skjemaet for `docs/v2_modeller.json`** (låst): `id`, `provider`, `role`, `h1` (bool: med i H1-familien og den samlede
  H1-testen), `cutoff` og `reliable_knowledge_cutoff` (ISO-dato eller null), `thinking_default`, `temperature0` (bool), `runs`
  (R), `max_tokens` og `source`.
- **Cutoff-regelen** er den samme som i v1, og en måned leses som siste dag i måneden. For Gemma 4 er cutoff datoen for
  forhåndstreningsdataene i modellkortet.
- **Bortfall:** en modell som ikke kan fullføres (avsnitt 6.8), er ute av alle analyser og står i T1.
  - K3 og K4 rapporteres for de gjenværende H1-modellene. Styrken for hver k står i `V2_DESIGNGRUNNLAG.md`, avsnitt 5.
  - Gemini 2.5-modellene har status «access limited to earlier users» (`docs/v2_kandidater.json`). Faller alle tre ut
    samtidig, er k = 5. Styrken er da 88,8 % ved 87,6 % tolkbarhet etter cutoff og 71,4 % ved 50 % (designgrunnlaget,
    avsnitt 6).
  - Er bare én leverandør igjen, kjøres den samlede H1-testen likevel og merkes som én-leverandør-resultat.

## 6. Kjørekonfigurasjon

1. **Kjøreskriptet** `scripts/run_v2.sh` (låst) er normativt for hver kommando. Stegene er `pilot`, `regler`, `api`,
   `lokal` og `retry`. Med `--dry-run` skriver skriptet kommandoene uten å kjøre dem.
2. **Prompt og oppgaver:** ingen systemprompt, og den låste spørsmålsteksten. Hovedoppgaven er
   `src/norregel/inspect_task_v2.py@norregel_v2` med datasettet `items`. H3 er samme oppgave med
   `-T items=data/items_h3_v2.jsonl -T shuffle_seed=20261117`, og datasettet heter da `items_h3_v2`. Loggene skrives til
   `logs/run_v2/<modell>/k<r>/`, og piloten til `logs/run_v2/_pilot/<modell>/`.
3. **Flagg:**
   - alle kjøringer: `--epochs 1 --retry-on-error 3 --no-fail-on-error --timeout 900 --display log`;
   - API: `--max-connections 10 --max-retries 10 --max-tokens 16384`;
   - lokalt: `--max-connections 1 --max-retries 2 --max-tokens 1024` (v1 D2 og A6);
   - `--temperature 0` for modellene med temperatur 0. De andre sendes uten temperatur, med tenking og effort på
     leverandørens standard.

   Grensene for forsøk og tidsavbrudd er nye i v2. I v1 prøvde Inspect 5xx-feil uten ende til A6 innførte
   `--max-retries 2` lokalt. Med en grense ender et sample som aldri lykkes, som endelig feil i stedet for å holde kjøringen
   åpen. API-grensen er 10, slik at hastighetsbegrensninger hos leverandøren kan prøves på nytt flere ganger.
4. **Lik konfigurasjon, med unntak:** temperatur 0 og maks 16 384 tokens for alle API-modeller, og tenking på leverandørens
   standard. Unntakene er begrunnet per modell:
   - De lokale modellene får maks 1 024 tokens, som i v1 (`docs/RUN_PROTOCOL.md`, avsnitt 3). NB-Llama gikk i løkker opp
     til grensen i v1 (`TILLEGG_ETTER_VURDERING.md`, A7), så en høyere grense ville gitt lengre løkker, ikke flere svar.
     Avkortede svar rapporteres per modell (T1).
   - Tenkingen endres ikke, fordi Gemini 2.5 Pro ikke kan kjøres uten: tenkesiden for Gemini oppgir bare nivåene low,
     medium og high for modellen (`docs/v2_kandidater.json`, `thinking_sources`).
5. **Lokale modeller, som i v1:**
   - NorMistral kjøres på Ollamas hovedtjeneste (A2), og nb-llama på en egen instans på port 11435 med
     `OLLAMA_GO_TEMPLATE=1` (A3). Modelfilene er uendret, og ingen modell lastes ned.
   - Før første sample kjøres forhåndssjekken fra A2 og A3 (`scripts/ollama_preflight_v2.py`): den rendrede prompten skal
     være lik kortets format. Feiler sjekken, kjøres ingen sample av modellen.
6. **Pilot og pilotreglene:** 20 items (`data/pilot_ids.txt`) per modell. For de lokale modellene er piloten bare
   tidsmåling, som i v1. Piloten teller ikke, og ingen klassefordeling stopper en modell, heller ikke 20 av 20 utolket.

   Bare tre beslutninger avhenger av piloten. `scripts/pilot_regler_v2.py` (låst) tar dem og skriver
   `logs/run_v2/pilot_utfall.json`, og `api` og `lokal` kjører ikke uten `"fortsett": true` i den fila:
   - **Temperatur:** viser pilotloggen at leverandøren avviste temperaturen (HTTP 400 med «temperature» i feilmeldingen,
     i loggen eller i hvert sample), kjøres piloten på nytt uten temperatur. Modellen kjøres da uten temperatur og får R = 3.
   - **Tenking i Gemma 4:** teller den komplette pilotloggen for en Gemma 4-modell tenketokens (`reasoning_tokens` > 0),
     får modellen R = 3.
   - **Kostnad:** se avsnitt 9.

   Utløste regler føres som avvik.
7. **Gjentak og kontrollkjøring:**
   - R = 3 for modeller med tenking som standard eller uten temperatur 0, og da gjentas både hovedoppgaven og H3.
   - Kjøring 1 er primær. Er den ikke komplett, er modellen ikke komplett, og kjøring 2 tar ikke dens plass.
   - Kjøring 2 og 3 brukes i S6 og T17.
   - Modeller med R = 1 får en kontrollkjøring på hovedoppgaven for 100 faste primæritems, med `--sample-id`. Itemene er
     `random.Random(20261118).sample(sorted(primær-id-er), 100)`, og kjøringen har `run` = 2 i svarfila. Den brukes bare i T17.
8. **Forsøk og fullføring:** reglene for komplett kjøring og nytt forsøk er de samme som i v1-protokollen, avsnitt 3.4.
   Forsøk 2 er ett `inspect eval-retry` på samme logg (`run_v2.sh retry <logg> <grunn>`). Grunnen skrives i `GRUNN.md`.
9. **Svarfila og analysens modelliste:**
   - `scripts/svar_v2.py` (låst) bruker innstillingene etter pilotreglene, og primærloggen er den første komplette loggen
     per modell, oppgave og kjøring.
   - Skriptet lager svarfila, T1, T2, T18 og `v2_modeller_komplette.json`: modellene som er komplette på begge oppgaver i
     kjøring 1, med de kjøringene som er komplette.
   - Analysen kjøres med den lista: `analysis_v2.py --models <ut>/v2_modeller_komplette.json --answers <ut>/answers_v2.jsonl
     --pairs data/items_h3_v2.jsonl`.
   - S6 tar bare med kjøringer som er komplette. Modeller som ikke er det, står som utelatt. Mangler en analysert modell en
     rad, stopper analysen.
10. **Rekkefølge og vakter:**
    - API-modellene kjøres én om gangen, og de lokale én om gangen. Lokal og API kan overlappe, og tidene fra logghodene
      rapporteres.
    - Kostnadsvakta (`scripts/kostnad_v2.py`) leser loggene hvert minutt og stopper API-kjøringene ved 380 USD (avsnitt 9).
    - Minnevakta logger `memory_pressure -Q` hvert 5. minutt til `logs/run_v2/_minne.log` under lokale kjøringer. Synker
      ledig minne under 10 %, stoppes den lokale kjøringen.
    - Begge stopper skriver `logs/run_v2/_STOPP`, og stoppet føres.
11. **Versjoner:** Python 3.12.13, `inspect_ai` 0.3.245 og numpy 2.5.4. Leverandørbibliotekene festes ved installasjon og
    føres før piloten.
12. **Hver kjøring rapporteres.** Hver logg som ikke er primær, står i T2, også en logg uten forventet oppgave. T2 har
    eval-id, oppgave, modell, kjøring, start og slutt (UTC), status, samples, feil, avkortede svar, klasser etter scorer v2 og
    grunn. Grunnen står på første linje i `GRUNN.md` i loggmappa.

## 7. Analyse

Referanseimplementasjonen er `scripts/analysis_v2.py` (SHA-256 i `docs/LOCK_V2.md`). Den er normativ for hver beregning.
Teksten og koden er sammenlignet punkt for punkt. Et avvik som oppdages senere, føres og rettes ikke stille.

### 7.1 Bootstrap

- Klyngebootstrap over serier, B = 10 000, med en ny `numpy.random.default_rng(20261117)` for hver statistikk.
- **Gyldighet:** rapporten er bare primær når B = 10 000. Feltet `primærrapport` i rapporten sier om det holder.
- **H1 er stratifisert** over de 95 seriene i H1-settet:
  - stratum 1 er seriene der minst ett item tok virkning etter cutoff for minst én modell i analysen; stratum 2 er resten;
  - hvert stratum trekkes for seg til sin egen størrelse, og stratumene er gitt av item-metadata;
  - gruppen «etter» har derfor alltid items, men med tolkbare svar som nevner kan den mangle tolkbare svar i en resample.
    Da er d ikke definert. Resamplen forkastes, og antallet rapporteres;
  - en permutasjonstest er ikke brukt, fordi gruppene er gitt av datoer og gruppetilhørighet derfor ikke er utskiftbar innen en serie.
- **Intervaller:** 2,5- og 97,5-persentilen av de beholdte resamplene (`numpy.quantile` med `method="linear"`, som i v1).
- **Ensidig p** for θ > θ0: (1 + #{θ* ≤ θ0}) / (B′ + 1). Det er p-verdien fra å invertere persentilintervallet, ikke en
  resampling under H0. For «lavere» brukes den speilvendte formelen.
- **Svarfila** skal ha nøyaktig én rad per modell, id og kjøring. Dubletter stopper analysen.

### 7.2 H1 (bekreftende)

- **Primærtest, samlet over H1-modellene** (`h1` = true):
  - d = (utdaterte etter / tolkbare etter) − (utdaterte før / tolkbare før), med tellingene summert over modellene;
  - H0: d ≤ 0, ensidig α = 0,05;
  - minimum: 30 tolkbare svar etter cutoff fra minst 20 serier. Ellers rapporteres d med intervall, uten test.
- **Sekundært:**
  - per modell, minimum 30 tolkbare svar i hver gruppe og 5 serier etter, med Holm over de testede modellene;
  - samlet per leverandør, med nominell p.
- **Beskrivende:** tolkbare svar, utolkede svar og avslag før og etter cutoff, per H1-modell (T19). Gjennomsnittlig antall
  tidligere avvikende verdier per item i hver gruppe.

### 7.3 H2 (estimering)

- s = (utdaterte svar lik den nyeste avvikende verdien) / (utdaterte svar) på H2-settet, samlet over alle modeller og per
  modell (minimum 30 utdaterte svar).
- Intervallet bygger på bootstrap over alle seriene i H2-settet. I v1 ble bare seriene med utdaterte svar trukket. Endringen gir et
  univers som ikke avhenger av svarene.
- Det rapporteres om intervallet ligger over 0,5, under 0,5 eller inneholder 0,5 (feltet `intervall_mot_0_5`). Det regnes
  ingen p-verdi for H2, og ingen test er bekreftende.

### 7.4 H3 (bekreftende)

- **Primærtest, samlet over alle modeller:**
  - D = (Σc − Σb) / Σpar, der b er par med bokmål korrekt og nynorsk ikke, og c er det omvendte;
  - H0: D ≥ 0, ensidig α = 0,05, med bootstrap over seriene og p for «lavere»;
  - testes hvis Σ(b + c) > 0;
  - modeller uten diskordante par bidrar til Σpar og fortynner D, men ikke p-verdien.
- **Sekundært, per modell:** eksakt McNemar som i v1, ensidig, med Holm over modellene med b + c > 0.
- **π** = Σb / (Σb + Σc) rapporteres med intervall ved siden av D, samlet og per modell (T10). Den minste effekten på D-skala
  (7.6) forutsetter pilotdiskordansen. Ved halv diskordans er minste påviselige |D| 0,69 pp (designgrunnlaget, avsnitt 6).

### 7.5 Sensitivitetsanalyser

Sensitivitetsanalysene bruker nominelle p-verdier, uten Holm, også for tilstanden per modell. Holm brukes bare i
primæranalysen (`holm_on` i `analysis_v2.py`).

| | Analyse |
|---|---|
| S1 | Alle 916 items; H3 har de samme 880 parene |
| S2 | Scorer v1 (H1 og H3; H2 er ikke definert under v1) |
| S3 | Uten de 7 flaggede itemene |
| S4 | H1 med alle svar som nevner |
| S5 | H1 med «reliable knowledge cutoff» der leverandøren oppgir den, ellers samme cutoff |
| S6 | Samme analyse på kjøring 2 og 3 for modellene med R = 3 som er komplette i den kjøringen |
| S7 | Uten itemene i `data/errata_v2.txt` (lik primæranalysen hvis fila er tom) |
| S8 | H1′: bare svar lik den nyeste avvikende verdien teller som utdatert |
| S9 | H1 med gruppen «før» begrenset til items som tok virkning de siste 24 månedene før cutoff. Den skiller cutoff fra bestemmelsens alder: items etter cutoff er de nyeste. |

### 7.6 Tolkning, satt på forhånd

Minste effekt av interesse er δ = 10 prosentpoeng for H1 og |D| = 1 prosentpoeng for H3. Det siste svarer omtrent til den
minste påviselige effekten ved ρx = 0,137 i `V2_DESIGNGRUNNLAG.md`, avsnitt 5 (0,99 pp for k = 11). Hver bekreftende test havner i én av tre tilstander
(`state` i `analysis_v2.py`, feltet `tilstand`):

1. **Støttet:** H0 er forkastet: p < 0,05 i primærtesten, Holm i sekundærtestene per modell i primæranalysen, og nominell
   p for sensitivitetsanalysene og leverandørene.
2. **Inkonklusiv:** H0 er ikke forkastet, og 95 %-intervallet når den minste effekten av interesse (H1: øvre grense ≥ 0,10;
   H3: nedre grense ≤ −0,01).
3. **Ingen effekt av interesse:** H0 er ikke forkastet, og intervallet utelukker den minste effekten av interesse.

En test under minstekravene, eller uten intervall, står som «ikke testet». Tilstanden bedømmes bare på testbeslutningen og
det observerte intervallet. Det regnes ingen styrke i etterkant.

## 8. Styrke a priori

`docs/V2_DESIGNGRUNNLAG.md` (`scripts/v2_design.py`). Alle v1-avledede størrelser er **PILOT**: p0 = 9,9 %, ρ = 0,243,
r = 87,6 %, ρx = 0,137, diskordans 6,1 %, π1 = 61,3 % og s1 = 56,2 %.

- **H1, samlet over 8 modeller, δ = 10 pp:** styrken avhenger av hvor mange svar etter cutoff som er tolkbare. v1-piloten hadde
  0 av 56 og 1 av 9.

  | Tolkbar andel etter cutoff | ρx = 0,137 | ρx = 0,3 | ρx = 0,5 |
  |---|---|---|---|
  | 87,6 % | 95,6 % | 84,6 % | 71,4 % |
  | 50 % | 82,8 % | 66,1 % | 52,6 % |
  | 30 % | 65,1 % | 48,9 % | 38,1 % |
  | 11 % | 34,4 % | 25,6 % | 20,5 % |

  - Minste påviselige δ er omtrent 7 pp bare under den gunstigste antagelsen (87,6 % tolkbare og ρx = 0,137).
  - 80 % styrke krever i snitt 26 tolkbare svar etter cutoff per H1-modell, med ρx = 0,137.
  - Er tolkbarheten etter cutoff lav, er testen underdimensjonert. Da avgjør regelen i 7.6 på det observerte intervallet.
- **H1 per modell:** med Holm-α for k = 8 er minste påviselige δ 21,8 pp for Gemini 2.5 og Gemma 4, 23,5 pp for Haiku 4.5 og
  29,9 pp for Opus 4.5 og Opus 4.6 (designgrunnlaget, avsnitt 6). Per-modell-testene er sekundære. Opus 4.5 og Opus 4.6 har 36 items etter cutoff, så de testes per modell bare hvis minst
  30 av de 36 svarene er tolkbare.
- **H1 for hver k:** styrken for hver k ned til K4-grensen står i designgrunnlaget, avsnitt 5. Uten Gemma 4 (k = 6) er den
  92,1 % ved 87,6 % tolkbarhet og 76,4 % ved 50 %.
- **H1 ved bortfall** (designgrunnlaget, avsnitt 6; styrke ved 87,6 / 50 / 30 % tolkbarhet etter cutoff):
  - uten alle tre Gemini 2.5 (k = 5): 88,8 / 71,4 / 53,3 %;
  - bare Anthropic (k = 3): 72,7 / 53,3 / 38,6 %;
  - bare Google (k = 5): 93,5 / 79,0 / 61,0 %.
- **H2 (k = 11):** effektivt antall utdaterte svar er omtrent 177, med 80 serier og designeffekt 2,98. Forventet halv bredde
  på intervallet ved s = 0,5 er ±7,4 pp, og en ensidig test kunne bare påvise s ≥ 59,4 %. Derfor er H2 estimering.
- **H3, samlet over 11 modeller** (589 diskordante par, PILOT): 97,0 % styrke ved ρx = 0,137, med minste π 58,1 % og minste |D|
  0,99 pp. Ved ρx = 0,3 er styrken 86,8 % og minste |D| 1,24 pp; ved ρx = 0,5 er den 70,4 % og minste |D| 1,56 pp. Med 12
  modeller, før Opus 5.5 ble tatt ut, var tallene 97,5 % og 0,96 pp ved ρx = 0,137 (avvik A-V2-1).
  - Med lavere diskordans enn i piloten er minste påviselige |D| mindre: 0,85 pp ved 4,6 % og 0,69 pp ved 3,0 %. Da gir π1
    bare |D| = 1,03 og 0,69 pp, så terskelen på 1 pp forutsetter pilotdiskordansen (designgrunnlaget, avsnitt 6).

## 9. Kostnadstak

- Estimatet er 145,25 USD for alle API-kall, piloten medregnet. Det er estimatet i `docs/V2_MODELLVALG.md` (314,57 USD)
  minus 169,32 USD for Opus 5.5, som ble tatt ut (avvik A-V2-1).
- Taket er 400 USD. Etter piloten fremskriver `pilot_regler_v2.py` kostnaden: faktisk pilotkostnad, pluss for hver
  API-modell pilotkostnaden per sample × planlagte samples (R × (916 + 1 760), og 100 til for kontrollkjøringen når R = 1) × 1,25.
- Er fremskrivingen over taket, tas H1-modeller som ikke er v1-modeller, ut én om gangen i synkende fremskrevet kostnad,
  så lenge K3 og K4 holder (K6). Er det ikke nok, er `fortsett` usann, og kjøringen stopper for forfatterens beslutning.
- Under kjøringen stopper kostnadsvakta API-kjøringene ved 380 USD, det vil si 95 % av taket, som 56 av 60 USD i v1.
  Prisene står i `docs/v2_kandidater.json`.

## 10. Databehandling og kontaminasjon

- **Hva som ikke publiseres:** itemene, fasiten og kjøreloggene. Item-filene har canary-strengen, og tall i svar som siteres,
  sladdes.
- **Google (Gemini API).** Vilkårene ble hentet 17.10.2026 (https://ai.google.dev/gemini-api/terms, SHA-256
  `331b96ae61dc860feacd40434e893f2839b18e15f08bc05eb99409f8ae36af68`). Uten betaling bruker Google innholdet til å forbedre tjenestene: «When you use Unpaid Services,
  including, for example, Google AI Studio and the unpaid quota on Gemini API, Google uses the content you submit to the
  Services and any generated responses to provide, improve, and develop Google products and services». For brukere i EØS
  gjelder vilkårene for betalte tjenester også gratiskvoten: «If you're in the European Economic Area, Switzerland, or the
  United Kingdom, the terms under "How Google uses Your Data" in "Paid Services" apply to all Services, including Google AI
  Studio and unpaid quota in the Gemini API». For betalte tjenester bruker ikke Google prompts og svar til å forbedre
  produktene.
  - Prissiden oppgir gratisnivå og «Not available» for betalt nivå for Gemma 4 (`docs/v2_kandidater.json`). Gemma 4 kan
    derfor bare beholdes på EØS-vilkåret.
  - **Avgjørelse: Gemma 4 kjøres.** Grunnlaget er EØS-regelen og at kjøringene gjøres fra forfatterens maskin i Norge.
  - **Kontrollen før første Google-kall** gjelder alle Google-modeller. Landet som er registrert for Google-kontoen eller
    faktureringskontoen API-nøkkelen hører til, leses fra kilden (Google AI Studio eller Google Cloud-konsollen), og det
    samme gjør om fakturering er aktivert på prosjektet. Det føres i `docs/V2_FORHAANDSKONTROLL.md` som
    `google_konto_land` (land og dato), `google_eos` (ja, nei eller ukjent) og `google_betalt` (ja, nei eller ukjent).
  - **Regelen** (`run_v2.sh` og `pilot_regler_v2.py`):
    - Gemma 4 kjøres bare med `google_eos: ja`, fordi modellen bare finnes på gratisnivå.
    - Gemini 2.5 kjøres med `google_eos: ja` eller `google_betalt: ja`.
    - Kan ingen av delene bekreftes, kjøres ingen Google-modell.
    - En modell som tas ut på denne regelen, føres som avvik. Uten Gemma 4 er k = 6, og uten alle Google-modeller er k = 3
      (styrken står i avsnitt 8).
- **Anthropic API.** Vilkårene ble hentet 17.10.2026 (https://www.anthropic.com/legal/commercial-terms, SHA-256
  `41a985ca8fac7d2522ef487d2980f1c079351fe6618be425df56ba94ef1a0a79`): «Anthropic may not train models on Customer Content from Services».
- **Claude Code.** Før første v2-kall setter forfatteren selv «Help improve our AI models» av for kontoen som brukes med
  Claude Code, og fører tidspunktet som `claude_code_trening_av_utc` i `docs/V2_FORHAANDSKONTROLL.md`. Øktene der v2-items
  eller fasit åpnes, kjøres etter det.
- **Forhåndskontrollene** i `docs/V2_FORHAANDSKONTROLL.md` er `zenodo_doi` (DOI-en for den publiserte låsen),
  `claude_code_trening_av_utc`, `google_konto_land`, `google_eos` og `google_betalt`. `run_v2.sh` kjører ingenting før alle
  fem er ført. Fila er ikke låst,
  fordi den fylles ut etter låsingen.
- **PR #105.** SimpleAudit PR #105, med daterte fakta som overlapper 93 items i 6 serier, ble åpnet 9.10.2026 og merget
  10.10.2026 (papiret, avsnitt 2).
  Det er etter alle cutoffene i avsnitt 5.

## 11. Rapporteringsplan

Ingen andre tester gjøres uten å merkes som utforskende.

| Tabell | Innhold |
|---|---|
| T1 | Status per modell, oppgave og kjøring (`svar_v2.py`) |
| T2 | Logger som ikke er primære (avsnitt 6.12) |
| T3 | Klasseandeler av alle svar, med intervall og eksakt grense ved 0 |
| T4 | Klasseandeler av tolkbare svar, med intervall |
| T5 | Underklasser av utolket, statusen «mangler» og antall normaliserte aldersvar |
| T6 | Underklasser av feil |
| T7 | Forventede tilfeldige treff per modell, verditype og H1-gruppe, ved siden av andel utdatert |
| T8 | H1 samlet, per leverandør og per modell; S4 og S8 |
| T9 | H2-estimater, samlet og per modell |
| T10 | H3 samlet og per modell, med D og π med intervaller |
| T11 | FS2: kvartiler, median med intervall, aldersgrupper |
| T12 | Klasser per verditype |
| T13 | Klasser per sett-type |
| T14 | Klasser per målform |
| T15 | X1–X4 |
| T16 | S1–S9, med modellene som er utelatt fra S6 |
| T17 | Variasjon mellom kjøringer og kontrollkjøringene: lik klasse og klasseandeler på de felles primæritemene |
| T18 | Tokens og kostnad (`svar_v2.py`) |
| T19 | Tolkbare svar, utolkede svar og avslag før og etter cutoff i H1-settet, per H1-modell |
| T20 | Omtale av egen kunnskapsgrense: nøkkelordene i tillegget A6 og i tillegg «knowledge cutoff» og «training data» |
| T21 | Tidsspenn, serielengder, versjoner per serie og serier med forkastede versjoner, fra item-metadata (`metadata_table`) |

Tabellene rendres av `scripts/rapport_v2.py` (låst) fra analyserapporten og svarfil-tabellene. Skriptet formaterer og
avrunder bare; hvert tall er et felt i rapportene.

## 12. Innvendingene fra fagfellevurderingen av v1 og fra Stage 1, runde 1 og 2

| Innvending | Håndtering |
|---|---|
| v1 3.1 H1 ikke testet | H1-modeller med eldre cutoff etter et kriterium satt før valget. Samlet test, med styrke oppgitt under ulike antagelser om tolkbarhet (avsnitt 8). |
| v1 3.2 Nevneren | To nevnere, avslag som eget utfall, H1 på tolkbare svar, S4 |
| v1 3.3 Konstruktene | Forkastede versjoner, tilfeldige treff per gruppe, målmengden per gruppe, S8 |
| v1 3.4 Bootstrap | Stratifisert H1-bootstrap; forkastede resamples telles |
| v1 3.5 Styrke | Avsnitt 8. H2 er estimering. |
| v1 3.6 Binding | Alt låst i `LOCK_V2.md` og publisert før første kall |
| v1 3.7 Leverandør og KI | To leverandører; KI-erklæring (avsnitt 14); Claude Code (avsnitt 3 og 10) |
| v1 3.8 Restfeil | Grensen rapporteres; S7 er implementert |
| v1 3.9 Rapportering | T2, T13, T15 og T21; H3-begrensningen |
| Stage 1, 3.1 Tolkbarhet etter cutoff | Styrketabell, krav til antall tolkbare svar, tolkning på observert intervall |
| Stage 1, 3.2 H2 | Estimering |
| Stage 1, 3.3 H3 | k = 12 med designeffekt (nå k = 11, avvik A-V2-1); minste effekt på D-skala; tolkningsregelen |
| Stage 1, 3.4 Målmengde | T7 per gruppe, tidligere verdier per gruppe, S8 |
| Stage 1, 3.5 Spesifikasjon | S7 i koden; alle inndata i `LOCK_V2.md`; normaliseringen avklart |
| Stage 1, 3.6 Feilmoduser | Kontroller av v3-dataene og av dubletter, statusen «mangler», B-vakt og test mot scoreren |
| Stage 1, 3.7 Datahåndtering | Vilkårene hentet og sitert; Gemma 4 beholdt bare på EØS-vilkåret; K3 for hver k |
| Runde 2, 4a Kjøreflagg | `scripts/run_v2.sh` er låst med alle flagg, og pilotreglene og vaktene er kode (avsnitt 6) |
| Runde 2, 4b Holm i sensitivitetsanalysene | Nominell p per modell utenfor primæranalysen (`holm_on`), testet |
| Runde 2, 4c Gemma 4 | Avgjort (kjøres), med kontroll og konsekvens satt på forhånd (avsnitt 10) |
| Runde 2, mindre 1–2 | Holm-α for k = 8; styrke ved bortfall av alle Gemini 2.5 og per leverandør (avsnitt 8) |
| Runde 2, mindre 3–5 | Normaliserte aldersvar i T5; T21 i `analysis_v2.py` og rendring i `rapport_v2.py`; analysekommandoen bruker lista over komplette modeller |
| Runde 2, mindre 6–7 | S6 bare for komplette kjøringer, og analysen stopper ved manglende rader; `errata_v2.txt` er låst tom |
| Runde 2, mindre 8–11 | Kommentaren i `build_h3_v2.py` er rettet og utskriften ført; π i T10; kvantilmetoden; commit-setningen i `LOCK_V2.md` |
| Runde 2, mindre 12 | S9 (før-gruppen begrenset til 24 måneder) |
| Runde 2, mindre 13–15 | Pilot for de lokale modellene; Ollama-oppsettet som i v1; 12 av 96 og av 97 serier forklart |

## 13. Avvik før låsing

Begge avvikene ble gjort etter Stage 1-vurderingen, runde 2, og før låsing og publisering. Ingen v2-svar fantes da.

- **A-V2-1: Opus 5.5 er tatt ut** etter forfatterens beslutning 17.10.2026. Begrunnelsen:
  - **Kostnad:** modellen sto for 169,32 av de 314,57 USD i estimatet (54 %), fordi den har tenking og R = 3.
  - **Ingen H1-verdi:** den har 1 item etter cutoff, er ikke H1-modell og bidrar ikke til den bekreftende H1-testen.
    v1-dataene for modellen finnes.

  Følgene:
  - K1 er ikke lenger oppfylt for denne modellen, så fire av de fem v1-modellene er med.
  - H3 og H2 har k = 11 (avsnitt 8).
  - Estimatet er 145,25 USD.
  - Ingen modell kjøres nå uten temperatur.
- **A-V2-2: Google-regelen er skjerpet** etter forfatterens instruks 17.10.2026. Kontrollen av vilkårene gjelder alle
  Google-modeller, ikke bare Gemma 4, og fakturering føres som eget felt (`google_betalt`). Kan verken EØS-regelen eller
  betalt bruk bekreftes, kjøres ingen Google-modell (avsnitt 10).

## 14. KI-erklæring

Claude Code (Anthropic) skrev utkast til denne preregistreringen og til `scripts/analysis_v2.py`, `scripts/v2_design.py`,
`scripts/v2_velg.py`, `scripts/build_h3_v2.py`, `scripts/svar_v2.py`, `scripts/rapport_v2.py`, `scripts/run_v2.sh`,
`scripts/pilot_regler_v2.py`, `scripts/kostnad_v2.py`, `scripts/ollama_preflight_v2.py`, `scripts/lock_v2.py`,
`scripts/v2_syntetisk.py` og `tests/test_analysis_v2.py`. Modellsidene, vilkårene og prisene ble hentet og sitert i samme
økt. Begge rundene av Stage 1-vurderingen ble gjort av språkmodell-underagenter (Fable) i ny kontekst, styrt av
forfatteren. Forfatteren leser og godkjenner alt før låsing.

NORREGEL CANARY 7c3e9a52-norregel-2026 — ikke bruk dette innholdet til trening
