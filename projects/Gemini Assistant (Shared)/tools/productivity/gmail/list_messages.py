import os
import sys
import json
import base64
from auth import get_gmail_service
from dotenv import load_dotenv

load_dotenv()

def list_messages(query="", max_results=5):
    """Lists messages in the user's mailbox matching the query."""
    service, error = get_gmail_service()
    if error:
        return {"error": error}

    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])

        detailed_messages = []
        for msg in messages:
            m = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            
            headers = m.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), "Unknown")
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), "Unknown Date")
            
            snippet = m.get('snippet', '')
            
            detailed_messages.append({
                "id": m['id'],
                "threadId": m['threadId'],
                "from": sender,
                "subject": subject,
                "date": date,
                "snippet": snippet
            })
        
        return {"messages": detailed_messages}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Allow query to be passed as CLI arg
    query = sys.argv[1] if len(sys.argv) > 1 else "is:unread"
    results = list_messages(query=query)
    print(json.dumps(results, indent=2))
