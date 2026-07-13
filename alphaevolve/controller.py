from __future__ import annotations

import logging
from pathlib import Path

from .config import Config
from .database import Program, ProgramDatabase
from .diff import DiffError, apply_diff, parse_diff_blocks
from .evaluator import evaluate_program
from .llm import LLMClient
from .prompt import build_prompt

log = logging.getLogger("alphaevolve")


class Controller:
    """Drives the AlphaEvolve-style loop: sample -> prompt -> generate diff ->
    apply -> evaluate -> insert into population, checkpointing periodically."""

    def __init__(
        self,
        config: Config,
        initial_program_path: str,
        evaluator_path: str,
        task_description: str,
        output_dir: str,
    ):
        self.config = config
        self.initial_program_path = initial_program_path
        self.evaluator_path = evaluator_path
        self.task_description = task_description
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db = ProgramDatabase(config.database.num_islands, config.database.population_size)
        self.llm = LLMClient(config.llm)

    def _eval(self, code: str) -> dict:
        return evaluate_program(
            code,
            self.evaluator_path,
            self.config.evaluator.timeout_seconds,
            str(self.output_dir / "_work"),
        )

    def run(self) -> Program:
        initial_code = Path(self.initial_program_path).read_text()
        scores = self._eval(initial_code)
        seed = self.db.add(initial_code, scores, generation=0, parent_id=None, island=0)
        log.info("seed program %s scores=%s", seed.id, scores)

        for iteration in range(1, self.config.evolution.max_iterations + 1):
            island = iteration % self.config.database.num_islands
            parent = self.db.sample_parent(island) or seed
            inspirations = self.db.sample_inspirations(island, self.config.database.num_inspirations)
            metric_names = [k for k in parent.scores if k != "error"]

            prompt = build_prompt(self.task_description, parent, inspirations, metric_names)

            child_code = None
            for attempt in range(1, self.config.evolution.max_diff_apply_retries + 1):
                try:
                    response = self.llm.generate(self.config.system_prompt, prompt)
                    blocks = parse_diff_blocks(response)
                    child_code = apply_diff(parent.code, blocks)
                    break
                except DiffError as e:
                    log.warning("iter %d attempt %d: %s", iteration, attempt, e)

            if child_code is None:
                log.warning("iter %d: failed to produce a valid diff, skipping", iteration)
                continue

            child_scores = self._eval(child_code)
            child = self.db.add(
                child_code,
                child_scores,
                generation=parent.generation + 1,
                parent_id=parent.id,
                island=island,
            )
            log.info(
                "iter %d: child %s (parent %s) scores=%s best=%.4f",
                iteration,
                child.id,
                parent.id,
                child_scores,
                self.db.best_program.metric,
            )

            if iteration % self.config.database.migration_interval == 0:
                self.db.migrate(self.config.database.migration_rate)

            if iteration % self.config.evolution.checkpoint_interval == 0:
                self._checkpoint(iteration)

        self._checkpoint(self.config.evolution.max_iterations, final=True)
        return self.db.best_program

    def _checkpoint(self, iteration: int, final: bool = False) -> None:
        self.db.save(self.output_dir / "database.json")
        best = self.db.best_program
        if best:
            (self.output_dir / "best_program.py").write_text(best.code)
            log.info(
                "%scheckpoint @ iter %d: best=%s metric=%.4f",
                "final " if final else "",
                iteration,
                best.id,
                best.metric,
            )
