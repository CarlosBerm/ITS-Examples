"""
get_model_directory.py — load the Model Directory tab from the LOCAL workbook into a DataFrame
of the models a batch run should evaluate, and expose a tab-existence check.

Local-file twin of GSheets Evaluation/get_model_directory.py. The Model Directory is a tab in
the SAME .xlsx as the Prompt Repository. It lists the models to evaluate and, for each, the
results tab its responses are written into:

    A: Model ID         the model name sent to the gateway (e.g. gpt-5.5)
    B: Model Tab Name   the results tab that model's responses are written into

The header row is row 5 (same convention as the Prompt Repository). Only rows with BOTH
columns filled are usable. The two partial-row cases (a Model ID with no tab, or a tab with no
Model ID) are reported and skipped, so a half-filled row never silently drops a model.

Reuses get_prompts' workbook helpers (open_workbook, _read_tab_dataframe, _find_column) — no
duplicated file-opening code.

Public API:
    get_model_directory_df(tab_name, workbook_path=None) -> DataFrame['Model ID','Model Tab Name']
    existing_tab_titles(workbook_path=None)              -> set of the workbook's tab titles
"""

import sys

import pandas as pd

# Importing get_prompts runs its os.chdir(<this folder>) + load_dotenv(".env") on import, so
# by the time these functions run, cwd is this folder and LOCAL_WORKBOOK is loaded.
from get_prompts import open_workbook, _read_tab_dataframe, _find_column

MODEL_ID_COLUMN = "Model ID"
MODEL_TAB_NAME_COLUMN = "Model Tab Name"

# The Model Directory table spans columns A–B (2 columns).
DIRECTORY_LAST_COLUMN = 2


def get_model_directory_df(tab_name, workbook_path=None):
    """Read the Model Directory `tab_name` and return a DataFrame of the rows that have BOTH a
    Model ID and a Model Tab Name. Partial rows are reported to the console and skipped.

    `workbook_path` defaults to env LOCAL_WORKBOOK.
    """
    wb = open_workbook(workbook_path, data_only=True, read_only=True)
    try:
        df = _read_tab_dataframe(wb, tab_name, DIRECTORY_LAST_COLUMN)
    finally:
        wb.close()

    model_col = _find_column(df.columns, MODEL_ID_COLUMN)
    tab_col = _find_column(df.columns, MODEL_TAB_NAME_COLUMN)
    missing = [
        name
        for name, col in ((MODEL_ID_COLUMN, model_col), (MODEL_TAB_NAME_COLUMN, tab_col))
        if col is None
    ]
    if missing:
        print(
            f"Error: the Model Directory is missing column(s) {missing}. "
            f"Found: {list(df.columns)}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Classify every row by which of the two cells are filled. Only both-filled rows are kept;
    # the two partial cases are reported so a half-filled row is never silently dropped.
    kept = []
    for _, row in df.iterrows():
        model_id = str(row[model_col]).strip()
        tab_value = str(row[tab_col]).strip()

        if model_id and tab_value:
            kept.append({MODEL_ID_COLUMN: model_id, MODEL_TAB_NAME_COLUMN: tab_value})
        elif model_id and not tab_value:
            print(
                f"⚠ Model '{model_id}' in the Model Directory has no Model Tab Name "
                "assigned — skipping it (there's nowhere to write its responses)."
            )
        elif tab_value and not model_id:
            print(
                f"⚠ Model Tab Name '{tab_value}' in the Model Directory has no Model ID "
                "assigned — skipping it (there's no model to evaluate for it)."
            )
        # both blank → silently ignore (an empty spacer row).

    directory_df = pd.DataFrame(kept, columns=[MODEL_ID_COLUMN, MODEL_TAB_NAME_COLUMN])
    if directory_df.empty:
        print(
            "Error: the Model Directory has no rows with both a Model ID and a Model Tab Name.",
            file=sys.stderr,
        )
        sys.exit(1)

    return directory_df


def existing_tab_titles(workbook_path=None):
    """Return the set of tab (worksheet) titles in the workbook.

    Used to confirm each Model Tab Name actually exists before a run spends any gateway tokens.
    `workbook_path` defaults to env LOCAL_WORKBOOK.
    """
    wb = open_workbook(workbook_path, data_only=True, read_only=True)
    try:
        return set(wb.sheetnames)
    finally:
        wb.close()


def main():
    # Standalone check: read + print the Model Directory (reads MODEL_DIRECTORY_TAB from .env,
    # falling back to "Model Directory").
    import os

    tab_name = os.environ.get("MODEL_DIRECTORY_TAB", "Model Directory").strip()
    directory_df = get_model_directory_df(tab_name)
    print(f"\nLoaded {len(directory_df)} model(s) from '{tab_name}':\n")
    print(directory_df.to_string(index=False))


if __name__ == "__main__":
    main()
