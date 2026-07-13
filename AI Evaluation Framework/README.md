# AI Evaluation Framework

A Python pipeline for **evaluating AI models against a shared prompt library**. Every model
answers the _same_ set of prompts through the [U-M GPT Toolkit](https://its.umich.edu/computing/ai/gpt-toolkit-in-depth)
gateway, and its responses are collected for scoring — so results across models are directly
comparable.

There are **two ways to run it**, sharing the same core logic but differing in where prompts
come from and where responses go:

|                      | **GSheets Evaluation**                          | **Local Evaluation**               |
| -------------------- | ----------------------------------------------- | ---------------------------------- |
| Prompts read from    | a shared **Google Sheet**                       | a **local file** on your machine   |
| Responses written to | tabs in the same Google Sheet                   | a **local file**                   |
| Extra setup          | Google Cloud service account + shared sheet     | none — just an API key             |
| Best for             | the team's shared, graded, dashboarded workflow | quick, offline, standalone runs    |
| Status               | ✅ built & tested                               | ✅ built & tested                   |

> **Setting up or running a mode?** Each folder has its own README with the exact steps:
> [`GSheets Evaluation/README.md`](GSheets%20Evaluation/README.md) ·
> [`Local Evaluation/README.md`](Local%20Evaluation/README.md). This document explains **what**
> the pipeline is and **why** it works the way it does.

---

## Why it's built this way

- **One shared prompt library → fair comparison.** Every model is graded on the exact same
  prompts (accuracy, instruction-following, context retention, safety/prompt-injection, math,
  robustness, ambiguity). Swapping models is a one-line change; the test set never drifts.
- **The Google Sheet is the single source of truth.** Non-technical evaluators edit prompts
  and score responses in one shared place. Scoring, categories, and dashboards **auto-compute**
  around the model outputs. Running the pipeline just refreshes the model-response columns
  in-place — no copy-paste, no emailed CSVs.
- **A local mode for when you don't need all that.** Not everyone has (or wants) a Google
  Cloud service account. Local Evaluation runs the same model logic against local files with
  nothing but an API key — good for quick iteration and offline testing.
- **Everything flows in memory (pandas DataFrames), no intermediate CSVs.** One command reads,
  runs, and writes. Fewer moving parts, no stale files left on disk.
- **Prompts run as one continuous conversation.** This is what makes multi-turn _memory_
  test cases work (e.g. "remember my student ID… ten prompts later, what is it?"). A guardrail
  in the system prompt tells the model to answer only the newest turn, so it doesn't replay the
  whole history.
- **Current facts are injected into the system prompt.** Web-verified 2026 U-M facts (president,
  enrollment, endowment, coach, latest championship) are supplied so models with older training
  cutoffs are graded against _today's_ ground truth instead of stale memorized data.
- **Adversarial prompts never abort a run.** Prompt-injection / policy-breaking test cases can
  make the gateway reject a request. Each call is wrapped so the failure is recorded **as that
  prompt's response** and the run keeps going.
- **Writes are surgical and safe.** The writer finds its target columns by header name and
  touches **only** the two response columns, leaving auto-computed columns and formulas intact.
  It overwrites in place (clearing stale rows from a longer previous run) and writes with the
  `RAW` option so a response beginning with `=` is stored as text, never executed as a formula.
- **Least-privilege service account.** Automation with no browser login and no human account.
  The read stages request read-only scope; only the write stage requests read/write.

---

## How the pipeline works

The core is three stages, chained entirely in memory:

```
   read prompts            ask the model              write responses
 ┌───────────────┐      ┌───────────────────┐      ┌────────────────────┐
 │ get_prompts   │ ───► │ get_responses     │ ───► │ populate_model_tab │   (GSheets)
 │  _df(tab)     │  df  │  _df(df, model)   │  df  │  (df, tab)         │
 └───────────────┘      └───────────────────┘      └────────────────────┘
   prompts DataFrame       responses DataFrame        results into the sheet
```

- **`get_prompts.py`** — reads the **Prompt Repository** tab (header on row 5, columns A–F),
  keeps only rows with a non-empty `Prompt Text`, and returns a DataFrame.
- **`get_responses.py`** — sends every prompt to the model over the gateway in one continuous
  conversation (with the current-facts system prompt and context-retention guardrail), catching
  per-prompt errors and recording them as the response. Returns a DataFrame of `Prompt ID` +
  `Model Output Response`.
- **`populate_model_tab.py`** — writes those two columns back into a model's results tab by
  header name (overwrite-in-place, formula-safe).

**GSheets Evaluation** offers two drivers on top of these stages:

- **`evaluate_model.py`** — evaluate **one** model into **one** results tab.
- **`batch_evaluate_models.py`** — evaluate **many** models in one run. It reads a **Model
  Directory** tab (`Model ID` + `Model Tab Name`, header row 5) via `get_model_directory.py`,
  checks that every target tab exists, reads the prompts once, then loops the models — writing
  each one's tab. Partial directory rows are warned-and-skipped; per-prompt errors are kept as
  responses; only an unexpected stage failure (e.g. a bad key) skips a single model, so one
  hiccup never kills the batch. A written/skipped summary prints at the end.

**Local Evaluation** offers the **same two drivers** (`evaluate_model.py` and
`batch_evaluate_models.py`) built on the **same three stages** — it just swaps the Google Sheet
for a local `.xlsx` workbook at both ends, reading and writing it with `openpyxl` instead of the
Sheets API. No Google Cloud, no service account: a `LOCAL_WORKBOOK` path in `.env` replaces the
sheet ID and the service-account key. The writer is held to the same standard as the GSheets one
— it finds the `Prompt ID` and `Model Output Response` columns by header name, overwrites in
place (clearing stale rows), stores responses as literal text so a leading `=` never becomes a
formula, and preserves every auto-computed column and dashboard (marking the file to recalculate
when it's next opened).

---

## Repository layout

```
AI Evaluation Framework/
├── README.md                        ← you are here (what & why)
├── Evaluation Framework Database Ver0.2.xlsx   ← local snapshot of the eval database
├── question_journey.html            ← presentation/animation of the pipeline
│
├── GSheets Evaluation/              ← evaluate against a shared Google Sheet  (built)
│   ├── README.md                     setup & how to run this mode
│   ├── evaluate_model.py             one model  → one tab   (driver)
│   ├── batch_evaluate_models.py      many models → many tabs (driver)
│   ├── get_prompts.py                stage 1: read Prompt Repository tab
│   ├── get_responses.py              stage 2: run prompts through the model
│   ├── populate_model_tab.py         stage 3: write responses back to a tab
│   ├── get_model_directory.py        read the Model Directory tab + tab-existence check
│   ├── requirements.txt
│   └── .env.example
│
└── Local Evaluation/               ← evaluate against a local .xlsx workbook  (built)
    ├── README.md                     setup & how to run this mode
    ├── evaluate_model.py             one model  → one tab   (driver)
    ├── batch_evaluate_models.py      many models → many tabs (driver)
    ├── get_prompts.py                stage 1: read Prompt Repository tab (+ shared workbook helpers)
    ├── get_responses.py              stage 2: run prompts through the model (identical to GSheets)
    ├── populate_model_tab.py         stage 3: write responses back to a tab
    ├── get_model_directory.py        read the Model Directory tab + tab-existence check
    ├── requirements.txt
    └── .env.example
```
