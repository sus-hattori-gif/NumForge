# Changelog

All notable changes to NumForge are documented in this file.

## [1.1.0] — 2025

### Added
- **Advanced pattern syntax**:
  - `[0-5]` digit ranges
  - `[02468]` digit sets
  - `[0,2,4,6,8]` comma-separated sets
  - `[0-3,7,9]` mixed ranges and digits
  - All classes are case-independent of `X` and can coexist.
- **Multiple output formats**: `txt`, `csv`, `jsonl`.
  - CSV includes a header and one number per row.
  - JSONL stores one `{"number": ..., "pattern": ..., "country": ...}` per line.
- **gzip compression** for output files (`.gz` extension).
- **Resume support**: interrupted jobs can be continued from the exact
  position via an atomic `.numforge.state` file. State file is
  automatically deleted after successful completion.
- **ETA display** during generation, plus improved progress formatting.
- **File size** and **format** shown in the completion summary.
- **Responsible-use notice** printed at the end of every generation.

### Changed
- `validators.validate_pattern` now delegates full syntax checking to
  the parser (single source of truth).
- `generator.iter_combinations` accepts an optional `start_index` for
  efficient resume via `itertools.islice`.
- `output.write_to_file` signature extended with `fmt`, `compressed`,
  `resume_state`, and `metadata` (backward-incompatible with v1.0 callers).
- `validators.validate_filename` now enforces the correct extension
  for the chosen format.

### Fixed
- Terminal progress no longer leaves an orphan newline when interrupted.
- CSV header is written only once, even on resume.

### Notes
- NumForge remains a **purely local** tool. No network requests,
  no verification, no messaging, no telecom interaction.