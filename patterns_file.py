"""Reader for multi-pattern files.

File format:
  - One pattern per line.
  - Lines starting with '#' are comments.
  - Blank lines are ignored.
  - Leading/trailing whitespace is stripped.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from validators import ValidationError, validate_pattern


def read_patterns(path: str) -> list[str]:
    """Read and validate all patterns from a file.

    Raises ValidationError on any malformed pattern or unreadable file.
    """
    p = Path(path)
    if not p.exists():
        raise ValidationError(f"Patterns file not found: {path}")
    if not p.is_file():
        raise ValidationError(f"Not a file: {path}")

    try:
        raw_lines = p.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValidationError(f"Cannot read patterns file: {exc}")

    patterns: list[str] = []
    for lineno, line in enumerate(raw_lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            patterns.append(validate_pattern(stripped))
        except ValidationError as exc:
            raise ValidationError(
                f"{path}:{lineno}: {exc}"
            ) from exc

    if not patterns:
        raise ValidationError(f"No valid patterns found in {path}.")

    return patterns