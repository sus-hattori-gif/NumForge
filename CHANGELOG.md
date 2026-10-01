# Changelog

## [1.2.0] — 2025

### Added
- **Non-interactive CLI** (`python main.py generate ...`, `preview`, `countries`, `profile`).
- **`--validate` flag**: applies lightweight local country rules (length + prefix)
  to drop structurally impossible numbers. Purely local; no network.
- **Multi-pattern input** via `--patterns-file patterns.txt` (one pattern per line,
  `#` comments allowed).
- **User profiles** stored as TOML in `./profiles/` or `~/.numforge/profiles/`.
  Manage via `python main.py profile list|show|save|delete`.
- **Log levels** `--log quiet|normal|verbose` for scripts and CI.
- **Exit codes**: 0 success, 1 runtime error, 2 invalid input.

### Changed
- `main.py` now detects CLI usage automatically; interactive menu moved to `interactive.py`.
- `countries.py` restructured: each country now has an `id` slug and a `CountryRules`.
- `write_to_file` gains a `quiet` parameter.
- Version bumped to `1.2.0`.

### Notes
- NumForge remains a purely local pattern-combination generator.
  It does **not** verify real phone numbers, does **not** make network
  requests, and does **not** interact with any telecom service.
  The `--validate` flag only performs local length + prefix checks.