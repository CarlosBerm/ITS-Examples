"""
populate_model_tab.py — write model responses back into a Google Sheet results tab.

Takes a responses DataFrame (the get_responses.py format: 'Prompt ID' and
'Model Output Response' columns) and writes those two columns, row by row, into the
matching columns of a results tab. Every OTHER column on that tab (Run ID, Date, Model
Name, Core/Subcategory, Score, ...) autogenerates, so this script touches ONLY the two
it's given and leaves the rest alone.

Behavior notes:
  * Overwrites in place starting at the first data row (row 6, since the header is row
    5). It does not append below existing data, and it clears any stale rows left over
    from a longer previous run.
  * Writes with valueInputOption="RAW" so a response that happens to start with '=' (or
    a code-like Prompt ID) is stored as literal text, never interpreted as a formula.

This needs WRITE access, which means two things beyond the read scripts:
  * the read/write scope below, and
  * the sheet must be shared with the service account as an EDITOR (Viewer can't write).

This is a library module driven by evaluate_model.py; its public entry point is
populate_model_tab(responses_df, tab_name, spreadsheet_id=None).

Configuration (Scripts/.env), same as the read scripts:
    GOOGLE_SERVICE_ACCOUNT_FILE   path to the service account JSON key
    GOOGLE_SHEET_ID               the spreadsheet ID (used if spreadsheet_id isn't passed)
"""

import os
import sys

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Run from this script's folder so .env and the key path resolve the same way as the
# sibling scripts.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

if not load_dotenv(".env"):
    print("Unable to load .env file.", file=sys.stderr)
    sys.exit(1)

SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

# Read/write scope — unlike the read scripts, this one has to modify the sheet.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The header row of the results tab, and therefore the first data row.
HEADER_ROW = 5
FIRST_DATA_ROW = HEADER_ROW + 1

# Column names shared between the responses DataFrame and the results tab's header.
PROMPT_ID_COLUMN = "Prompt ID"
RESPONSE_COLUMN = "Model Output Response"


def get_sheets_service():
    """Authenticate with the service account and return a write-capable Sheets client."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(
            f"Error: service account key '{SERVICE_ACCOUNT_FILE}' not found. "
            "Set GOOGLE_SERVICE_ACCOUNT_FILE in .env or place the key next to this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def _find_column_index(header, target):
    """Return the 0-based index of `target` in `header`, ignoring case/whitespace."""
    target_norm = target.strip().lower()
    for i, name in enumerate(header):
        if str(name).strip().lower() == target_norm:
            return i
    return None


def _column_letter(index):
    """Convert a 0-based column index to its A1 letter(s) (0 -> A, 25 -> Z, 26 -> AA)."""
    letters = ""
    index += 1  # A1 columns are 1-based.
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def populate_model_tab(responses_df, tab_name, spreadsheet_id=None):
    """Write the Prompt ID and Model Output Response columns of `responses_df` into
    `tab_name`, overwriting any existing values in those two columns.

    Args:
        responses_df: DataFrame with 'Prompt ID' and 'Model Output Response' columns.
        tab_name: the results tab (worksheet) to write into.
        spreadsheet_id: spreadsheet to write to; defaults to env GOOGLE_SHEET_ID.
    """
    spreadsheet_id = spreadsheet_id or os.environ.get("GOOGLE_SHEET_ID")
    if not spreadsheet_id:
        print(
            "Error: no spreadsheet id given and GOOGLE_SHEET_ID is not set in .env.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Make sure the DataFrame has what we need before touching the sheet.
    for column in (PROMPT_ID_COLUMN, RESPONSE_COLUMN):
        if column not in responses_df.columns:
            print(
                f"Error: the responses DataFrame is missing a '{column}' column. "
                f"Found: {list(responses_df.columns)}",
                file=sys.stderr,
            )
            sys.exit(1)

    service = get_sheets_service()
    sheets = service.spreadsheets()

    # Read the tab's header row (row 5) and locate the two columns by name, so we write
    # into the right columns even if the layout shifts — and never touch the autogenerate
    # columns.
    try:
        header_result = (
            sheets.values()
            .get(spreadsheetId=spreadsheet_id, range=f"'{tab_name}'!{HEADER_ROW}:{HEADER_ROW}")
            .execute()
        )
    except HttpError as e:
        status = getattr(e.resp, "status", "?")
        print(f"Error: the Sheets API returned HTTP {status} — {e.reason}", file=sys.stderr)
        if str(status) == "403":
            print(
                "  A 403 usually means the sheet isn't shared with the service account "
                "as an EDITOR. Writing needs Editor access, not just Viewer.",
                file=sys.stderr,
            )
        elif str(status) in ("400", "404"):
            print(
                f"  Check GOOGLE_SHEET_ID and that a tab named '{tab_name}' exists in a "
                "native Google Sheet (not an uploaded .xlsx).",
                file=sys.stderr,
            )
        sys.exit(1)

    header = header_result.get("values", [[]])
    header = header[0] if header else []

    prompt_idx = _find_column_index(header, PROMPT_ID_COLUMN)
    response_idx = _find_column_index(header, RESPONSE_COLUMN)
    missing = [
        name
        for name, idx in ((PROMPT_ID_COLUMN, prompt_idx), (RESPONSE_COLUMN, response_idx))
        if idx is None
    ]
    if missing:
        print(
            f"Error: couldn't find column(s) {missing} in row {HEADER_ROW} of "
            f"'{tab_name}'. Header was: {header}",
            file=sys.stderr,
        )
        sys.exit(1)

    prompt_col = _column_letter(prompt_idx)
    response_col = _column_letter(response_idx)

    # Build column vectors, coercing NaN/None away (JSON can't carry NaN).
    prompt_ids = [[v] for v in responses_df[PROMPT_ID_COLUMN].fillna("").astype(str)]
    responses = [[v] for v in responses_df[RESPONSE_COLUMN].fillna("").astype(str)]
    n = len(responses_df)

    last_data_row = HEADER_ROW + n  # rows FIRST_DATA_ROW .. HEADER_ROW + n

    try:
        # Overwrite the two columns in place (RAW = store text literally, no formula eval).
        if n > 0:
            sheets.values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "valueInputOption": "RAW",
                    "data": [
                        {
                            "range": f"'{tab_name}'!{prompt_col}{FIRST_DATA_ROW}:{prompt_col}{last_data_row}",
                            "values": prompt_ids,
                        },
                        {
                            "range": f"'{tab_name}'!{response_col}{FIRST_DATA_ROW}:{response_col}{last_data_row}",
                            "values": responses,
                        },
                    ],
                },
            ).execute()

        # Clear any leftover rows below the new data (a shorter run than last time), so
        # this overwrites rather than leaving stale rows behind. Values only — formatting
        # and the autogenerate columns' formulas are preserved.
        clear_start = last_data_row + 1
        sheets.values().batchClear(
            spreadsheetId=spreadsheet_id,
            body={
                "ranges": [
                    f"'{tab_name}'!{prompt_col}{clear_start}:{prompt_col}",
                    f"'{tab_name}'!{response_col}{clear_start}:{response_col}",
                ]
            },
        ).execute()
    except HttpError as e:
        status = getattr(e.resp, "status", "?")
        print(f"Error while writing: HTTP {status} — {e.reason}", file=sys.stderr)
        if str(status) == "403":
            print(
                "  Writing needs the service account shared as EDITOR on the sheet.",
                file=sys.stderr,
            )
        sys.exit(1)

    print(
        f"Wrote {n} row(s) into '{tab_name}' "
        f"(columns {prompt_col}='{PROMPT_ID_COLUMN}', {response_col}='{RESPONSE_COLUMN}', "
        f"rows {FIRST_DATA_ROW}-{last_data_row})."
    )
