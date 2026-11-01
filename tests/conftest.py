"""The item files of norregel are closed and not in this repository. Tests that read them are skipped when
data/items.jsonl is absent; with the closed files in place they run as in the deposited version."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TRENGER_ITEMS = {"test_subclasses", "test_rejected", "test_duplicates", "test_missing", "test_normalised"}


def pytest_collection_modifyitems(config, items):
    if (ROOT / "data" / "items.jsonl").exists():
        return
    hopp = pytest.mark.skip(reason="needs the closed item files (data/items.jsonl), which are not public")
    for item in items:
        if item.name in TRENGER_ITEMS:
            item.add_marker(hopp)
