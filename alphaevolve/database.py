from __future__ import annotations

import dataclasses
import itertools
import json
import random
import time
from pathlib import Path
from typing import Any


@dataclasses.dataclass
class Program:
    id: str
    code: str
    scores: dict[str, float]
    metric: float
    generation: int
    parent_id: str | None
    island: int
    created_at: float = dataclasses.field(default_factory=time.time)
    metadata: dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Program":
        return Program(**d)


class ProgramDatabase:
    """Island-based population of evolved programs, MAP-Elites-inspired.

    Programs are split across `num_islands` independent sub-populations that
    evolve semi-independently (each capped at `population_size`, sorted best
    first) with periodic migration between them. This keeps a few strong
    lineages from prematurely dominating the whole population.
    """

    def __init__(self, num_islands: int = 3, population_size: int = 40):
        self.num_islands = num_islands
        self.population_size = population_size
        self._islands: list[list[Program]] = [[] for _ in range(num_islands)]
        self._by_id: dict[str, Program] = {}
        self._id_counter = itertools.count()
        self.best_program: Program | None = None

    def _next_id(self) -> str:
        return f"prog_{next(self._id_counter):06d}"

    def add(
        self,
        code: str,
        scores: dict[str, float],
        generation: int,
        parent_id: str | None,
        island: int,
        metadata: dict[str, Any] | None = None,
    ) -> Program:
        numeric_scores = {k: v for k, v in scores.items() if isinstance(v, (int, float))}
        metric = numeric_scores.get(
            "combined_score",
            sum(numeric_scores.values()) / max(len(numeric_scores), 1) if numeric_scores else float("-inf"),
        )
        program = Program(
            id=self._next_id(),
            code=code,
            scores=scores,
            metric=metric,
            generation=generation,
            parent_id=parent_id,
            island=island % self.num_islands,
            metadata=metadata or {},
        )
        self._by_id[program.id] = program

        pop = self._islands[program.island]
        pop.append(program)
        pop.sort(key=lambda p: p.metric, reverse=True)
        if len(pop) > self.population_size:
            for removed in pop[self.population_size :]:
                self._by_id.pop(removed.id, None)
            del pop[self.population_size :]

        if self.best_program is None or program.metric > self.best_program.metric:
            self.best_program = program
        return program

    def sample_parent(self, island: int) -> Program | None:
        """Sample a parent biased towards the fitter half of the island."""
        pop = self._islands[island % self.num_islands]
        if not pop:
            return None
        k = max(1, len(pop) // 2)
        return random.choice(pop[:k])

    def sample_inspirations(self, island: int, n: int) -> list[Program]:
        """Sample top programs from *other* islands, for cross-pollination."""
        island = island % self.num_islands
        others = [p for i, pop in enumerate(self._islands) if i != island for p in pop[:3]]
        random.shuffle(others)
        return others[:n]

    def migrate(self, rate: float = 0.1) -> None:
        """Copy a fraction of each island's best programs into the next island."""
        if self.num_islands < 2:
            return
        for i, pop in enumerate(self._islands):
            if not pop:
                continue
            n_migrants = max(1, int(len(pop) * rate))
            migrants = pop[:n_migrants]
            target = self._islands[(i + 1) % self.num_islands]
            target.extend(migrants)
            target.sort(key=lambda p: p.metric, reverse=True)
            del target[self.population_size :]

    def all_programs(self) -> list[Program]:
        return list(self._by_id.values())

    def save(self, path: str | Path) -> None:
        data = {
            "num_islands": self.num_islands,
            "population_size": self.population_size,
            "islands": [[p.to_dict() for p in pop] for pop in self._islands],
            "best_program_id": self.best_program.id if self.best_program else None,
        }
        Path(path).write_text(json.dumps(data, indent=2))

    @staticmethod
    def load(path: str | Path) -> "ProgramDatabase":
        data = json.loads(Path(path).read_text())
        db = ProgramDatabase(data["num_islands"], data["population_size"])
        max_id = -1
        for i, pop in enumerate(data["islands"]):
            for pd in pop:
                program = Program.from_dict(pd)
                db._islands[i].append(program)
                db._by_id[program.id] = program
                max_id = max(max_id, int(program.id.split("_")[1]))
        db._id_counter = itertools.count(max_id + 1)
        if data.get("best_program_id"):
            db.best_program = db._by_id.get(data["best_program_id"])
        return db
