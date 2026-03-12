"""Shared logging for EA tools — writes structured JSON logs to temp/tools-logs/."""
import json
import logging
import os
from datetime import datetime

LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "temp", "tools-logs")


def get_tool_logger(tool_name: str) -> logging.Logger:
    """Get a logger that writes JSON lines to temp/tools-logs/<tool>-YYYY-MM-DD.jsonl"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, f"{tool_name}-{datetime.now().strftime('%Y-%m-%d')}.jsonl")

    logger = logging.getLogger(f"ea.{tool_name}")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        handler.setFormatter(JsonFormatter(tool_name))
        logger.addHandler(handler)
        # Also log to stderr
        stderr_handler = logging.StreamHandler()
        stderr_handler.setFormatter(logging.Formatter(f"[{tool_name}] %(message)s"))
        stderr_handler.setLevel(logging.WARNING)
        logger.addHandler(stderr_handler)
    return logger


class JsonFormatter(logging.Formatter):
    def __init__(self, tool_name: str):
        super().__init__()
        self.tool_name = tool_name

    def format(self, record):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tool": self.tool_name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "data"):
            entry["data"] = record.data
        return json.dumps(entry)
