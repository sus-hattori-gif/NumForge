"""Interactive menu for NumForge.

This is the same UX as v1.1, moved into its own module so main.py
can route between interactive and CLI modes.
"""

from __future__ import annotations

import os
import sys

from config import (
    CONFIRMATION_THRESHOLD,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_FILENAME,
    MAX_COMBINATIONS,
    SUPPORTED_FORMATS,
    VERSION,
)
from countries import COUNTRIES, get_country_by_index
from generator import iter_combinations
from output import (
    clear_state,
    load_state,
    preview_in_terminal,
    print_summary,
    write_to_file,
)
from rules import filter_valid
from validators import (
    ValidationError,
    calculate_combinations,
    count_unknowns,
    validate_filename,
    validate_menu_choice,
    validate_output_directory,
    validate_pattern,
)


BANNER = f"""================================
          NumForge
            v{VERSION}
================================"""


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def prompt(message: str) -> str:
    try:
        return input(message).strip()
    except EOFError:
        print("\nInput closed. Exiting.")
        sys.exit(0)


def pause() -> None:
    try:
        input("\nPress Enter to continue...")
    except EOFError:
        pass


# ---------------------------------------------------------------------------
# Menu screens
# ---------------------------------------------------------------------------

def choose_country():
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
    print()
    print(f"Available patterns for {country.name}:")
    for idx, pat in enumerate(country.patterns, start=1):
        print(f"  {idx}. {pat}")
    custom_idx = len(country.patterns) + 1
    print(f"  {custom_idx}. Enter a custom pattern")
    print()
    print("  Syntax: X = any digit, [0-5] = range, [02468] = set")

    while True:
        raw = prompt("Enter number: ")
        try:
            choice = validate_menu_choice(raw, 1, custom_idx)
        except ValidationError as exc:
            print(f"  [!] {exc}")
            continue

        if choice == custom_idx:
            custom = prompt("Enter custom pattern: ")
            try:
                return validate_pattern(custom)
            except ValidationError as exc:
                print(f"  [!] {exc}")
                continue

        return country.patterns[choice - 1]


def show_settings() -> None:
    print()
    print("Current settings:")
    print(f"  Confirmation threshold : {CONFIRMATION_THRESHOLD:,} combinations")
    print(f"  Maximum combinations   : {MAX_COMBINATIONS:,}")
    print(f"  Placeholder character  : X")
    print(f"  Supported formats      : {', '.join(SUPPORTED_FORMATS)}")
    print(f"  Version                : {VERSION}")
    print()
    pause()


def confirm_large_generation(total: int) -> bool:
    if total <= CONFIRMATION_THRESHOLD:
        return True
    print()
    print(f"  [!] This will generate {total:,} combinations.")
    answer = prompt("  Continue? [y/N]: ").lower()
    return answer in ("y", "yes")


def choose_output_mode() -> str:
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


def choose_format() -> str:
    print()
    print("Output format:")
    print("  1. TXT")
    print("  2. CSV")
    print("  3. JSONL")
    while True:
        raw = prompt("Enter number: ")
        try:
            choice = validate_menu_choice(raw, 1, 3)
            return SUPPORTED_FORMATS[choice - 1]
        except ValidationError as exc:
            print(f"  [!] {exc}")


def choose_compression() -> bool:
    print()
    print("Compress output with gzip?")
    print("  1. No")
    print("  2. Yes (.gz)")
    while True:
        raw = prompt("Enter number: ")
        try:
            choice = validate_menu_choice(raw, 1, 2)
            return choice == 2
        except ValidationError as exc:
            print(f"  [!] {exc}")


def choose_validate(country) -> bool:
    if not country.rules.valid_prefixes and not country.rules.allowed_lengths:
        return False
    print()
    print(f"Apply structural rules for {country.name}?")
    print(f"  Valid prefixes : {len(country.rules.valid_prefixes)}")
    print(f"  Valid lengths  : {country.rules.allowed_lengths}")
    print("  1. No  (keep all combinations)")
    print("  2. Yes (drop impossible numbers)")
    while True:
        raw = prompt("Enter number: ")
        try:
            choice = validate_menu_choice(raw, 1, 2)
            return choice == 2
        except ValidationError as exc:
            print(f"  [!] {exc}")


def ask_for_output_path(fmt: str, compressed: bool) -> str:
    while True:
        directory = prompt(
            f"Output directory [press Enter for '{DEFAULT_OUTPUT_DIR}']: "
        ) or DEFAULT_OUTPUT_DIR
        try:
            directory = validate_output_directory(directory)
            break
        except ValidationError as exc:
            print(f"  [!] {exc}")

    suggested = DEFAULT_OUTPUT_FILENAME
    if suggested.endswith(".txt") and fmt != "txt":
        suggested = suggested[: -len(".txt")] + f".{fmt}"

    while True:
        filename = prompt(
            f"Filename [press Enter for '{suggested}']: "
        ) or suggested
        try:
            filename = validate_filename(filename, fmt=fmt)
            break
        except ValidationError as exc:
            print(f"  [!] {exc}")

    path = os.path.join(directory, filename)
    if compressed and not path.endswith(".gz"):
        path += ".gz"
    return path


def run_generation() -> None:
    country = choose_country()
    pattern = choose_pattern(country)

    unknowns = count_unknowns(pattern)
    total = calculate_combinations(pattern)

    print()
    print(f"  Country              : {country.name} ({country.code})")
    print(f"  Pattern              : {pattern}")
    print(f"  Variable positions   : {unknowns}")
    print(f"  Total combinations   : {total:,}")

    if total > MAX_COMBINATIONS:
        print()
        print(f"  [!] Requested combinations ({total:,}) exceed the configured")
        print(f"      maximum of {MAX_COMBINATIONS:,}. Aborting for safety.")
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
        print("-" * 44)
        preview_in_terminal(iter_combinations(pattern), total)
        print("-" * 44)
        pause()
        return

    fmt = choose_format()
    compressed = choose_compression()
    use_validate = choose_validate(country)
    path = ask_for_output_path(fmt, compressed)

    metadata = {
        "country": country.id,
        "patterns": pattern,
    }

    source = iter_combinations(pattern)
    if use_validate:
        source = filter_valid(source, country)

    written_now = write_to_file(
        source,
        path,
        total,
        fmt=fmt,
        compressed=compressed,
        resume_state=None,
        metadata=metadata,
    )

    print_summary(
        written_now=written_now,
        previously_written=0,
        total=total,
        path=path,
        fmt=fmt,
        compressed=compressed,
    )
    pause()


# ---------------------------------------------------------------------------
# Top-level menu
# ---------------------------------------------------------------------------

def main_menu() -> None:
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