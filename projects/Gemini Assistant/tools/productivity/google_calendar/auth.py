import os
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Scopes for reading and writing calendar events
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Authenticates and returns the Google Calendar service object."""
    creds = None
    # 1. Try Service Account first (Best for headless/CLI)
    service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if service_account_file and os.path.exists(service_account_file):
        creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES)
    
    # 2. Fallback to User OAuth (Requires browser first time)
    else:
        token_path = 'token.json'
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                cred_file = os.getenv("GOOGLE_CLIENT_SECRET_FILE", "credentials.json")
                if not os.path.exists(cred_file):
                    return None, f"Credentials file not found: {cred_file}"
                flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds), None
