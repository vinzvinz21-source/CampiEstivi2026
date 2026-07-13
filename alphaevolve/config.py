from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import yaml


@dataclasses.dataclass
class LLMConfig:
    model: str = "claude-sonnet-5"
    temperature: float = 0.8
    max_tokens: int = 8192
    api_key_env: str = "ANTHROPIC_API_KEY"


@dataclasses.dataclass
class DatabaseConfig:
    num_islands: int = 3
    population_size: int = 40
    migration_interval: int = 20
    migration_rate: float = 0.1
    num_inspirations: int = 3


@dataclasses.dataclass
class EvaluatorConfig:
    timeout_seconds: float = 30.0


@dataclasses.dataclass
class EvolutionConfig:
    max_iterations: int = 100
    checkpoint_interval: int = 10
    max_diff_apply_retries: int = 3


@dataclasses.dataclass
class Config:
    llm: LLMConfig = dataclasses.field(default_factory=LLMConfig)
    database: DatabaseConfig = dataclasses.field(default_factory=DatabaseConfig)
    evaluator: EvaluatorConfig = dataclasses.field(default_factory=EvaluatorConfig)
    evolution: EvolutionConfig = dataclasses.field(default_factory=EvolutionConfig)
    system_prompt: str = (
        "You are an expert programmer participating in an evolutionary coding "
        "process. You will be shown a program and its performance metrics, and "
        "must propose a small, targeted improvement using SEARCH/REPLACE diff "
        "blocks."
    )

    @staticmethod
    def from_yaml(path: str | Path) -> "Config":
        data: dict[str, Any] = yaml.safe_load(Path(path).read_text()) or {}
        return Config(
            llm=LLMConfig(**data.get("llm", {})),
            database=DatabaseConfig(**data.get("database", {})),
            evaluator=EvaluatorConfig(**data.get("evaluator", {})),
            evolution=EvolutionConfig(**data.get("evolution", {})),
            system_prompt=data.get("system_prompt", Config.system_prompt),
        )
