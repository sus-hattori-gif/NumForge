"""Output handling for NumForge: terminal display and file writing."""

from __future__ import annotations

import gzip
import json
import os
import sys
import time
from datetime import datetime
from typing import Iterator, Optional

from config import PROGRESS_INTERVAL, STATE_SUFFIX
from validators import confirm_overwrite


# ---------------------------------------------------------------------------
# Terminal preview
# ---------------------------------------------------------------------------

def preview_in_terminal(
    iterator: Iterator[str],
    total: int,
    preview_limit: int = 50,
) -> int:
    """Print up to `preview_limit` combinations to the terminal."""
    printed = 0
    for item in iterator:
        print(item)
        printed += 1
        if printed >= preview_limit:
            break
    if total > printed:
        print(f"... ({total - printed:,} more combinations not shown) ...")
    return printed


# ---------------------------------------------------------------------------
# State file (for resume)
# ---------------------------------------------------------------------------

def _state_path(output_path: str) -> str:
    return output_path + STATE_SUFFIX


def load_state(output_path: str) -> Optional[dict]:
    """Load a resume state for `output_path`, or None if absent."""
    path = _state_path(output_path)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def save_state(output_path: str, state: dict) -> None:
    """Atomically save resume state."""
    path = _state_path(output_path)
    tmp = path + ".tmp"
    state["updated_at"] = datetime.now().isoformat(timespec="seconds")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except OSError:
        pass  # Non-fatal


def clear_state(output_path: str) -> None:
    """Remove resume state if present."""
    path = _state_path(output_path)
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _open_writer(path: str, fmt: str, compressed: bool, append: bool):
    """Return a file object opened for text writing (plain or gzip)."""
    mode = "at" if append else "wt"
    if compressed:
        # gzip append creates a new member — valid and readable.
        gzip_mode = "ab" if append else "wb"
        return gzip.open(path, gzip_mode, compresslevel=6, encoding="utf-8", newline="\n")
    return open(path, mode, encoding="utf-8", newline="\n")


def _format_line(number: str, fmt: str, metadata: dict) -> str:
    """Serialize a single combination into a line."""
    if fmt == "txt":
        return number + "\n"
    if fmt == "csv":
        # Escape is minimal: digits and dashes don't need CSV quoting,
        # but we quote defensively.
        return f'"{number}"\n'
    if fmt == "jsonl":
        obj = {"number": number}
        obj.update(metadata)
        return json.dumps(obj, ensure_ascii=False) + "\n"
    raise ValueError(f"Unknown format: {fmt}")


def _write_header(fh, fmt: str, metadata: dict) -> None:
    """Write a format-specific header if needed."""
    if fmt == "csv":
        cols = ["number"] + list(metadata.keys())
        fh.write(",".join(cols) + "\n")


# ---------------------------------------------------------------------------
# File writing (with progress, resume, Ctrl+C handling)
# ---------------------------------------------------------------------------

def write_to_file(
    iterator: Iterator[str],
    path: str,
    total: int,
    fmt: str = "txt",
    compressed: bool = False,
    resume_state: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> int:
    """Write all combinations from `iterator` to `path`.

    Returns the number of combinations written in THIS run (not including
    any combinations that were written in a previous, resumed run).
    """
    metadata = metadata or {}

    # Resume bookkeeping
    append = False
    start_index = 0
    previously_written = 0
    header_already_present = False

    if resume_state:
        start_index = int(resume_state.get("written", 0))
        previously_written = start_index
        append = start_index > 0 and os.path.exists(path)
        header_already_present = append

    # If not resuming but the file exists, ask before overwriting.
    if not append:
        if not confirm_overwrite(path):
            print("Aborted: file not overwritten.")
            return 0

    state = {
        "pattern": resume_state.get("pattern") if resume_state else None,
        "format": fmt,
        "compressed": compressed,
        "output_path": os.path.abspath(path),
        "total": total,
        "written": start_index,
        "started_at": (
            resume_state.get("started_at")
            if resume_state
            else datetime.now().isoformat(timespec="seconds")
        ),
    }
    save_state(path, state)

    # Open writer
    fh = _open_writer(path, fmt, compressed, append=append)

    # Write header for CSV only if we're starting fresh
    if fmt == "csv" and not header_already_present:
        _write_header(fh, fmt, metadata)

    written_now = 0
    start = time.time()
    last_report = start

    # Skip already-generated combinations for resume.
    source = iterator
    if start_index > 0:
        from itertools import islice
        source = islice(iterator, start_index, None)

    try:
        for combo in source:
            fh.write(_format_line(combo, fmt, metadata))
            written_now += 1

            if written_now % PROGRESS_INTERVAL == 0:
                now = time.time()
                elapsed = now - start
                speed = written_now / elapsed if elapsed > 0 else 0.0
                done_total = previously_written + written_now
                pct = (done_total / total) * 100 if total else 100.0
                remaining = max(total - done_total, 0)
                eta = remaining / speed if speed > 0 else 0.0
                sys.stdout.write(
                    f"\r  Progress: {done_total:,}/{total:,} "
                    f"({pct:5.1f}%) | {speed:,.0f} gen/s | "
                    f"elapsed {elapsed:5.1f}s | ETA {_fmt_duration(eta)}"
                )
                sys.stdout.flush()
                last_report = now

                # Periodic state flush
                state["written"] = done_total
                save_state(path, state)

        fh.close()

    except KeyboardInterrupt:
        try:
            fh.close()
        except Exception:
            pass
        done_total = previously_written + written_now
        state["written"] = done_total
        save_state(path, state)
        elapsed = time.time() - start
        print(
            f"\n\n[!] Generation interrupted by user (Ctrl+C).\n"
            f"    Partial output saved to : {path}\n"
            f"    Combinations written    : {done_total:,}\n"
            f"    Elapsed time            : {elapsed:.1f}s\n"
            f"    Resume state saved      : {_state_path(path)}\n"
            f"    Run NumForge again and select the same output file to resume."
        )
        return written_now

    # Success: clear state
    clear_state(path)

    # Final progress line
    done_total = previously_written + written_now
    elapsed = time.time() - start
    speed = written_now / elapsed if elapsed > 0 else 0.0
    sys.stdout.write(
        f"\r  Progress: {done_total:,}/{total:,} (100.0%) | "
        f"{speed:,.0f} gen/s | elapsed {elapsed:5.1f}s"
    )
    sys.stdout.flush()
    print()

    return written_now


def _fmt_duration(seconds: float) -> str:
    """Format a duration like '1h 23m' or '45s'."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}m"
    return f"{seconds / 3600:.1f}h"


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(
    written_now: int,
    previously_written: int,
    total: int,
    path: Optional[str],
    fmt: str = "txt",
    compressed: bool = False,
) -> None:
    """Print a final completion summary."""
    print()
    print("=" * 44)
    print("  Generation complete")
    print("=" * 44)
    if previously_written:
        print(f"  Resumed from           : {previously_written:,}")
    print(f"  Written in this run    : {written_now:,}")
    print(f"  Total in file          : {previously_written + written_now:,}")
    if total and (previously_written + written_now) < total:
        print(f"  Combinations requested : {total:,}")
    if path:
        print(f"  Output file            : {os.path.abspath(path)}")
        print(f"  Format                 : {fmt}" + (" (gzip)" if compressed else ""))
        size = _safe_size(path)
        if size is not None:
            print(f"  File size              : {_human_size(size)}")
    print()
    print("  Note: This tool only generates local numeric combinations.")
    print("  It does not verify, call, or message any phone number.")
    print()


def _safe_size(path: str) -> Optional[int]:
    try:
        return os.path.getsize(path)
    except OSError:
        return None


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n:.1f} PB"