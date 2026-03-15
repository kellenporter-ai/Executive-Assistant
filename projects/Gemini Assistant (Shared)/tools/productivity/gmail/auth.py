import os
import sys
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Scopes for Gmail: modify allows read/write/drafting but not full deletion of the account
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Token storage — always outside the repo to prevent accidental commits
TOKEN_DIR = os.path.join(os.path.expanduser("~"), ".config", "gemini-ea", "tokens")
TOKEN_PATH = os.path.join(TOKEN_DIR, "token_gmail.json")

def get_gmail_service():
    """Authenticates and returns the Gmail service object.

    Auth methods (checked in order):
    1. Service account via GOOGLE_SERVICE_ACCOUNT_FILE env var
    2. User OAuth via GOOGLE_CLIENT_SECRET_FILE env var (opens browser first time)

    Tokens are stored in ~/.config/gemini-ea/tokens/ — never in the project directory.
    """
    creds = None

    # 1. Try Service Account first (best for headless/CLI)
    service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if service_account_file:
        if not os.path.exists(service_account_file):
            return None, f"GOOGLE_SERVICE_ACCOUNT_FILE is set but file not found: {service_account_file}"
        creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES)

    # 2. User OAuth (requires GOOGLE_CLIENT_SECRET_FILE)
    else:
        # Check for existing token
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                cred_file = os.getenv("GOOGLE_CLIENT_SECRET_FILE")
                if not cred_file:
                    return None, (
                        "Gmail not configured. Set one of these environment variables in your .env file:\n"
                        "  GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json\n"
                        "  GOOGLE_CLIENT_SECRET_FILE=/path/to/client-secret.json\n"
                        "See SETUP.md for details."
                    )
                if not os.path.exists(cred_file):
                    return None, f"GOOGLE_CLIENT_SECRET_FILE is set but file not found: {cred_file}"
                flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save token outside the repo
            os.makedirs(TOKEN_DIR, exist_ok=True)
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds), None
