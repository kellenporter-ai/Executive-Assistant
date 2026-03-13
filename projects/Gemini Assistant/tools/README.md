# Tools: The Deterministic Execution Layer

This directory contains modular scripts (Python/Node.js) that allow the Executive Assistant to interact with the external world.

## Principles
1. **Single Responsibility:** Each script should do one thing well (e.g., `send_slack_message.py`).
2. **Deterministic:** Scripts handle all API complexity, authentication, and error retries.
3. **Structured Input/Output:** Tools take semantic parameters as CLI arguments and return structured JSON.
4. **Abstracted Complexity:** The LLM should never have to construct raw HTTP requests.

## Categories
- **Communication:** Slack, Email, Discord
- **Productivity:** Google Calendar, Notion, Airtable
- **Research:** Tavily, Perplexity, Web Scrapers
- **System:** File transformations, local environment checks

## Usage
Agents invoke these tools via `run_shell_command`. 
Example: `python3 tools/google_calendar/create_event.py --title "Meeting" --start "2026-03-13T10:00:00"`
