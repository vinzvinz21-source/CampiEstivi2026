"""Evaluator for the function-minimization example.

Loads the candidate program, runs its run_search(), and scores it: lower
target-function values are better, so the score is the negated value.
"""
import importlib.util
import time


def evaluate(program_path: str) -> dict:
    spec = importlib.util.spec_from_file_location("candidate", program_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    start = time.time()
    try:
        point, value = module.run_search()
    except Exception as e:
        return {"combined_score": -1000.0, "error": str(e)}
    elapsed = time.time() - start

    return {
        "combined_score": -value,
        "value": value,
        "point_x": point[0],
        "point_y": point[1],
        "elapsed_seconds": elapsed,
    }
