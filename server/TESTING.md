# Testing Guide

This guide explains how to test the IDS middleware using the included test script and manual methods.

---

## Prerequisites

- The IDS server must be running (see [SETUP.md](SETUP.md))
- `requests` Python package installed (`pip install requests`)
- A second terminal for sending test traffic

---

## Automated Test Suite

The test script sends a variety of attack payloads and normal requests, then retrieves the detection log.

### Run the test script

From the **project root**:

```bash
python -m app.tests.test_ids
```

Against a custom host:

```bash
python -m app.tests.test_ids http://192.168.1.50:8000
```

### What the test script covers

The script runs **9 categories** of traffic sequentially with a 3-second pause between each request to allow packet capture to complete:

| # | Category              | Description                                              | Requests |
|---|-----------------------|----------------------------------------------------------|----------|
| 1 | Normal traffic        | `GET /` and `GET /health` — baseline legitimate requests | 2        |
| 2 | Reconnaissance        | Probes common sensitive paths (`.env`, `/admin`, `/wp-login.php`, `/.git/config`, etc.) | 10       |
| 3 | SQL Injection         | Query parameters with `OR 1=1`, `UNION SELECT`, `DROP TABLE` payloads | 4        |
| 4 | XSS                   | `<script>`, `<img onerror>`, `<svg onload>` in query parameters | 3        |
| 5 | Directory Traversal   | `../../etc/passwd` and URL-encoded path traversal variants | 3        |
| 6 | Command Injection     | POST bodies with shell commands (`;cat /etc/passwd`, reverse shell attempts) | 2        |
| 7 | DoS Simulation        | 50 rapid-fire `GET /` requests in a tight loop           | 50       |
| 8 | Fuzzing               | Oversized POST payloads (100KB raw, 50KB JSON)           | 2        |
| 9 | Backdoor Headers      | Shellshock-style `User-Agent`, spoofed `X-Forwarded-For` | 1        |

### Reading the output

At the end, the script fetches `GET /logs` and prints a summary:

```
Total entries logged: 77

  !! ATTACK  /.env                                    [Reconnaissance]
     NORMAL  /
  !! ATTACK  /search?q=' OR '1'='1' --                [Exploits]
  ...
```

- `!! ATTACK` — binary model classified as attack, with the multiclass type in brackets
- `   NORMAL` — classified as legitimate traffic

---

## Manual Testing

### Normal request

```bash
curl http://localhost:8000/
```

### Reconnaissance probe

```bash
curl http://localhost:8000/.env
curl http://localhost:8000/.git/config
curl http://localhost:8000/wp-login.php
```

### SQL injection

```bash
curl "http://localhost:8000/search?q=' OR '1'='1' --"
curl "http://localhost:8000/items?id=1;DROP TABLE users;--"
```

### XSS

```bash
curl "http://localhost:8000/search?q=<script>alert('xss')</script>"
```

### Command injection

```bash
curl -X POST http://localhost:8000/api/run \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "cmd=;cat /etc/passwd"
```

### DoS burst

```bash
for i in $(seq 1 50); do curl -s http://localhost:8000/ > /dev/null & done
wait
```

### Oversized payload (fuzzing)

```bash
python -c "print('A'*100000)" | curl -X POST http://localhost:8000/api/data \
  -H "Content-Type: application/octet-stream" \
  --data-binary @-
```

### Shellshock-style header

```bash
curl http://localhost:8000/ \
  -H "User-Agent: () { :; }; /bin/bash -c 'cat /etc/passwd'"
```

---

## Inspecting Results

### View detection log via API

```bash
curl http://localhost:8000/logs | python -m json.tool
```

### View the raw log file

The log is written to `ids_log.json` in the project root. Each entry contains:

```json
{
  "timestamp": "2026-03-10T12:34:56.789000+00:00",
  "endpoint": "/search?q=' OR '1'='1' --",
  "client_ip": "172.17.0.1",
  "features": {
    "L4_SRC_PORT": 54321,
    "L4_DST_PORT": 8000,
    "PROTOCOL": 6,
    "...": "... (41 features total)"
  },
  "binary_classification": "Attack",
  "attack_type": "Exploits"
}
```

### Clear the log

Delete the file to start fresh:

```bash
rm ids_log.json
```

---

## Important Notes

- **3-second gap:** Each test request waits 3 seconds for the Scapy sniffer to capture packets. If results are missing, increase `SNIFF_TIMEOUT` in `app/config.py`.
- **Localhost traffic:** Scapy may not capture loopback traffic on some systems. If running locally and getting empty captures, test from a different machine or use Docker with `--network host`.
- **Classification depends on network features, not payloads:** The IDS model classifies based on packet-level flow features (timing, sizes, flags, throughput), not HTTP content. The same SQL injection sent slowly vs in a burst may produce different classifications.
- **Elevated privileges:** Scapy requires admin/root access. Without it, packet capture will silently fail and all traffic will appear normal with zeroed features.
