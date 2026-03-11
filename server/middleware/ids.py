"""
IDS middleware for FastAPI.

Intercepts every incoming HTTP request, captures associated network
packets via Scapy, extracts flow features, classifies the traffic,
and logs the result — all without blocking the response.
"""

import asyncio
import logging
import threading
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from server.config import EXCLUDED_PATH_PREFIXES
from server.services.capture import PacketCapture
from server.services.classifier import IDSClassifier
from server.services.features import extract_features
from server.utils.logging import log_detection

logger = logging.getLogger("ids")

# Maximum body bytes to store in the log (avoids huge log entries for file uploads, etc.)
MAX_BODY_LOG_BYTES = 4096


class IDSMiddleware(BaseHTTPMiddleware):
    """Middleware that analyses every request with the IDS pipeline."""

    def __init__(self, app, classifier: IDSClassifier) -> None:
        super().__init__(app)
        self.classifier = classifier

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"
        server_port = request.url.port or (
            443 if request.url.scheme == "https" else 80
        )
        qs = request.url.query
        endpoint = request.url.path + (f"?{qs}" if qs else "")
        method = request.method

        # Skip IDS analysis for internal monitoring / dashboard endpoints.
        if request.url.path.startswith(EXCLUDED_PATH_PREFIXES):
            return await call_next(request)

        # Capture headers before forwarding the request.
        headers = dict(request.headers)

        # Read the body; Starlette caches it so downstream handlers still receive it.
        raw_body = await request.body()
        if len(raw_body) > MAX_BODY_LOG_BYTES:
            body_log: str | None = raw_body[:MAX_BODY_LOG_BYTES].decode("utf-8", errors="replace") + f" … [{len(raw_body)} bytes total, truncated]"
        elif raw_body:
            body_log = raw_body.decode("utf-8", errors="replace")
        else:
            body_log = None

        # Start packet capture in a background thread
        capture = PacketCapture(client_ip, server_port)
        capture.start()

        # Give Scapy's BPF filter a moment to activate before the TCP exchange
        # begins; without this, fast requests complete before any packets are seen.
        await asyncio.sleep(0.1)

        # Let the request proceed normally
        response = await call_next(request)

        # Wait for packet capture without blocking the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, capture.wait)

        # Offload CPU-bound classification to a daemon thread so we
        # don't block the async event loop.
        threading.Thread(
            target=self._classify_and_log,
            args=(capture.packets, client_ip, server_port, method, endpoint, headers, body_log),
            daemon=True,
        ).start()

        return response

    def _classify_and_log(
        self,
        packets,
        client_ip: str,
        server_port: int,
        method: str,
        endpoint: str,
        headers: dict[str, str],
        body: str | None,
    ) -> None:
        """Extract features, classify, and persist the detection result."""
        if not packets:
            logger.debug("No packets captured for %s — skipping classification", endpoint)
            return

        try:
            features = extract_features(packets, client_ip, server_port)
            result = self.classifier.classify(features)

            log_detection({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "method": method,
                "endpoint": endpoint,
                "client_ip": client_ip,
                "request": {
                    "headers": headers,
                    "body": body,
                },
                "features": {
                    k: round(v, 6) if isinstance(v, float) else v
                    for k, v in features.items()
                },
                "binary_classification": result.binary_label,
                "explanation": result.explanation,
            })

            if result.binary_label == "Attack":
                logger.warning(
                    "ATTACK detected from %s — %s %s",
                    client_ip,
                    method,
                    endpoint,
                )
            else:
                logger.info(
                    "Normal traffic from %s — %s %s",
                    client_ip,
                    method,
                    endpoint,
                )

        except Exception as exc:
            logger.error("IDS middleware error: %s", exc, exc_info=True)
