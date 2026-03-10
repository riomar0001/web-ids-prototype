# Installation Guide

Step-by-step instructions for installing and running the IDS Prototype locally or via Docker.

---

## Local Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd prototype
```

---

### 2. Backend Setup

#### 2a. Create a Python Virtual Environment

```bash
cd server
python -m venv .venv
```

Activate the virtual environment:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

#### 2b. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies installed:

| Package      | Version  | Purpose                          |
|--------------|----------|----------------------------------|
| fastapi      | 0.135.0  | Web framework                    |
| uvicorn      | 0.41.0   | ASGI server                      |
| scikit-learn | 1.8.0    | Random Forest models             |
| shap         | 0.50.0   | Model explainability             |
| scapy        | 2.7.0    | Packet capture                   |
| numpy        | 2.4.2    | Numerical computations           |
| pydantic     | 2.12.5   | Data validation                  |

#### 2c. Install System Packet Capture Library

```bash
# Debian / Ubuntu
sudo apt install libpcap-dev

# Fedora / RHEL
sudo dnf install libpcap-devel

# macOS (via Homebrew)
brew install libpcap

# Windows
# Download and install Npcap from: https://npcap.com/
```

#### 2d. Add ML Model Files

Place the following trained model files into `server/model/`:

```
server/model/
├── rf_model.joblib
├── rf_multiclass.joblib
├── feature_names.json
├── attack_labels.json
└── metadata.json
```

See [SETUP.md](SETUP.md#ml-model-files) for details on training these models.

#### 2e. Start the Backend

```bash
# From the project root (prototype/)
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

> On Linux/macOS, prefix with `sudo` for raw socket access:
> ```bash
> sudo uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
> ```

The API will be available at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

---

### 3. Frontend Setup

Open a **new terminal** and navigate to the client directory:

```bash
cd client
```

#### 3a. Install Node Dependencies

```bash
npm install
```

#### 3b. Start the Development Server

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

> Vite proxies all `/api` requests to `http://localhost:8000` automatically — no CORS configuration needed during development.

---

### 4. Verify the Installation

With both servers running, open `http://localhost:5173` in your browser.

Check the backend health endpoint:

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

Check that logs are being written:

```bash
curl "http://localhost:8000/logs?page=1&page_size=5"
```

---

## Docker Installation

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed and running

### 1. Build the Backend Image

```bash
cd server
docker build -t ids-server .
```

### 2. Run the Container

```bash
docker run \
  --cap-add=NET_RAW \
  -p 8000:8000 \
  -v $(pwd)/model:/app/model \
  ids-server
```

| Flag                        | Purpose                                          |
|-----------------------------|--------------------------------------------------|
| `--cap-add=NET_RAW`         | Grants raw socket access for Scapy               |
| `-p 8000:8000`              | Maps container port to host                      |
| `-v $(pwd)/model:/app/model`| Mounts model files into the container            |

### 3. Frontend with Docker (Optional)

The frontend can be served as a static build from the backend container, or run separately:

```bash
cd client
npm run build
# Serve client/dist/ with any static file server
```

---

## Running Tests

```bash
cd server
pytest tests/
```

---

## Common Issues

### Server fails to start — model files not found

```
FileNotFoundError: server/model/rf_model.joblib not found
```

**Fix:** Add the trained model `.joblib` and `.json` files to `server/model/`. See [SETUP.md](SETUP.md#ml-model-files).

---

### Packet capture returns no features (all zeros)

All 41 features are 0.0 in the log.

**Fix:** The process lacks raw socket permissions. Run with `sudo` or grant `CAP_NET_RAW`. See [SETUP.md](SETUP.md#packet-capture-permissions).

---

### Frontend shows "Failed to fetch" or connection errors

**Fix:** Ensure the backend is running on port 8000 before starting the frontend. Check `http://localhost:8000/health`.

---

### Port 8000 already in use

```bash
# Find the process using the port
lsof -i :8000        # Linux / macOS
netstat -ano | findstr :8000   # Windows

# Use a different port
uvicorn server.main:app --port 8001
```

Then update the Vite proxy in `client/vite.config.js`:

```js
proxy: {
  '/api': 'http://localhost:8001'
}
```

---

### Windows: Scapy import errors

Install Npcap from [https://npcap.com/](https://npcap.com/) and restart your terminal. Run the backend as Administrator.
