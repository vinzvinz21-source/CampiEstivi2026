import pytest

from alphaevolve.diff import DiffError, apply_diff, parse_diff_blocks


def test_parse_single_block():
    text = """
Some rationale.

<<<<<<< SEARCH
x = 1
=======
x = 2
>>>>>>> REPLACE
"""
    assert parse_diff_blocks(text) == [("x = 1", "x = 2")]


def test_parse_multiple_blocks():
    text = """
<<<<<<< SEARCH
a = 1
=======
a = 2
>>>>>>> REPLACE

<<<<<<< SEARCH
b = 1
=======
b = 2
>>>>>>> REPLACE
"""
    assert parse_diff_blocks(text) == [("a = 1", "a = 2"), ("b = 1", "b = 2")]


def test_parse_no_blocks_raises():
    with pytest.raises(DiffError):
        parse_diff_blocks("no diff here")


def test_apply_diff_replaces_unique_match():
    original = "def f():\n    return 1\n"
    result = apply_diff(original, [("return 1", "return 2")])
    assert result == "def f():\n    return 2\n"


def test_apply_diff_missing_search_raises():
    with pytest.raises(DiffError):
        apply_diff("abc", [("xyz", "123")])


def test_apply_diff_ambiguous_match_raises():
    with pytest.raises(DiffError):
        apply_diff("a\na\n", [("a", "b")])


def test_apply_diff_sequential_blocks():
    original = "x = 1\ny = 2\n"
    result = apply_diff(original, [("x = 1", "x = 10"), ("y = 2", "y = 20")])
    assert result == "x = 10\ny = 20\n"
