"""Evaluator for the wellbeing-outcome-prediction example.

Loads a CSV (path from the ALPHAEVOLVE_DATA_CSV env var, falling back to
the bundled synthetic sample) with columns:
    participant_id, program, pre_score, post_score
plus any further numeric covariates (e.g. session_duration_min,
session_frequency_per_week, age, group_size).

The candidate program must define:
    build_and_predict(train_df, test_df) -> array-like of predicted post_score

Scored via k-fold cross-validation: mean out-of-sample R^2 minus its
standard deviation across folds, so models that generalize consistently are
rewarded over models that overfit a single lucky split (a real risk with the
small sample sizes typical of community wellbeing programs).
"""
import importlib.util
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_DATA_PATH = Path(__file__).parent / "sample_data.csv"
N_FOLDS = 5
REQUIRED_COLUMNS = {"participant_id", "program", "pre_score", "post_score"}


def _load_data() -> pd.DataFrame:
    path = os.environ.get("ALPHAEVOLVE_DATA_CSV", str(DEFAULT_DATA_PATH))
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Dataset at {path} is missing required columns: {missing}")
    return df


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1.0 - ss_res / ss_tot


def evaluate(program_path: str) -> dict:
    spec = importlib.util.spec_from_file_location("candidate", program_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "build_and_predict"):
        return {"combined_score": -1000.0, "error": "missing build_and_predict()"}

    df = _load_data()
    n_folds = min(N_FOLDS, len(df))
    rng = np.random.RandomState(42)
    indices = rng.permutation(len(df))
    folds = np.array_split(indices, n_folds)

    fold_r2 = []
    start = time.time()
    try:
        for i in range(len(folds)):
            test_idx = folds[i]
            train_idx = np.concatenate([folds[j] for j in range(len(folds)) if j != i])
            train_df = df.iloc[train_idx].reset_index(drop=True)
            test_df = df.iloc[test_idx].reset_index(drop=True)

            preds = np.asarray(
                module.build_and_predict(train_df, test_df.drop(columns=["post_score"])),
                dtype=float,
            )
            if preds.shape[0] != len(test_df):
                return {"combined_score": -1000.0, "error": "prediction length mismatch"}
            fold_r2.append(_r2(test_df["post_score"].to_numpy(dtype=float), preds))
    except Exception as e:
        return {"combined_score": -1000.0, "error": str(e)}
    elapsed = time.time() - start

    mean_r2 = float(np.mean(fold_r2))
    std_r2 = float(np.std(fold_r2))
    return {
        "combined_score": mean_r2 - std_r2,
        "mean_r2": mean_r2,
        "std_r2": std_r2,
        "n_folds": len(folds),
        "elapsed_seconds": elapsed,
    }
