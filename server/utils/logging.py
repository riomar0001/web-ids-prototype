"""
JSON-based IDS detection logger.

Each detection result is appended as an entry to a JSON array file.
"""

import json
import logging
import threading
from typing import Any

from server.config import LOG_FILE

logger = logging.getLogger("ids")

_log_lock = threading.Lock()


def log_detection(entry: dict[str, Any]) -> None:
    """Thread-safe append of a detection entry to the JSON log file."""
    with _log_lock:
        if LOG_FILE.exists():
            data: list = json.loads(LOG_FILE.read_text())
        else:
            data = []
        data.append(entry)
        LOG_FILE.write_text(json.dumps(data, indent=2))


def read_log() -> list[dict[str, Any]]:
    """Return all logged detection entries."""
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text())
    return []
