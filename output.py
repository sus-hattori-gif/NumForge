"""Output handling: terminal display and file writing for NumForge."""

from __future__ import annotations

import os
import sys
import time
from typing import Iterable, Iterator

from config import PROGRESS_INTERVAL
from validators import confirm_overwrite


def preview_in_terminal(
    iterator: Iterator[str],
    total: int,
    preview_limit: int = 50,
) -> int:
    """Print up to `preview_limit` combinations to the terminal.

    Returns the number of items actually printed.
    """
    printed = 0
    for item in iterator:
        print(item)
        printed += 1
        if printed >= preview_limit:
            break
    if total > printed:
        print(f"... ({total - printed:,} more combinations not shown) ...")
    return printed


def write_to_file(
    iterator: Iterator[str],
    path: str,
    total: int,
) -> int:
    """Write all combinations from `iterator` to `path`.

    Progress is shown inline. Ctrl+C is handled gracefully: the partial
    file remains valid, and the user is informed.

    Returns the number of combinations written.
    """
    if not confirm_overwrite(path):
        print("Aborted: file not overwritten.")
        return 0

    written = 0
    start = time.time()
    last_report = start
    last_written = 0

    # Write to a temporary file then rename atomically, so a Ctrl+C
    # never leaves a partially-written *final* file in an inconsistent state.
    tmp_path = path + ".part"

    try:
        with open(tmp_path, "w", encoding="utf-8", newline="\n") as fh:
            for combo in iterator:
                fh.write(combo)
                fh.write("\n")
                written += 1

                if written % PROGRESS_INTERVAL == 0 or written == total:
                    now = time.time()
                    elapsed = now - start
                    speed = written / elapsed if elapsed > 0 else 0.0
                    pct = (written / total) * 100 if total else 100.0
                    sys.stdout.write(
                        f"\r  Progress: {written:,}/{total:,} "
                        f"({pct:5.1f}%) | {speed:,.0f} gen/s | {elapsed:5.1f}s"
                    )
                    sys.stdout.flush()
                    last_report = now
                    last_written = written

        os.replace(tmp_path, path)

    except KeyboardInterrupt:
        # Best-effort: keep whatever was written so far in a .part file.
        try:
            if os.path.exists(tmp_path):
                os.replace(tmp_path, path)
        except OSError:
            pass
        elapsed = time.time() - start
        print(
            f"\n\n[!] Generation interrupted by user (Ctrl+C).\n"
            f"    Partial output saved to: {path}\n"
            f"    Combinations written: {written:,}\n"
            f"    Elapsed time: {elapsed:.1f}s"
        )
        return written

    print()  # newline after inline progress
    return written


def print_summary(written: int, total: int, path: str | None) -> None:
    """Print a final completion summary."""
    print()
    print("=" * 40)
    print("  Generation complete")
    print("=" * 40)
    print(f"  Combinations generated : {written:,}")
    if total and written < total:
        print(f"  Combinations requested : {total:,}")
    if path:
        print(f"  Output file            : {path}")
    print()