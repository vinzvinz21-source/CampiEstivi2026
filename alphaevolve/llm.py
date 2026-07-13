from __future__ import annotations

import os

from .config import LLMConfig

try:
    import anthropic
except ImportError:  # pragma: no cover - exercised only when dependency missing
    anthropic = None


class LLMClient:
    """Thin wrapper around the Anthropic API used to generate diffs."""

    def __init__(self, config: LLMConfig):
        if anthropic is None:
            raise RuntimeError(
                "The 'anthropic' package is required. Install with: pip install anthropic"
            )
        api_key = os.environ.get(config.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Set the {config.api_key_env} environment variable with your Anthropic API key"
            )
        self.config = config
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
