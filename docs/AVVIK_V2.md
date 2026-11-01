# Avvik i norregel v2

Den låste preregistreringen er `docs/PREREG_V2.md` (Zenodo 2.0, 10.5281/zenodo.23437444, låsen i commit `ef205af`).
Avvik A-V2-1 og A-V2-2 ble gjort før låsing og står i `PREREG_V2.md`, avsnitt 13. Avvikene etter låsing står bare her og
i `docs/V2_KJORELOGG.md`.

`PREREG_V2.md` og de andre låste filene er ikke endret, med ett unntak: `scripts/run_v2.sh` ble endret under A-V2-6, og
låsen ble laget på nytt i commit `d68ce0d` (`docs/LOCK_V2.md`, linje 17). Ellers ville en endring brutt låsen
(`scripts/lock_v2.py --check`), og da kjører `scripts/run_v2.sh` ingenting.

- **A-V2-1 (før låsing):** Opus 5.5 er tatt ut (kostnad, ingen H1-verdi). Se `PREREG_V2.md`, avsnitt 13.
- **A-V2-2 (før låsing):** Google-regelen er skjerpet til alle Google-modeller. Se `PREREG_V2.md`, avsnitt 10 og 13.
- **A-V2-3 (etter piloten, før første hovedkall, 17.10.2026, commit `58db758`):** Gemini 2.5 Pro og Gemini 2.5 Flash-Lite
  falt bort etter regelen i `PREREG_V2.md`, avsnitt 5 (linje 133): en modell som ikke kan fullføres, er ute av alle
  analyser.
  - **Grunnlag:** i piloten endte 20 av 20 samples for begge modellene i feilen «This model … is no longer available to
    new users» (`docs/V2_KJORELOGG.md`, pilottabellen).
  - **Gjennomføring:** hovedkjøringen brukte `scripts/run_v2.sh` med modellene oppgitt eksplisitt. Etter A-V2-5 var det
    åtte modeller, startet med `api` (fire Anthropic, deretter to Gemma 4) og `lokal` (to). Selve skriptet ble endret under
    A-V2-6. De to modellene har ingen hovedlogger. `scripts/svar_v2.py` fører dem i T1 som ikke komplette, uten forsøk, og
    holder dem utenfor analysen.
  - **H1-modellene som var igjen:** seks, fra to leverandører: Haiku 4.5, Opus 4.5, Opus 4.6, Gemini 2.5 Flash, Gemma 4
    26B og Gemma 4 31B.
  - **Styrke:** K3 for de seks var 92,1 % ved 87,6 % tolkbarhet etter cutoff (`pilot_regler_v2.k3`, med de låste formlene
    og PILOT-parametrene).
- **A-V2-4 (samme tidspunkt, commit `58db758`):** den låste definisjonen av «komplett» dekket ikke en logg med status
  `success` der alle samples er feil.
  - Etter definisjonen (v1-protokollen 3.4, `svar_v2.py`) ville en slik kjøring telle som komplett, med bare endelige
    feil. **En slik kjøring regnes som bortfall, ikke som komplett.**
  - Definisjonen er ikke endret ellers. En kjøring med noen endelige feil, men ikke bare feil, er fortsatt komplett.
  - **Regelen ble ikke utløst i hovedkjøringen.** Ingen komplett kjøring består av bare feil. Det høyeste antallet
    endelige feil er 4 av 1 760 (NorMistral, H3; `docs/V2_KJORELOGG.md`, tabellen over hovedkjøringen).
- **A-V2-5 (17.10.2026, forfatterens beslutning, commit `aaf9952`, 14:49:09 UTC):** Gemini 2.5 Flash falt bort.
  - **Tidspunkt:** avviket ble ført før første Google-kall i hovedkjøringen. Gemma 4 26B k1 startet 15:09:20 UTC
    (`docs/V2_KJORELOGG.md`). Anthropic-kallene pågikk da.
  - **Grunn:** gratiskvoten er 20 kall per døgn mot 8 028 kall som trengs (R = 3). Ingen enkeltkjøring kan fullføres innen
    ett døgn (`docs/V2_KJORELOGG.md`, Google-kvoten).
  - **Modellen har ingen hovedlogger.** `scripts/svar_v2.py` fører den i T1 som ikke komplett og holder den utenfor
    analysen, som under A-V2-3.
  - **H1-modellene som var igjen:** fem, fra to leverandører: Haiku 4.5, Opus 4.5, Opus 4.6, Gemma 4 26B og Gemma 4 31B.
  - **Styrke:** K3 for de fem var 88,8 % ved 87,6 % tolkbarhet etter cutoff og 71,4 % ved 50 % (`pilot_regler_v2.k3` og
    `v2_design.h1_power`, med de låste formlene og PILOT-parametrene). Det er samme modellsett og samme tall som scenarioet
    «uten alle tre Gemini 2.5» i `V2_DESIGNGRUNNLAG.md`, avsnitt 6.
  - Gemma 4 ble kjørt på gratisnivået over flere døgn (`docs/V2_KJORELOGG.md`).
- **A-V2-6 (17.10.2026, forfatterens beslutning, commit `d68ce0d`):** H3-stien i `scripts/run_v2.sh` ble rettet.
  - **Feilen:** den låste versjonen sendte en relativ sti (`-T items=data/items_h3_v2.jsonl`, linje 39 i 2.0-fila), og
    Inspect fant ikke fila når oppgaven ble kjørt (`FileNotFoundError`). Feilen kom før noe sample ble sendt, så det ble
    ikke gjort noe kall og ikke skrevet noen logg.
  - **Hvem den rammet:** H3 i kjøring 1 for de fire Anthropic-modellene (14:48–15:08 UTC). H3-forsøkene i løkkene for
    Gemma 4 og de lokale modellene feilet på samme måte, fordi de kjørende prosessene hadde lest den gamle versjonen.
  - **Rettingen:** stien ble absolutt (`-T "items=$PWD/data/items_h3_v2.jsonl"`). I tillegg ble bryteren `ONLY_H3=1` lagt
    til. Med den kjører `api` og `lokal` bare H3 for k1..kR, uten hovedoppgave og kontrollkjøring.
  - **Uendret:** flagg, modeller, seed, datasett og alt annet. Det viser diffen i `d68ce0d`.
  - **Test:** rettingen ble prøvd med Inspects testmodell `mockllm` (ingen leverandørkall). Den ga status `success`,
    datasettet `items_h3_v2` og 1 760 samples.
  - **Gjennomføring:** H3 ble kjørt med `ONLY_H3=1`, for de lokale modellene etter lokalkøen og for API-modellene etter
    API-køen (tidene står under A-V2-7).
  - **Låsen** ble laget på nytt (`docs/LOCK_V2.md`):
    - `run_v2.sh` i låsen fra 2.0 (`ef205af`) har SHA-256 `a3d1a8787d1cb156…`;
    - `run_v2.sh` i låsen fra `d68ce0d` har SHA-256 `10583cc721375666…`.

    Ingen annen fil i låsen er endret.
  - **I Zenodo 2.1** heter de rettede filene `run_v2_A-V2-6.sh` og `LOCK_V2_A-V2-6.md`. Filene `run_v2.sh` og `LOCK_V2.md` i
    posten er de opprinnelige fra 2.0.
- **A-V2-7 (H3 under en lås som ikke var publisert; ført 20.10.2026, commit `e0883f3`):** `PREREG_V2.md` (linje 10) krever at låsen publiseres før første
  v2-kall. Låsen fra `d68ce0d` ble ikke publisert før H3-kjøringene, som gikk under den:
  - **lokalt:** 17.10.2026 22:43:30 – 18.10.2026 11:35:52 UTC;
  - **API:** 18.10.2026 15:57:25 – 20.10.2026 13:08:34 UTC.

  Tidene står i T1 (`docs/V2_KJORELOGG.md`, tabellen over hovedkjøringen). Den eneste forskjellen fra den publiserte låsen
  er `run_v2.sh` (A-V2-6). Den nye låsen publiseres i Zenodo 2.1.
- **A-V2-8 (pilotloggene står ikke i T2; ført 20.10.2026, commit `e0883f3`):** `PREREG_V2.md`, avsnitt 6.12 (linje 208), sier at hver logg som ikke er primær,
  står i T2.
  - Det låste `scripts/svar_v2.py` leser bare `logs/run_v2/<modell>/k<r>/` (linje 3 og 90), ikke pilotmappa
    `logs/run_v2/_pilot/`.
  - De 11 pilotloggene står derfor ikke i T2. De står med tider og feiltall i `docs/V2_KJORELOGG.md`, pilottabellen.
  - T2 er tom fordi det ikke finnes noen ikke-primær logg i hovedmappene.
- **A-V2-9 (utløst pilotregel; utløst 17.10.2026, ført her 20.10.2026):** tenkeregelen ble utløst for Gemma 4 26B og
  Gemma 4 31B.
  - **Regelen:** `PREREG_V2.md`, linje 177: en Gemma 4-modell som teller tenketokens i den komplette pilotloggen, får R = 3.
  - **Utfallet:** de to modellene talte 170 567 og 26 924 tenketokens og fikk R = 3. Kilden er
    `logs/run_v2/pilot_utfall.json`, feltene `reasoning_tokens` og `avvik`, og pilottabellen i `docs/V2_KJORELOGG.md`.
  - **Hvorfor det står her:** `PREREG_V2.md`, linje 181, sier at utløste regler føres som avvik.
