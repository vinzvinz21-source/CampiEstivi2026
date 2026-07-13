"""Generates SYNTHETIC placeholder data for the wellbeing-outcomes example.

This is not real data. Replace sample_data.csv with your own pre/post
survey export (same column names) before drawing any real conclusions.
Run: python generate_sample_data.py
"""
import numpy as np
import pandas as pd

rng = np.random.RandomState(0)
PROGRAMS = ["forest_therapy", "rhythm2recovery", "rhythm2school"]
PROGRAM_EFFECT = {"forest_therapy": 6.0, "rhythm2recovery": 8.0, "rhythm2school": 5.0}

N = 120
rows = []
for i in range(N):
    program = PROGRAMS[i % len(PROGRAMS)]
    duration = int(rng.choice([30, 45, 60, 90]))
    frequency = int(rng.choice([1, 2, 3]))
    pre_score = rng.normal(50, 10)
    effect = PROGRAM_EFFECT[program] * (duration / 60) * (frequency / 2)
    post_score = pre_score + effect + rng.normal(0, 5)
    rows.append(
        {
            "participant_id": f"P{i:04d}",
            "program": program,
            "session_duration_min": duration,
            "session_frequency_per_week": frequency,
            "pre_score": round(pre_score, 1),
            "post_score": round(post_score, 1),
        }
    )

pd.DataFrame(rows).to_csv("sample_data.csv", index=False)
print(f"Wrote {N} synthetic rows to sample_data.csv")
