import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load from global .env if available
load_dotenv()

def tavily_search(query: str, api_key: str = None):
    """
    Deterministic search tool using Tavily API.
    Returns structured JSON results.
    """
    if not api_key:
        api_key = os.getenv("TAVILY_API_KEY")
    
    if not api_key:
        return {"error": "TAVILY_API_KEY not found in environment or arguments."}

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "smart",
        "include_answer": True,
        "max_results": 5
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Structure the output for the LLM to consume
        results = {
            "query": query,
            "answer": data.get("answer"),
            "results": [
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": (r.get("content", "")[:500] + "...") if r.get("content") else "" 
                } for r in data.get("results", [])
            ]
        }
        return results
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python3 tavily_search.py '<query>'" }))
        sys.exit(1)
    
    query = sys.argv[1]
    # In a real tool, we might use argparse for more complex flags
    print(json.dumps(tavily_search(query), indent=2))
