"""Shared stats computation used by both the REST endpoint and WS broadcasts."""

from typing import Any


def compute_stats(logs: list[dict[str, Any]]) -> dict:
    attack_type_counts: dict[str, int] = {}
    unique_ips: set[str] = set()
    total_attacks = 0

    for entry in logs:
        unique_ips.add(entry["client_ip"])
        if entry["binary_classification"] == "Attack":
            total_attacks += 1
            t = entry.get("attack_type") or "Unknown"
            attack_type_counts[t] = attack_type_counts.get(t, 0) + 1

    total = len(logs)
    top_attack = (
        max(attack_type_counts, key=lambda x: attack_type_counts.get(x, 0))
        if attack_type_counts
        else None
    )

    return {
        "total_requests": total,
        "total_attacks": total_attacks,
        "total_normal": total - total_attacks,
        "unique_ips": len(unique_ips),
        "top_attack_type": top_attack,
        "attack_type_counts": attack_type_counts,
    }
