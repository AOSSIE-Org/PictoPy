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

# --- venv activation helper ---
# Tries each candidate venv folder name in order, using the correct
# activate path per OS (bin/activate on Unix, Scripts/activate on Windows).
activate_venv() {
    local base_dir="$1"
    shift
    local candidates=("$@")

    for name in "${candidates[@]}"; do
        local venv_dir="$base_dir/$name"
        if [[ "$OS_TYPE" == "windows" ]]; then
            if [[ -f "$venv_dir/Scripts/activate" ]]; then
                source "$venv_dir/Scripts/activate"
                return 0
            fi
        else
            if [[ -f "$venv_dir/bin/activate" ]]; then
                source "$venv_dir/bin/activate"
                return 0
            fi
        fi
    done

    echo -e "${RED}Could not find a venv in $base_dir (looked for: ${candidates[*]})${NC}"
    echo -e "${YELLOW}${SETUP_HINT}${NC}"
    return 1
}

# Verifies a command exists inside the *currently activated* venv, with
# guidance to reinstall dependencies rather than a bare "command not found".
require_venv_cmd() {
    local cmd="$1"
    local venv_dir="$2"
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${RED}'$cmd' not found in venv at $venv_dir.${NC}"
        echo -e "${YELLOW}The venv exists but looks incomplete. Try:${NC}"
        if [[ "$OS_TYPE" == "windows" ]]; then
            echo -e "${YELLOW}  source \"$venv_dir/Scripts/activate\" && pip install -r requirements.txt${NC}"
        else
            echo -e "${YELLOW}  source \"$venv_dir/bin/activate\" && pip install -r requirements.txt${NC}"
        fi
        echo -e "${YELLOW}...or rerun: $SETUP_HINT${NC}"
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
        activate_venv "$BACKEND_DIR" ".env" "venv" || exit 1
        require_venv_cmd "uvicorn" "$BACKEND_DIR/.env" || exit 1
        if [[ "$MODE" == "prod" ]]; then
            echo "[BACKEND] Starting in production mode on port 52123..."
            uvicorn main:app --host 0.0.0.0 --port 52123 --workers "${WORKERS:-1}"
        else
            echo "[BACKEND] Starting in dev mode on port 52123..."
            uvicorn main:app --host 0.0.0.0 --port 52123 --reload
        fi
    ) 2>&1 | sed -u 's/^/[BACKEND] /' &
    PIDS+=($!)
}

start_sync() {
    (
        cd "$SYNC_DIR"
        activate_venv "$SYNC_DIR" ".sync-env" "venv" || exit 1
        echo "[SYNC] Starting sync-microservice on port 52124..."
        if [[ "$MODE" == "prod" ]]; then
            require_venv_cmd "uvicorn" "$SYNC_DIR/.sync-env" || exit 1
            uvicorn main:app --host 0.0.0.0 --port 52124
        else
            require_venv_cmd "fastapi" "$SYNC_DIR/.sync-env" || exit 1
            fastapi dev --port 52124
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
