import sys
import json
import argparse
from datetime import datetime, timedelta
from auth import get_calendar_service
from dotenv import load_dotenv

load_dotenv()

def create_event(summary, start_time, end_time, location=None, description=None):
    """Inserts an event into the user's primary calendar."""
    service, error = get_calendar_service()
    if error:
        return {"error": error}

    event = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'UTC', # Adjust as needed
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'UTC',
        },
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        return {
            "status": "success",
            "id": event.get("id"),
            "link": event.get("htmlLink"),
            "summary": event.get("summary")
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Google Calendar event.")
    parser.add_argument("--summary", required=True, help="Event title")
    parser.add_argument("--start", required=True, help="Start ISO 8601 (e.g., 2026-03-13T10:00:00Z)")
    parser.add_argument("--end", required=True, help="End ISO 8601 (e.g., 2026-03-13T11:00:00Z)")
    parser.add_argument("--location", help="Event location")
    parser.add_argument("--description", help="Event description")

    args = parser.parse_args()

    result = create_event(args.summary, args.start, args.end, args.location, args.description)
    print(json.dumps(result, indent=2))
