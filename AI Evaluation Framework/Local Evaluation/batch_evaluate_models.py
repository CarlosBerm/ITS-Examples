"""
batch_evaluate_models.py — evaluate MANY models in one run against a shared prompt library,
using a LOCAL workbook.

Local-file twin of GSheets Evaluation/batch_evaluate_models.py. Where evaluate_model.py
evaluates a single model, this driver reads a Model Directory tab (Model ID + Model Tab Name)
from the SAME local .xlsx and runs the pipeline once per model, writing each model's responses
into its own results tab.

Pipeline:
    1. read the Model Directory       (get_model_directory.get_model_directory_df)
    2. check every Model Tab Name exists (get_model_directory.existing_tab_titles)
    3. read the Prompt Repository once (get_prompts.get_prompts_df) — shared by all models
    4. per model: get responses (per-prompt errors are recorded AS the response text, same as
       evaluate_model.py) and write the tab (get_responses.get_responses_df,
       populate_model_tab.populate_model_tab)
    5. print a success / skip summary

Set the two tab names below, then run:

    cd "Local Evaluation"
    python batch_evaluate_models.py

The workbook comes from LOCAL_WORKBOOK in .env (all tabs live in the same .xlsx). Results are
written into it in place, so point LOCAL_WORKBOOK at a copy if you want to keep a pristine
snapshot.
"""

# ============================ INPUT FIELDS — set these ============================
MODEL_DIRECTORY_TAB = "Model Directory"        # tab listing Model ID + Model Tab Name
PROMPT_REPOSITORY_TAB = "Prompt Repository"    # tab to read prompts from (shared by all models)
# =================================================================================

from get_model_directory import (
    MODEL_ID_COLUMN,
    MODEL_TAB_NAME_COLUMN,
    get_model_directory_df,
    existing_tab_titles,
)
from get_prompts import get_prompts_df
from get_responses import get_responses_df
from populate_model_tab import populate_model_tab


def main():
    # 1. Model Directory ---------------------------------------------------------
    print(f"Reading the Model Directory from '{MODEL_DIRECTORY_TAB}'...")
    directory_df = get_model_directory_df(MODEL_DIRECTORY_TAB)
    print(f"  {len(directory_df)} model(s) with both a Model ID and a Model Tab Name.\n")

    # results collects one entry per model for the final summary:
    #   (model_id, tab, status, detail)  where status is "ok" | "skipped" | "failed".
    results = []

    # 2. Check every Model Tab Name exists BEFORE spending any gateway tokens -----
    print("Checking that each Model Tab Name exists in the workbook...")
    titles = existing_tab_titles()

    valid = []  # [(model_id, tab), ...] — models whose tab was located
    for _, row in directory_df.iterrows():
        model_id = row[MODEL_ID_COLUMN]
        tab = row[MODEL_TAB_NAME_COLUMN]
        if tab in titles:
            valid.append((model_id, tab))
        else:
            available = ", ".join(sorted(titles)) or "(none)"
            print(
                f"⚠ Model '{model_id}': its Model Tab Name '{tab}' was not found in the "
                f"workbook — skipping. Available tabs: {available}"
            )
            results.append((model_id, tab, "skipped", "Model Tab Name not found"))

    if not valid:
        print("\nNo models with a locatable Model Tab Name — nothing to evaluate.\n")
        _print_summary(results)
        return
    print(f"  {len(valid)} model(s) ready to evaluate.\n")

    # 3. Prompt Repository (read once, reused by every model) --------------------
    print(f"Reading prompts from '{PROMPT_REPOSITORY_TAB}'...")
    prompts_df = get_prompts_df(PROMPT_REPOSITORY_TAB)
    print(f"  loaded {len(prompts_df)} prompt(s).\n")

    # 4. Evaluate each model and write its tab. Per-prompt errors — including content-policy
    #    refusals and empty/filtered completions — are recorded AS the response text by
    #    get_responses_df and kept in the tab (same behavior as evaluate_model.py). Only an
    #    unexpected failure of the whole stage (e.g. a bad key or a save/permission error)
    #    skips that one model, so a single hiccup doesn't kill the whole batch. -----------
    total_models = len(valid)
    for i, (model_id, tab) in enumerate(valid, start=1):
        print(f"===== [{i}/{total_models}] Evaluating '{model_id}' -> '{tab}' =====")
        try:
            responses_df = get_responses_df(prompts_df, model_id, tab)
            populate_model_tab(responses_df, tab)
            results.append((model_id, tab, "ok", f"{len(responses_df)} rows written"))
        except SystemExit as e:
            # A pipeline stage called sys.exit (e.g. a save/permission error). Its own
            # diagnostic already printed above; record it and move on to the next model.
            print(
                f"\n⚠ '{model_id}' -> '{tab}' failed and was skipped "
                f"(a pipeline stage exited with code {e.code}). See the error above."
            )
            results.append((model_id, tab, "failed", f"pipeline exited (code {e.code})"))
        except Exception as e:
            # Never let one model kill the whole batch.
            print(
                f"\n⚠ '{model_id}' -> '{tab}' failed and was skipped: "
                f"{type(e).__name__}: {e}"
            )
            results.append((model_id, tab, "failed", f"{type(e).__name__}: {e}"))

        print()

    # 5. Summary -----------------------------------------------------------------
    _print_summary(results)


def _print_summary(results):
    """Print the end-of-run summary: which models were written, and which were skipped/failed."""
    print("========================= DONE — batch summary =========================")

    succeeded = [r for r in results if r[2] == "ok"]
    not_written = [r for r in results if r[2] != "ok"]

    print(f"Written ({len(succeeded)}):")
    if succeeded:
        for model_id, tab, _status, detail in succeeded:
            print(f"  ✓ {model_id} -> {tab}  ({detail})")
    else:
        print("  (none)")

    print(f"Skipped / failed ({len(not_written)}):")
    if not_written:
        for model_id, tab, status, detail in not_written:
            print(f"  ✗ {model_id} -> {tab}  ({status}: {detail})")
    else:
        print("  (none)")


if __name__ == "__main__":
    main()
