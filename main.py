"""NumForge — CLI entry point.

NumForge generates all possible numeric combinations matching a
user-defined phone-number pattern. It is a purely local tool.
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
from validators import (
    ValidationError,
    calculate_combinations,
    count_unknowns,
    validate_filename,
    validate_format,
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
    print("  Syntax: X = any digit, [0-5] = range, [02468] = set, [0,2,4] = set")

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
    print("(Edit config.py to change these values.)")
    pause()


# ---------------------------------------------------------------------------
# Generation workflow
# ---------------------------------------------------------------------------

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
    print("  1. TXT   (plain text, one number per line)")
    print("  2. CSV   (with header)")
    print("  3. JSONL (one JSON object per line)")
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
    print("  1. No  (plain file)")
    print("  2. Yes (file + .gz, much smaller for large jobs)")
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

    # Build a default filename suggestion based on format + compression.
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


def maybe_resume(path: str, pattern: str, fmt: str, compressed: bool) -> dict | None:
    """Check for a state file and ask the user whether to resume."""
    state = load_state(path)
    if not state:
        return None

    same_pattern = state.get("pattern") == pattern
    written = state.get("written", 0)

    print()
    print(f"  [!] Found a previous run in progress:")
    print(f"      File     : {path}")
    print(f"      Written  : {written:,}")
    print(f"      Pattern  : {state.get('pattern')}")
    if not same_pattern:
        print(f"      WARNING  : This pattern differs from the current one.")
    print()
    print("  1. Resume from where it stopped")
    print("  2. Start over (delete previous output)")
    print("  3. Cancel")

    while True:
        raw = prompt("  Select: ")
        try:
            choice = validate_menu_choice(raw, 1, 3)
        except ValidationError as exc:
            print(f"  [!] {exc}")
            continue

        if choice == 1:
            return state
        if choice == 2:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError as exc:
                print(f"  [!] Could not remove old file: {exc}")
                return None
            clear_state(path)
            return None
        return {"_cancelled": True}


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
        print("-" * 44)
        preview_in_terminal(iter_combinations(pattern), total)
        print("-" * 44)
        pause()
        return

    # File mode
    fmt = choose_format()
    compressed = choose_compression()
    path = ask_for_output_path(fmt, compressed)

    resume_state = maybe_resume(path, pattern, fmt, compressed)
    if resume_state and resume_state.get("_cancelled"):
        print("  Cancelled.")
        pause()
        return

    previously_written = resume_state.get("written", 0) if resume_state else 0

    metadata = {
        "pattern": pattern,
        "country": country.name,
        "country_code": country.code,
    }

    written_now = write_to_file(
        iter_combinations(pattern),
        path,
        total,
        fmt=fmt,
        compressed=compressed,
        resume_state=resume_state,
        metadata=metadata,
    )

    print_summary(
        written_now=written_now,
        previously_written=previously_written,
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


def main() -> None:
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()