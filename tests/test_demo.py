"""Runs the README example (examples/demo.py) on its synthetic items and checks the classes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "examples"))
import demo  # noqa: E402


def test_demo():
    assert demo.main() == {"korrekt": 2, "utdatert": 2, "feil": 1, "utolket": 1}
