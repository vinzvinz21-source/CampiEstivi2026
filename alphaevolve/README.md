# AlphaEvolve (Claude edition)

A minimal, self-contained reimplementation of the core loop behind DeepMind's
[AlphaEvolve](https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/),
using the Claude API instead of Gemini. It evolves a Python program against a
metric you define, by repeatedly:

1. Sampling a parent program from an island-based population (plus a few
   "inspiration" programs from other islands, for diversity).
2. Asking Claude to propose a small, targeted improvement as one or more
   `SEARCH/REPLACE` diff blocks.
3. Applying the diff to produce a child program.
4. Evaluating the child in an isolated subprocess against your evaluator.
5. Inserting the child back into the population, keeping the best performers.

This is a standalone tool, unrelated to the rest of this repository.

## Install

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## Quick start

Run the bundled example, which evolves a random-search heuristic to better
minimize a non-convex 2D function:

```bash
python -m alphaevolve.cli \
  examples/function_minimization/initial_program.py \
  examples/function_minimization/evaluator.py \
  --config configs/example.yaml \
  --task "Improve run_search() so it finds a lower value of target_function with the same evaluation budget." \
  --iterations 30 \
  --output out/function_minimization \
  -v
```

The best program found is written to `out/function_minimization/best_program.py`,
and the full population to `out/function_minimization/database.json`.

## Writing your own problem

You need two files:

- **`initial_program.py`** — a seed program. If you only want the LLM to
  touch part of the file, wrap that part in:

  ```python
  # EVOLVE-BLOCK-START
  ...
  # EVOLVE-BLOCK-END
  ```

- **`evaluator.py`** — exposes `evaluate(program_path: str) -> dict`. It is
  run in a fresh subprocess (with a timeout) against every candidate
  program, and must return a JSON-serializable dict of metrics. Include a
  `combined_score` key (higher is better) to control ranking directly;
  otherwise the average of all numeric values is used.

Then point the CLI at your files and adjust `configs/example.yaml` (model,
population size, number of islands, iterations, timeout, etc.) as needed.

## Package layout

| File | Responsibility |
|---|---|
| `config.py` | YAML-backed config dataclasses |
| `diff.py` | Parses/applies `SEARCH/REPLACE` diff blocks |
| `database.py` | Island-based population of evolved programs |
| `prompt.py` | Builds the prompt sent to Claude |
| `llm.py` | Anthropic API client wrapper |
| `evaluator.py` | Runs the user evaluator in a sandboxed subprocess |
| `controller.py` | The evolution loop and checkpointing |
| `cli.py` | Command-line entry point |

## Tests

Unit tests cover diff parsing/application and the population database (no
API calls needed):

```bash
pip install pytest
pytest tests/
```
