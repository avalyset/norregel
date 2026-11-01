# norregel

norregel is a closed benchmark of dated numeric values in Norwegian statutes, regulations and parliamentary decisions.
It asks a language model
for the value of, for example, a rate or an amount on a given date, and scores the answer deterministically against the
value history of that item: correct, outdated (an earlier value in the item's series), other error, or uninterpreted.
The items are built mechanically from Lovdata's open data.

This repository holds the code, the deposited tests (those that need the items are skipped), the item manifest of the
Borealis study and
the documentation that has been published with the Zenodo records. **The item files themselves are closed and are not
in this repository** (see [Closed items](#closed-items)).

## Records

| what | identifier |
|---|---|
| norregel, all versions (concept DOI) | [10.5281/zenodo.23422302](https://doi.org/10.5281/zenodo.23422302) |
| norregel v2.0 (preregistration of v2) | [10.5281/zenodo.23437444](https://doi.org/10.5281/zenodo.23437444) |
| norregel v2.1 (results of v2) | [10.5281/zenodo.23502580](https://doi.org/10.5281/zenodo.23502580) |
| norregel paper | [arXiv:2610.29207](https://arxiv.org/abs/2610.29207) |
| norregel × Borealis, preregistration | [10.5281/zenodo.23858965](https://doi.org/10.5281/zenodo.23858965) |
| norregel × Borealis, results record | 10.5281/zenodo.23870450 (reserved; not yet published) |

## Contents

- `src/norregel/`: the scorers (`score.py` for v1, `score_v2.py` for v2), the Lovdata document parser (`parse.py`) and the
  Inspect tasks.
- `scripts/`: item building, the v1 and v2 analyses, the v2 run design and reporting scripts.
- `tests/`: the deposited v2 analysis test; `conftest.py` skips the parts that need the closed items.
- `docs/`: preregistrations (v1, addendum, v2), run protocol, model lists, deviations, errata, results and the redaction
  notes, as deposited on Zenodo.
- `borealis/`: the frozen files of the norregel × Borealis preregistration (run script, analysis, lock file, synthetic
  test, item manifest with item IDs only, and the script that built it), byte-identical with the deposit.
- `LOCK_MANIFEST.md`, `data/exclusions_tillegg.json`, `data/errata_v2.txt`: the v1 lock and the published exclusions and
  errata.

## Installation

Python 3.12 or later.

```bash
git clone https://github.com/avalyset/norregel.git
cd norregel
python -m pip install "inspect_ai==0.3.245" numpy
```

The package is used from source, with `src` on the Python path (as `pyproject.toml` sets for pytest); it is not built
as a wheel. The Inspect tasks need `inspect_ai==0.3.245` (`pyproject.toml`), and the analysis scripts need `numpy`. The
Borealis run script (`borealis/f4_modal.py`) also needs `modal`, and runs `vllm` and `huggingface_hub` inside the Modal container. The tests need only `numpy`
and `pytest`:

```bash
python -m pip install numpy pytest
python -m pytest -q -rs
```

Without the closed items, two tests run and five are skipped with the reason shown.

## Use

The scorer can be used on its own, for example `from norregel import score_v2`, with `src` on the Python path. The
classes and the rules are described in `docs/PREREG_V2.md`, `docs/PREREG_TILLEGG.md` and in the paper.

## Reproducing v2 and the Borealis study

- **v2:** the preregistration (`docs/PREREG_V2.md`), the model list (`docs/v2_modeller.json`), the run log
  (`docs/V2_KJORELOGG.md`) and the analysis (`scripts/analysis_v2.py`) are here. The run script and the other locked
  files, except the closed item files and `data/pilot_ids.txt`, are in the Zenodo record 10.5281/zenodo.23437444 and
  its later versions; the lock is `LOCK_V2.md` in those records.
- **Borealis:** the frozen run script, analysis and manifest are in `borealis/` and in the preregistration
  10.5281/zenodo.23858965. The code for the results (operator script, (b) run copies, descriptive and report scripts)
  will be in the results record when it is published.

Both need the closed item files. The Borealis analysis checks the sha256 of `data/items.jsonl` against the manifest
before it computes anything.

## Closed items

The item files (`data/items.jsonl`, `data/items_h3.jsonl`, `data/items_h3_v2.jsonl`, `data/v3_items.jsonl`) are not
published, so that the benchmark can still be used for evaluation; they are not in the Zenodo records either. The
sha256 values of `items.jsonl` and `items_h3.jsonl` are in `LOCK_MANIFEST.md` and `docs/RUN_PROTOCOL.md`, that of
`items.jsonl` also in `borealis/manifest_v1.json`, and those of the v2 files in `LOCK_V2.md` in the Zenodo records.
Raw model answers to the items are not published.

## Source attribution

Inneholder data under Norsk lisens for offentlige data (NLOD) tilgjengeliggjort av Stiftelsen Lovdata. (Contains data under the Norwegian Licence for Open Government Data (NLOD) made available by Stiftelsen Lovdata.) Licence: NLOD 2.0, https://data.norge.no/nlod/no/2.0. Source: https://api.lovdata.no/. The items were derived from these data by norregel (extraction, chaining, question templates); these changes were made by the author and are not Lovdata's responsibility.

## Licence

The contents of this repository are under the Creative Commons Attribution 4.0 International licence (`LICENSE`), the
licence of the Zenodo records. See `NOTICE`.

## Feedback

Use the [Issues](https://github.com/avalyset/norregel/issues) of this repository for questions, errors and suggestions.
See `CONTRIBUTING.md`.

## Citation

See `CITATION.cff`.

## AI disclosure

Claude Code (Anthropic) was used as a tool under the author's direction to write code, documentation and this
repository. The author is responsible for the content.
