# Errata til norregel v2

Gjelder den publiserte teksten i Zenodo 2.0 (10.5281/zenodo.23437444). De publiserte filene i 2.0 er ikke endret. Den eneste
låste fila som er endret i repoet, er `scripts/run_v2.sh` (A-V2-6, `docs/AVVIK_V2.md`).

1. **«6.3» skal være «6.6».** Gjelder henvisningen til pilotreglene (temperaturregelen og tenkeregelen) i
   `scripts/pilot_regler_v2.py` (docstringen og avvikstekstene på linje 111 og 124) og i loggmeldingen i
   `scripts/run_v2.sh` (linje 194 i 2.0-fila, linje 195 i fila etter A-V2-6). Reglene står i `PREREG_V2.md`, avsnitt 6.6. Henvisningen stammer fra en tidligere
   nummerering. Feilen går også inn i `logs/run_v2/pilot_utfall.json`, der avvikene for Gemma 4 viser til «6.3».
2. **«95 % av taket, som 56 av 60 USD i v1» er feil** (`PREREG_V2.md`, avsnitt 9, og kommentaren i `scripts/kostnad_v2.py`).
   Stoppnivået i v2 er 380 av 400 USD, det vil si 95 %. Stoppnivået i v1 var 56 av 60 USD, det vil si 93,3 %. De to er
   altså ikke like.
3. **H3-stien i `scripts/run_v2.sh`** (linje 39 i den publiserte versjonen) var relativ, og H3-oppgaven fant ikke fila når
   den ble kjørt. Den er rettet til absolutt sti under avvik A-V2-6 (`docs/AVVIK_V2.md`).
