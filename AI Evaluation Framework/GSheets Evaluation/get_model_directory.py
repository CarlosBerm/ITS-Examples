"""
get_model_directory.py — load the Model Directory tab into a DataFrame of the models a batch
run should evaluate, and expose a tab-existence check.

The Model Directory is a tab in the SAME Google Sheet as the Prompt Repository. It lists the
models to evaluate and, for each, the results tab its responses are written into:

    A: Model ID         the model name sent to the gateway (e.g. gpt-5.5)
    B: Model Tab Name   the results tab that model's responses are written into

The header row is row 5 (same convention as the Prompt Repository). Only rows with BOTH
columns filled are usable. The two partial-row cases (a Model ID with no tab, or a tab with
no Model ID) are reported and skipped, so a half-filled row never silently drops a model.

Reuses get_prompts' service-account auth and column matcher — read-only access is enough
since this module only reads.

Public API:
    get_model_directory_df(tab_name, spreadsheet_id=None) -> DataFrame['Model ID','Model Tab Name']
    existing_tab_titles(spreadsheet_id=None)              -> set of the sheet's tab titles
"""

import os
import sys

import pandas as pd
from googleapiclient.errors import HttpError

# Importing get_prompts runs its os.chdir(<this folder>) + load_dotenv(".env") on import,
# so by the time these functions run, cwd is this folder and GOOGLE_SHEET_ID is loaded.
from get_prompts import get_sheets_service, _find_column

MODEL_ID_COLUMN = "Model ID"
MODEL_TAB_NAME_COLUMN = "Model Tab Name"

# The Model Directory table's header row (same as the Prompt Repository).
HEADER_ROW = 5


def _resolve_spreadsheet_id(spreadsheet_id):
    """Return the passed spreadsheet id or fall back to env GOOGLE_SHEET_ID."""
    spreadsheet_id = spreadsheet_id or os.environ.get("GOOGLE_SHEET_ID")
    if not spreadsheet_id:
        print("Error: GOOGLE_SHEET_ID is not set in .env.", file=sys.stderr)
        sys.exit(1)
    return spreadsheet_id


def get_model_directory_df(tab_name, spreadsheet_id=None):
    """Read the Model Directory `tab_name` and return a DataFrame of the rows that have BOTH
    a Model ID and a Database Tab. Partial rows are reported to the console and skipped.

    `spreadsheet_id` defaults to env GOOGLE_SHEET_ID.
    """
    spreadsheet_id = _resolve_spreadsheet_id(spreadsheet_id)

    # Header row is row 5, columns A–B. Quote the tab so names with spaces work.
    tab = (tab_name or "").strip()
    range_name = f"'{tab}'!A{HEADER_ROW}:B" if tab else f"A{HEADER_ROW}:B"

    service = get_sheets_service()
    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
    except HttpError as e:
        status = getattr(e.resp, "status", "?")
        print(f"Error: the Sheets API returned HTTP {status} — {e.reason}", file=sys.stderr)
        if str(status) == "400":
            print(
                f"  A 400 usually means the tab '{tab_name}' doesn't exist, or the file is "
                "an uploaded .xlsx rather than a native Google Sheet.",
                file=sys.stderr,
            )
        elif str(status) == "403":
            print(
                "  A 403 usually means the sheet isn't shared with the service account. "
                "Add the client_email from the service account JSON as a Viewer.",
                file=sys.stderr,
            )
        elif str(status) == "404":
            print("  A 404 usually means GOOGLE_SHEET_ID is wrong.", file=sys.stderr)
        sys.exit(1)

    values = result.get("values", [])
    if not values:
        print(f"No data found in range '{range_name}'.", file=sys.stderr)
        sys.exit(1)

    header = values[0]
    data_rows = values[1:]

    # The API drops trailing empty cells, so rows are ragged. Pad (and defensively truncate)
    # every row to the header width so the DataFrame is rectangular.
    width = len(header)
    normalized_rows = [(row + [""] * width)[:width] for row in data_rows]
    df = pd.DataFrame(normalized_rows, columns=header)

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


def existing_tab_titles(spreadsheet_id=None):
    """Return the set of tab (worksheet) titles in the spreadsheet.

    Used to confirm each Database Tab actually exists before a run spends any gateway tokens.
    `spreadsheet_id` defaults to env GOOGLE_SHEET_ID.
    """
    spreadsheet_id = _resolve_spreadsheet_id(spreadsheet_id)
    service = get_sheets_service()
    try:
        meta = (
            service.spreadsheets()
            .get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title")
            .execute()
        )
    except HttpError as e:
        status = getattr(e.resp, "status", "?")
        print(
            f"Error: couldn't read the spreadsheet's tab list (HTTP {status} — {e.reason}).",
            file=sys.stderr,
        )
        sys.exit(1)
    return {sheet["properties"]["title"] for sheet in meta.get("sheets", [])}


def main():
    # Standalone check: read + print the Model Directory (reads MODEL_DIRECTORY_TAB from .env,
    # falling back to "Model Directory").
    tab_name = os.environ.get("MODEL_DIRECTORY_TAB", "Model Directory").strip()
    directory_df = get_model_directory_df(tab_name)
    print(f"\nLoaded {len(directory_df)} model(s) from '{tab_name}':\n")
    print(directory_df.to_string(index=False))


if __name__ == "__main__":
    main()
