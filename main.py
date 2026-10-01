"""NumForge — CLI entry point.

Two modes:
  - Interactive: python main.py
  - Non-interactive: python main.py <command> [options]

NumForge is a purely local tool. It never performs network requests,
never verifies numbers, and never interacts with telecom services.
"""

from __future__ import annotations

import sys


def _looks_like_cli(argv: list[str]) -> bool:
    """Detect whether argv looks like a non-interactive command."""
    if not argv:
        return False
    first = argv[0]
    # Known subcommands / global flags.
    known = {"generate", "preview", "countries", "profile"}
    if first in known:
        return True
    if first in ("-h", "--help", "--version"):
        return True
    return False


def main() -> None:
    argv = sys.argv[1:]

    if _looks_like_cli(argv):
        from cli import run
        sys.exit(run(argv))

    # Interactive mode
    from interactive import main_menu
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()