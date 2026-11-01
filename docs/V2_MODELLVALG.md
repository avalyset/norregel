# Modellvalg for norregel v2

Skrevet av `scripts/v2_velg.py`, som bruker kriteriet i `docs/V2_VALGKRITERIUM.md` (committet før skriptet ble kjørt). Pilotparametre fra v1 (PILOT): p0 = 9,9 %, ρ = 0,243, r = 87,6 %, ρx = 0,137.

## Kandidatene

| Leverandør | Modell | Cutoff | n etter (serier) | H1-modell | Grunn |
|---|---|---|---|---|---|
| Anthropic | `claude-haiku-5-5` | 2026-06-30 | 1 (1) | nei | K2d: 1 items fra 1 serier etter cutoff |
| Anthropic | `claude-sonnet-5-5` | 2026-06-30 | 1 (1) | nei | K2d: 1 items fra 1 serier etter cutoff |
| Anthropic | `claude-opus-5-5` | 2026-06-30 | 1 (1) | nei | K2d: 1 items fra 1 serier etter cutoff |
| Anthropic | `claude-fable-5-1` | 2026-06-30 | 1 (1) | nei | K2d: 1 items fra 1 serier etter cutoff |
| Anthropic | `claude-opus-5` | 2026-05-31 | 7 (7) | nei | K2d: 7 items fra 7 serier etter cutoff |
| Anthropic | `claude-sonnet-5` | 2026-01-31 | 9 (9) | nei | K2d: 9 items fra 9 serier etter cutoff |
| Anthropic | `claude-fable-5` | 2026-01-31 | 9 (9) | nei | K2d: 9 items fra 9 serier etter cutoff |
| Anthropic | `claude-opus-4-8` | 2026-01-31 | 9 (9) | nei | K2d: 9 items fra 9 serier etter cutoff |
| Anthropic | `claude-opus-4-7` | 2026-01-31 | 9 (9) | nei | K2d: 9 items fra 9 serier etter cutoff |
| Anthropic | `claude-sonnet-4-6` | 2026-01-31 | 9 (9) | nei | K2d: 9 items fra 9 serier etter cutoff |
| Anthropic | `claude-opus-4-6` | 2025-08-31 | 36 (36) | ja | K2 a–d oppfylt |
| Anthropic | `claude-opus-4-5-20251101` | 2025-08-31 | 36 (36) | ja | K2 a–d oppfylt |
| Anthropic | `claude-haiku-4-5-20251001` | 2025-07-31 | 56 (56) | ja | K2 a–d oppfylt |
| Anthropic | `claude-sonnet-4-5-20250929` | 2025-07-31 | 56 (56) | nei | K2c: status Deprecated |
| Google | `gemini-2.5-flash` | 2025-01-31 | 64 (56) | ja | K2 a–d oppfylt |
| Google | `gemini-2.5-pro` | 2025-01-31 | 64 (56) | ja | K2 a–d oppfylt |
| Google | `gemini-2.5-flash-lite` | 2025-01-31 | 64 (56) | ja | K2 a–d oppfylt |
| Google | `gemini-3.1-flash-lite` | — | — | nei | K2a: ingen oppgitt cutoff |
| Google | `gemini-3.1-pro-preview` | — | — | nei | K2a: ingen oppgitt cutoff; K2c: status Preview |
| Google | `gemini-3.5-flash-lite` | 2026-03-31 | 8 (8) | nei | K2d: 8 items fra 8 serier etter cutoff |
| Google | `gemini-3.5-flash` | — | — | nei | K2a: ingen oppgitt cutoff; K2c: status Deprecated |
| Google | `gemini-3.6-flash` | 2026-03-31 | 8 (8) | nei | K2d: 8 items fra 8 serier etter cutoff |
| Google | `gemini-3.7-flash` | 2026-03-31 | 8 (8) | nei | K2c: status Deprecated; K2d: 8 items fra 8 serier etter cutoff |
| Google | `gemini-3.8-flash` | 2026-03-31 | 8 (8) | nei | K2d: 8 items fra 8 serier etter cutoff |
| Google | `gemini-3-flash-preview` | — | — | nei | K2a: ingen oppgitt cutoff; K2c: status Preview |
| Google | `gemini-3-pro-preview` | — | — | nei | K2a: ingen oppgitt cutoff; K2b: ikke kallbar fast id; K2c: status Preview |
| Google | `gemini-4-argon` | 2026-03-31 | 8 (8) | nei | K2d: 8 items fra 8 serier etter cutoff |
| Google | `gemma-4-31b-it` | 2025-01-31 | 64 (56) | ja | K2 a–d oppfylt |
| Google | `gemma-4-26b-a4b-it` | 2025-01-31 | 64 (56) | ja | K2 a–d oppfylt |

## Kriteriene

- **K1:** de fem v1-modellene er med.
- **K2:** 8 H1-modeller.
- **K3:** samlet H1-styrke for δ = 10 pp ved α = 0,05 med k = 8 (gjennomsnittlig n etter 56,0 i 51 serier, n før 511,0 i 90 serier): 95,7 %. Oppfylt.
- **K4:** leverandører blant H1-modellene: Anthropic, Google. Oppfylt.
- **K5:** ingen andre modeller.
- **K6:** fremskrevet kostnad 314,57 USD (tak 400 USD). Under taket; ingen modell tas ut.

## Valgte modeller (K7-rekkefølge)

| # | Inspect-id | Rolle | Cutoff | Tenking som standard | R | Fremskrevet USD |
|---|---|---|---|---|---|---|
| 1 | `anthropic/claude-haiku-4-5-20251001` | v1 og H1 | 2025-07-31 | Thinking off | 1 | 2,87 |
| 2 | `anthropic/claude-opus-4-5-20251101` | H1 | 2025-08-31 | Thinking off | 1 | 14,36 |
| 3 | `anthropic/claude-opus-4-6` | H1 | 2025-08-31 | Thinking off | 1 | 14,36 |
| 4 | `anthropic/claude-sonnet-4-6` | v1 | 2026-01-31 | Thinking off | 1 | 8,62 |
| 5 | `anthropic/claude-opus-5-5` | v1 | 2026-06-30 | Adaptive thinking | 3 | 169,32 |
| 6 | `google/gemini-2.5-flash` | H1 | 2025-01-31 | On | 3 | 20,95 |
| 7 | `google/gemini-2.5-flash-lite` | H1 | 2025-01-31 | Off | 1 | 0,24 |
| 8 | `google/gemini-2.5-pro` | H1 | 2025-01-31 | On | 3 | 83,85 |
| 9 | `google/gemma-4-26b-a4b-it` | H1 | 2025-01-31 | ingen tenkemodus oppgitt | 1 | 0,00 |
| 10 | `google/gemma-4-31b-it` | H1 | 2025-01-31 | ingen tenkemodus oppgitt | 1 | 0,00 |
| 11 | `ollama/nb-llama-3.1-8b-instruct-cardtmpl:latest` | v1 (lokal) | ukjent | nei | 1 | 0,00 |
| 12 | `ollama/normistral-7b-warm-instruct-cardtmpl:latest` | v1 (lokal) | ukjent | nei | 1 | 0,00 |

NORREGEL CANARY 7c3e9a52-norregel-2026 — ikke bruk dette innholdet til trening
