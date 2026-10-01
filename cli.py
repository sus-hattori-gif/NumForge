"""Non-interactive CLI for NumForge.

Supports the full generation pipeline without any user prompts.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

from config import (
    DEFAULT_OUTPUT_DIR,
    MAX_COMBINATIONS,
    SUPPORTED_FORMATS,
    VERSION,
)
from countries import (
    COUNTRIES,
    Country,
    get_country_by_id,
    list_country_ids,
)
from generator import iter_combinations
from logging_setup import Log
from output import (
    load_state,
    preview_in_terminal,
    print_summary,
    write_to_file,
)
from patterns_file import read_patterns_file
from profile import Profile, list_profiles, load_profile, save_profile
from rules import filter_valid
from validators import (
    ValidationError,
    calculate_combinations,
    validate_filename,
    validate_format,
    validate_output_directory,
    validate_pattern,
)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="numforge",
        description=(
            "NumForge — generate local numeric combinations from phone-number "
            "patterns. Purely local; never verifies or contacts real numbers."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version", version=f"NumForge {VERSION}")
    p.add_argument(
        "--log",
        choices=("quiet", "normal", "verbose"),
        default="normal",
        help="Log verbosity (default: normal).",
    )

    sub = p.add_subparsers(dest="command", required=True)

    # ---- generate ------------------------------------------------------
    g = sub.add_parser("generate", help="Generate combinations and write to a file.")
    _add_common_input_args(g)
    g.add_argument("-o", "--output", help="Output file path.")
    g.add_argument(
        "-f", "--format",
        choices=SUPPORTED_FORMATS,
        default=None,
        help="Output format (default: inferred from extension, else txt).",
    )
    g.add_argument("--gzip", action="store_true", help="Compress output with gzip.")
    g.add_argument(
        "--validate", action="store_true",
        help="Drop structurally invalid numbers using the country's local rules.",
    )
    g.add_argument(
        "--max", type=int, default=None,
        help=f"Override MAX_COMBINATIONS (default: {MAX_COMBINATIONS:,}).",
    )
    g.add_argument(
        "--yes", "-y", action="store_true",
        help="Skip the large-job confirmation prompt.",
    )
    g.add_argument(
        "--profile", help="Load settings from a saved profile.",
    )

    # ---- preview -------------------------------------------------------
    pv = sub.add_parser("preview", help="Show the first N combinations without writing.")
    _add_common_input_args(pv)
    pv.add_argument("-n", "--limit", type=int, default=50, help="How many to show.")

    # ---- countries -----------------------------------------------------
    sub.add_parser("countries", help="List supported countries and patterns.")

    # ---- profile -------------------------------------------------------
    pf = sub.add_parser("profile", help="Manage saved profiles.")
    pf_sub = pf.add_subparsers(dest="profile_cmd", required=True)

    pf_sub.add_parser("list", help="List all saved profiles.")

    pf_show = pf_sub.add_parser("show", help="Show a profile.")
    pf_show.add_argument("name")

    pf_del = pf_sub.add_parser("delete", help="Delete a profile.")
    pf_del.add_argument("name")

    pf_save = pf_sub.add_parser("save", help="Save a new profile.")
    pf_save.add_argument("name")
    pf_save.add_argument("-c", "--country", required=True)
    pf_save.add_argument("-p", "--pattern")
    pf_save.add_argument("--patterns-file")
    pf_save.add_argument("-f", "--format", choices=SUPPORTED_FORMATS, default="txt")
    pf_save.add_argument("--gzip", action="store_true")
    pf_save.add_argument("-d", "--output-dir", default=".")
    pf_save.add_argument("-o", "--output-filename")
    pf_save.add_argument("--validate", action="store_true")

    return p


def _add_common_input_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-c", "--country",
        help=f"Country id ({', '.join(list_country_ids())}).",
    )
    parser.add_argument(
        "-p", "--pattern",
        help="Pattern with X and [...] placeholders.",
    )
    parser.add_argument(
        "--patterns-file",
        help="Read multiple patterns from a text file (one per line).",
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_countries(log: Log) -> int:
    for c in COUNTRIES:
        print(f"\n{c.name}  ({c.id}, {c.code})")
        for pat in c.patterns:
            print(f"  {pat}")
        if c.rules.valid_prefixes:
            print(f"  [rules] prefixes: {len(c.rules.valid_prefixes)}")
            print(f"  [rules] lengths : {c.rules.allowed_lengths}")
    return 0


def cmd_profile(args: argparse.Namespace, log: Log) -> int:
    sub = args.profile_cmd

    if sub == "list":
        names = list_profiles()
        if not names:
            log.info("No profiles found.")
            return 0
        for n in names:
            print(n)
        return 0

    if sub == "show":
        try:
            prof = load_profile(args.name)
        except ValidationError as exc:
            log.error(str(exc))
            return 1
        for k, v in prof.__dict__.items():
            print(f"  {k:18} = {v}")
        return 0

    if sub == "delete":
        from profile import delete_profile
        ok = delete_profile(args.name)
        if ok:
            log.info(f"Deleted profile '{args.name}'.")
            return 0
        log.error(f"Profile '{args.name}' not found.")
        return 1

    if sub == "save":
        prof = Profile(
            name=args.name,
            country=args.country,
            pattern=args.pattern,
            patterns_file=args.patterns_file,
            format=args.format,
            compressed=args.gzip,
            output_dir=args.output_dir,
            output_filename=args.output_filename,
            validate=args.validate,
        )
        try:
            path = save_profile(prof)
        except ValidationError as exc:
            log.error(str(exc))
            return 1
        log.info(f"Saved profile to: {path}")
        return 0

    log.error("Unknown profile command.")
    return 1


def _resolve_inputs(args: argparse.Namespace, log: Log) -> tuple[Country, list[str]]:
    """Return (country, [patterns...]) from args or from a profile."""
    profile: Optional[Profile] = None
    if getattr(args, "profile", None):
        profile = load_profile(args.profile)
        log.verbose(f"Loaded profile '{profile.name}'.")

    country_id = args.country or (profile.country if profile else None)
    if not country_id:
        raise ValidationError("Country is required (use -c or --profile).")

    try:
        country = get_country_by_id(country_id)
    except KeyError as exc:
        raise ValidationError(str(exc))

    patterns: list[str] = []
    single = args.pattern or (profile.pattern if profile else None)
    if single:
        patterns.append(validate_pattern(single))

    pf = args.patterns_file or (profile.patterns_file if profile else None)
    if pf:
        patterns.extend(read_patterns_file(pf))

    if not patterns:
        raise ValidationError(
            "At least one pattern is required (-p, --patterns-file, or profile)."
        )

    return country, patterns


def cmd_preview(args: argparse.Namespace, log: Log) -> int:
    try:
        country, patterns = _resolve_inputs(args, log)
    except ValidationError as exc:
        log.error(str(exc))
        return 2

    for pattern in patterns:
        total = calculate_combinations(pattern)
        log.info(f"\nPattern: {pattern}  ({total:,} combinations)")
        print("-" * 44)
        preview_in_terminal(iter_combinations(pattern), total, preview_limit=args.limit)
        print("-" * 44)

    return 0


def cmd_generate(args: argparse.Namespace, log: Log) -> int:
    profile: Optional[Profile] = None
    if getattr(args, "profile", None):
        try:
            profile = load_profile(args.profile)
        except ValidationError as exc:
            log.error(str(exc))
            return 2

    try:
        country, patterns = _resolve_inputs(args, log)
    except ValidationError as exc:
        log.error(str(exc))
        return 2

    # Resolve format
    fmt = args.format or (profile.format if profile else None)
    output_path = args.output or None

    if output_path and not fmt:
        ext = os.path.splitext(output_path)[1].lower().lstrip(".")
        if ext == "gz":
            ext = os.path.splitext(os.path.splitext(output_path)[0])[1].lower().lstrip(".")
        if ext in SUPPORTED_FORMATS:
            fmt = ext
    fmt = fmt or "txt"
    try:
        fmt = validate_format(fmt)
    except ValidationError as exc:
        log.error(str(exc))
        return 2

    # Resolve compression
    compressed = bool(args.gzip or (profile.compressed if profile else False))

    # Resolve output path
    if not output_path:
        out_dir = (profile.output_dir if profile else DEFAULT_OUTPUT_DIR) or "."
        try:
            out_dir = validate_output_directory(out_dir)
        except ValidationError as exc:
            log.error(str(exc))
            return 2

        filename = (profile.output_filename if profile else None) or f"numforge_results.{fmt}"
        try:
            filename = validate_filename(filename, fmt=fmt)
        except ValidationError as exc:
            log.error(str(exc))
            return 2

        output_path = os.path.join(out_dir, filename)

    if compressed and not output_path.endswith(".gz"):
        output_path += ".gz"

    # Resolve max-combinations
    max_combos = args.max or (profile.max_combinations if profile else None) or MAX_COMBINATIONS

    # Total across all patterns
    totals = [calculate_combinations(p) for p in patterns]
    grand_total = sum(totals)

    if grand_total > max_combos:
        log.error(
            f"Requested combinations ({grand_total:,}) exceed the configured "
            f"maximum of {max_combos:,}. Use --max to raise it if you really need to."
        )
        return 1

    # Confirmation
    if grand_total > 100_000 and not args.yes:
        log.warn(f"This will generate {grand_total:,} combinations.")
        try:
            answer = input("Continue? [y/N]: ").strip().lower()
        except EOFError:
            answer = "n"
        if answer not in ("y", "yes"):
            log.info("Aborted.")
            return 0

    # Validation filter
    use_validate = bool(args.validate or (profile.validate if profile else False))
    if use_validate:
        log.info(f"[validate] Filtering with local rules for {country.name}.")
        if not country.rules.valid_prefixes and not country.rules.allowed_lengths:
            log.warn("No rules defined for this country; validation skipped.")

    # Check resume
    resume_state = load_state(output_path)
    if resume_state:
        prev = resume_state.get("written", 0)
        log.warn(
            f"Found previous state for '{output_path}' ({prev:,} written). "
            f"Starting over (delete the state file to force resume in interactive mode)."
        )

    # Iterate over all patterns
    def _all_combinations():
        for p in patterns:
            yield from iter_combinations(p)

    source = _all_combinations()
    if use_validate and (country.rules.valid_prefixes or country.rules.allowed_lengths):
        source = filter_valid(source, country)

    metadata = {
        "country": country.id,
        "patterns": "|".join(patterns),
    }

    written = write_to_file(
        source,
        output_path,
        grand_total,
        fmt=fmt,
        compressed=compressed,
        resume_state=None,
        metadata=metadata,
        quiet=(args.log == "quiet"),
    )

    print_summary(
        written_now=written,
        previously_written=0,
        total=grand_total,
        path=output_path,
        fmt=fmt,
        compressed=compressed,
    )
    return 0


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def run(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    log = Log(level=args.log)

    if args.command == "countries":
        return cmd_countries(log)
    if args.command == "profile":
        return cmd_profile(args, log)
    if args.command == "preview":
        return cmd_preview(args, log)
    if args.command == "generate":
        return cmd_generate(args, log)

    parser.print_help()
    return 2