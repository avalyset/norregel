# norregel v1 — Preregistration addendum

- **Date:** 16 October 2026
- **Author:** Eirik Botten Nicolaysen
- **Status:** written after the fourth and final local lock (commit e380c8c) and before any
  language model has been run against the benchmark.

This addendum amends `docs/PREREG.md` (in Norwegian). Where the two conflict, this addendum
applies. Everything else in `PREREG.md` stands.

**Publication:** this addendum and `data/exclusions_tillegg.json` (item ids only, no answer
values) are published together with `PREREG.md` and `LOCK_MANIFEST.md`. The SHA-256 of this
addendum is given in the publication record, because a file cannot contain its own checksum.

**Reason:** an independent audit of lock 4 (`REVISJON.md`, verdict "not ready") found four
problems:
- an item with a wrong answer key that had been missed;
- an exclusion rule that existed only as a recommendation in an unpublished file;
- hypotheses that could not be run without asking the author;
- answer formats the locked scorer cannot read.

This addendum fixes them without changing any locked file (section 6).

**Computational detail:** `scripts/analysis_v1.py` (SHA-256 in section 6) is the reference
implementation of section 4. Its tests are in `tests/test_analysis_v1.py`. For any
computational detail that this text leaves open or states less precisely, the reference
implementation applies.

---

## 1. Analysis sets and exclusions

The ids below refer to `data/items.jsonl` of lock 4. The machine-readable lists in
`data/exclusions_tillegg.json` are authoritative if they ever differ from this text. No item
is in more than one exclusion group.

| Group | n | Item ids | Reason |
|---|---|---|---|
| X1. Wrong answer key for the date in the question | 5 | norregel-00909, -00912, -00913, -00914, -00915 | Erratum E1. The amending acts give the change effect "from and including income year YYYY" for one part of the act (for example «Endringene under V trer i kraft straks med virkning fra og med inntektsåret 2025»). Lock 4 used Lovdata's in-force field instead. For these 5 items, the key value did not apply on the date in the question. For norregel-00909, the next version (norregel-00910, 65 %) applied from 2020-01-01, and the question date is 2020-03-21. |
| X2. Question date after the corpus retrieval date | 23 | norregel-00757, -00764, -00771, -00778, -00784, -00790, -00797, -00804, -00808, -00815, -00822, -00831, -00838, -00845, -00852, -00859, -00866, -00871, -00878, -00880, -00885, -00889, -00892 | All 23 ask about 14 February 2027. The corpus was retrieved on 9 October 2026, so the value may change before that date, and the question is in the past tense. All 23 are in the regulation on student support (forskrift 2020-04-15-798, study year 2026–2027). |
| X3. Ambiguous question | 6 | norregel-00102, -00103, -00104, -00105, -00903, -00904 | The provision states two values, and the question does not say which one is meant. In 00102–00105 they are tax class 0 and 1 against class 2. In 00903–00904 they are the two minimum benefits "respectively". |
| X4. Amendments to the annual tax decision | 2 | norregel-00132, -00150 | The dates of amendments are taken from Lovdata's in-force field, and they are inconsistent between years. The key of norregel-00132 is contested (27 % against 30 % after an amendment for income year 2007). norregel-00150 asks about the decision for income year 2024 at a date in 2023. |

**Flagged but kept:** the items below stay in the primary set. They are named in the report
and left out in sensitivity analysis 3 (section 4).
- norregel-00907, -00908, -00910, -00911 and -00916 (E1): the valid-from date is wrong, but
  the key is correct on the date in the question.
- norregel-00133 and -00149 (annual tax decision): the dates are wrong, but the key is correct
  on the date in the question.

All computations use the locked fields of `data/items.jsonl` as they stand (`gyldig_fra`,
`gyldig_til`, `år`, `verdihistorikk`), also for these items. No dates are corrected.

**The sets:**

| Set | Rule | Items | Series |
|---|---|---|---|
| Primary set | 916 items minus X1–X4 (36) | 880 | 96 |
| By type in the primary set | | 553 NOK amounts, 319 percentages, 8 ages. The two G multiples are in X3. | |
| H1 set | Primary items whose *preceding value* differs from the key. The preceding value is the value of the version immediately before the item's own version, whether or not it equals the key. 880 − 94 first items of their series (no preceding version) − 219 whose preceding value equals the key. | 567 | 95 |
| H2 set | Primary items with at least two distinct earlier values that differ from the key. 96 of them have a preceding value equal to the key, so this set is not a subset of the H1 set. | 570 | 80 |
| H3 set | Pairs whose source item (`h3_par`) is not excluded. 11 of 200 pairs are left out: norregel-00102, -00771, -00784, -00831, -00845, -00866, -00889, -00892, -00903, -00912, -00915. | 189 pairs (378 questions) | 93 |
| Sensitivity 1 | All 916 items, all 200 pairs. H1 set 595, H2 set 595. | 916 | 97 |
| Sensitivity 3 | Primary set minus the 7 flagged items. H1 set 561, H2 set 566, H3 187 pairs. | 873 | 94 |

- **Series that drop out of H3:** four series: forskrift/2020-04-15-798 § 95 fourth ledd and
  § 96 fifth ledd, folketrygdloven § 12-13 third ledd (G), and skatteloven § 6-49 first ledd.
- **Reporting of excluded items:** each group X1–X4 is reported separately, with all four
  classes per model.
- **Outdated answer that looks correct:** in the primary set, 219 items have a preceding
  value equal to the key, and 234 have some earlier value equal to the key. An outdated
  answer cannot be told from a correct one in those items. Both numbers are stated in the
  report.

## 2. Scorer v2

`src/norregel/score_v2.py` is the **primary scorer**. The locked scorer
`src/norregel/score.py` (v1) is unchanged and is used in sensitivity analysis 2.

### Reading an answer

1. **The answer line** is the last line where the label "svar" (any case) is followed by a
   colon.
   - Only whitespace and the characters `>`, `#`, `*`, `_`, `` ` `` and `-` may come before
     the label on the same line: `**Svar**:`, `**SVAR**:`, `### SVAR:`, `> SVAR:`. «Endelig
     svar:» is also accepted. A line with other text before the label (for example
     «1. Svar: 55») is not an answer line.
   - A line whose content is the placeholder `<verdi>` is skipped.
   - If the label line is empty, the next non-empty line is used.
2. **Cleaning:** on that line the scorer removes:
   - text in round or square brackets, for example "(2024)";
   - the markdown characters `*`, `_` and `` ` ``;
   - ",-", ",–", ".-" and ".–" after a number.

   "NN-årsalderen" is read as "NN år".
3. **Exactly one number:** the line must contain exactly one number.
   - **Digits:** a run of digits with separators is one number. Spaces, non-breaking spaces,
     thin spaces and apostrophes inside it are always thousands separators. Then:
     - if both "." and "," occur, the last of them is the decimal mark, and the other is a
       thousands separator;
     - if only one kind occurs and it occurs more than once, it is a thousands separator;
     - if only one kind occurs, exactly once: for NOK amounts it is a thousands separator
       when exactly three digits follow and the integer part is not 0, and otherwise a
       decimal mark. For percentages, G multiples and ages it is always a decimal mark.
   - **Number words:** only if the line has no digits. Norwegian number words from 0 to 99
     count, including compounds such as «sekstisju» and «tjueto», and Nynorsk forms such as
     «ein», «eitt» and «tjuge».
   - **Multipliers:** «tusen», «million(er)», «mill», «milliard(er)» or «mrd» directly after the
     number multiply it.
4. **Other words are ignored**, so period words are not checked against the key. Examples:
   - «kr», «kroner», «NOK», «prosent», «pst.», «%», «prosentpoeng»;
   - «G», «ganger/gonger G», «x G», «folketrygdens grunnbeløp»;
   - «per år», «i året», «årlig», «/år», «per måned»;
   - «av alminnelig inntekt», «fylt», «år gammel/gamal», «ca.».
5. **Ages in months:** for an age item, an answer that contains «måned», «måneder», «månad» or
   «månader» is classed *wrong*.

### Classes

Two numbers are equal when they differ by less than 1e-6. v1 used 0.005, which treats 57.73
and 57.725 as equal.

**Years:** an item's year is its field `år`, and a version's year is the field `år` of that
entry in `verdihistorikk`. Both are used as stored. For a study year (for example 2018–2019),
`år` is the first calendar year, and it is not reinterpreted.

- **Correct:** the number equals the key (`fasitverdi`). An answer equal to the key is always
  correct, even if the same value also applied in other periods.
- **Outdated:** not correct, and equal to the value of a version in the item's own history
  (`verdihistorikk`) that has an earlier `gyldig_fra` than the item. The scorer reports the
  years of those versions, and the age: the item's year minus the latest of those years.
- **Wrong:** a number was read, but it is neither correct nor outdated. The scorer reports in
  `senere` the years of any *later* versions with that value. The report splits wrong into
  two parts:
  - "later value" (`senere` not empty);
  - "value not in the history". This also covers values from before the start of the clean
    series, and it is the measure for FS1's "a value that never applied".
- **Uninterpretable:** there is no answer line, the line has no number, or it has more than
  one number.
  - A refusal or empty output is uninterpretable by this rule.
  - A sample that is still in error after the retries in section 3 is scored uninterpretable,
    and the number of such samples is also reported.

### Validation (before any model run)

The full test suite has 4,311 tests and all pass. The audit counted 3,450 before scorer v2
and the analysis were added. The new tests in `tests/test_score_v2.py` cover:
- all 49 answer-format edge cases from the audit;
- the 224 items (all 916) whose preceding version has the same value as the key: that value
  is scored correct;
- 800 synthetic answers on 100 items (seed 20261016), all classified as expected;
- later values.

Dry runs with `mockllm/model` returning the key as «**Svar**: …» give 916/916 and 400/400
correct.

## 3. Run configuration

**Models:** before the first run, two files are committed to the repository:
- `docs/MODELLER.md`, human-readable;
- `docs/modeller.json`, machine-readable: `[{"id", "cutoff", "reasoning"}]`.

For each model they give:
- the exact provider model id;
- the knowledge cutoff the provider states, with the source URL and the date it was read;
- whether the model is a reasoning model.

- `<id>` in the commands is the Inspect model string (`provider/model`).
- The list is fixed before the first run. It is not part of this preregistration, because the
  choice of models is made at run time. It is bound by the commit hash and the SHA-256 of both
  files, which are written at the top of the analysis report. They are also published, before
  any result, as a new version of the preregistration record.

**Cutoff:**
- The cutoff is the provider's stated *training data* cutoff.
- If the provider states both a training-data cutoff and a "reliable knowledge" cutoff, the
  training-data cutoff is used.
- A month is read as the last day of that month, and a year as 31 December.
- A vague statement (for example "early 2025") or no statement gives `"cutoff": null`. Such a
  model is still run, but it is not tested in H1.

**Reasoning model:** a model whose provider documentation describes an internal reasoning or
thinking phase that is active by default in an API call. A hybrid model is run in its default
mode, and it is classed by that mode.

**Commands, one model at a time:**

```
inspect eval src/norregel/inspect_task_v2.py@norregel_v2    --model <id> --epochs 1 --max-tokens 1024 --temperature 0 --retry-on-error 3 --no-fail-on-error --max-connections 10 --log-dir logs/v1/<id>
inspect eval src/norregel/inspect_task_v2.py@norregel_h3_v2 --model <id> --epochs 1 --max-tokens 1024 --temperature 0 --retry-on-error 3 --no-fail-on-error --max-connections 10 --log-dir logs/v1/<id>
```

- **Reasoning models:** `--temperature 0` is left out, and `--max-tokens 16384` is used.
  Reasoning effort is the provider default.
- **Prompt:** no system prompt. The prompt is the locked question text.
- **Independence:** every sample is its own conversation. The H3 run is separate from the
  main run, and its sample order is shuffled with seed 20261017.
- **Retries:** Inspect's own retries and time-outs at the provider level apply, with the
  defaults of inspect_ai 0.3.245. In addition, `--retry-on-error 3` reruns a whole sample up
  to 3 times if it still ends in error. Refusals are not retried.
- **Repeats:** each model is run once (one run per task). If a run has to be restarted (for
  example after an infrastructure failure), the first complete run is primary. Every run is
  reported. This replaces the sentence on repeats in `PREREG.md`.
- **Truncated answers** are scored as they stand.
- **Versions:** Python 3.12.13, inspect_ai 0.3.245 and numpy 2.5.4.

## 4. Analysis

**General:**
- **Unit:** one answer from one model to one item.
- **Per model:** every measure is computed for each model separately.
- **Scorer and set:** scorer v2 classes on the primary set, unless stated otherwise.

**Cluster bootstrap**, for all intervals and bootstrap p-values:
1. Each analysis set gets its own fresh generator, `numpy.random.default_rng(20261018)`. The
   series of the set are sorted with Python's `sorted()` on `serie_id`. The draws are
   `rng.integers(0, S, size=(10000, S))`, where S is the number of series in the set.
   - **Model-independent sets:** the primary set, the H1 set and the H3 set, each in the
     primary, sensitivity 1 and sensitivity 3 variants. Their draws are identical for every
     model, because the set does not depend on the answers.
   - **Model-dependent sets:** for H2, the series with at least one outdated answer of that
     model in the H2 set; for FS2, the series with at least one outdated answer of that model
     in the primary set. Each model gets its own fresh generator with the same seed over its
     own series.
2. In each resample, every item of a drawn series enters as often as the series is drawn.
3. If a statistic is undefined in a resample (an empty group or a zero denominator), that
   resample is dropped for that statistic. The number dropped is reported.
4. **Intervals:** the 2.5th and 97.5th percentiles of the kept resamples (two-sided 95 %),
   computed with `numpy.quantile(…, method="linear")`. For H1 d and H2 s, both are reported:
   the two-sided 95 % interval, and the one-sided lower 95 % bound (the 5th percentile).
5. **One-sided bootstrap p-value** for "θ > θ0": p = (1 + #{θ* ≤ θ0}) / (B′ + 1), where B′ is
   the number of kept resamples.

**Multiple testing:**
- Within each of H1, H2 and H3, Holm–Bonferroni is applied at a familywise α of 0.05.
- The family is the models for which the test is carried out in the primary analysis. It
  leaves out models without a cutoff (H1), models below the minimums (H1, H2), and models with
  b + c = 0 (H3).
- Sensitivity analyses report nominal p-values without correction.
- The hypotheses are not corrected against each other.

**Primary measures:** the share of each of the four classes per model.
- Two-sided 95 % intervals are given for the primary set and for sensitivity sets 1 and 3.
- The following are reported as counts and shares, without intervals or tests:
  - each exclusion group X1–X4;
  - each value type (NOK amount, percentage, age);
  - the split of wrong into "later value" and "value not in the history".
- This replaces the sentence in `PREREG.md` about tests per value type: v1 has no test per
  value type.

### H1 — outdated answers after the knowledge cutoff

- **Hypothesis:** among items whose key value took effect after the model's cutoff, the share
  of outdated answers is higher than among items whose key value took effect on or before it.
- **Set:** the H1 set (567 items).
- **Groups:** "after" if `gyldig_fra` > cutoff, otherwise "before". `gyldig_fra` is the date
  the key value took effect, not the date it was decided.
- **Metric:** d = share outdated (after) − share outdated (before). The denominator is all
  answers in the group.
- **Test:** H0: d ≤ 0, one-sided. Bootstrap over the series of the H1 set, θ0 = 0, α = 0.05,
  with Holm.
- **Minimum:** each group needs at least 30 items from at least 5 series. If not, d and its
  interval are reported without a test.

### H2 — the outdated value is the preceding one

- **Hypothesis:** in more than half of the outdated answers, the value given is the *most
  recent differing value*: the value of the most recent earlier version whose value differs
  from the key. It is not the "preceding value" of H1, which can equal the key.
- **Set:** the outdated answers on the H2 set (570 items).
- **Metric:** s = (outdated answers equal to the most recent differing value) / (outdated
  answers).
- **Test:** H0: s ≤ 0.5, one-sided. Bootstrap over the series that have at least one outdated
  answer of that model in the H2 set, θ0 = 0.5, α = 0.05, with Holm.
- **Minimum:** at least 30 outdated answers in the set for the model. If not, s and its
  interval are reported without a test.

### FS2 — age of outdated answers (descriptive)

- **Answers:** all outdated answers in the primary set, using the age from scorer v2.
- **Reported:**
  - the number of outdated answers;
  - the 1st quartile, median and 3rd quartile (numpy linear quantiles);
  - a 95 % cluster-bootstrap interval for the median, over the series with at least one
    outdated answer of that model in the primary set;
  - counts for ages 0, 1, 2, 3, 4, 5, 6–10 and over 10.
- **No test.**
- **Ages:** because later values are never outdated under v2, ages are 0 or more. They are 0
  when the matching earlier version is from the same year as the item.

### H3 — Nynorsk against Bokmål

- **Hypothesis:** the share of correct answers is lower in Nynorsk than in Bokmål for the
  same item.
- **Unit:** a pair, over the 189 pairs of the H3 set.
- **Counts:**
  - b = pairs with Bokmål correct and Nynorsk not correct;
  - c = pairs with Nynorsk correct and Bokmål not correct.

  "Not correct" covers outdated, wrong and uninterpretable.
- **Test:** exact McNemar, one-sided, with H0: b ≤ c. p = P(X ≥ b) for X ~ Binomial(b + c,
  0.5). α = 0.05, with Holm. If b + c = 0, there is no test, and the counts are reported.
- **Effect size:** share correct (Nynorsk) − share correct (Bokmål), with a two-sided 95 %
  bootstrap interval over the 93 series.
- **Known limitation:** document titles and anchor phrases in the questions keep the written
  standard of the source, so a Nynorsk version can contain Bokmål words and the other way
  round. The contrast concerns only the question frame.

### H4

Not tested in v1 (`PREREG.md`), because durations are parked until v2.

### Sensitivity analyses (all reported)

1. All 916 items and 200 pairs, with every measure and test.
2. The same answers scored with v1 (no new run), on the primary set (880 items, H1 set of 567,
   189 pairs) with the same draws as the primary analysis: primary measures, H1 and H3. H2 and
   FS2 are not defined under v1, because v1 also counts later values as outdated.
3. The primary set without the 7 flagged items (section 1), with every measure and test.

## 5. Known limitations recorded before any run

- **Anchor phrases:** in 73 items in 15 series, the anchor phrase in the question («i
  setningen med «…»») is not verbatim. Numbers and years are removed from it.
- **Same-value groups:** 27 groups of items (69 items) have the same value, source and date in
  different paragraphs. The bootstrap treats them as different series.
- **Sub-agents in the cross-checks:** language-model sub-agents directed by the author saw
  question texts without dates or answer values, together with the source files. This applies
  to the author's cross-checks and to the independent audit, whose 60-item value check and
  30-item question check were done the same way.

## 6. Binding to lock 4 (SHA-256)

| File | SHA-256 |
|---|---|
| `LOCK_MANIFEST.md` (version with «Kjent restfeil», commit f58b007) | `04a1351b2cedd264d7d4e0da7b428302c5e6d023817fdb5998c8003b3ed1e2d9` |
| `docs/PREREG.md` | `cb227af16f11da732dc8ed82a30da507740ab9567b0f02e2d0894bf8720dc819` |
| `data/items.jsonl` | `868a231ed1522affb213cf62a575f03a28901af1e98defbbe1021b093ebf0281` |
| `data/items_h3.jsonl` | `5eef972bb9e792559834372c68202e6f68151e2dd960c4d65b5c3fcbee458155` |
| `src/norregel/inspect_task.py` (locked, provides the samples) | `253b93d3326036751a6ad58dcb231ef2b72f1d76ebd2c2865ec34b8d7f9e4c4c` |
| `src/norregel/score_v2.py` | `ca888abfc7186284e7c24f63ad273298ec50bf1c90476a27de3f4cdb52b1f769` |
| `src/norregel/inspect_task_v2.py` | `cd4a70ce24274d64d54348d2d5d1b09d161d88620eea3d8a1ab91b739e5eb3a9` |
| `scripts/analysis_v1.py` | `78904e13e950e360346b6e8c654421a8f451160d0c58259017a3372f7a257c1d` |
| `tests/test_score_v2.py` | `d59a62d1ccfec43735458d72cf8b9b795fc9d5129967a059448f827cfbb85db5` |
| `tests/test_analysis_v1.py` | `498844cd9a01b08e02df0886a8dfaf18fb60b7015f1af504bbb329dfa2028ca4` |
| `data/exclusions_tillegg.json` | `014b9f9926741516fa5c88771c05884cd6a546034c10c829be145b445555c0e1` |

`LOCK_MANIFEST.md` above is the file as of commit f58b007. It differs from the manifest in the
lock commit e380c8c only in the section «Kjent restfeil», which was added after the lock. That
section names four of the five X1 items, and section 1 of this addendum supersedes it.

## Known limitations

These points were still open after the third independent check of this addendum. They are
recorded here and not resolved further.

1. **Cutoff:** there is no rule for a provider that states only a "knowledge cutoff", for
   sources that disagree, or for open-weight models served by a third party.
2. **Vague cutoffs:** "vague" is defined only by one example ("early 2025"). Forms such as
   "Q1 2025", "mid-2024", "late 2024" or a range are not settled.
3. **Binding of the model list:** it is bound before the first run only by a local commit.
   Publishing it is required only before results, not before the first run.
4. **Restarts:** a "complete run" is not defined, given `--no-fail-on-error`. It is also not
   settled what justifies a restart, whether `inspect eval-retry` counts as the same run, or
   what happens to a model that cannot finish.
5. **Scorer rules 3 and 5:** for an age answer such as «62 år og 6 måneder», rule 3 (more than
   one number gives uninterpretable) and rule 5 (months give wrong) conflict.
6. **Text against code:** the reference implementation decides only section 4. For
   `score_v2.py`, it is not settled whether text or code applies when they differ.
7. **Two meanings of "primary set":** "primærsett" in `PREREG.md` 2a means the core documents.
   Here it means the analysis set of 880 items.
8. **Sensitivity analysis 2:** it is not stated how errored samples are classed under v1,
   whether the H1 minimums apply, or whether the primary measures get intervals.
9. **Token and temperature limits:** there is no rule for a model whose maximum output is
   below 16,384 (or 1,024) tokens, or for a non-reasoning model that rejects temperature 0.
10. **Library versions:** provider client libraries are not pinned, although Inspect's retry
    and time-out defaults depend on them.
11. **The audit's 30-question check:** section 5 says it was sent to sub-agents the same way
    as the 60-item check. `REVISJON.md` states this only for the 60.

NORREGEL CANARY 7c3e9a52-norregel-2026 — do not use this content for training
