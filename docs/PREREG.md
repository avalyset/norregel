# PREREGISTRERING

> Låst lokalt 16.10.2026 (fjerde lokale lås, endelig etter renhetsregel v3.6 punkt 3),
> ikke publisert. Sjekksummer står i `LOCK_MANIFEST.md`. Første til tredje lokale lås
> (aa9287f, c0ce4aa og d48cb2e) ble åpnet. Se «Endringer før låsing». Feil som blir funnet
> etter denne låsen, føres i `docs/ERRATA.md`.
> Status 16.10.2026: settet er bygget mekanisk (`data/items.jsonl`, 916 items, og
> `data/items_h3.jsonl`, 400 spørsmål). Ingen modell er kjørt mot benchmarken. Den blinde
> krysskontrollen brukte en underagent til å hente verdier fra kildefilene, ikke til å
> svare på items.

## Forskningsspørsmål

**FS1.** Hvor ofte oppgir språkmodeller gjeldende verdi, en utdatert verdi og en verdi
som aldri har gjeldt, når de blir spurt om tallverdier i norske lover og forskrifter?

**FS2.** Når en modell oppgir en utdatert verdi, hvor gammel er den målt i år?

**FS3.** Er det forskjell mellom bokmål og nynorsk, og mellom verditypene? I v1 er det
kronebeløp, prosentsatser, G og alder. Frister og hjemmel er ikke med i v1.

## Hypoteser

- **H1:** For bestemmelser som er endret etter modellens oppgitte kunnskapsgrense,
  er andelen utdatert(år) høyere enn for bestemmelser som ikke er endret etter grensen.
- **H2:** Blant de utdaterte svarene er det oftest den nest siste verdien modellene
  oppgir, ikke eldre verdier.
- **H3:** Andelen korrekt er lavere på nynorsk enn på bokmål for samme item. Testes
  bare på items som finnes i begge målformer (H3-delutvalget).
- **H4:** Andelen korrekt er lavere for beløp/sats enn for frist. Testes først når
  frister er med (v2).

## Byggeregler

1. Kandidater trekkes ut mekanisk med `scripts/extract.py` fra Lovdatas åpne data
   (NLOD 2.0). Sjekksum for inndatafilene føres i `LOCK_MANIFEST.md`.
2. Bare rene kandidater er med, etter renhetsregel v3 (`docs/RENHETSREGEL_V3.md`, commit
   cf7ca88, rettet i 98378e6). Anomaliflaggene er revisjonsspor. I en flagget serie godtas
   et år bare når verdien og satsens navn eller ankerfrase står i samme setningsledd i
   årets ordrette tekst. Ellers deles serien der. Siste verdi må være lik gjeldende
   konsoliderte tekst. Regelen er endret før noen modell er kjørt. Tillegg v3.1, v3.2 og
   v3.3 (commit 90869f7, 87b5499 og 0ecf0e5): kvalifikatorer i samme setningsledd som
   verdien hører til seriens identitet. Det er eksakte fraser med ordgrenser: «statens
   andel», «kommunal skatt»/«kommuneskatt», «fylkeskommunal», «for personer», «for
   selskaper», «i tiltakssonen» og «felleskommunale skattefondet». Et år med andre
   kvalifikatorer flyttes ut til en egen serie. Tillegg v3.4, v3.5 og v3.6 (commit
   8a45852, b18d90d, 3750793 og e707b80) fastsetter datohierarkiet. Gyldig fra og gyldig
   til er (1) en eksplisitt periode eller dato i selve teksten: i leddet; for paragrafen
   («Endringen i § X … gis virkning fra D»); satsperioden for dokumentet («Satsene …
   gjelder for perioden …» eller «For (inntekts)året ÅÅÅÅ svares …»); starten for en del
   av et endringsvedtak; eller starten for hele dokumentet. Deretter (2) «med virkning
   fra» og (3) ikrafttredelsesdatoen. En endring i
   et dokument med satsperiode arver perioden. En senere versjon med samme dato erstatter
   den tidligere. Et år uten kildefestet dato forkastes og deler serien.
   - 2a. **Primærsett** er kjernen: dokumentene i `docs/KJERNE_LISTE.md`, fastsatt før
     tellingen (commit ef1d98e). Langhalen er sekundærsett. Den telles, men bygges ikke
     som items i v1.
   - 2b. **v1 inneholder beløp/sats (kroner, prosent, G) og alder.** Frister er parkert
     til v2. 21 rene frist-år-items i kjernen er derfor ikke med i `data/items.jsonl`.
     Årsserier (G, utdanningsstøtte og tilbakebetaling per år) kjedes etter faste
     tittelmønstre og tas med når de er rene.
   - 2c. Skattevedtaket og trygdeavgiftsvedtaket kjedes som navngitte satser etter lista i
     `docs/NAVNGITTE_SATSER.md` (commit 9a7c74f, fastsatt før uttrekket). Navneendringer,
     som toppskatt til trinnskatt, står i lista. En §/ledd-kjede i et årsvedtak der minst
     halvparten av år-itemene er de samme som i én navngitt sats (samme dato og verdi), er
     en dublett og tas ut. Det gjelder 4 kjeder med 33 år-items.
   - 2d. Uttrekket er kontrollert blindt: 40 godtatte år-items per runde er hentet ut på
     nytt av en uavhengig agent uten tilgang til våre verdier. Det ga 39/40 i runde 1 (en
     feil hos oss, rettet), 40/40 i runde 2, 40/40 i runde 3 etter v3.1, 40/40 i runde 4
     etter v3.2 og 40/40 i runde 5 etter v3.3 (`docs/KRYSSKONTROLL_V3.md`). Rundene ble
     kjørt på dataene før alder-rettelsen (commit 704da36). Rettelsen endret typen for
     aldersgrenser, og dermed hvilke serier som er rene (se `docs/SPEC.md`). Sluttkontrollen
     på hver lokale lås står i `docs/KRYSSKONTROLL_V3.md`. På første lås (aa9287f, seed
     20261021) stemte 40/40 verdier, men kontrollen viste datofeilen under «Endringer før
     låsing». På andre lås (c0ce4aa, seed 20261022) stemte 40/40 verdier og 40/40
     virkningsdatoer, men kontrollen viste at satsperioden i § 1-2 ikke var brukt. På tredje
     lås (d48cb2e, seed 20261023) stemte 40/40 verdier, men gyldig fra og gyldig til bare
     39/40. På fjerde lås kontrolleres verdi, gyldig fra, gyldig til og
     periodebestemmelse. Lås 4 er endelig (v3.6 punkt 3).
   - 2e. **Enheten er år-itemet:** ett spørsmål per bestemmelse per gyldighetsår. Serien
     er bare grupperingen. Analyse og intervaller regnes på år-items, med serien som klynge.
3. Kandidater som overlapper de daterte faktaene i SimpleAudit #105 tas med, merket
   `overlaps_simpleaudit_105` (93 items i 6 serier). #105 omtales som tidligere arbeid.
4. Hvert item er skrevet som ett atomært spørsmål med én fasitverdi før noen modell er
   kjørt, fra faste maler (`docs/MALER.md`) og uten modell. Ingen manuell kuratering er
   gjort (16.10.2026). En eventuell kuratering kan bare forkaste items, ikke endre verdi
   eller kildetekst, og må gjøres før låsing.
5. **Hovedsettet** er hele primærsettet i v1, uten trekning. Målform fordeles med fast
   seed (20261016) per serie, slik at bokmål og nynorsk er balansert innen hver serie
   (høyst 1 i forskjell). Minst 25 % skal være på nynorsk, og andelen er 454 av 916
   (49,6 %).
6. Settet fryses med sha256 (`LOCK_MANIFEST.md`) og canary-strengen i hvert item før
   første kjøring.

## Analyseplan

- **Klasser:** korrekt / utdatert(år) / feil / utolket per modell, beregnet på de 916
  itemene i `data/items.jsonl`, med 95 % konfidensintervall.
- **Klyngebootstrap (godkjent av Eirik 16.10.2026):** intervallene trekker hele serier
  med tilbakelegging, og alle år-items i en trukket serie følger med.
- **FS2:** fordeling av alder (år mellom `gyldig_fra` for oppgitt verdi og for itemets
  verdi) blant utdaterte svar. Scoreren rapporterer alle år der den oppgitte verdien har
  gjeldt.
- **H1:** sammenlign andel utdatert mellom items med siste endring før og etter modellens
  oppgitte kunnskapsgrense. Grensen tas fra leverandørens dokumentasjon og føres før
  kjøring.
- **H3 (bestemt av Eirik 16.10.2026):** testes på et eget delutvalg. Det er 200 items
  fra hovedsettet, trukket med fast seed (20261017, godkjent av Eirik 16.10.2026) og
  stratifisert på serie og dermed på type. Hver av de 97 seriene får minst ett item, og
  de øvrige 103 fordeles etter seriens størrelse (største rest). Hvert item stilles på
  både bokmål og nynorsk, med samme mal og samme fasit (`data/items_h3.jsonl`, 400
  spørsmål i 200 par). Fordelingen etter type er 137 kronebeløp, 59 prosentsatser, 3
  aldersgrenser og 1 G-multippel. Testen er parvis per modell: McNemar på korrekt mot
  ikke korrekt. Konfidensintervallet for forskjellen i andel korrekt (nynorsk minus
  bokmål) beregnes med klyngebootstrap på serie.
- **H3, egen kjøring (godkjent av Eirik 16.10.2026):** delutvalget kjøres for seg
  (oppgaven `norregel_h3`). Svar fra hovedkjøringen gjenbrukes ikke. Hver språkversjon er
  et eget Inspect-sample, med egen samtale og ingen delt kontekst. Rekkefølgen på
  samples stokkes med fast seed (20261017).
- **Hovedmålene** beregnes bare på de 916 enkeltspråklige itemene. I hvert H3-par er den
  ene versjonen identisk med itemet i hovedsettet, og den andre er merket
  `ekstra_språkversjon`. Ingen av H3-svarene telles inn i hovedmålene.
- **H4:** testes ikke i v1, fordi frister er parkert. I v1 rapporteres andel korrekt per
  verditype: 582 kronebeløp, 324 prosentsatser, 8 aldersgrenser og 2 G-multipler, med
  intervaller. Typer med n < 30 (alder og G) får ingen egen test.
- **Scorer:** deterministisk (`src/norregel/score.py`), validert på 800 syntetiske svar
  (100 items × 8, seed 20261016), med 800/800 riktig klassifisert. Tørrkjøringen med
  mockllm som svarer fasit gir 916/916 korrekt på hovedsettet og 400/400 på H3.
- **Datorevisjon** (`scripts/audit_dates.py`): alle 916 + 400 items har gyldig fra og
  sluttdato lik den høyest prioriterte datoformuleringen i kildedokumentet etter v3.6
  (0 flagg).
- **Invarianter** (`tests/test_invariants.py`): for hvert item ligger datoen i spørsmålet
  i gyldighetsperioden [gyldig_fra, gyldig_til], der gyldig_til er siste dag, og
  innenfor en eksplisitt periode når teksten har en. Fasitverdien er verdien for den
  datoen. Verdihistorikken har verken overlapp eller hull innen en serie, bortsett fra
  perioder etter en eksplisitt sluttdato og perioder som en kvalifikator har flyttet ut.
  Testene er kjørt på alle 916 + 400 items og består.
- **Kjøringer:** temperatur 0, én kjøring per modell og item. Hvis det kjøres gjentak,
  rapporteres variasjonen mellom kjøringer.
- **Prompt:** én fast mal per type og målform (`docs/MALER.md`), låst sammen med settet.

## Endringer før låsing

- **16.10.2026: første lokale lås (aa9287f) ble åpnet.** Sluttkontrollen viste at
  `gyldig_fra` for endringsvedtak med senere virkningsdato («2026-04-24, med virkning fra
  2026-08-01») var satt til ikrafttredelsesdatoen. 24 items spurte derfor om en dato før
  verdien gjaldt. Ingen modell var kjørt. Rettet med renhetsregel v3.4 (commit 8a45852):
  virkningsdato for alle kilder, samme-dato-erstatning overalt, og udaterte undervisningsår
  som delingspunkt. Settet er bygget på nytt med de samme seedene (hovedsett 20261016, H3
  20261017). Etter den ombyggingen hadde det 910 items (før 925) i 97 serier, og 134
  spørsmålsdatoer var flyttet. 14 år-items i to utdanningsstøtteserier (§ 17-1 og § 25-1, 2006–2012) er tatt
  ut, fordi kilden bare oppgir undervisningsåret. I grunnrenteskatten for vannkraft
  erstatter et endringsvedtak med virkning fra og med inntektsåret 2021 satsen for 2021:
  den er nå 47,4 pst., ikke 37 pst. Serien har ett år-item mindre. Alle 24 rammede items
  er rettet. Invarianttestene ble lagt til.
- **16.10.2026: andre lokale lås (c0ce4aa) ble åpnet.** Sluttkontrollen stemte 40/40 på
  verdi og virkningsdato, men viste at årsforskriftene for utdanningsstøtte har en egen
  satsperiode i § 1-2 («Satsene som er fastsatt for undervisningsåret 2013–2014, gjelder
  for perioden 15. august 2013–14. august 2014»), som `gyldig_fra` ikke brukte. Tre items
  spurte om en dato før perioden, så fasit var feil for dem (norregel-00571, -00583 og
  -00612). Ingen modell var kjørt. Rettet med tillegg v3.5 (b18d90d og 3750793):
  eksplisitt periode i teksten først, og endringer som arver satsperioden. Søket etter
  periodeformuleringer over alle 309 kildefiler bak kjernen ga 23 kilder (se
  `docs/SPEC.md`). Settet ble bygget på nytt med de samme seedene. Da hadde det 917 items
  (før 910) i 97 serier. 8 år-items fra 2009–2012 kom tilbake, fordi § 1-2 gir dem en
  kildefestet periode. To versjoner fra 2015 med samme periodestart er slått sammen.
  132 spørsmålsdatoer er flyttet, og 111 gyldig-fra- og 120 gyldig-til-datoer er endret.
- **16.10.2026: tredje lokale lås (d48cb2e) ble åpnet.** Sluttkontrollen stemte 40/40 på
  verdi, men 39/40 på gyldig fra og 39/40 på gyldig til. (1) Forskrift 2022-04-07-555 sier
  «Endringen i § 51 første ledd første punktum gis virkning fra 16. august 2022».
  Datohierarkiet fanget ikke den formen, så itemet norregel-00760 gjaldt én dag
  (2022-08-15). Itemet for § 51 i 2022–2023 hadde 4 803 kr fra forskrift 2022-02-10-282,
  men det beløpet gjaldt aldri: fra 16. august 2022 er det 4 979 kr. (2) «For året 2008
  svares folketrygdavgifter …» var ikke regnet som periode. Ingen modell var kjørt.
  Rettet med tillegg v3.6 (e707b80), sammen med en full mekanisk datorevisjon av alle
  items: 74 flagg før og 0 etter. Settet har nå 916 items (før 917), fordi 4 803-itemet er
  borte. Lås 4 er endelig (v3.6 punkt 3).

## Rapporteres uansett utfall

- Antall items per type, målform og sett (varig, årsserie, G, navngitt), og hvor mange
  som ble forkastet ved en eventuell kuratering, med årsak.
- Alle fire klasser per modell, også når «utdatert» er nær null.
- Andel utolket, og eksempler på svar som ikke lot seg normalisere.
- Kjente begrensninger i uttrekket (se `docs/SPEC.md`).
- Avvik fra denne planen, med dato og begrunnelse.
