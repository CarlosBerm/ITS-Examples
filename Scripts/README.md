# Running `csv_questions.py`

This guide walks you through everything needed to run `csv_questions.py`, starting from a clean machine. The script reads a list of questions from a CSV file, sends each one to a model through the [U-M GPT Toolkit](https://its.umich.edu/computing/ai/gpt-toolkit-in-depth) API, and writes every question/response pair to `output.csv`.

## What the script does

1. Loads your API credentials from a `.env` file.
2. Reads questions from `input_questions.csv` (a CSV with a `question` column).
3. Sends each question to the configured model using the Chat Completions API.
4. Saves the results to `output.csv` next to the script.

> **Note:** The script calls `os.chdir()` to its own folder when it runs. That means `.env`, `input_questions.csv`, and the generated `output.csv` are **always** read from and written to the `Scripts/` folder — no matter which directory you launch the script from.

## Prerequisites

- **Python 3.9 or newer** — check with `python3 --version`.
- **git** — check with `git --version`.
- **A U-M GPT Toolkit API key and base URL.** See the [GPT Toolkit documentation](https://its.umich.edu/computing/ai/gpt-toolkit-in-depth) for how to request access.

## Step 1 — Clone the repository

```bash
git clone https://github.com/CarlosBerm/ITS-Examples.git
cd ITS-Examples
```

This creates an `ITS-Examples/` folder containing the `Scripts/` and `Python/` directories used below. Run the remaining commands from the repository root (`ITS-Examples/`) unless noted otherwise.

## Step 2 — Create and activate a virtual environment

A virtual environment keeps this project's dependencies isolated from the rest of your system.

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Once activated, your shell prompt shows `(.venv)`. Run `deactivate` at any time to exit the environment. The `.venv/` folder is already git-ignored, so it won't be committed.

## Step 3 — Install dependencies

The Python dependencies are pinned in `Python/requirements.txt` (this includes `pandas`, which the script uses to read and write CSVs):

```bash
pip install -r Python/requirements.txt
```

## Step 4 — Configure your credentials

The script loads credentials from a `.env` file **in the `Scripts/` folder**. A template lives in the `Python/` folder; copy it into `Scripts/`:

```bash
cp Python/.env.example Scripts/.env
```

Then open `Scripts/.env` and fill in your values. The script only uses the first three variables below, but the template includes others used by the broader example collection:

| Variable | Required by this script | Description |
|----------|:---:|-------------|
| `OPENAI_API_KEY` | ✅ | Your U-M GPT Toolkit API key |
| `OPENAI_API_BASE` | ✅ | The gateway base URL |
| `MODEL` | ✅ | The model to send questions to (must support Chat Completions) |
| `IMAGE_MODEL` | — | Used by other examples only |
| `EMBEDDING_MODEL` | — | Used by other examples only |
| `REASONING_MODEL` | — | Used by other examples only |

To see the list of valid model names for `MODEL`, run `python Python/get_models.py`. Make sure the model you pick supports the **Chat Completions** endpoint — see the compatibility matrix in the [top-level README](../README.md). The `.env` file is git-ignored, so your key will never be committed.

## Step 5 — Prepare your questions

Edit `Scripts/input_questions.csv`. It must have a header row with a column named exactly `question`, with one question per row:

```csv
question
Compare traditional publishing to self-publishing.
What might happen if humans colonized Mars?
How do I set up two-factor authentication on Gmail?
```

The repository ships with a sample `input_questions.csv` you can edit or replace.

## Step 6 — Run the script

```bash
cd Scripts
python csv_questions.py
```

As it runs, the script prints each question, the model's response, and a running progress count. When it finishes you'll see `DONE!`.

## Output

The script writes `output.csv` to the `Scripts/` folder with two columns:

| Column | Description |
|--------|-------------|
| `question` | The question taken from the input file |
| `response` | The model's answer |

Each run overwrites `output.csv`, so rename or move the file if you want to keep previous results.

## Troubleshooting

| Symptom | Likely cause and fix |
|---------|----------------------|
| `Unable to load .env file.` | No `.env` in the `Scripts/` folder. Complete Step 4. |
| `KeyError: 'OPENAI_API_KEY'` (or `OPENAI_API_BASE` / `MODEL`) | A required variable is missing from `.env`. Make sure all three are set. |
| `Error: File 'input_questions.csv' not found.` | The input CSV is missing from `Scripts/`. Complete Step 5. |
| `Error: 'question' column not found in CSV.` | Your input CSV's header column isn't named `question`. Rename it. |
| `ModuleNotFoundError: No module named 'pandas'` (or `openai`, `dotenv`) | Dependencies aren't installed, or the virtual environment isn't activated. Re-run Steps 2 and 3. |
| `command not found: python` | Use `python3` instead of `python` (common on macOS/Linux), or confirm the venv is activated. |
| An authentication or 4xx error from the API | Double-check `OPENAI_API_KEY` and `OPENAI_API_BASE`, and confirm `MODEL` supports Chat Completions in the compatibility matrix. |
