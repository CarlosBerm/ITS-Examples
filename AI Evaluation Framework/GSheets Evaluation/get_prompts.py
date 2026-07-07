"""
get_prompts.py — main driver: load the prompt library sheet into a pandas DataFrame.

Reads the prompt library table from the project's Google Sheet (the "database")
via the Google Sheets API, authenticating with a service account. The table's
header row is row 5 and spans columns A–F:

    A: Prompt ID
    B: Core Category (auto)
    C: Subcategory
    D: Context
    E: Prompt Text
    F: Ground Truth / Evaluation Standard

Only rows whose 'Prompt Text' cell is non-empty are kept — that's the prompt that
gets sent to the AI being evaluated.

Configure the following in Scripts/.env:
    GOOGLE_SERVICE_ACCOUNT_FILE   path to the service account JSON key (default service_account.json)
    GOOGLE_SHEET_ID               the spreadsheet ID (the part between /d/ and /edit in its URL)
    GOOGLE_SHEET_TAB              the tab/worksheet name that holds the prompt library
"""

import os
import sys

from dotenv import load_dotenv
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Set the current working directory to the same directory as this file, so the
# .env file and the service account JSON are found no matter where it's run from.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load configuration (credentials path, sheet id, tab name) from the .env file.
if not load_dotenv(".env"):
    print("Unable to load .env file.", file=sys.stderr)
    sys.exit(1)

# Path to the service account JSON key downloaded from Google Cloud.
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

# Default spreadsheet ID (between /d/ and /edit in the sheet's URL). get_prompts_df()
# takes a spreadsheet_id argument and falls back to this env value.
SPREADSHEET_ID = os.environ.get("GOOGLE_SHEET_ID")

# Read-only access is all this reader needs.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The prompt library table's header row is row 5 and spans columns A–F.
HEADER_ROW = 5

# The column whose emptiness decides whether a row is a real prompt.
PROMPT_TEXT_COLUMN = "Prompt Text"


def get_sheets_service():
    """Authenticate with the service account and return a Sheets API client."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(
            f"Error: service account key '{SERVICE_ACCOUNT_FILE}' not found. "
            "Download it from Google Cloud and place it next to this script "
            "(or set GOOGLE_SERVICE_ACCOUNT_FILE in .env).",
            file=sys.stderr,
        )
        sys.exit(1)

    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    # cache_discovery=False avoids a noisy warning and a needless on-disk cache.
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def _find_column(columns, target):
    """Return the actual column name matching `target`, ignoring case/whitespace."""
    target_norm = target.strip().lower()
    for column in columns:
        if str(column).strip().lower() == target_norm:
            return column
    return None


def get_prompts_df(tab_name, spreadsheet_id=None):
    """Fetch the prompt library from `tab_name` and return it as a DataFrame.

    The first returned row (sheet row 5) is used as the header. Only rows with a
    non-empty 'Prompt Text' are kept. `spreadsheet_id` defaults to env GOOGLE_SHEET_ID.
    """
    spreadsheet_id = spreadsheet_id or SPREADSHEET_ID
    if not spreadsheet_id:
        print("Error: GOOGLE_SHEET_ID is not set in .env.", file=sys.stderr)
        sys.exit(1)

    # Header row is row 5, columns A–F. Quote the tab so names with spaces work; with no
    # tab, fall back to the first visible sheet.
    tab = (tab_name or "").strip()
    range_name = f"'{tab}'!A{HEADER_ROW}:F" if tab else f"A{HEADER_ROW}:F"

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
                "  A 400 usually means either the range/tab is wrong (check that "
                f"the tab '{tab_name}' matches a real tab), or the file is an "
                "uploaded Excel (.xlsx) rather than a native Google Sheet. The Sheets "
                "API only works on native Sheets — in Drive open the file and use "
                "File > Save as Google Sheets, then point GOOGLE_SHEET_ID at that copy.",
                file=sys.stderr,
            )
        elif str(status) == "403":
            print(
                "  A 403 usually means the sheet isn't shared with the service "
                "account. Open the sheet > Share, and add the client_email from "
                "your service account JSON as a Viewer.",
                file=sys.stderr,
            )
        elif str(status) == "404":
            print(
                "  A 404 usually means GOOGLE_SHEET_ID is wrong (the spreadsheet "
                "wasn't found).",
                file=sys.stderr,
            )
        sys.exit(1)

    values = result.get("values", [])
    if not values:
        print(f"No data found in range '{range_name}'.", file=sys.stderr)
        sys.exit(1)

    header = values[0]
    data_rows = values[1:]

    # The API drops trailing empty cells, so rows are ragged. Pad (and defensively
    # truncate) every row to the header width so the DataFrame is rectangular.
    width = len(header)
    normalized_rows = [(row + [""] * width)[:width] for row in data_rows]

    df = pd.DataFrame(normalized_rows, columns=header)

    prompt_col = _find_column(df.columns, PROMPT_TEXT_COLUMN)
    if prompt_col is None:
        print(
            f"Error: expected a '{PROMPT_TEXT_COLUMN}' column. Found: {list(df.columns)}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Keep only rows whose Prompt Text is non-empty (ignoring surrounding whitespace).
    keep = df[prompt_col].astype(str).str.strip() != ""
    df = df[keep].reset_index(drop=True)

    return df


def main():
    tab_name = os.environ.get("GOOGLE_SHEET_TAB", "").strip()
    df = get_prompts_df(tab_name)
    source = tab_name if tab_name else "the first sheet"
    print(f"Loaded {len(df)} prompt(s) from '{source}'.\n")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
