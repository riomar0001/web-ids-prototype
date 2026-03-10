# IDS Prototype — Intrusion Detection System

A real-time, machine learning-powered Intrusion Detection System (IDS) with a React dashboard. The system intercepts HTTP traffic, extracts 41 network features, classifies requests using Random Forest models, and explains detections using SHAP values.

---

## Overview

```
prototype/
├── client/          # React 19 + Vite frontend dashboard
└── server/          # FastAPI + Scapy + scikit-learn backend
```

### How It Works

1. **Intercept** — A global FastAPI middleware captures every incoming HTTP request.
2. **Capture** — Scapy sniffs the associated network packets in a background thread (non-blocking).
3. **Extract** — 41 network-level features are derived from the captured traffic (flow duration, packet sizes, TCP flags, inter-arrival times, etc.).
4. **Classify** — A two-stage Random Forest pipeline predicts:
   - **Binary**: Normal vs. Attack
   - **Multiclass**: Specific attack category (DoS, Exploits, Reconnaissance, Generic, Fuzzers, Analysis, Backdoor, Shellcode, Worms)
5. **Explain** — SHAP values identify the top 5 features that drove each prediction.
6. **Log** — Results are appended to `ids_log.json` in a thread-safe manner.
7. **Visualize** — The React dashboard polls the API every 5 seconds and displays detections in real time.

---

## Features

- **Real-time detection** with non-blocking background packet analysis
- **41-feature extraction** covering flow, size, timing, TCP, and directional traffic metrics
- **Explainable AI** — SHAP-powered per-request feature importance
- **Filterable log table** — Filter by classification, attack type, IP, or endpoint
- **Live statistics** — Total requests, attack count, top attack type, unique IPs
- **Attack breakdown chart** — Visual distribution of attack categories
- **HTTP method badges** — Color-coded GET / POST / PUT / DELETE indicators
- **Pagination** — Configurable page size for large log datasets
- **Docker-ready** — Containerized backend with `NET_RAW` support for Scapy

---

## Tech Stack

| Layer     | Technology                              |
|-----------|-----------------------------------------|
| Frontend  | React 19, Vite 7, plain CSS             |
| Backend   | FastAPI, Uvicorn, Starlette             |
| ML        | scikit-learn (Random Forest), SHAP      |
| Networking| Scapy (packet capture & parsing)        |
| Data      | numpy, joblib, Pydantic                 |
| Storage   | JSON file (`ids_log.json`)              |
| Container | Docker (python:3.12-slim + libpcap-dev) |

---

## API Endpoints

| Method | Path          | Description                              |
|--------|---------------|------------------------------------------|
| GET    | `/`           | Status check                             |
| GET    | `/health`     | Model status and loaded feature count    |
| GET    | `/logs`       | Paginated detection log with filters     |
| GET    | `/logs/stats` | Aggregate attack statistics              |

### `/logs` Query Parameters

| Parameter        | Type    | Description                              |
|------------------|---------|------------------------------------------|
| `page`           | int     | Page number (default: 1)                 |
| `page_size`      | int     | Results per page (default: 20)           |
| `classification` | string  | `Normal` or `Attack`                     |
| `attack_type`    | string  | e.g., `DoS`, `Reconnaissance`            |
| `client_ip`      | string  | Filter by source IP                      |
| `search`         | string  | Search across endpoint and IP fields     |
| `sort`           | string  | Sort order                               |

---

## Project Status

> **Note:** ML model files (`server/model/`) are not included in the repository and must be trained or obtained separately before the server can start. See [SETUP.md](SETUP.md) for details.

---

## Documentation

- [SETUP.md](SETUP.md) — Environment setup and configuration
- [INSTALLATION.md](INSTALLATION.md) — Step-by-step installation guide
