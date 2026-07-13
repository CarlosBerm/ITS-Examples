# GSheets Evaluation — setup & run

Evaluate models against a shared **Google Sheet** and write their responses back into it.
For what this does and why, see the [main README](../README.md).

## Prerequisites

- **Python 3.9+** (`python3 --version`).
- A **U-M GPT Toolkit API key + base URL** — see the
  [GPT Toolkit docs](https://its.umich.edu/computing/ai/gpt-toolkit-in-depth). List valid model
  names with `python ../../Python/get_models.py`.
- This repo cloned, with a virtual environment active:
  ```bash
  git clone https://github.com/CarlosBerm/ITS-Examples.git
  cd "ITS-Examples/AI Evaluation Framework"
  python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
  ```

## Setup

**1. Install dependencies**

```bash
pip install -r "GSheets Evaluation/requirements.txt"
```

**2. Create a service account & share the sheet**

- In Google Cloud, create a **service account** and download its **JSON key**. Store it
  **outside** the repo (key files are git-ignored regardless).
- Open the evaluation spreadsheet → **Share**, and add the service account's `client_email`:
  - **Viewer** is enough to _read_ prompts, but
  - **Editor** is required to _write_ responses back.
- The spreadsheet must be a **native Google Sheet**, not an uploaded `.xlsx`. If it's an Excel
  upload, open it in Drive → **File → Save as Google Sheets**.

**3. Configure `.env`**

```bash
cp "GSheets Evaluation/.env.example" "GSheets Evaluation/.env"
```

| Variable                      | Description                                                        |
| ----------------------------- | ----------------------------------------------------------------- |
| `OPENAI_API_KEY`              | your U-M GPT Toolkit API key                                      |
| `OPENAI_API_BASE`             | the gateway base URL                                              |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | path to the service-account JSON key                             |
| `GOOGLE_SHEET_ID`             | the spreadsheet ID (the part between `/d/` and `/edit` in its URL) |

> The individual stage modules can be run standalone for debugging; those read an optional
> `GOOGLE_SHEET_TAB`. The drivers don't need it — they set tab names at the top of the file.

**4. Spreadsheet structure the code expects** (every tab uses **row 5 as its header**):

| Tab                   | Purpose                                     | Key columns                                                     |
| --------------------- | ------------------------------------------- | -------------------------------------------------------------- |
| **Prompt Repository** | the shared prompt library                   | A–F incl. `Prompt ID`, `Prompt Text`                           |
| **Model Directory**   | which models the batch driver evaluates     | `Model ID`, `Model Tab Name`                                   |
| one tab **per model** | where that model's responses land           | `Prompt ID`, `Model Output Response` (+ auto-computed columns) |

## Running

Run from inside this folder:

```bash
cd "GSheets Evaluation"
```

### One model — `evaluate_model.py`

Edit the input fields at the top of the file, then run it:

```python
MODEL                 = "gpt-5.5"            # model to evaluate (must be valid on the gateway)
PROMPT_REPOSITORY_TAB = "Prompt Repository"  # tab to read prompts from
MODEL_OUTPUT_TAB      = "GPT-5.5"            # tab to write responses into
```

```bash
python evaluate_model.py
```

### Many models — `batch_evaluate_models.py`

List the models in the **Model Directory** tab (one `Model ID` + `Model Tab Name` per row),
set the two fields at the top of the file, then run:

```python
MODEL_DIRECTORY_TAB   = "Model Directory"
PROMPT_REPOSITORY_TAB = "Prompt Repository"
```

```bash
python batch_evaluate_models.py
```

It prints per-model `[i/N] <model> -> <tab>` progress and a written/skipped summary at the end.

### Reasoning mode (automatic)

If a model's **results tab name contains the word "Reasoning"** (e.g. `GPT-5-mini (Reasoning)`,
`Claude Opus 4.6 (Reasoning)`), every call for that model is made with the gateway's reasoning at
its **highest** setting (`reasoning_effort="high"`). Any other tab is called with **no reasoning
parameter** — the gateway default. So the same base model can be evaluated both ways just by
giving it a plain tab and a "(Reasoning)" tab: set `MODEL_OUTPUT_TAB` to the "(Reasoning)" tab for
one model, or list both tabs in the Model Directory for a batch run. The console line
`... [highest reasoning effort]` vs `... [default — no reasoning parameter]` shows which was used.

## Troubleshooting

| Symptom                                       | Likely cause & fix                                                                          |
| --------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `Unable to load .env file.`                   | No `.env` in this folder. Copy it from `.env.example`.                                       |
| `GOOGLE_SHEET_ID is not set in .env.`         | Missing/mistyped var. It must be exactly `GOOGLE_SHEET_ID`.                                  |
| HTTP **400** "must not be an Office file"     | The file is an uploaded `.xlsx`, or a tab name is wrong. Convert to a native Sheet; recheck tab names. |
| HTTP **403** on read/write                    | The sheet isn't shared with the service account. Add its `client_email` — as **Editor** to write. |
| HTTP **404**                                  | `GOOGLE_SHEET_ID` points to the wrong (or nonexistent) spreadsheet.                         |
| `service account key … not found`             | `GOOGLE_SERVICE_ACCOUNT_FILE` path is wrong. Point it at your downloaded JSON key.           |
| `Model Tab Name '…' was not found` (batch)    | A `Model Tab Name` in the Model Directory doesn't match a real tab. Fix the name or create the tab. |
| `ModuleNotFoundError` (pandas / openai / google…) | Dependencies not installed, or the venv isn't active. Re-run the install step.           |
