"""Inspect task for norregel: one sample per year item in data/items.jsonl.

The scorer is norregel.score (deterministic, no model). Score value is "C" for korrekt and
"I" otherwise; the class (korrekt / utdatert / feil / utolket) and, for utdatert, the years
are in the score metadata. Do not run this against a model without approval.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import Metric, SampleScore, Score, Target, accuracy, metric, scorer, stderr
from inspect_ai.solver import TaskState, generate

from norregel.score import score as norregel_score

ITEMS = Path(__file__).resolve().parents[2] / "data" / "items.jsonl"
ITEMS_H3 = ITEMS.with_name("items_h3.jsonl")
H3_ORDER_SEED = 20261017  # PREREG_UTKAST.md, H3: sample order is shuffled with this seed


def load_samples(path: Path = ITEMS) -> list[Sample]:
    samples = []
    for line in path.open(encoding="utf-8"):
        item = json.loads(line)
        samples.append(Sample(id=item["id"], input=item["spørsmål"], target=str(item["fasitverdi"]),
                              metadata={k: v for k, v in item.items() if k not in ("spørsmål",)}))
    return samples


def _share(klasse: str) -> Metric:
    def m(scores: list[SampleScore]) -> float:
        n = len(scores)
        return sum(1 for s in scores if (s.score.metadata or {}).get("klasse") == klasse) / n if n else 0.0
    return m


@metric
def andel_utdatert() -> Metric:
    return _share("utdatert")


@metric
def andel_feil() -> Metric:
    return _share("feil")


@metric
def andel_utolket() -> Metric:
    return _share("utolket")


@scorer(metrics=[accuracy(), stderr(), andel_utdatert(), andel_feil(), andel_utolket()])
def norregel_scorer():
    async def run(state: TaskState, target: Target) -> Score:
        item = state.metadata
        r = norregel_score(state.output.completion, {**item, "type": item["type"]})
        return Score(value="C" if r.klasse == "korrekt" else "I", answer=None if r.lest is None else str(r.lest),
                     explanation=r.klasse, metadata={"klasse": r.klasse, "år": r.år, "enhet": r.enhet})
    return run


@task
def norregel(items: str = str(ITEMS), shuffle_seed: int | None = None) -> Task:
    """Each sample is its own conversation (no shared context between samples)."""
    dataset = MemoryDataset(load_samples(Path(items)), name=Path(items).stem)
    if shuffle_seed is not None:
        dataset.shuffle(seed=shuffle_seed)
    return Task(dataset=dataset, solver=generate(), scorer=norregel_scorer())


@task
def norregel_h3() -> Task:
    """H3 subset: 400 samples (200 pairs), each language version an independent sample,
    run on its own with the order shuffled by a fixed seed."""
    return norregel(items=str(ITEMS_H3), shuffle_seed=H3_ORDER_SEED)


def class_counts(log) -> Counter:
    return Counter(s.scores["norregel_scorer"].metadata["klasse"] for s in log.samples)
