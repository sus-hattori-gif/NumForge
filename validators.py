"""Input validation helpers for NumForge."""

from __future__ import annotations

import os
import re
from typing import Optional

from config import PLACEHOLDER


# Allowed characters in a phone pattern: digits, the placeholder, and common
# formatting characters (+, -, space, parentheses).
_ALLOWED_PATTERN_RE = re.compile(r"^[0-9X+\-\s()]+$")


class ValidationError(Exception):
    """Raised when user input fails validation."""


def validate_pattern(pattern: str) -> str:
    """Validate and normalize a phone-number pattern.

    Returns the cleaned pattern (spaces stripped only for counting, but
    formatting characters retained in output).
    """
    if pattern is None:
        raise ValidationError("Pattern is empty.")

    cleaned = pattern.strip()
    if not cleaned:
        raise ValidationError("Pattern is empty.")

    if not _ALLOWED_PATTERN_RE.match(cleaned):
        raise ValidationError(
            "Pattern contains unsupported characters. "
            "Allowed: digits 0-9, placeholder 'X', and '+ - ( ) space'."
        )

    if PLACEHOLDER not in cleaned:
        raise ValidationError(
            f"Pattern must contain at least one '{PLACEHOLDER}' placeholder."
        )

    return cleaned


def count_unknowns(pattern: str) -> int:
    """Return the number of unknown-digit placeholders in a pattern."""
    return pattern.count(PLACEHOLDER)


def calculate_combinations(pattern: str) -> int:
    """Return the total number of combinations for a pattern."""
    return 10 ** count_unknowns(pattern)


def validate_menu_choice(choice: str, min_value: int, max_value: int) -> int:
    """Validate a numeric menu choice within an inclusive range."""
    try:
        value = int(choice)
    except (TypeError, ValueError):
        raise ValidationError("Please enter a valid number.")
    if not min_value <= value <= max_value:
        raise ValidationError(f"Please enter a number between {min_value} and {max_value}.")
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


def validate_filename(name: str) -> str:
    """Validate a candidate filename (without path)."""
    name = name.strip()
    if not name:
        raise ValidationError("Filename cannot be empty.")
    if any(sep in name for sep in ("/", "\\")):
        raise ValidationError("Filename must not contain path separators.")
    invalid_chars = set('<>:"|?*')
    if any(ch in invalid_chars for ch in name):
        raise ValidationError("Filename contains invalid characters.")
    if not name.lower().endswith(".txt"):
        name += ".txt"
    return name


def confirm_overwrite(path: str) -> bool:
    """Return True if it is safe to write to `path`.

    Asks the user for explicit confirmation if the file already exists.
    """
    if not os.path.exists(path):
        return True
    answer = input(f"File '{path}' already exists. Overwrite? [y/N]: ").strip().lower()
    return answer in ("y", "yes")