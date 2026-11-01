# Modeller (låst før første kjøring; rad 4–5 endret ved A2/A3)

Lista er bindende fra commit-en som legger til denne fila, `docs/modeller.json` og
`docs/RUN_PROTOCOL.md` (`3c554cff4cbea02f02896a58c2f778bb4ef8ea87`). Rad 5 ble endret i
`d151cd7cc164e3ca2df17b8b8ec643b0576e1909` (A2) og rad 4 i `988472f21cacebfdb9ed2f8d34de4ffd8e125f4a` (A3).
Maskinlesbar utgave: `docs/modeller.json` (`id`, `cutoff`, `reasoning`).
Kildene er lest 16.10.2026. SHA-256 er over fila slik den ble hentet (`curl -sL <url>`); sidene kan
endre seg senere.

Regler for cutoff og reasoning: `docs/RUN_PROTOCOL.md` avsnitt 3.1, 3.2 og 3.6.

| # | Inspect-id | Leverandørens id | Cutoff | Reasoning | Kjøres |
|---|---|---|---|---|---|
| 1 | `anthropic/claude-haiku-4-5-20251001` | `claude-haiku-4-5-20251001` (aliaset `claude-haiku-4-5` peker hit) | 2025-07-31 | nei | API |
| 2 | `anthropic/claude-sonnet-4-6` | `claude-sonnet-4-6` | 2026-01-31 | nei | API |
| 3 | `anthropic/claude-opus-5-5` | `claude-opus-5-5` (nyeste Opus i `GET /v1/models` 16.10.2026, opprettet 2026-09-21; kilde ikke lagret) | 2026-06-30 | ja | API |
| 4 | `ollama/nb-llama-3.1-8b-instruct-cardtmpl:latest` | HF-repo `NbAiLab/nb-llama-3.1-8B-Instruct-Q4_K_M-GGUF`, fil `nb-llama-3.1-8b-instruct-q4_k_m.gguf`, blob `sha256:6d72cb0a1d18c300564be44d57c06ce1203f05d465d90735f2402e447d6490e9`, chat-malen fra modellkortet med fast dato (endring A3; Modelfile `docs/modelfiles/nb-llama-3.1-8b-instruct-cardtmpl.Modelfile`) | `null` (ukjent) | nei | lokal |
| 5 | `ollama/normistral-7b-warm-instruct-cardtmpl:latest` | HF-repo `ltg/normistral-7b-warm-instruct`, GGUF Q4_K_M, blob `sha256:ed1f173921eea691b44ec8a7324079ff4c800046a9e2b396bdfd410449305088`, chat-malen fra modellkortet (endring A2; Modelfile `docs/modelfiles/normistral-7b-warm-instruct-cardtmpl.Modelfile`) | `null` (ukjent) | nei | lokal |

Modell 5 fantes allerede lokalt (4,4 GB). Ingenting ble hentet. `mistral:latest` er derfor ikke med.

## 1. claude-haiku-4-5-20251001

- **Cutoff 2025-07-31** (treningsdata, «Jul 2025» leses som siste dag i måneden).
- Kilde: https://platform.claude.com/docs/en/models/haiku-4-5/overview (hentet som `.md`), sha256 `bec0ed34119af773736e4ee5897e25cf43b1261a5e63b77b0639fb36814f32e7`.
- Ordrett fra kapabilitetstabellen: `| Training data cutoff | Jul 2025 |`. Samme tabell har `| Reliable knowledge cutoff | Feb 2025 |`. Treningsdatagrensen brukes (tillegget, avsnitt 3).
- Modell-id: siden oppgir `claude-haiku-4-5-20251001`; `claude-haiku-4-5` er aliaset. Den daterte id-en brukes.
- Reasoning: **nei**. https://platform.claude.com/docs/en/build-with-claude/thinking (sha256 `10ef0f5b2135b7cf07c66e8e36c8a03bde9c85b86d75eafe3c35db8f0d642f47`), tabellraden `| Claude Haiku 4.5 | Thinking off | 400 error | Extended thinking | 400 error | Thinking off |` (kolonnen «No thinking field» er `Thinking off`).
- Maks output 64K tokens (kilde: modellsiden i linjen «Kilde» over, med URL og sha256). Det er over 1 024.
- Pris: 1 USD inn / 5 USD ut per million tokens (https://platform.claude.com/docs/en/about-claude/pricing, sha256 `d0dc6009ff1bae0023eec432d7c21d4a3b71a71e542ac350dbfd13dc85a8b862`, rad `| Claude Haiku 4.5 | $1 / MTok | $1.25 / MTok | $2 / MTok | $0.10 / MTok | $5 / MTok |`).

## 2. claude-sonnet-4-6

- **Cutoff 2026-01-31** («Jan 2026»).
- Kilde: https://platform.claude.com/docs/en/models/sonnet-4-6/overview, sha256 `6289990a037450f8f9675682d3b115b5d82e4adce3711995f39ba041f9cf4730`.
- Ordrett: `| Training data cutoff | Jan 2026 |`. Samme tabell: `| Reliable knowledge cutoff | Aug 2025 |`.
- Reasoning: **nei**. Thinking-siden, `| Claude Sonnet 4.6 | Thinking off | Adaptive thinking | Extended thinking (deprecated) | 400 error | Thinking off |`. Uten `thinking`-felt er tenking av. Kjøringen sender ikke feltet.
- Maks output 128K tokens (kilde ikke lagret).
- Pris: 3 / 15 USD (`| Claude Sonnet 4.6 | $3 / MTok | $3.75 / MTok | $6 / MTok | $0.30 / MTok | $15 / MTok |`).

## 3. claude-opus-5-5

- **Cutoff 2026-06-30** («Jun 2026»).
- Kilde: https://platform.claude.com/docs/en/models/opus-5-5/overview, sha256 `db3d6cbf322fadb625f19337625d9b10eaa1acb1b5565403c563dd2195bfe142`. Modelloversikten (https://platform.claude.com/docs/en/about-claude/models/overview, sha256 `02faed97309963e7c90d18a80ff0f6ba7cf6099d46a7cc1b2ac600ceaebac578`) gir det samme.
- Ordrett: `| Training data cutoff | Jun 2026 |` og `| Reliable knowledge cutoff | Jun 2026 |`.
- Reasoning: **ja**. Modellsiden: `| Thinking | Adaptive (always on) |`; thinking-siden: `| Claude Opus 5.5 | Adaptive thinking | Adaptive thinking | 400 error | 400 error | 400 error |`. Standard effort er `medium` (kilde ikke lagret). Kjøringen sender ikke `thinking` eller `effort`.
- Sampling: Opus 5.5 tar ikke temperatur utenom standard (migreringsguiden for Opus 5.5, https://platform.claude.com/docs/en/models/opus-5-5/migration-guide (hentet som `.md` 17.10.2026), sha256 `33c264e04d5f3aa638ebcbba85e2eb27e23b9792aeee1bc374d2267f1e70d261`: «Sampling parameters removed» … «including Claude Opus 5.5, returns a 400 error»). Reasoning-modeller kjøres uten `--temperature` uansett (tillegget, avsnitt 3), så dette utløser ikke avvisningsregelen.
- Maks output 128K tokens, over 16 384 (kilde ikke lagret).
- Pris: 4 / 20 USD (`| Claude Opus 5.5 | $4 / MTok | $5 / MTok | $8 / MTok | $0.20 / MTok | $20 / MTok |`). Tenketokens faktureres som output (kilde ikke lagret).

## 4. ollama/nb-llama-3.1-8b-instruct-cardtmpl:latest

- **Endret ved A3 (16.10.2026).** Første versjon av lista hadde `ollama/nb-llama-3.1-8b:latest`. Vektene er de samme (samme blob). Bare chat-malen er byttet, se `docs/RUN_PROTOCOL.md` A3.
- **Opphav fastslått 16.10.2026:** SHA-256 av blobben, `6d72cb0a1d18c300564be44d57c06ce1203f05d465d90735f2402e447d6490e9`, er lik SHA-256 for `nb-llama-3.1-8b-instruct-q4_k_m.gguf` i `NbAiLab/nb-llama-3.1-8B-Instruct-Q4_K_M-GGUF` (HF-API: `https://huggingface.co/api/models/NbAiLab/nb-llama-3.1-8B-Instruct-Q4_K_M-GGUF?blobs=true`, sha256 av svaret `a4438815e976e47fb45d1bb997bb4c31cb0d0423f384c905f9cb8fb8561329be`). Kortet (`https://huggingface.co/NbAiLab/nb-llama-3.1-8B-Instruct-Q4_K_M-GGUF`, sha256 `4fe4a63533371789b863af753eb4516c043892f889d74d545436e94aac009403`) sier `base_model: "NB-Llama-3.1-8B-Instruct"`, lisens llama3.1, og oppgir ingen cutoff. GGUF-en har `bos_token_id` 128000, `eos_token_id` 128009 (`<|eot_id|>`) og Llama 3.1-malen (4 614 tegn) som `tokenizer.chat_template`.
- **Cutoff `null`.** Kortet oppgir ingen dato. Linjen «Cutting Knowledge Date: December 2023» i malen er Metas malkonstant (kilde ikke lagret), ikke en opplysning fra NbAiLab, og telles ikke. Kortet som oppgir «May 2024» (`NbAiLab/nb-notram-llama-3.1-8b-instruct`; kilde ikke lagret) gjelder en annen modell.
- Arkitektur Llama, 8,0 B parametre, Q4_K_M, kontekst 131 072 (kilde ikke lagret).
- Mal (A3): kortets mal uten system- eller verktøymelding, med standarddatoen `26 Jul 2024` og `<|begin_of_text|>`, slik at prompten er den samme hver dag. Stoppsekvensene (`<|start_header_id|>`, `<|end_header_id|>`, `<|eot_id|>`) og samplingparametrene i den opprinnelige lokale modellen (seed 42, temperature 0, top_k 1, top_p 1) er uendret arvet. Ingen systemprompt gis av oss.
- Reasoning: nei.

## 5. ollama/normistral-7b-warm-instruct-cardtmpl:latest

- **Endret ved A2 (16.10.2026, før første sample i full kjøring).** Første versjon av lista hadde `ollama/hf.co/ltg/normistral-7b-warm-instruct:Q4_K_M`. Vektene er de samme (samme blob). Bare chat-malen er byttet til modellkortets, se `docs/RUN_PROTOCOL.md` A2.
- Variant: **instruct**, ikke basemodell. Repo `ltg/normistral-7b-warm-instruct`, kortets tittel «Instruction-tuned NorMistral-7b-warm», HF-tagger `instruction` og `chat`. SHA-256 av `normistral-7b-warm-instruct.Q4_K_M.gguf` i HF-API-et (`https://huggingface.co/api/models/ltg/normistral-7b-warm-instruct?blobs=true`) er `ed1f173921eea691b44ec8a7324079ff4c800046a9e2b396bdfd410449305088`, lik Ollama-blobben.

- **Cutoff `null`.** Modellkortet (https://huggingface.co/ltg/normistral-7b-warm-instruct, sha256 `c26a75716824b8cf1a9cab2490ccaad2db81ceba7ce00f0b4b13de2a26cf6aa8`) oppgir ingen dato. Det sier at basismodellen er initialisert fra Mistral-7B-v0.1 og videre forhåndstrent på norske data.
- 7,25 B parametre, Q4_K_M, kontekstlengde 2 048 i Ollama (kilde ikke lagret). Lengste spørsmål er 409 tegn, så prompt + 1 024 svartokens er innenfor.
- Mal (A2): modellkortets ChatML-lignende format `<|im_start|> user\n…<|im_end|>\n<|im_start|> assistant\n` (med mellomrom etter taggen), uten systemprompt. Stoppsekvenser `<|im_start|>` og `<|im_end|>`.
- Reasoning: nei.

## Vage cutoffs

Ingen av de fem modellene har en vag cutoff (tre har en måned, to har ingen). Sensitivitetsanalysen uten
vage cutoffs er derfor lik hovedanalysen for H1 og blir ikke regnet separat.
