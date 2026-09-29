"""Input validation helpers for NumForge."""

from __future__ import annotations

import os
import re
from typing import Optional

from config import PLACEHOLDER, SUPPORTED_FORMATS


# Allowed characters in a phone pattern: digits, placeholder, formatting,
# and character-class brackets.
_ALLOWED_PATTERN_RE = re.compile(r"^[0-9X+\-\s()\[\],]+$")


class ValidationError(Exception):
    """Raised when user input fails validation."""


def validate_pattern(pattern: str) -> str:
    """Validate a phone-number pattern.

    Supported syntax:
      - digits 0-9 .......... fixed digit
      - X ................... any digit 0-9
      - [0-5] ............... digit range
      - [02468] ............. digit set
      - [0,2,4,6,8] ......... digit set (comma-separated)
      - [0-3,7,9] ........... mixed ranges and digits
      - +, -, (, ), space ... kept as-is in output
    """
    if pattern is None:
        raise ValidationError("Pattern is empty.")

    cleaned = pattern.strip()
    if not cleaned:
        raise ValidationError("Pattern is empty.")

    if not _ALLOWED_PATTERN_RE.match(cleaned):
        raise ValidationError(
            "Pattern contains unsupported characters. "
            "Allowed: 0-9, 'X', '[...]', and '+ - ( ) space'."
        )

    # Must contain at least one unknown
    if PLACEHOLDER not in cleaned and "[" not in cleaned:
        raise ValidationError(
            "Pattern must contain at least one 'X' or '[...]' placeholder."
        )

    # Delegate full validation to the parser (checks brackets, ranges).
    from generator import parse_pattern  # local import to avoid cycles
    parse_pattern(cleaned)  # raises ValidationError on bad syntax

    return cleaned


def count_unknowns(pattern: str) -> int:
    """Return the total number of variable positions in the pattern."""
    from generator import parse_pattern, ChoiceToken
    tokens = parse_pattern(pattern)
    return sum(1 for t in tokens if isinstance(t, ChoiceToken))


def calculate_combinations(pattern: str) -> int:
    """Return the total number of combinations for a pattern."""
    from generator import parse_pattern, ChoiceToken
    tokens = parse_pattern(pattern)
    total = 1
    for t in tokens:
        if isinstance(t, ChoiceToken):
            total *= len(t.digits)
    return total


def validate_menu_choice(choice: str, min_value: int, max_value: int) -> int:
    """Validate a numeric menu choice within an inclusive range."""
    try:
        value = int(choice)
    except (TypeError, ValueError):
        raise ValidationError("Please enter a valid number.")
    if not min_value <= value <= max_value:
        raise ValidationError(
            f"Please enter a number between {min_value} and {max_value}."
        )
    return value


def validate_output_directory(path: str) -> str:
    """Ensure the given directory exists (creating it if needed) and is writable."""
    path = path.strip() or "."
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as exc:
        raise ValidationError(f"Cannot create directory '{path}': {exc}")

    if not os.path.isdir(path):
        raise ValidationError(f"'{path}' is not a directory.")
    if not os.access(path, os.W_OK):
        raise ValidationError(f"Directory '{path}' is not writable.")
    return path


def validate_filename(name: str, fmt: str = "txt") -> str:
    """Validate a candidate filename and enforce the correct extension."""
    name = name.strip()
    if not name:
        raise ValidationError("Filename cannot be empty.")
    if any(sep in name for sep in ("/", "\\")):
        raise ValidationError("Filename must not contain path separators.")
    invalid_chars = set('<>:"|?*')
    if any(ch in name for ch in invalid_chars):
        raise ValidationError("Filename contains invalid characters.")

    # Strip any known extension and reattach the correct one.
    base = name
    for ext in (".txt", ".csv", ".jsonl", ".gz"):
        if base.lower().endswith(ext):
            base = base[: -len(ext)]

    suffix = f".{fmt}"
    if fmt == "txt" and name.lower().endswith(".txt.gz"):
        return name  # already correct
    return base + suffix


def validate_format(fmt: str) -> str:
    """Validate an output format name."""
    fmt = fmt.strip().lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValidationError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}."
        )
    return fmt


def confirm_overwrite(path: str) -> bool:
    """Return True if it is safe to write to `path`."""
    if not os.path.exists(path):
        return True
    answer = input(f"File '{path}' already exists. Overwrite? [y/N]: ").strip().lower()
    return answer in ("y", "yes")