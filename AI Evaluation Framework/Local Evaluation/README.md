# Local Evaluation — setup & run

Evaluate models against a **local `.xlsx` workbook** — no Google Cloud, no service account, no
shared sheet. Just an API key and the file on your disk. For what this does and why, see the
[main README](../README.md).

It is the same three-stage pipeline as GSheets Evaluation (read prompts → ask the model →
write responses), and the same drivers (`evaluate_model.py` for one model,
`batch_evaluate_models.py` for many). The only difference is that every read and write targets
a local workbook via `openpyxl` instead of the Google Sheets API. Because it's the same eval
database — the `Prompt Repository`, `Model Directory`, and per-model tabs all live in the one
`.xlsx`, with the header on row 5 — results stay directly comparable with the GSheets mode.

## Prerequisites

- **Python 3.9+** (`python3 --version`).
- A **U-M GPT Toolkit API key + base URL** — see the
  [GPT Toolkit docs](https://its.umich.edu/computing/ai/gpt-toolkit-in-depth). List valid model
  names with `python ../../Python/get_models.py`.
- A **local copy of the eval database `.xlsx`** (a native Excel workbook). The repo ships one:
  `../Evaluation Framework Database Ver0.2.xlsx`.
- This repo cloned, with a virtual environment active:
  ```bash
  git clone https://github.com/CarlosBerm/ITS-Examples.git
  cd "ITS-Examples/AI Evaluation Framework"
  python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
  ```

## Setup

**1. Install dependencies**

```bash
pip install -r "Local Evaluation/requirements.txt"
```

**2. Configure `.env`**

```bash
cp "Local Evaluation/.env.example" "Local Evaluation/.env"
```

| Variable          | Description                                                                 |
| ----------------- | --------------------------------------------------------------------------- |
| `OPENAI_API_KEY`  | your U-M GPT Toolkit API key                                                 |
| `OPENAI_API_BASE` | the gateway base URL                                                        |
| `LOCAL_WORKBOOK`  | path to the `.xlsx` eval database to read prompts from and write results to. Relative paths are resolved from this `Local Evaluation/` folder. Defaults to `../Evaluation Framework Database Ver0.2.xlsx`. |

The difference from GSheets Evaluation: **no `GOOGLE_*` variables** (nothing talks to Google),
and a `LOCAL_WORKBOOK` path instead of a sheet ID.

> **Responses are written into `LOCAL_WORKBOOK` in place** — the same way the GSheets mode
> overwrites the shared sheet. The writer touches only the `Prompt ID` and
> `Model Output Response` columns (found by header name) and preserves every other column's
> formulas, so the auto-computed categories, scores, and dashboards keep working; they
> **recalculate the next time you open the file** in Excel / LibreOffice / Google Sheets.
> If you want to keep a pristine snapshot, point `LOCAL_WORKBOOK` at a **copy**. (Note:
> round-tripping the file through `openpyxl` drops one advanced cross-sheet dropdown; the
> ordinary dropdowns, values, and formulas are preserved.)

## Running

**Evaluate one model** — set `MODEL`, `PROMPT_REPOSITORY_TAB`, and `MODEL_OUTPUT_TAB` at the
top of `evaluate_model.py`, then:

```bash
cd "Local Evaluation"
python evaluate_model.py
```

**Evaluate many models in one run** — list the models in the workbook's `Model Directory` tab
(`Model ID` + `Model Tab Name`, one per row, header on row 5), set `MODEL_DIRECTORY_TAB` and
`PROMPT_REPOSITORY_TAB` at the top of `batch_evaluate_models.py`, then:

```bash
cd "Local Evaluation"
python batch_evaluate_models.py
```

It checks that every target tab exists **before** spending any gateway tokens, evaluates each
model, writes its tab, and prints a written/skipped summary. Each `Model Tab Name` must already
exist as a tab in the workbook.

You can also run the stages standalone for a quick check (no driver):

```bash
python get_prompts.py           # print the prompts it would send
python get_model_directory.py   # print the models a batch run would evaluate
```

## Troubleshooting

| Symptom                                          | Likely cause & fix                                                             |
| ------------------------------------------------ | ------------------------------------------------------------------------------ |
| `Unable to load .env file.`                      | No `.env` in this folder. Copy it from `.env.example`.                          |
| `KeyError: 'OPENAI_API_KEY'` / `OPENAI_API_BASE` | A required variable is missing from `.env`. Set both.                          |
| `local workbook '...' not found`                 | `LOCAL_WORKBOOK` points nowhere. Set it to your `.xlsx` (relative to this folder). |
| `no tab named '...' in the workbook`             | The tab name doesn't match a sheet in the workbook. Check for exact spelling.   |
| `couldn't save '...'. Is it open in Excel?`      | The workbook is locked by another program. Close it and re-run.                 |
| `ModuleNotFoundError` (pandas / openai / openpyxl …) | Dependencies not installed, or the venv isn't active. Re-run the install step. |
