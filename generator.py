"""Memory-efficient combination generator for NumForge.

The engine is intentionally independent of the CLI. It exposes pure
iterators that yield one combination at a time so that arbitrarily
large outputs never need to be held in memory.

Pattern syntax (v1.1):
    - digits 0-9        fixed characters
    - X                 any digit 0-9
    - [0-5]             digit range
    - [02468]           digit set
    - [0,2,4,6,8]       digit set (commas ignored)
    - [0-3,7,9]         mixed
    - any other char    kept verbatim (formatting)
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import islice, product
from typing import Iterable, Iterator, Union

from config import PLACEHOLDER
from validators import ValidationError


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FixedToken:
    """A literal character that appears unchanged in every output."""

    char: str


@dataclass(frozen=True)
class ChoiceToken:
    """A position that expands to one of the digits in `digits`."""

    digits: str  # e.g. "0123456789", "02468", "012345"


Token = Union[FixedToken, ChoiceToken]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_ALL_DIGITS = "0123456789"


def _parse_bracket_content(content: str) -> str:
    """Parse the inside of a `[...]` class into a sorted digit string.

    Supported forms:
        "0-5"        -> "012345"
        "02468"      -> "02468"
        "0,2,4,6,8"  -> "02468"
        "0-3,7,9"    -> "0123789"
    """
    if not content:
        raise ValidationError("Empty character class '[]' in pattern.")

    result: set[str] = set()
    i = 0
    n = len(content)

    while i < n:
        ch = content[i]

        if ch == "," or ch.isspace():
            i += 1
            continue

        if not ch.isdigit():
            raise ValidationError(
                f"Invalid character '{ch}' inside '[...]'. Only digits, '-' and ',' allowed."
            )

        # Check for range "a-b"
        if i + 2 < n and content[i + 1] == "-" and content[i + 2].isdigit():
            start = int(ch)
            end = int(content[i + 2])
            if start > end:
                raise ValidationError(
                    f"Invalid range '{ch}-{content[i + 2]}' in pattern."
                )
            for d in range(start, end + 1):
                result.add(str(d))
            i += 3
            continue

        # Check for trailing '-' (error) like "0-"
        if i + 1 < n and content[i + 1] == "-":
            raise ValidationError(
                f"Incomplete range starting at '{ch}' in pattern."
            )

        result.add(ch)
        i += 1

    if not result:
        raise ValidationError("Empty character class '[]' in pattern.")

    return "".join(sorted(result))


def parse_pattern(pattern: str) -> list[Token]:
    """Parse a pattern string into a list of tokens.

    Raises ValidationError on malformed syntax.
    """
    tokens: list[Token] = []
    i = 0
    n = len(pattern)

    while i < n:
        ch = pattern[i]

        if ch == PLACEHOLDER:
            tokens.append(ChoiceToken(_ALL_DIGITS))
            i += 1
            continue

        if ch == "[":
            close = pattern.find("]", i + 1)
            if close == -1:
                raise ValidationError("Unclosed '[' in pattern.")
            content = pattern[i + 1: close]
            digits = _parse_bracket_content(content)
            tokens.append(ChoiceToken(digits))
            i = close + 1
            continue

        if ch == "]":
            raise ValidationError("Unexpected ']' in pattern (no matching '[').")

        tokens.append(FixedToken(ch))
        i += 1

    if not tokens:
        raise ValidationError("Pattern is empty.")

    return tokens


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def iter_combinations(pattern: str, start_index: int = 0) -> Iterator[str]:
    """Yield all combinations of `pattern`.

    If `start_index > 0`, the first `start_index` results are skipped
    efficiently via itertools.islice (useful for resume).

    The generator is lazy: only one combination is materialized at a time.
    """
    tokens = parse_pattern(pattern)

    choice_positions: list[int] = []
    choice_digits: list[str] = []
    template: list[str] = []

    for idx, token in enumerate(tokens):
        if isinstance(token, ChoiceToken):
            choice_positions.append(idx)
            choice_digits.append(token.digits)
            template.append("")  # placeholder slot
        else:
            template.append(token.char)

    # No variable positions? Yield the literal pattern once.
    if not choice_positions:
        if start_index == 0:
            yield "".join(template)
        return

    iterator = product(*choice_digits)
    if start_index > 0:
        iterator = islice(iterator, start_index, None)

    for combo in iterator:
        for pos, digit in zip(choice_positions, combo):
            template[pos] = digit
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