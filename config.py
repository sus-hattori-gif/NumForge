"""Global configuration constants for NumForge."""

# Threshold above which an explicit confirmation prompt is required.
CONFIRMATION_THRESHOLD: int = 100_000

# Hard cap on combinations to prevent accidental enormous outputs.
MAX_COMBINATIONS: int = 10_000_000

# Number of combinations generated between progress updates.
PROGRESS_INTERVAL: int = 10_000

# Placeholder character for unknown digits.
PLACEHOLDER: str = "X"

# Default output directory (used if user presses Enter).
DEFAULT_OUTPUT_DIR: str = "."

# Default output filename.
DEFAULT_OUTPUT_FILENAME: str = "numforge_results.txt"