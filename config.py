"""Global configuration constants for NumForge."""

# Threshold above which an explicit confirmation prompt is required.
CONFIRMATION_THRESHOLD: int = 100_000

# Hard cap on combinations to prevent accidental enormous outputs.
MAX_COMBINATIONS: int = 10_000_000

# Number of combinations generated between progress updates / state saves.
PROGRESS_INTERVAL: int = 10_000

# Placeholder character for any digit 0-9.
PLACEHOLDER: str = "X"

# Default output directory (used if user presses Enter).
DEFAULT_OUTPUT_DIR: str = "."

# Default output filename.
DEFAULT_OUTPUT_FILENAME: str = "numforge_results.txt"

# Supported output formats.
SUPPORTED_FORMATS: tuple[str, ...] = ("txt", "csv", "jsonl")

# State file suffix (appended to output path).
STATE_SUFFIX: str = ".numforge.state"

# Version marker.
VERSION: str = "1.1.0"