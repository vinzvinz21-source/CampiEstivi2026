from __future__ import annotations

import re

_BLOCK_RE = re.compile(
    r"<{5,}\s*SEARCH\s*\n(.*?)\n={5,}\s*\n(.*?)\n>{5,}\s*REPLACE",
    re.DOTALL,
)

EVOLVE_BLOCK_START = "# EVOLVE-BLOCK-START"
EVOLVE_BLOCK_END = "# EVOLVE-BLOCK-END"


class DiffError(Exception):
    """Raised when an LLM response cannot be parsed into a diff, or a diff
    cannot be applied to the parent program."""


def parse_diff_blocks(text: str) -> list[tuple[str, str]]:
    """Extract (search, replace) pairs from an LLM response."""
    blocks = [(m.group(1), m.group(2)) for m in _BLOCK_RE.finditer(text)]
    if not blocks:
        raise DiffError("No SEARCH/REPLACE blocks found in LLM response")
    return blocks


def apply_diff(original: str, blocks: list[tuple[str, str]]) -> str:
    """Apply SEARCH/REPLACE blocks sequentially to `original`.

    Each search string must match exactly once; this keeps edits precise and
    forces the LLM to quote real code back at us, rather than silently
    rewriting the wrong location.
    """
    result = original
    for search, replace in blocks:
        count = result.count(search)
        if count == 0:
            raise DiffError(f"SEARCH block not found in program:\n{search[:200]}")
        if count > 1:
            raise DiffError(
                f"SEARCH block matches {count} locations, must be unique:\n{search[:200]}"
            )
        result = result.replace(search, replace, 1)
    return result


def extract_evolve_section(code: str) -> str:
    """Return the EVOLVE-BLOCK section of `code`, or the whole thing if absent."""
    start = code.find(EVOLVE_BLOCK_START)
    end = code.find(EVOLVE_BLOCK_END)
    if start == -1 or end == -1:
        return code
    return code[start : end + len(EVOLVE_BLOCK_END)]


def replace_evolve_section(code: str, new_section: str) -> str:
    """Replace the EVOLVE-BLOCK section of `code` with `new_section`."""
    start = code.find(EVOLVE_BLOCK_START)
    end = code.find(EVOLVE_BLOCK_END)
    if start == -1 or end == -1:
        return new_section
    return code[:start] + new_section + code[end + len(EVOLVE_BLOCK_END) :]
