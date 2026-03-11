"""
Application configuration and constants.
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent          # .../app/
MODEL_DIR = APP_DIR / "model"                      # .../app/model/
LOG_FILE = APP_DIR.parent / "ids_log.json"         # .../ids_log.json

# ---------------------------------------------------------------------------
# Model metadata (loaded once at import time)
# ---------------------------------------------------------------------------
FEATURE_NAMES: list[str] = json.loads((MODEL_DIR / "feature_names.json").read_text())

# ---------------------------------------------------------------------------
# Network / detection settings
# ---------------------------------------------------------------------------
WEB_PORTS: set[int] = {80, 443, 8080, 8443, 8000, 8888, 3000, 5000}

# Duration (seconds) for Scapy to sniff packets per request.
# Must exceed the longest expected server response delay — time-based SQL injection
# payloads (e.g. PG_SLEEP(5), WAITFOR DELAY '0:0:5') hold the connection for 5 s.
SNIFF_TIMEOUT: float = 8.0

# URL path prefixes that are excluded from IDS analysis.
# These are internal/monitoring endpoints only ever called by the dashboard
# or health checks — classifying them generates false positives and log noise.
EXCLUDED_PATH_PREFIXES: tuple[str, ...] = (
    "/logs",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)

# Heuristic mapping of well-known destination ports → nDPI-style L7 protocol
# numeric identifiers.  Used when true DPI is unavailable.
L7_PROTO_MAP: dict[int, int] = {
    80: 7,       # HTTP
    443: 91,     # TLS / SSL
    8080: 7,     # HTTP alt
    8443: 91,    # HTTPS alt
    8000: 7,     # HTTP dev
    8888: 7,     # HTTP dev
    3000: 7,     # HTTP dev
    5000: 7,     # HTTP dev
    53: 5,       # DNS
    22: 92,      # SSH
    21: 1,       # FTP
}
