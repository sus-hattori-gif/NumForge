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

NumForge v1.1 supports four pattern constructs:

| Syntax | Meaning | Example |
|---|---|---|
| `0`–`9` | Fixed digit | `09` |
| `X` | Any digit 0–9 | `09XX...` |
| `[a-b]` | Digit range | `[0-5]` = 0,1,2,3,4,5 |
| `[abc]` | Digit set | `[02468]` = even digits |
| `[a,b,c]` | Set with commas | `[0,2,4,6,8]` |
| `[a-c,e]` | Mixed | `[0-3,7,9]` = 0,1,2,3,7,9 |

Formatting characters `+`, `-`, `(`, `)`, and space are preserved.

**Examples:**

| Pattern | Combinations |
|---|---|
| `0912XXX1234` | 1,000 |
| `0912[0-5]XX123` | 600 |
| `0912[02468]XX123` | 500 |
| `0912{1,3,5,7,9}XX123` (فقط با `[...]`) | — |
| `0912[0-3,7,9]XX123` | 600 |
| `+1 (XXX) XXX-XXXX` | 10,000,000,000 ⚠️ |

---

## Examples

### Example 1 — small pattern

Input:

```
Pattern: 0912XXX123
```

## Output System

After choosing a pattern, NumForge asks:

1. **Output mode**: terminal preview (first 50) or save to file.
2. **Format**: `txt`, `csv`, or `jsonl`.
3. **Compression**: plain or `.gz`.
4. **Directory** and **filename**.

Example paths:

```
D:\NumForge\results.csv
/home/user/numforge/results.jsonl.gz
```

Overwriting an existing file requires explicit confirmation.

### Resume after Ctrl+C

If a job is interrupted, a `.numforge.state` file is written next to
the output. On the next run, selecting the same output file offers:

- Resume from where it stopped
- Start over (delete previous output)
- Cancel

The state file is removed automatically after successful completion.
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

---

## Non-Interactive CLI (v1.2)

Run NumForge without the interactive menu:

```bash
# Basic generation
python main.py generate -c ir -p "0912XXX1234" -o out.txt

# CSV output with gzip
python main.py generate -c ir -p "0912XXX" -o out.csv.gz -f csv --gzip

# Apply structural rules
python main.py generate -c ir -p "09XXXXXXXXX" -o out.txt --validate

# Multi-pattern from file
python main.py generate -c ir --patterns-file patterns.txt -o all.txt

# Load a saved profile
python main.py generate --profile iran-tests

# Preview only
python main.py preview -c ir -p "0912XXX" -n 20

# List countries
python main.py countries

# Version
python main.py --version
```

### Flags

| Flag | Description |
|---|---|
| `-c, --country` | Country id (`ir`, `az`, `tr`, `us`, `uk`) |
| `-p, --pattern` | Pattern with `X` and `[...]` |
| `--patterns-file` | File with one pattern per line |
| `-o, --output` | Output file path |
| `-f, --format` | `txt`, `csv`, `jsonl` |
| `--gzip` | Compress with gzip |
| `--validate` | Apply local country rules |
| `--max N` | Override max combinations |
| `-y, --yes` | Skip large-job confirmation |
| `--log` | `quiet`, `normal`, `verbose` |

### Exit Codes

- `0` — success
- `1` — runtime error
- `2` — invalid input

## Profiles

Save reusable settings:

```bash
python main.py profile save iran-tests -c ir -p "0912XXX" -f csv --gzip --validate
python main.py profile list
python main.py profile show iran-tests
python main.py generate --profile iran-tests
```

Profiles live in `./profiles/<name>.toml` or `~/.numforge/profiles/<name>.toml`.

### Example profile

```toml
name = "iran-tests"
country = "ir"
pattern = "0912[0-5]XX1234"
format = "csv"
compressed = true
output_dir = "./results"
validate = true
```

## Local Structural Validation

With `--validate`, NumForge filters out combinations that cannot be
real phone numbers *for the selected country* — based only on local
length and prefix rules.

**This is not verification.** It does not check whether a number
exists, is assigned, or is reachable. It never contacts any service.