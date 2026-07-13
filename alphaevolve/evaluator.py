from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

_RESULT_MARKER = "__ALPHAEVOLVE_RESULT__"

_RUNNER_TEMPLATE = """
import importlib.util
import json


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


evaluator_module = _load_module("_alphaevolve_evaluator", {evaluator_path!r})
result = evaluator_module.evaluate({program_path!r})
print({marker!r} + json.dumps(result))
"""


def evaluate_program(code: str, evaluator_path: str, timeout: float, work_dir: str) -> dict:
    """Run the user-supplied evaluator against `code` in an isolated subprocess.

    The evaluator module must expose `evaluate(program_path: str) -> dict`,
    where the returned dict contains numeric metrics and, ideally, a
    `combined_score` key (higher is better) used to rank programs.
    """
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)

    program_path = None
    runner_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", dir=work, delete=False) as f:
            f.write(code)
            program_path = f.name

        with tempfile.NamedTemporaryFile("w", suffix=".py", dir=work, delete=False) as f:
            f.write(
                _RUNNER_TEMPLATE.format(
                    evaluator_path=str(Path(evaluator_path).resolve()),
                    program_path=program_path,
                    marker=_RESULT_MARKER,
                )
            )
            runner_path = f.name

        try:
            proc = subprocess.run(
                [sys.executable, runner_path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"error": f"timeout after {timeout}s", "combined_score": float("-inf")}

        if proc.returncode != 0:
            return {"error": proc.stderr[-2000:], "combined_score": float("-inf")}

        for line in proc.stdout.splitlines():
            if line.startswith(_RESULT_MARKER):
                try:
                    result = json.loads(line[len(_RESULT_MARKER) :])
                except json.JSONDecodeError:
                    break
                if "combined_score" not in result:
                    numeric = [v for v in result.values() if isinstance(v, (int, float))]
                    result["combined_score"] = sum(numeric) / len(numeric) if numeric else float("-inf")
                return result

        return {"error": "evaluator did not return a result", "combined_score": float("-inf")}
    finally:
        for p in (program_path, runner_path):
            if p:
                Path(p).unlink(missing_ok=True)
