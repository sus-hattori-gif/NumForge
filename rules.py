"""Structural validation filter for NumForge.

This module only performs LOCAL checks (length and known prefixes).
It does NOT verify real numbers, does NOT query any service, and
does NOT contact any network.
"""

from __future__ import annotations

from typing import Iterator

from countries import Country


def filter_valid(
    iterator: Iterator[str],
    country: Country,
) -> Iterator[str]:
    """Yield only the combinations that pass the country's local rules.

    This is a lazy generator: it never materializes the full list.
    """
    rules = country.rules
    for number in iterator:
        if rules.is_valid(number):
            yield number


def estimate_valid_ratio(pattern: str, country: Country) -> float:
    """Return a rough estimate of the valid ratio.

    Only used for user-facing warnings; not exact. Samples the pattern
    space at a few points and computes a ratio.
    """
    # Quick heuristic: if no prefix check is configured, ratio is 1.0.
    if not country.rules.valid_prefixes:
        return 1.0

    # The pattern itself determines the prefix when it starts with digits.
    from generator import parse_pattern, ChoiceToken

    tokens = parse_pattern(pattern)
    fixed_prefix = ""
    for token in tokens:
        if isinstance(token, ChoiceToken):
            break
        fixed_prefix += token.char

    digits_only = "".join(ch for ch in fixed_prefix if ch.isdigit())
    if not digits_only:
        return 1.0

    # Count how many known prefixes share this prefix.
    matches = sum(1 for p in country.rules.valid_prefixes if p.startswith(digits_only))
    return 1.0 if matches > 0 else 0.0