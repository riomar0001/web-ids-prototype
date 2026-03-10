# Setup Guide

## Prerequisites

- Python 3.12+
- pip
- Docker (optional, for containerized deployment)
- Administrator/root privileges (required for Scapy packet sniffing)

---

## Local Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r docker-requirements.txt
```

### 3. Verify model files

Ensure the following files exist inside `app/model/`:

| File                     | Description                          |
|--------------------------|--------------------------------------|
| `rf_model.joblib`        | Binary classifier (Normal vs Attack) |
| `rf_multiclass.joblib`   | Multiclass attack type classifier    |
| `feature_names.json`     | Ordered list of 41 input features    |
| `attack_labels.json`     | Attack type label mapping            |
| `metadata.json`          | Model metadata and performance info  |

### 4. Run the application

From the **project root** (parent of `app/`):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> **Note:** Scapy requires elevated privileges to capture packets.
>
> - **Windows:** Run your terminal as Administrator
> - **Linux/macOS:** Use `sudo` or grant `CAP_NET_RAW` capability

### 5. Verify the server is running

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "models_loaded": true,
  "binary_model": "rf_model.joblib",
  "multiclass_model": "rf_multiclass.joblib",
  "feature_count": 41
}
```

---

## Docker Setup

### 1. Build the image

From the `app/` directory:

```bash
cd app
docker build -t web-ids .
```

### 2. Run the container

```bash
docker run --cap-add=NET_RAW -p 8000:8000 web-ids
```

`--cap-add=NET_RAW` grants the container permission to capture raw network packets, which Scapy requires.

### 3. Verify

```bash
curl http://localhost:8000/health
```

---

## API Endpoints

| Method | Path      | Description                        |
|--------|-----------|------------------------------------|
| GET    | `/`       | Root status check                  |
| GET    | `/health` | Model and service health info      |
| GET    | `/logs`   | Retrieve all IDS detection entries |

---

## Project Structure

```
app/
├── main.py              App factory — creates FastAPI, loads models, wires middleware & routes
├── config.py            Paths, feature names, constants
├── Dockerfile           Container build instructions
├── docker-requirements.txt  Minimal pip dependencies for the app
├── middleware/
│   └── ids.py           IDS middleware — orchestrates capture → extract → classify → log
├── services/
│   ├── capture.py       Scapy packet sniffing in a daemon thread
│   ├── features.py      41-feature vector extraction from raw packets
│   └── classifier.py    Two-stage Random Forest classification pipeline
├── utils/
│   └── logging.py       Thread-safe JSON log writer and reader
├── routes/
│   └── health.py        Health, status, and log endpoints
├── model/
│   ├── rf_model.joblib
│   ├── rf_multiclass.joblib
│   ├── feature_names.json
│   ├── attack_labels.json
│   └── metadata.json
└── tests/
    └── test_ids.py      Automated test payloads
```

---

## How It Works

1. Every incoming HTTP request passes through the **IDS middleware**
2. The middleware starts a **Scapy packet capture** filtered to the client IP and server port
3. The request proceeds normally — the response is not blocked or delayed
4. After the response, captured packets are processed to **extract 41 network flow features**
5. The **binary model** classifies the traffic as Normal or Attack
6. If classified as Attack, the **multiclass model** identifies the specific attack type
7. Results are written to `ids_log.json` with timestamp, endpoint, client IP, features, and classification
