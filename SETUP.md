# PictoPy Dev Setup Guide

This guide covers how to set up and run PictoPy locally for development on **Windows** and **Linux/macOS**.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 18+ | Frontend build |
| Rust + Cargo | latest stable | Tauri desktop framework |
| Python | 3.12 | Backend + sync microservice |
| Conda (Miniconda) | any | Python environment management |

---

## Quick Start (Recommended)

Both scripts handle all prerequisite installation, environment setup, and launch all three services automatically.

### Windows

Open **PowerShell** in the PictoPy root directory and run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\dev-setup.ps1
```

> If prompted by Windows Defender, choose "Run anyway".

### Linux / macOS

Open a terminal in the PictoPy root directory and run:

```bash
bash dev-setup.sh
```

> On macOS, Homebrew must be installed first: https://brew.sh

---

## What the Scripts Do

Both scripts run the same four phases:

**Phase 1 — Prerequisites**
- Installs Node.js if missing
- Installs Rust + Cargo via rustup if missing
- Installs Visual Studio C++ Build Tools (Windows) or system libs (Linux) required by Tauri
- Installs Miniconda if missing

**Phase 2 — Service Setup**
- Installs frontend npm dependencies (`frontend/node_modules`)
- Creates conda environment for the backend (`backend/.env`) and installs Python packages
- Creates conda environment for the sync microservice (`sync-microservice/.sync-env`) and installs Python packages

**Phase 3 — Launch**
- Starts the Python backend on port `52123`
- Starts the sync microservice on port `52124`
- Starts the Tauri frontend (React + Rust)

**Phase 4 — Health Check**
- Verifies backend and sync microservice are reachable
- Streams logs from all three services with colour-coded prefixes (`[BACKEND]`, `[SYNC]`, `[FRONTEND]`)

Press **Ctrl+C** to stop all services.

---

## Manual Setup (Alternative)

If you prefer to set up each service individually:

### 1. Frontend

```bash
cd frontend
npm install
npm run tauri dev
```

> **Windows only:** Rust requires Visual Studio C++ Build Tools (`link.exe`).
> Install via: `winget install Microsoft.VisualStudio.2022.BuildTools --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"`

### 2. Backend

```bash
cd backend
conda create -p .env python=3.12 -y
conda run -p .env pip install -r requirements.txt
conda run -p .env python main.py
```

Backend runs at: `http://localhost:52123`

### 3. Sync Microservice

```bash
cd sync-microservice
conda create -p .sync-env python=3.12 -y
conda run -p .sync-env pip install -r requirements.txt
conda run -p .sync-env fastapi dev --port 52124
```

Sync microservice runs at: `http://localhost:52124`

---

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| Backend (Python/FastAPI) | 52123 | Image processing, face recognition, albums |
| Sync Microservice (Python/FastAPI) | 52124 | File sync and watching |
| Frontend (Tauri/React) | — | Desktop app window (not a browser port) |

All three must be running for the app to work correctly.

---

## Troubleshooting

### `cargo` not found after installing Rust
Close and reopen your terminal — Rust adds itself to PATH only for new sessions.

### `link.exe` not found (Windows)
Visual Studio C++ Build Tools are missing. Run:
```powershell
winget install Microsoft.VisualStudio.2022.BuildTools --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```
Then reopen your terminal and retry.

### `chmod` not recognized (Windows)
`chmod` is a Linux command. On Windows, skip it — just run `.\dev-setup.ps1` directly.

### App window opens but shows a blank page
The Python backend is not running. Start it manually:
```bash
cd backend
conda run -p .env python main.py
```

### Script fails on emoji / encoding error (Windows PowerShell)
Your PowerShell version may not support Unicode. Upgrade to PowerShell 7+:
```powershell
winget install Microsoft.PowerShell
```

### Port already in use
Kill the process occupying the port:
```powershell
# Windows
netstat -ano | findstr :52123
taskkill /PID <pid> /F
```
```bash
# Linux/macOS
lsof -ti:52123 | xargs kill
```
