# NumForge

**NumForge** is a lightweight command-line tool for generating all possible
numeric combinations that match a user-defined phone-number pattern.

It is a purely **local** tool. It does not perform network requests, does not
verify real phone numbers, and does not interact with any telecom, messaging,
or external service. It is intended for testing, development, and educational
purposes only.

---

## Features

- Interactive terminal menu — no GUI required.
- Country presets: **Iran, Azerbaijan, Turkey, United States, United Kingdom**.
- Predefined patterns per country + user-defined custom patterns.
- Uses `X` as the placeholder for unknown digits.
- Accurate combination count **before** generation begins.
- Confirmation prompt for large jobs.
- Configurable hard cap on total combinations.
- Memory-efficient generator (never stores all results in RAM).
- Live progress: count, percentage, speed, elapsed time.
- Graceful `Ctrl+C` handling — partial output is preserved safely.
- Output preview in terminal or saved to a `.txt` file.
- Overwrite protection with explicit confirmation.
- Input validation with clear error messages.

---

## Requirements

- Python **3.11+**
- No third-party packages

---

## Installation

```bash
git clone <your-repo-url> NumForge
cd NumForge
python --version  # ensure 3.11+
```

There is nothing to install — the project uses only the standard library.

---

## Usage

### Windows

```powershell
python main.py
```

### Linux / macOS

```bash
python3 main.py
```

Follow the on-screen prompts:

1. Choose a country.
2. Choose a predefined pattern or enter a custom one.
3. Review the calculated combination count.
4. Confirm if the job is large.
5. Choose output mode (terminal preview or file).
6. If saving to a file, provide a directory and filename.

---

## Pattern Syntax

- Digits `0`–`9` are treated as **known**.
- `X` is the placeholder for an **unknown** digit (expands to 0–9).
- Formatting characters `+`, `-`, `(`, `)`, and space are preserved.
- A pattern must contain at least one `X`.

Examples:

| Pattern           | Meaning                                                     |
| ----------------- | ----------------------------------------------------------- |
| `0912XXX1234`     | Known prefix/suffix; 3 unknowns → 1,000 combinations        |
| `98XXXXXXXXXX`    | 10 unknowns → 10,000,000,000 combinations                   |
| `+1 (XXX) XXX-XXXX` | 10 unknowns; formatting preserved                         |

---

## Examples

### Example 1 — small pattern

Input:

```
Pattern: 0912XXX123
```

Output:

```
Country              : Iran (+98)
Pattern              : 0912XXX123
Unknown positions    : 3
Total combinations   : 1,000
```

Preview (first few lines):

```
0912000123
0912001123
...
```

### Example 2 — saving to file

```
Output directory: /home/user/numforge
Filename        : results
```

Saved as `/home/user/numforge/results.txt`.

### Example 3 — progress output

```
  Progress: 40,000/100,000 ( 40.0%) | 512,340 gen/s |   0.1s
```

### Example 4 — Ctrl+C handling

```
[!] Generation interrupted by user (Ctrl+C).
    Partial output saved to: /home/user/numforge/results.txt
    Combinations written: 42,133
    Elapsed time: 0.3s
```

---

## Project Structure

```
NumForge/
├── main.py          # CLI entry point and interactive workflow
├── generator.py     # Memory-efficient combination generator
├── countries.py     # Country definitions and patterns
├── validators.py    # Input and pattern validation
├── output.py        # Terminal display + file writing
├── config.py        # Tunable constants
├── README.md
└── requirements.txt
```

---

## Configuration

Edit `config.py` to tune:

- `CONFIRMATION_THRESHOLD` — ask for confirmation above this count.
- `MAX_COMBINATIONS` — hard cap to prevent enormous outputs.
- `PROGRESS_INTERVAL` — how often to refresh progress.
- `PLACEHOLDER` — the unknown-digit placeholder (default `X`).
- `DEFAULT_OUTPUT_DIR` / `DEFAULT_OUTPUT_FILENAME`.

---

## Limitations

- Generates **all** combinations mechanically; it does not know which
  numbers are actually assigned or reachable.
- Large patterns (e.g. 10 unknown digits = 10 billion combinations) can
  produce huge files. Use the built-in cap and confirmation prompt.
- Pattern characters are limited to digits, `X`, and formatting characters.

---

## Legal and Responsible Use

NumForge is a **local pattern-combination generator** for testing,
development, and educational use. It does **not**:

- scan or verify phone numbers,
- send SMS, make calls, or use Telegram/WhatsApp,
- query telecom APIs,
- discover contacts,
- target real individuals.

You are responsible for how you use this tool and for complying with all
applicable laws in your jurisdiction. Do not use NumForge for spam,
harassment, unauthorized access, or any illegal activity.
