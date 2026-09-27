"""Memory-efficient combination generator for NumForge.

The engine is intentionally independent of the CLI. It exposes a single
generator that yields formatted strings one at a time, so arbitrarily
large outputs never need to be held in memory.
"""

from __future__ import annotations

from itertools import product
from typing import Iterable, Iterator

from config import PLACEHOLDER


def iter_combinations(pattern: str) -> Iterator[str]:
    """Yield all combinations of `pattern` with `PLACEHOLDER` replaced by 0-9.

    Uses `itertools.product` which is a lazy iterator: only one
    combination is materialized at a time.

    Example:
        >>> list(iter_combinations("12X"))
        ['120', '121', ..., '129']
    """
    unknown_indices = [i for i, ch in enumerate(pattern) if ch == PLACEHOLDER]

    if not unknown_indices:
        yield pattern
        return

    # Convert pattern to a mutable list for fast per-combination rebuilds.
    template = list(pattern)
    digits = "0123456789"

    for combo in product(digits, repeat=len(unknown_indices)):
        for idx, d in zip(unknown_indices, combo):
            template[idx] = d
        yield "".join(template)


def iter_chunks(iterator: Iterable[str], size: int) -> Iterator[list[str]]:
    """Yield lists of at most `size` items from `iterator`."""
    chunk: list[str] = []
    for item in iterator:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk