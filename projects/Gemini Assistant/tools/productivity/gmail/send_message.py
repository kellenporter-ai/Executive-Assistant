import sys
import json
import base64
import argparse
from email.mime.text import MIMEText
from auth import get_gmail_service
from dotenv import load_dotenv

load_dotenv()

def create_message(sender, to, subject, message_text):
    """Create a message for an email."""
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw}

def send_message(to, subject, body):
    """Send an email message."""
    service, error = get_gmail_service()
    if error:
        return {"error": error}

    try:
        message = create_message('me', to, subject, body)
        sent_message = service.users().messages().send(userId='me', body=message).execute()
        return {
            "status": "success",
            "id": sent_message['id'],
            "threadId": sent_message['threadId']
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a Gmail message.")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Email body text")

    args = parser.parse_args()

    result = send_message(args.to, args.subject, args.body)
    print(json.dumps(result, indent=2))
