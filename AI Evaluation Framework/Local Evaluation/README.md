# Local Evaluation — setup & run

Evaluate models against **local files** — no Google Cloud, no service account, no shared sheet.
Just an API key. For what this does and why, see the [main README](../README.md).

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
pip install -r "Local Evaluation/requirements.txt"
```

**2. Configure `.env`**

```bash
cp "Local Evaluation/.env.example" "Local Evaluation/.env"
```

| Variable          | Description                  |
| ----------------- | --------------------------- |
| `OPENAI_API_KEY`  | your U-M GPT Toolkit API key |
| `OPENAI_API_BASE` | the gateway base URL         |

That's the entire difference from GSheets Evaluation: **no `GOOGLE_*` variables**, because
nothing talks to Google.

## Running

> 🚧 **Runner in progress.** The Local Evaluation driver is not built yet. Once it lands, it will
> read prompts from a local file, run them through the model, and write responses to a local
> results file — and this section will get the concrete run command. The setup above is all
> that's needed to be ready for it.

## Troubleshooting

| Symptom                                    | Likely cause & fix                                                        |
| ------------------------------------------ | ------------------------------------------------------------------------- |
| `Unable to load .env file.`                | No `.env` in this folder. Copy it from `.env.example`.                     |
| `KeyError: 'OPENAI_API_KEY'` / `OPENAI_API_BASE` | A required variable is missing from `.env`. Set both.               |
| `ModuleNotFoundError` (pandas / openai …)  | Dependencies not installed, or the venv isn't active. Re-run the install step. |
