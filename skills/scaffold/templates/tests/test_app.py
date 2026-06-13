"""Basic tests for the demo app — intentionally minimal."""
from app import summarise


def test_summarise_empty():
    assert summarise([]) == {"count": 0}


def test_summarise_rows():
    assert summarise([("a",), ("b",)]) == {"count": 2}
