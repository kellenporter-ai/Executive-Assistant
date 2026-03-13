import os
import sys
import json
import argparse
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

def get_slack_history(channel_id, limit=5):
    """Retrieves recent messages from a Slack channel."""
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        return {"error": "SLACK_BOT_TOKEN not found in environment."}
    
    client = WebClient(token=token)

    try:
        response = client.conversations_history(
            channel=channel_id,
            limit=limit
        )
        messages = response["messages"]
        
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "user": msg.get("user"),
                "text": msg.get("text"),
                "ts": msg.get("ts"),
                "type": msg.get("type")
            })
            
        return {"channel": channel_id, "messages": formatted_messages}
    except SlackApiError as e:
        return {"error": str(e.response['error'])}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get Slack channel history.")
    parser.add_argument("--channel", required=True, help="Channel ID")
    parser.add_argument("--limit", type=int, default=5, help="Number of messages to retrieve")

    args = parser.parse_args()
    
    result = get_slack_history(args.channel, args.limit)
    print(json.dumps(result, indent=2))
