"""Log-level helpers for NumForge.

NumForge uses three levels:
  - quiet    : only errors and final summary
  - normal   : default (progress, warnings)
  - verbose  : extra diagnostic info

We do not use the `logging` module here because the output is
interactive and formatted for the terminal. Instead, a tiny wrapper
exposes `info()` / `warn()` / `verbose()`.
"""

from __future__ import annotations

import sys


class Log:
    def __init__(self, level: str = "normal") -> None:
        self.level = level

    def info(self, msg: str) -> None:
        if self.level in ("normal", "verbose"):
            print(msg)

    def warn(self, msg: str) -> None:
        if self.level != "quiet":
            print(f"[!] {msg}", file=sys.stderr)

    def error(self, msg: str) -> None:
        print(f"[x] {msg}", file=sys.stderr)

    def verbose(self, msg: str) -> None:
        if self.level == "verbose":
            print(f"[.] {msg}")

    def always(self, msg: str) -> None:
        print(msg)