"""NumForge — CLI entry point.

NumForge generates all possible numeric combinations matching a
user-defined phone-number pattern. It is a purely local tool: it never
performs network requests, never verifies real numbers, and never
interacts with any telecom or messaging service.
"""

from __future__ import annotations

import sys
from typing import Optional

from config import (
    CONFIRMATION_THRESHOLD,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_FILENAME,
    MAX_COMBINATIONS,
)
from countries import COUNTRIES, get_country_by_index
from generator import iter_combinations
from output import preview_in_terminal, print_summary, write_to_file
from validators import (
    ValidationError,
    calculate_combinations,
    count_unknowns,
    validate_filename,
    validate_menu_choice,
    validate_output_directory,
    validate_pattern,
)


BANNER = """================================
          NumForge
================================"""


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def prompt(message: str) -> str:
    """Read a line from stdin, trimming whitespace."""
    try:
        return input(message).strip()
    except EOFError:
        print("\nInput closed. Exiting.")
        sys.exit(0)


def pause() -> None:
    """Wait for the user to press Enter."""
    try:
        input("\nPress Enter to continue...")
    except EOFError:
        pass


# ---------------------------------------------------------------------------
# Menu screens
# ---------------------------------------------------------------------------

def choose_country() -> "object":
    """Display the country selection menu and return the chosen Country."""
    print()
    print("Select a country:")
    for idx, country in enumerate(COUNTRIES, start=1):
        print(f"  {idx}. {country.name} ({country.code})")

    while True:
        raw = prompt("Enter number: ")
        try:
            index = validate_menu_choice(raw, 1, len(COUNTRIES))
            return get_country_by_index(index)
        except ValidationError as exc:
            print(f"  [!] {exc}")


def choose_pattern(country) -> str:
    """Prompt the user to pick a predefined pattern or enter a custom one."""
    print()
    print(f"Available patterns for {country.name}:")
    for idx, pat in enumerate(country.patterns, start=1):
        print(f"  {idx}. {pat}")
    custom_idx = len(country.patterns) + 1
    print(f"  {custom_idx}. Enter a custom pattern")

    while True:
        raw = prompt("Enter number: ")
        try:
            choice = validate_menu_choice(raw, 1, custom_idx)
        except ValidationError as exc:
            print(f"  [!] {exc}")
            continue

        if choice == custom_idx:
            custom = prompt("Enter custom pattern (use 'X' for unknown digits): ")
            try:
                return validate_pattern(custom)
            except ValidationError as exc:
                print(f"  [!] {exc}")
                continue

        return country.patterns[choice - 1]


def show_settings() -> None:
    """Show configurable constants."""
    print()
    print("Current settings:")
    print(f"  Confirmation threshold : {CONFIRMATION_THRESHOLD:,} combinations")
    print(f"  Maximum combinations   : {MAX_COMBINATIONS:,}")
    print(f"  Placeholder character  : X")
    print()
    print("(Edit config.py to change these values.)")
    pause()


# ---------------------------------------------------------------------------
# Generation workflow
# ---------------------------------------------------------------------------

def confirm_large_generation(total: int) -> bool:
    """Ask the user to confirm generation if `total` is large."""
    if total <= CONFIRMATION_THRESHOLD:
        return True
    print()
    print(f"  [!] This will generate {total:,} combinations.")
    answer = prompt("  Continue? [y/N]: ").lower()
    return answer in ("y", "yes")


def choose_output_mode() -> str:
    """Return 'terminal' or 'file'."""
    print()
    print("Output options:")
    print("  1. Preview in terminal (first 50 results)")
    print("  2. Save all results to a file")
    while True:
        raw = prompt("Enter number: ")
        try:
            choice = validate_menu_choice(raw, 1, 2)
            return "terminal" if choice == 1 else "file"
        except ValidationError as exc:
            print(f"  [!] {exc}")


def ask_for_output_path() -> str:
    """Ask for directory and filename, then return the full path."""
    import os

    while True:
        directory = prompt(
            f"Output directory [press Enter for '{DEFAULT_OUTPUT_DIR}']: "
        ) or DEFAULT_OUTPUT_DIR
        try:
            directory = validate_output_directory(directory)
            break
        except ValidationError as exc:
            print(f"  [!] {exc}")

    while True:
        filename = prompt(
            f"Filename [press Enter for '{DEFAULT_OUTPUT_FILENAME}']: "
        ) or DEFAULT_OUTPUT_FILENAME
        try:
            filename = validate_filename(filename)
            break
        except ValidationError as exc:
            print(f"  [!] {exc}")

    return os.path.join(directory, filename)


def run_generation() -> None:
    """Full interactive generation workflow."""
    country = choose_country()
    pattern = choose_pattern(country)

    unknowns = count_unknowns(pattern)
    total = calculate_combinations(pattern)

    print()
    print(f"  Country              : {country.name} ({country.code})")
    print(f"  Pattern              : {pattern}")
    print(f"  Unknown positions    : {unknowns}")
    print(f"  Total combinations   : {total:,}")

    if total > MAX_COMBINATIONS:
        print()
        print(f"  [!] Requested combinations ({total:,}) exceed the configured")
        print(f"      maximum of {MAX_COMBINATIONS:,}. Aborting for safety.")
        print("      Edit config.py to raise the limit if you really need to.")
        pause()
        return

    if not confirm_large_generation(total):
        print("  Aborted.")
        pause()
        return

    mode = choose_output_mode()

    if mode == "terminal":
        print()
        print("Preview:")
        print("-" * 40)
        preview_in_terminal(iter_combinations(pattern), total)
        print("-" * 40)
    else:
        path = ask_for_output_path()
        written = write_to_file(iter_combinations(pattern), path, total)
        print_summary(written, total, path)

    pause()


# ---------------------------------------------------------------------------
# Top-level menu
# ---------------------------------------------------------------------------

def main_menu() -> None:
    """Main interactive loop."""
    while True:
        print()
        print(BANNER)
        print()
        print("1. Generate combinations")
        print("2. Settings")
        print("3. Exit")
        raw = prompt("Select an option: ")

        try:
            choice = validate_menu_choice(raw, 1, 3)
        except ValidationError as exc:
            print(f"  [!] {exc}")
            continue

        if choice == 1:
            run_generation()
        elif choice == 2:
            show_settings()
        else:
            print("Goodbye.")
            return


def main() -> None:
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()