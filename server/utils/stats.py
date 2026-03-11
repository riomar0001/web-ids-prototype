"""Shared stats computation used by both the REST endpoint and WS broadcasts."""

from typing import Any


def compute_stats(logs: list[dict[str, Any]]) -> dict:
    unique_ips: set[str] = set()
    total_attacks = 0

    for entry in logs:
        unique_ips.add(entry["client_ip"])
        if entry["binary_classification"] == "Attack":
            total_attacks += 1

    total = len(logs)

    return {
        "total_requests": total,
        "total_attacks": total_attacks,
        "total_normal": total - total_attacks,
        "unique_ips": len(unique_ips),
    }
