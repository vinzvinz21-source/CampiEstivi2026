from __future__ import annotations

import argparse
import logging

from .config import Config
from .controller import Controller


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="alphaevolve",
        description="Evolve programs with Claude, AlphaEvolve-style.",
    )
    parser.add_argument("initial_program", help="Path to the seed program (.py)")
    parser.add_argument(
        "evaluator", help="Path to evaluator.py exposing evaluate(program_path) -> dict"
    )
    parser.add_argument("--config", default=None, help="Path to a YAML config file")
    parser.add_argument(
        "--task", default="Improve the program's metrics.", help="Task description for the LLM"
    )
    parser.add_argument("--output", default="alphaevolve_output", help="Output directory")
    parser.add_argument("--iterations", type=int, default=None, help="Override max_iterations")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = Config.from_yaml(args.config) if args.config else Config()
    if args.iterations is not None:
        config.evolution.max_iterations = args.iterations

    controller = Controller(config, args.initial_program, args.evaluator, args.task, args.output)
    best = controller.run()
    print(f"\nBest program: {best.id} (generation {best.generation})")
    print(f"Scores: {best.scores}")
    print(f"Saved to {args.output}/best_program.py")


if __name__ == "__main__":
    main()
