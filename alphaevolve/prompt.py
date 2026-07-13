from __future__ import annotations

from .database import Program

DIFF_INSTRUCTIONS = """
Propose ONE targeted improvement to the program above by outputting one or
more SEARCH/REPLACE blocks in exactly this format:

<<<<<<< SEARCH
<exact lines to find, copied verbatim from the program>
=======
<the new lines to replace them with>
>>>>>>> REPLACE

Rules:
- The SEARCH text must match the program exactly (including whitespace) and
  must be unique — it may appear only once in the program.
- Keep each block focused and minimal; do not rewrite the whole program.
- You may emit multiple SEARCH/REPLACE blocks if needed.
- If the program has EVOLVE-BLOCK-START / EVOLVE-BLOCK-END markers, only
  modify code between them.
- You may add at most one short line of rationale before the blocks; do not
  add any explanation after them.
"""


def build_prompt(
    task_description: str,
    parent: Program,
    inspirations: list[Program],
    metric_names: list[str],
) -> str:
    scores_str = ", ".join(f"{k}={v:.4f}" for k, v in parent.scores.items() if isinstance(v, (int, float)))
    parts = [
        f"# Task\n{task_description}\n",
        f"# Current program (generation {parent.generation}, id={parent.id})\n"
        f"Scores: {scores_str}\n\n```python\n{parent.code}\n```\n",
    ]
    if inspirations:
        parts.append(
            "# Other high-performing variants for inspiration "
            "(reuse ideas, do not copy verbatim)\n"
        )
        for insp in inspirations:
            insp_scores = ", ".join(
                f"{k}={v:.4f}" for k, v in insp.scores.items() if isinstance(v, (int, float))
            )
            parts.append(f"## Variant {insp.id} (scores: {insp_scores})\n```python\n{insp.code}\n```\n")
    parts.append(f"# Goal\nImprove these metrics: {', '.join(metric_names)}. Higher is better.\n")
    parts.append(DIFF_INSTRUCTIONS)
    return "\n".join(parts)
