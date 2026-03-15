import os
import sys
import json
import datetime
from auth import get_calendar_service
from dotenv import load_dotenv

load_dotenv()

def list_events(max_results=10):
    """Lists the next N events on the user's primary calendar."""
    service, error = get_calendar_service()
    if error:
        return {"error": error}

    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    try:
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=max_results, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            formatted_events.append({
                "id": event.get("id"),
                "summary": event.get("summary"),
                "start": start,
                "location": event.get("location"),
                "description": event.get("description"),
                "link": event.get("htmlLink")
            })
        
        return {"events": formatted_events}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    results = list_events()
    print(json.dumps(results, indent=2))
