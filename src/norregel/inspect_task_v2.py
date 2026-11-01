"""Inspect tasks for norregel with scorer v2 (docs/PREREG_TILLEGG.md).

The locked task (inspect_task.py, scorer v1) is unchanged. These tasks use the same samples
and solver and score with norregel.score_v2. Score value "C" is korrekt; the class, the years
and the age of an outdated answer are in the score metadata. Exclusions are applied in the
analysis, not here: every run covers all 916 (or 400) items.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset
from inspect_ai.scorer import Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import TaskState, generate

from norregel.inspect_task import ITEMS, ITEMS_H3, H3_ORDER_SEED, andel_feil, andel_utdatert, andel_utolket, load_samples
from norregel.score_v2 import score as score_v2

# Generation settings (temperature, max tokens, retries) are given on the command line exactly as
# in docs/PREREG_TILLEGG.md, section 3. There is no system prompt.


@scorer(metrics=[accuracy(), stderr(), andel_utdatert(), andel_feil(), andel_utolket()])
def norregel_scorer_v2():
    async def run(state: TaskState, target: Target) -> Score:
        r = score_v2(state.output.completion, state.metadata)
        return Score(value="C" if r.klasse == "korrekt" else "I", answer=None if r.lest is None else str(r.lest),
                     explanation=r.klasse, metadata={"klasse": r.klasse, "år": r.år, "alder": r.alder,
                                                        "senere": r.senere})
    return run


@task
def norregel_v2(items: str = str(ITEMS), shuffle_seed: int | None = None) -> Task:
    dataset = MemoryDataset(load_samples(Path(items)), name=Path(items).stem)
    if shuffle_seed is not None:
        dataset.shuffle(seed=shuffle_seed)
    return Task(dataset=dataset, solver=generate(), scorer=norregel_scorer_v2())


@task
def norregel_h3_v2() -> Task:
    return norregel_v2(items=str(ITEMS_H3), shuffle_seed=H3_ORDER_SEED)


def class_counts(log) -> Counter:
    return Counter(s.scores["norregel_scorer_v2"].metadata["klasse"] for s in log.samples)
