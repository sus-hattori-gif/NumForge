"""Profile management for NumForge.

A profile is a TOML file that stores the common CLI options so the user
can run `numforge generate --profile iran-tests` without retyping flags.

Search order (first match wins):
    1. ./profiles/<name>.toml       (project-local)
    2. ~/.numforge/profiles/<name>.toml   (user home)
"""

from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Optional

from config import HOME_PROFILE_DIR, LOCAL_PROFILE_DIR


# tomllib is available in Python 3.11+.
if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore


@dataclass
class Profile:
    """A saved set of CLI options."""

    name: str = ""
    country: str = ""            # slug like "ir"
    pattern: str = ""
    format: str = "txt"
    compressed: bool = False
    output_dir: str = "."
    output_name: str = ""        # optional; if empty, auto-named
    validate: bool = True        # whether to apply country rules
    quiet: bool = False
    verbose: bool = False
    max_combinations: int = 0    # 0 means "use config default"

    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        """Build a Profile from a parsed TOML dict, ignoring unknown keys."""
        valid = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid}
        return cls(**filtered)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _local_dir() -> Path:
    return Path(LOCAL_PROFILE_DIR).resolve()


def _home_dir() -> Path:
    return Path.home() / HOME_PROFILE_DIR


def profile_search_paths(name: str) -> list[Path]:
    """Return the candidate paths for a profile, in priority order."""
    return [
        _local_dir() / f"{name}.toml",
        _home_dir() / f"{name}.toml",
    ]


def find_profile_path(name: str) -> Optional[Path]:
    """Return the first existing profile path, or None."""
    for p in profile_search_paths(name):
        if p.exists():
            return p
    return None


# ---------------------------------------------------------------------------
# Load / save / list / delete
# ---------------------------------------------------------------------------

def load_profile(name: str) -> Profile:
    """Load a profile by name.

    Raises FileNotFoundError if not found in either location.
    Raises ValueError on parse errors.
    """
    path = find_profile_path(name)
    if path is None:
        raise FileNotFoundError(f"Profile '{name}' not found.")

    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except Exception as exc:
        raise ValueError(f"Cannot parse profile '{path}': {exc}") from exc

    profile = Profile.from_dict(data)
    if not profile.name:
        profile.name = name
    return profile


def save_profile(profile: Profile, location: str = "local") -> Path:
    """Save a profile to disk.

    location = "local"  -> ./profiles/<name>.toml
    location = "home"   -> ~/.numforge/profiles/<name>.toml
    """
    if not profile.name:
        raise ValueError("Profile has no name.")

    if location == "home":
        directory = _home_dir()
    else:
        directory = _local_dir()

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{profile.name}.toml"

    # We use a minimal hand-written TOML writer to avoid depending on
    # tomli_w for such a small amount of data.
    lines: list[str] = []
    for key, value in profile.to_dict().items():
        lines.append(_toml_line(key, value))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def list_profiles() -> list[tuple[str, Path]]:
    """Return (name, path) for every profile found, deduplicated."""
    seen: dict[str, Path] = {}
    for directory in (_local_dir(), _home_dir()):
        if not directory.exists():
            continue
        for p in directory.glob("*.toml"):
            name = p.stem
            # Local takes priority: only add if not already seen.
            seen.setdefault(name, p)
    return sorted(seen.items(), key=lambda x: x[0].lower())


def delete_profile(name: str) -> bool:
    """Delete a profile from whichever location it exists in.

    Returns True if a file was removed.
    """
    removed = False
    for p in profile_search_paths(name):
        if p.exists():
            p.unlink()
            removed = True
    return removed


# ---------------------------------------------------------------------------
# Minimal TOML writer
# ---------------------------------------------------------------------------

def _toml_line(key: str, value) -> str:
    """Serialize a single key=value pair as TOML."""
    if isinstance(value, bool):
        return f"{key} = {'true' if value else 'false'}"
    if isinstance(value, int):
        return f"{key} = {value}"
    # Everything else is quoted as a string.
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'{key} = "{escaped}"'