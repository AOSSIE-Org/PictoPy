#!/bin/bash

# Unified dev/prod launcher for PictoPy: backend, sync-microservice, and frontend
#
# Requires bash (Linux, macOS, Git Bash, or WSL on Windows). If you're on
# Windows without Git Bash/WSL, use `node scripts/run.js` instead.
#
# Usage:
#   ./run.sh          -> dev mode (default)
#   ./run.sh --test    -> dev mode (kept as an alias for backward compatibility)
#   ./run.sh --prod    -> production mode

set -e

# --- Colors (matches scripts/setup.sh conventions) ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

MODE="dev"
if [[ "$1" == "--prod" ]]; then
    MODE="prod"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
SYNC_DIR="$ROOT_DIR/sync-microservice"
FRONTEND_DIR="$ROOT_DIR/frontend"

# --- OS detection (same approach as scripts/setup.sh and scripts/setup.js) ---
case "$(uname -s)" in
    Linux*)     OS_TYPE="linux" ;;
    Darwin*)    OS_TYPE="macos" ;;
    MINGW*|MSYS*|CYGWIN*) OS_TYPE="windows" ;;
    *)
        OS_TYPE="unknown"
        echo -e "${YELLOW}Warning: unrecognized OS '$(uname -s)'. Assuming Unix-like behavior.${NC}"
        ;;
esac

SETUP_HINT="Run 'npm run setup' from the repo root to install dependencies."
if [[ "$OS_TYPE" == "windows" ]]; then
    SETUP_HINT="Run 'npm run setup' from the repo root (this launches scripts/setup.ps1 on Windows)."
fi

# --- Preflight: fail fast with guidance instead of a raw "command not found" ---
require_cmd() {
    local cmd="$1"
    local guidance="$2"
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${RED}Error: required command '$cmd' not found.${NC}"
        echo -e "${YELLOW}${guidance}${NC}"
        exit 1
    fi
}

require_dir() {
    local dir="$1"
    local label="$2"
    if [[ ! -d "$dir" ]]; then
        echo -e "${RED}Error: $label directory not found at $dir${NC}"
        echo -e "${YELLOW}Make sure you're running this from a full PictoPy checkout.${NC}"
        exit 1
    fi
}

require_dir "$BACKEND_DIR" "backend"
require_dir "$SYNC_DIR" "sync-microservice"
require_dir "$FRONTEND_DIR" "frontend"

require_cmd "node" "Node.js not found. Install it from https://nodejs.org, or $SETUP_HINT"
require_cmd "npm" "npm not found (usually bundled with Node.js). Install Node.js from https://nodejs.org, or $SETUP_HINT"
require_cmd "cargo" "Rust/Cargo not found (required by 'npm run tauri dev'). Install it from https://rustup.rs, or $SETUP_HINT"

# --- venv resolution helper ---
# Tries each candidate venv folder name in order and prepends its bin dir
# (bin/ on Unix, Scripts/ on Windows) to PATH directly. Deliberately does
# NOT `source <venv>/activate`: that script bakes in an absolute path at
# creation time (see its VIRTUAL_ENV= line and pyvenv.cfg), and silently
# breaks -- falling through to system Python with no error -- if the venv
# folder is ever renamed or moved after creation, which happens easily
# since ".env"/".venv" naming is inconsistent across tooling. Resolving
# the bin dir fresh from its current location every run sidesteps that.
resolve_venv() {
    local base_dir="$1"
    shift
    local candidates=("$@")
    local bin_subdir="bin"
    [[ "$OS_TYPE" == "windows" ]] && bin_subdir="Scripts"

    for name in "${candidates[@]}"; do
        local venv_dir="$base_dir/$name"
        if [[ -f "$venv_dir/$bin_subdir/activate" ]]; then
            echo "$venv_dir/$bin_subdir"
            return 0
        fi
    done

    echo -e "${RED}Could not find a venv in $base_dir (looked for: ${candidates[*]})${NC}" >&2
    echo -e "${YELLOW}${SETUP_HINT}${NC}" >&2
    return 1
}

# pip/uvicorn/fastapi console-script launchers generated inside a venv have
# proven unreliable on some platforms (see scripts/run.js for the Windows
# case that motivated this). Invoking everything as `python -m <module>`
# sidesteps those launcher stubs entirely.
export PYTHONUNBUFFERED=1
export PYTHONUTF8=1

# Installs a service's Python dependencies before starting it, matching
# `source <venv>/activate && pip install -r requirements.txt` from the
# project's README. Blocking by design: the server must not start against
# a venv with missing/outdated packages.
pip_install() {
    local prefix="$1"
    echo "[$prefix] Installing dependencies from requirements.txt..."
    if ! python -m pip install -r requirements.txt; then
        echo -e "${RED}[$prefix] pip install -r requirements.txt failed.${NC}"
        return 1
    fi
    return 0
}

PIDS=()

cleanup() {
    echo ""
    echo "Shutting down all services..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null
    done
    wait 2>/dev/null
    exit 0
}
trap cleanup INT TERM

start_backend() {
    (
        echo "[BACKEND] Starting... ${BACKEND_DIR}"
        cd "$BACKEND_DIR"
        bin_dir=$(resolve_venv "$BACKEND_DIR" ".env" "venv") || exit 1
        export PATH="$bin_dir:$PATH"
        pip_install "BACKEND" || exit 1
        if [[ "$MODE" == "prod" ]]; then
            echo "[BACKEND] Starting in production mode on port 52123..."
            python -m uvicorn main:app --host 0.0.0.0 --port 52123 --workers "${WORKERS:-1}"
        else
            # Backend pins fastapi-cli==0.0.3, which predates
            # `fastapi.__main__` (no `python -m fastapi` support), unlike
            # sync-microservice's newer fastapi-cli. Use uvicorn directly.
            echo "[BACKEND] Starting in dev mode on port 52123..."
            python -m uvicorn main:app --host 0.0.0.0 --port 52123 --reload
        fi
    ) 2>&1 | sed -u 's/^/[BACKEND] /' &
    PIDS+=($!)
}

start_sync() {
    (
        cd "$SYNC_DIR"
        bin_dir=$(resolve_venv "$SYNC_DIR" ".sync-env" "venv") || exit 1
        export PATH="$bin_dir:$PATH"
        pip_install "SYNC" || exit 1
        echo "[SYNC] Starting sync-microservice on port 52124..."
        if [[ "$MODE" == "prod" ]]; then
            python -m uvicorn main:app --host 0.0.0.0 --port 52124
        else
            python -m fastapi dev --port 52124
        fi
    ) 2>&1 | sed -u 's/^/[SYNC] /' &
    PIDS+=($!)
}

start_frontend() {
    (
        cd "$FRONTEND_DIR"
        if [[ ! -d "node_modules" ]]; then
            echo -e "${RED}[FRONTEND] node_modules not found.${NC}"
            echo -e "${YELLOW}[FRONTEND] ${SETUP_HINT}${NC}"
            exit 1
        fi
        echo "[FRONTEND] Starting Tauri dev..."
        npm run tauri dev
    ) 2>&1 | sed -u 's/^/[FRONTEND] /' &
    PIDS+=($!)
}

echo "Starting PictoPy (mode: $MODE, OS: $OS_TYPE)..."
start_backend
start_sync
start_frontend

wait
