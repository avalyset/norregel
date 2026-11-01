"""Runnable example of the norregel v2 scorer on two synthetic items (examples/demo_items.jsonl).

The items are invented for this example and are not norregel items. Run from the repository root:

    PYTHONPATH=src python examples/demo.py
"""
import json
from collections import Counter
from pathlib import Path

from norregel import score_v2

ITEMS = Path(__file__).with_name("demo_items.jsonl")

# Synthetic model answers: (item id, completion)
ANSWERS = [
    ("demo-001", "Satsen var 303 kroner.\nSVAR: 303 kr"),   # the value in force on the date: correct
    ("demo-001", "SVAR: 202"),                             # an earlier value of the same series: outdated
    ("demo-001", "SVAR: 404"),                             # a later value: error (later value)
    ("demo-001", "Jeg vet ikke."),                         # no answer line: uninterpreted
    ("demo-002", "**Svar**: 6,25 %"),                      # an earlier value: outdated
    ("demo-002", "SVAR: 7,5 prosent"),                     # correct
]


def main() -> Counter:
    items = {i["id"]: i for i in (json.loads(l) for l in ITEMS.read_text(encoding="utf-8").splitlines() if l.strip())}
    classes = Counter()
    for item_id, completion in ANSWERS:
        r = score_v2.score(completion, items[item_id])
        classes[r.klasse] += 1
        print(f"{item_id}: {completion.splitlines()[-1]!r:<22} -> {r.klasse} (read {r.lest}, earlier years {r.år}, later years {r.senere})")
    print(dict(classes))
    return classes


if __name__ == "__main__":
    main()
