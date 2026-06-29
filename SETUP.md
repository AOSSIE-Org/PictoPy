# PictoPy Dev Setup Guide

This guide covers how to get the PictoPy development environment running on your machine — either automatically with a single script, or manually step by step.

---

## Quick Start (Recommended)

### Windows

```powershell
# One-time: allow script execution for this session only
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

# Run the setup script
.\dev-setup.ps1
```

### Linux / macOS

```bash
chmod +x dev-setup.sh
./dev-setup.sh
```

The script handles everything: installs prerequisites, creates conda environments, installs dependencies, launches all 3 services, and runs a health check. On re-runs it skips anything already installed.

---

## What the Script Does

**Phase 1 — Prerequisites:** Detects your OS and installs Node.js, Rust/Cargo, Miniconda, and platform-specific Tauri dependencies (webkit2gtk on Linux, VS C++ Build Tools + WebView2 on Windows) if missing.

**Phase 2 — Service Setup:** Creates conda environments for the backend (`.env`) and sync microservice (`.sync-env`), installs pip dependencies, and runs `npm install` for the frontend.

**Phase 3 — Launch:** Starts all 3 services in a single terminal with color-coded log prefixes `[BACKEND]`, `[SYNC]`, `[FRONTEND]`. Press `Ctrl+C` to stop all services cleanly.

**Phase 4 — Health Check:** Pings both Python servers after 10 seconds to confirm they started successfully.

---

## Services & Ports

| Service           | Port  | Start Command                          |
|-------------------|-------|----------------------------------------|
| Python Backend    | 52123 | `fastapi dev --port 52123`             |
| Sync Microservice | 52124 | `fastapi dev --port 52124`             |
| Tauri Frontend    | —     | `npm run tauri dev`                    |

---

## Manual Setup

If you prefer to set up manually or the script doesn't work on your OS:

### Prerequisites

- [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install)
- [Node.js](https://nodejs.org) (v20+)
- [Rust](https://rustup.rs)
- Tauri system dependencies — see [tauri.app/start/prerequisites](https://tauri.app/start/prerequisites/)

### Step 1 — Frontend

```bash
cd frontend
npm install
npm run tauri dev
```

### Step 2 — Backend

```bash
cd backend
conda create -p .env python=3.12 -y
conda activate ./.env
pip install -r requirements.txt
fastapi dev --port 52123
```

### Step 3 — Sync Microservice

```bash
cd sync-microservice
conda create -p .sync-env python=3.12 -y
conda activate ./.sync-env
pip install -r requirements.txt
fastapi dev --port 52124
```

Run each in a separate terminal.

---

## Troubleshooting

**Missing `libGL.so.1` (OpenCV error on Linux)**
```bash
sudo apt install -y libglib2.0-dev libgl1-mesa-glx
```

**`gobject-2.0` not found**
```bash
sudo apt install -y libglib2.0-dev pkg-config
```

**Port already in use**

Find and kill the process holding the port:
```bash
# Safe form — only kills if a process is found
lsof -ti :52123 | xargs -r kill -9
lsof -ti :52124 | xargs -r kill -9
```

**conda not found after fresh install**

Restart your terminal. Conda adds itself to PATH in `.bashrc`/`.zshrc` but the change only takes effect in a new session.

**Rust/cargo not found after fresh install (Windows)**

Restart PowerShell after rustup installs, then re-run `dev-setup.ps1`.