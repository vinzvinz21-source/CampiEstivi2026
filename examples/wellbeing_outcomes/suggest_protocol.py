"""Decision-support utility: given an evolved model (best_program.py) and the
training data it was fit on, grid-searches over feasible protocol parameters
and reports which combination the model predicts will maximize the outcome.

This is exploratory decision support, not a validated clinical or
statistical conclusion -- treat suggestions as hypotheses to test, not facts.

Usage:
    python suggest_protocol.py <best_program.py> <train.csv> [options]
"""
import argparse
import importlib.util
import itertools

import numpy as np
import pandas as pd


def _load_model(path: str):
    spec = importlib.util.spec_from_file_location("evolved", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_and_predict


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", help="Path to the evolved best_program.py")
    parser.add_argument("train_csv", help="CSV the model should be fit on")
    parser.add_argument("--pre-score", type=float, default=50.0)
    parser.add_argument("--durations", type=int, nargs="+", default=[30, 45, 60, 90])
    parser.add_argument("--frequencies", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument(
        "--programs", nargs="+", default=["forest_therapy", "rhythm2recovery", "rhythm2school"]
    )
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    build_and_predict = _load_model(args.model_path)
    train_df = pd.read_csv(args.train_csv)

    candidates = [
        {
            "participant_id": "candidate",
            "program": program,
            "session_duration_min": duration,
            "session_frequency_per_week": frequency,
            "pre_score": args.pre_score,
        }
        for program, duration, frequency in itertools.product(
            args.programs, args.durations, args.frequencies
        )
    ]
    candidates_df = pd.DataFrame(candidates)
    predictions = np.asarray(build_and_predict(train_df, candidates_df), dtype=float)
    candidates_df["predicted_post_score"] = predictions
    candidates_df["predicted_delta"] = predictions - args.pre_score

    ranked = candidates_df.sort_values("predicted_delta", ascending=False)
    print(ranked.head(args.top).to_string(index=False))


if __name__ == "__main__":
    main()
