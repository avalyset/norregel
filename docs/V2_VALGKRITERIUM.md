# Modellvalgkriterium for norregel v2

Skrevet 17.10.2026, før noen modell er valgt. Kriteriet committes før `scripts/v2_velg.py` kjøres, og valget logges i
`docs/V2_MODELLVALG.md`. Inndata er `docs/v2_kandidater.json` (modellene nøklene kunne kalle 17.10.2026, med cutoff,
status og tenkestandard fra leverandørenes egne sider) og `docs/V2_DESIGNGRUNNLAG.md` (H1-grupper fra item-metadata,
pilotparametre fra v1, styrke a priori og kostnadsestimat).

**K1. Kontinuitet.** De fem v1-modellene tas med, med de samme Inspect-id-ene og, for de lokale modellene, de samme
Modelfilene som i v1: `anthropic/claude-haiku-4-5-20251001`, `anthropic/claude-sonnet-4-6`, `anthropic/claude-opus-5-5`,
`ollama/nb-llama-3.1-8b-instruct-cardtmpl:latest` og `ollama/normistral-7b-warm-instruct-cardtmpl:latest`.

**K2. H1-modell.** En kandidat er H1-modell når alle disse holder:
- a) leverandørens egen side (modellside eller modellkort) oppgir en kunnskaps- eller treningsdatacutoff med måned og år;
  datoen er siste dag i måneden, som i v1;
- b) id-en er fast (ikke et alias som `*-latest`), og leverandørens modell-API listet den for nøkkelen 17.10.2026;
- c) statusen på leverandørens side er verken «Deprecated» eller «Preview»;
- d) H1-settet har minst 30 items fra minst 20 serier etter cutoff, og minst 30 items fra minst 5 serier før.

**K3. Styrke.** Den samlede H1-testen over H1-modellene skal ha minst 80 % styrke for δ = 10 prosentpoeng ved ensidig
α = 0,05. Styrken regnes som i designgrunnlaget, avsnitt 3, med k = antall H1-modeller og gjennomsnittlige gruppestørrelser
for disse modellene. Holder ikke K3, er H1 ikke testbar i v2, og det skal stå i preregistreringen.

**K4. Leverandører.** H1-modellene skal komme fra minst to leverandører når det finnes nøkler for minst to. Holder ikke
K4, er valget ugyldig og stopper.

**K5. Ingen andre modeller.** En modell som verken er v1-modell (K1) eller H1-modell (K2), tas ikke med.

**K6. Kostnad.** Antall kjøringer per modell er R = 3 for en modell som kjøres med tenking som standard eller uten
temperatur 0, og ellers R = 1 pluss en kontrollkjøring på 100 faste items. Fremskrevet kostnad for API-kallene (designgrunnlaget,
avsnitt 4, med R per modell og kontrollkjøringene) skal være under taket på 400 USD, piloten medregnet. Er den over, tas
H1-modeller som ikke er v1-modeller, ut én om gangen i synkende kostnadsrekkefølge, så lenge K3 og K4 fortsatt holder. Er
kostnaden fortsatt over taket, stopper valget for forfatterens beslutning.

**K7. Rekkefølge.** Modellene listes etter leverandør (alfabetisk), så cutoff (eldst først), så id (alfabetisk). Ingen
andre valg gjøres ved skjønn.
