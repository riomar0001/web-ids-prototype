# Setup Guide

This document covers environment configuration, prerequisites, and how to prepare the project for development or production use.

---

## Prerequisites

### System Requirements

| Requirement | Minimum Version | Notes                                      |
|-------------|-----------------|--------------------------------------------|
| Python      | 3.12+           | Required for the FastAPI backend           |
| Node.js     | 18+             | Required for the React frontend            |
| npm         | 9+              | Comes bundled with Node.js                 |
| libpcap     | any             | Required by Scapy for packet capture       |
| Git         | any             | For cloning the repository                 |

### Platform Notes

**Linux (Recommended)**
- Install libpcap: `sudo apt install libpcap-dev` (Debian/Ubuntu) or `sudo dnf install libpcap-devel` (Fedora)
- Scapy packet capture requires root or `CAP_NET_RAW` capability

**Windows**
- Install [Npcap](https://npcap.com/) — Scapy's Windows packet capture driver
- Run the backend with administrator privileges for raw socket access

**macOS**
- libpcap ships with Xcode Command Line Tools
- Run with `sudo` for raw socket access

---

## Environment Configuration

### Backend (`server/`)

The backend is configured via `server/config.py`. No `.env` file is required by default, but the following constants can be adjusted:

| Constant              | Default         | Description                                         |
|-----------------------|-----------------|-----------------------------------------------------|
| `LOG_FILE`            | `ids_log.json`  | Path to the detection log output file               |
| `MODEL_DIR`           | `server/model/` | Directory containing trained ML model artifacts     |
| `SNIFF_TIMEOUT`       | `8.0` seconds   | Packet capture window per request                   |
| `WEB_PORTS`           | 80, 443, 8000…  | Ports considered "web traffic" for feature tagging  |
| `EXCLUDED_PATH_PREFIXES` | `/logs`, `/health`… | Paths skipped by IDS middleware             |

### Frontend (`client/`)

The Vite dev server proxies `/api/*` requests to `http://localhost:8000` automatically.

For production or a custom backend URL, set:

```bash
VITE_API_URL=http://your-backend-host:8000
```

in a `.env` file inside the `client/` directory.

---

## ML Model Files

The server requires pre-trained model artifacts in `server/model/`:

| File                      | Description                                |
|---------------------------|--------------------------------------------|
| `rf_model.joblib`         | Binary classifier (Normal vs. Attack)      |
| `rf_multiclass.joblib`    | Multiclass attack-type classifier          |
| `feature_names.json`      | Ordered list of the 41 feature names       |
| `attack_labels.json`      | Attack category label mapping              |
| `metadata.json`           | Model training metadata                    |

> These files are **not** included in the repository. Train your own models using the UNSW-NB15 or NSL-KDD dataset with the 41 features defined in `server/services/features.py`, then place the exported files in `server/model/`.

### Verifying Model Files

After placing model files, verify the server loads them correctly:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "model_loaded": true,
  "feature_count": 41
}
```

---

## Packet Capture Permissions

Scapy requires raw socket access. Without proper permissions, packet capture will silently fail and all features will default to zero.

**Linux — grant capability without root:**

```bash
sudo setcap cap_net_raw=eip $(which python3)
```

**Linux / macOS — run with sudo:**

```bash
sudo uvicorn server.main:app --host 0.0.0.0 --port 8000
```

**Docker:**

```bash
docker run --cap-add=NET_RAW <image>
```

---

## Development vs. Production

### Development

- Frontend hot-reloads via Vite (`npm run dev`)
- Backend reloads via Uvicorn `--reload` flag
- API proxy in `vite.config.js` routes `/api` to `localhost:8000`

### Production

1. Build the frontend: `npm run build` (outputs to `client/dist/`)
2. Serve `client/dist/` with a static file server (nginx, Caddy, or FastAPI `StaticFiles`)
3. Run Uvicorn behind a reverse proxy (nginx recommended)
4. Ensure the backend process has `CAP_NET_RAW` or runs as root

---

## Docker Setup

See [INSTALLATION.md](INSTALLATION.md) for Docker-specific instructions.

The `server/Dockerfile` uses:
- Base image: `python:3.12-slim`
- System package: `libpcap-dev`
- Required runtime flag: `--cap-add=NET_RAW`
