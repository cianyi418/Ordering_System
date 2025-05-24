import gspread
from oauth2client.service_account import ServiceAccountCredentials
from ..config import get_google_credentials, GOOGLE_SHEET_ID

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

_client = None

# Initialize GSpread Client
def get_client():
    global _client
    if _client is None:
        creds_json = get_google_credentials()
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        _client = gspread.authorize(creds)
    return _client

# Get the worksheet (default is Orders)
def get_sheet(name="Orders"):
    return get_client().open_by_key(GOOGLE_SHEET_ID).worksheet(name)

# Additional provision of obtaining Users table
def get_users_sheet():
    return get_sheet("Users")
