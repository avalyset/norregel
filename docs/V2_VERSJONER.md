# Versjoner i kjøremiljøet for v2

Ført 17.10.2026 før piloten (`docs/PREREG_V2.md`, avsnitt 6.11). Fila er ikke låst.

| Pakke | Versjon |
|---|---|
| Python | 3.12.13 |
| inspect_ai | 0.3.245 |
| anthropic | 0.125.0 |
| google-genai | 2.31.0 |
| google-auth | 2.62.0 |
| openai (brukes av Inspect for Ollama) | 2.54.0 |
| numpy | 2.5.4 |
| tenacity | 9.1.4 |
| httpx | 0.28.1 |
| pydantic | 2.14.1 |
| Ollama | 0.35.1 |

- **google-genai** manglet i miljøet og ble installert før piloten. Inspect krever minst 1.69.0, og den nyeste versjonen,
  2.31.0, ble valgt.
- **tenacity:** alle google-genai-versjoner fra 1.69.0 krever tenacity < 9.2.0. Installasjonen byttet derfor tenacity
  9.2.1 med 9.1.4. Inspect 0.3.245 krever tenacity uten versjonsgrense.
- **Ingen andre pakker ble endret.** Installasjonen la i tillegg til cffi, cryptography, pyasn1, pyasn1-modules,
  pycparser og websockets.
