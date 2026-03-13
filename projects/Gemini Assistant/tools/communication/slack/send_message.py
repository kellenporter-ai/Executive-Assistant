import os
import sys
import json
import argparse
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

def send_slack_message(channel_id, text):
    """Sends a message to a Slack channel."""
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        return {"error": "SLACK_BOT_TOKEN not found in environment."}
    
    client = WebClient(token=token)

    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=text
        )
        return {
            "status": "success",
            "ts": response["ts"],
            "channel": response["channel"]
        }
    except SlackApiError as e:
        return {"error": str(e.response['error'])}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a Slack message.")
    parser.add_argument("--channel", required=True, help="Channel ID or name")
    parser.add_argument("--text", required=True, help="Message text")

    args = parser.parse_args()
    
    result = send_slack_message(args.channel, args.text)
    print(json.dumps(result, indent=2))
