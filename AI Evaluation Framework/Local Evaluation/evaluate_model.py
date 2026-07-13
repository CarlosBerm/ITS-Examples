"""
evaluate_model.py — single driver for the LOCAL AI evaluation pipeline. Evaluates 1 model.

Local-file twin of GSheets Evaluation/evaluate_model.py. Chains the three stages end to end,
entirely in memory (pandas DataFrames), against a local .xlsx workbook instead of a Google
Sheet:

    read prompts (get_prompts)  ->  ask the model (get_responses)  ->  write results (populate_model_tab)

Set the three input fields below, then run:

    cd "Local Evaluation"
    python evaluate_model.py

The workbook itself comes from LOCAL_WORKBOOK in .env (all three tabs live in the same .xlsx);
this driver only chooses the model and the two tabs. There is no Google Cloud or service
account — reading and writing the local file needs nothing but the file itself (and an API
key for the gateway). The results are written into the workbook in place, so point
LOCAL_WORKBOOK at a copy if you want to keep a pristine snapshot.
"""

# ============================ INPUT FIELDS — set these ============================
MODEL = "gpt-5.5"                            # model to evaluate (must be valid on the gateway)
PROMPT_REPOSITORY_TAB = "Prompt Repository"  # tab to read prompts from
MODEL_OUTPUT_TAB = "GPT-5.5"                 # tab to write the model's responses into
# =================================================================================

from get_prompts import get_prompts_df
from get_responses import get_responses_df
from populate_model_tab import populate_model_tab


def main():
    print(f"Reading prompts from '{PROMPT_REPOSITORY_TAB}'...")
    prompts_df = get_prompts_df(PROMPT_REPOSITORY_TAB)
    print(f"  loaded {len(prompts_df)} prompt(s).\n")

    responses_df = get_responses_df(prompts_df, MODEL)

    print(f"\nWriting {len(responses_df)} response(s) to '{MODEL_OUTPUT_TAB}'...")
    populate_model_tab(responses_df, MODEL_OUTPUT_TAB)

    print("\nDONE! Evaluation run complete.")


if __name__ == "__main__":
    main()
