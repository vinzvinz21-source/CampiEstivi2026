"""Seed program for the function-minimization example.

The evaluator calls run_search() and scores it on how close it gets to the
global minimum of a non-convex 2D function, within a fixed evaluation budget.
"""
import math
import random


def target_function(x: float, y: float) -> float:
    # Non-convex function with several local minima; global min near (2, -1).
    return (
        (x ** 2 + y ** 2) / 10
        - 2 * math.exp(-((x - 2) ** 2 + (y + 1) ** 2))
        - 1.5 * math.exp(-((x + 2) ** 2 + (y - 1) ** 2))
    )


# EVOLVE-BLOCK-START
def run_search(budget: int = 200):
    """Return the best (x, y) found within `budget` function evaluations."""
    best_point = (0.0, 0.0)
    best_value = target_function(*best_point)
    for _ in range(budget):
        x = random.uniform(-5, 5)
        y = random.uniform(-5, 5)
        value = target_function(x, y)
        if value < best_value:
            best_value = value
            best_point = (x, y)
    return best_point, best_value
# EVOLVE-BLOCK-END


if __name__ == "__main__":
    point, value = run_search()
    print(point, value)
