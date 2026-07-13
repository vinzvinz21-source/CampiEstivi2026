import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")

EXAMPLE_DIR = Path(__file__).parent.parent / "examples" / "wellbeing_outcomes"
sys.path.insert(0, str(EXAMPLE_DIR))

from evaluator import _r2  # noqa: E402
from alphaevolve.evaluator import evaluate_program  # noqa: E402


def test_r2_perfect_prediction_is_one():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert _r2(y, y) == pytest.approx(1.0)


def test_r2_mean_prediction_is_zero():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    pred = np.full_like(y, y.mean())
    assert _r2(y, pred) == pytest.approx(0.0)


def test_seed_program_beats_trivial_baseline(tmp_path):
    code = (EXAMPLE_DIR / "initial_program.py").read_text()
    result = evaluate_program(
        code,
        str(EXAMPLE_DIR / "evaluator.py"),
        timeout=15,
        work_dir=str(tmp_path),
    )
    assert "error" not in result
    # Ridge on pre_score + program + session params should explain most of
    # the variance in the synthetic sample and generalize reasonably well.
    assert result["mean_r2"] > 0.5
    assert result["combined_score"] > 0.3


def test_evaluator_reports_missing_function(tmp_path):
    bad_code = "def not_the_right_name():\n    return None\n"
    result = evaluate_program(
        bad_code,
        str(EXAMPLE_DIR / "evaluator.py"),
        timeout=15,
        work_dir=str(tmp_path),
    )
    assert result["combined_score"] == -1000.0
    assert "missing build_and_predict" in result["error"]
