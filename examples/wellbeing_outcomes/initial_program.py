"""Seed program for the wellbeing-outcome-prediction example.

Baseline: ridge regression on pre_score, session parameters, and a one-hot
encoding of `program`, predicting post_score directly.
"""
import numpy as np
import pandas as pd


# EVOLVE-BLOCK-START
def build_and_predict(train_df: pd.DataFrame, test_df: pd.DataFrame):
    """Fit on train_df and return predicted post_score for each row of test_df."""

    def design_matrix(df: pd.DataFrame, program_categories: list[str]) -> np.ndarray:
        numeric_cols = [
            c
            for c in df.columns
            if c not in ("participant_id", "program", "post_score")
            and pd.api.types.is_numeric_dtype(df[c])
        ]
        blocks = [df[numeric_cols].to_numpy(dtype=float)]
        for cat in program_categories:
            blocks.append((df["program"] == cat).to_numpy(dtype=float).reshape(-1, 1))
        blocks.append(np.ones((len(df), 1)))  # intercept
        return np.hstack(blocks)

    program_categories = sorted(train_df["program"].unique())
    X_train = design_matrix(train_df, program_categories)
    y_train = train_df["post_score"].to_numpy(dtype=float)

    ridge_lambda = 1.0
    XtX = X_train.T @ X_train + ridge_lambda * np.eye(X_train.shape[1])
    weights = np.linalg.solve(XtX, X_train.T @ y_train)

    X_test = design_matrix(test_df, program_categories)
    return X_test @ weights
# EVOLVE-BLOCK-END
