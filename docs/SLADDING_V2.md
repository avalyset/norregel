# Redaction in version 2.1

The norregel items, both questions and reference values, are withheld to limit contamination of future training data.
Version 1.2 (SLADDING.md in the record) replaced every number in a verbatim quote of a model answer by «[verdi]», because
an answer can repeat the reference value. Version 2.1 narrows that rule to numbers that can be reference values: NOK
amounts, percentages, multiples of G and ages. The years the models gave for their own knowledge limit are kept because
they are a finding of the paper. The mechanical check below found none of these years equal to a reference value or an
earlier value.

The years in the models' statements of their own knowledge limit appear in:

- RESULTS_V2.md, table T20;
- TILLEGG_ETTER_VURDERING.md, table A6;
- TALLKILDER_papir_v1.md.

| File | Numbers redacted | What was checked |
|---|---|---|
| RESULTS_V2.md | 0 | Rendered by `rapport_v2.py` from the analysis report. It contains tables of counts, shares, intervals and test results, and in T20 the time expressions the models gave for their own knowledge limit. It has no quoted answers with values that can be reference values. |
| TILLEGG_ETTER_VURDERING.md | 0 | Table A6 quotes the time expressions the models gave for their own knowledge limit. Those are years, not item values. The file has no other quotes of model answers. |
| TALLKILDER_papir_v1.md | 0 | Number sources of the revised version 1 paper. Its rows for the models' knowledge limit carry the same years as A6. |

The other files contain no quotes of model answers and are not redacted:

- ITEM_KLASSER_V2.csv;
- V2_KJORELOGG.md, AVVIK_V2.md, ERRATA_V2.md and V2_VERSJONER.md, which contain error messages from the providers, not
  model answers;
- the code (item_klasser_v2.py and run_v2_A-V2-6.sh);
- LOCK_V2_A-V2-6.md;
- errata_v2.txt.

A mechanical check of every file against the item file found no question text and no item ID outside
ITEM_KLASSER_V2.csv. It also found no number of four or more digits equal to a reference value or an earlier value, apart
from one coincidence in TALLKILDER_papir_v1.md (a number of resamples).

## Files in version 2.1

- **RESULTS_V2.md:** the results of the version 2 run. The locked `rapport_v2.py` renders it from the analysis report.
- **ITEM_KLASSER_V2.csv:** the class of every answer, described below. `item_klasser_v2.py` writes it.
- **V2_KJORELOGG.md:** the run log.
- **AVVIK_V2.md:** the deviations after locking, A-V2-3 to A-V2-9.
- **ERRATA_V2.md:** the errata to version 2.0.
- **V2_VERSJONER.md:** the package versions.
- **run_v2_A-V2-6.sh and LOCK_V2_A-V2-6.md:** the run script and the lock after deviation A-V2-6. They correspond to
  `scripts/run_v2.sh` and `docs/LOCK_V2.md` in the repository at commit `d68ce0d`. The script has an absolute path for the H3
  task and the switch `ONLY_H3=1`, which runs only the H3 task. The files `run_v2.sh` and `LOCK_V2.md`
  from version 2.0 are kept unchanged in this record.
- **TILLEGG_ETTER_VURDERING.md:** the supplementary analyses written after the review of the version 1 paper. The review
  is the repository file `docs/vurderinger/FAGFELLEVURDERING.md` and is not part of this record. «Underagenten» in
  section A5 is the language-model sub-agent that did the blind final check on the fourth lock (repository file
  `docs/ERRATA.md`, lines 8–11; paper, `paper/main.tex`, lines 129–130). The review was done by a language model (Claude
  Fable, run as a Claude Code sub-agent on 17 October 2026), not by a human reviewer.
- **TALLKILDER_papir_v1.md:** the number sources of the revised version 1 paper (`paper/TALLKILDER.md`). It replaces
  nothing; TALLKILDER.md from version 1.2 is kept.
- **errata_v2.txt:** `data/errata_v2.txt`, the errata file used in S7. It lists no item. Its SHA-256 equals the row in `docs/LOCK_V2.md`, line 54.
- **SHA256SUMS_v2_1:** the SHA-256 checksums of the files added in version 2.1.

## ITEM_KLASSER_V2.csv

`item_klasser_v2.py` writes this file from the answer file of `svar_v2.py`. The class is the one used in the analysis
(`analysis_v2.classify`: the version 1 normalisation, then scorer v2).

- `task`: `norregel_v2` for the main task, or `norregel_h3_v2` for H3, which has the Bokmål and Nynorsk versions of the
  same item.
- `item_id`: the item ID. H3 IDs end in `-nb` or `-nn`.
- `model`: the Inspect model ID.
- `run`: the run. Run 1 is primary. For models with one run, run 2 is the control run on 100 fixed items.
- `class`: `korrekt`, `utdatert`, `feil` or `utolket`.
- `subclass`: the preregistered sub-class:
  - for `utolket`: `avslag`, `ingen_svarlinje`, `flere_tall`, `ett_tall_uleselig` or `endelig_feil`;
  - for `feil`: `senere_verdi`, `forkastet_versjon` or `utenfor_historikken`;
  - empty otherwise.
- `final_error`: 1 if the sample was still in error after the retries. Such samples are scored `utolket`.
- `i_primærsett`: for the main task, 1 if the item is in the primary set. For H3, 1 if the pair's source item is not
  excluded.

## Not included

The item files, the answer file and the run logs are not published.
