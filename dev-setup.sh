#!/bin/bash

# =============================================================================
# PictoPy Dev Setup & Launch Script
# Supports: Linux (Debian/Ubuntu/Arch) and macOS
# Usage: bash dev-setup.sh
# =============================================================================

set -euo pipefail

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Helpers ───────────────────────────────────────────────────────────────────
ok()     { echo -e "${GREEN}✓${NC} $1"; }
skip()   { echo -e "${CYAN}→${NC} $1 (already installed, skipping)"; }
info()   { echo -e "${BLUE}▸${NC} $1"; }
warn()   { echo -e "${YELLOW}⚠${NC} $1"; }
fail()   { echo -e "${RED}✗${NC} $1"; exit 1; }
header() {
  echo ""
  echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BOLD}  $1${NC}"
  echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ── Detect OS ─────────────────────────────────────────────────────────────────
detect_os() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
  elif [[ -f /etc/debian_version ]]; then
    OS="debian"
  elif [[ -f /etc/arch-release ]]; then
    OS="arch"
  elif [[ -f /etc/fedora-release ]]; then
    OS="fedora"
  else
    OS="linux-other"
  fi
  info "Detected OS: $OS"
}

# ── Script directory ──────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/backend"
SYNC_DIR="$SCRIPT_DIR/sync-microservice"

# ── Validate PictoPy root ─────────────────────────────────────────────────────
if [[ ! -d "$FRONTEND_DIR" || ! -d "$BACKEND_DIR" || ! -d "$SYNC_DIR" ]]; then
  fail "Please run this script from the root of the PictoPy repository."
fi

# ── Process group cleanup on Ctrl+C ──────────────────────────────────────────
# Each service is started in its own process group (setsid) so kill -TERM -- -PID
# kills the entire group including fastapi/tauri child processes, not just the wrapper.
PGRPS=()
cleanup() {
  echo ""
  warn "Shutting down all services..."
  for pgrp in "${PGRPS[@]}"; do
    kill -TERM -- "-$pgrp" 2>/dev/null || true
  done
  ok "All services stopped. Goodbye!"
  exit 0
}
trap cleanup SIGINT SIGTERM

# =============================================================================
# PHASE 1 — PREREQUISITES
# =============================================================================
header "Phase 1: Checking Prerequisites"

detect_os

# ── Node.js ───────────────────────────────────────────────────────────────────
if command -v node &>/dev/null; then
  skip "Node.js ($(node --version))"
else
  info "Installing Node.js..."
  if [[ "$OS" == "mac" ]]; then
    brew install node || fail "Homebrew not found. Install it from https://brew.sh first."
  elif [[ "$OS" == "debian" ]]; then
    # Download to temp file and verify before executing
    NODESOURCE_SCRIPT="$(mktemp)"
    curl -fsSL https://deb.nodesource.com/setup_20.x -o "$NODESOURCE_SCRIPT"
    sudo -E bash "$NODESOURCE_SCRIPT"
    rm -f "$NODESOURCE_SCRIPT"
    sudo apt-get install -y nodejs
  elif [[ "$OS" == "arch" ]]; then
    sudo pacman -S --noconfirm nodejs npm
  else
    warn "Cannot auto-install Node.js on this OS. Install manually from https://nodejs.org"
    fail "Node.js is required."
  fi
  ok "Node.js installed ($(node --version))"
fi

# ── Rust / Cargo ──────────────────────────────────────────────────────────────
if command -v cargo &>/dev/null; then
  skip "Rust/Cargo ($(cargo --version))"
else
  info "Installing Rust via rustup..."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  source "$HOME/.cargo/env"
  ok "Rust installed ($(cargo --version))"
fi

# ── Tauri system dependencies (Linux only) ────────────────────────────────────
if [[ "$OS" == "debian" ]]; then
  info "Checking Tauri system dependencies..."
  TAURI_DEPS=(
    libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf
    libglib2.0-dev libgl1-mesa-glx pkg-config build-essential
    curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev
  )
  MISSING_DEPS=()
  for dep in "${TAURI_DEPS[@]}"; do
    dpkg -s "$dep" &>/dev/null || MISSING_DEPS+=("$dep")
  done
  if [[ ${#MISSING_DEPS[@]} -eq 0 ]]; then
    skip "All Tauri system dependencies"
  else
    info "Installing missing system deps: ${MISSING_DEPS[*]}"
    sudo apt-get update -qq
    sudo apt-get install -y "${MISSING_DEPS[@]}"
    ok "Tauri system dependencies installed"
  fi
elif [[ "$OS" == "arch" ]]; then
  info "Checking Tauri system dependencies (Arch)..."
  sudo pacman -S --needed --noconfirm webkit2gtk base-devel curl wget file openssl \
    appmenu-gtk-module gtk3 libappindicator-gtk3 librsvg libvips
  ok "Tauri system dependencies installed"
elif [[ "$OS" == "mac" ]]; then
  skip "Tauri system dependencies (not needed on macOS)"
fi

# ── Miniconda ─────────────────────────────────────────────────────────────────
if command -v conda &>/dev/null; then
  skip "Miniconda/Conda ($(conda --version))"
else
  info "Installing Miniconda..."
  if [[ "$OS" == "mac" ]]; then
    MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
    [[ "$(uname -m)" != "arm64" ]] && MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
  else
    MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
  fi
  # Download to temp file
  MINICONDA_SCRIPT="$(mktemp)"
  curl -fsSL "$MINICONDA_URL" -o "$MINICONDA_SCRIPT"
  bash "$MINICONDA_SCRIPT" -b -p "$HOME/miniconda3"
  rm -f "$MINICONDA_SCRIPT"
  export PATH="$HOME/miniconda3/bin:$PATH"
  conda init bash 2>/dev/null || true
  ok "Miniconda installed"
  warn "You may need to restart your terminal after setup for conda to work globally."
fi

# Ensure conda is available in this session
export PATH="$(conda info --base 2>/dev/null)/bin:$PATH"

# =============================================================================
# PHASE 2 — SERVICE SETUP
# =============================================================================
header "Phase 2: Setting Up Services"

# ── Frontend ──────────────────────────────────────────────────────────────────
info "Frontend: checking node_modules..."
if [[ -d "$FRONTEND_DIR/node_modules" ]]; then
  skip "Frontend npm dependencies"
else
  info "Frontend: running npm install..."
  (cd "$FRONTEND_DIR" && npm install)
  ok "Frontend dependencies installed"
fi

# ── Backend ───────────────────────────────────────────────────────────────────
info "Backend: checking conda environment..."
BACKEND_ENV="$BACKEND_DIR/.env"
if [[ -d "$BACKEND_ENV" ]]; then
  skip "Backend conda environment (.env)"
else
  info "Backend: creating conda environment with Python 3.12..."
  conda create -p "$BACKEND_ENV" python=3.12 -y
  ok "Backend conda environment created"
fi

# Always run pip install — idempotent and catches requirements.txt changes
info "Backend: installing/syncing Python dependencies..."
conda run -p "$BACKEND_ENV" pip install -r "$BACKEND_DIR/requirements.txt" --quiet
ok "Backend Python packages ready"

# ── Sync Microservice ─────────────────────────────────────────────────────────
info "Sync microservice: checking conda environment..."
SYNC_ENV="$SYNC_DIR/.sync-env"
if [[ -d "$SYNC_ENV" ]]; then
  skip "Sync microservice conda environment (.sync-env)"
else
  info "Sync microservice: creating conda environment with Python 3.12..."
  conda create -p "$SYNC_ENV" python=3.12 -y
  ok "Sync microservice conda environment created"
fi

# Always run pip install — idempotent and catches requirements.txt changes
info "Sync microservice: installing/syncing Python dependencies..."
conda run -p "$SYNC_ENV" pip install -r "$SYNC_DIR/requirements.txt" --quiet
ok "Sync microservice Python packages ready"

# =============================================================================
# PHASE 3 — LAUNCH ALL SERVICES
# =============================================================================
header "Phase 3: Launching All Services"

# Launch each service in its own process group via setsid
# This ensures kill -TERM -- -PGRP kills fastapi/tauri children too

info "Starting backend on port 52123..."
setsid bash -c "cd '$BACKEND_DIR' && conda run -p '$BACKEND_ENV' fastapi dev --port 52123 2>&1 | \
  while IFS= read -r line; do echo -e '${GREEN}[BACKEND]${NC}   '"'"'$line'"'"'; done" &
PGRPS+=("$!")

info "Starting sync microservice on port 52124..."
setsid bash -c "cd '$SYNC_DIR' && conda run -p '$SYNC_ENV' fastapi dev --port 52124 2>&1 | \
  while IFS= read -r line; do echo -e '${YELLOW}[SYNC]${NC}      '"'"'$line'"'"'; done" &
PGRPS+=("$!")

info "Starting Tauri frontend..."
setsid bash -c "cd '$FRONTEND_DIR' && npm run tauri dev 2>&1 | \
  while IFS= read -r line; do echo -e '${BLUE}[FRONTEND]${NC}  '"'"'$line'"'"'; done" &
PGRPS+=("$!")

# =============================================================================
# PHASE 4 — HEALTH CHECK
# =============================================================================
header "Phase 4: Health Check"

info "Waiting 10 seconds for services to start..."
sleep 10

HEALTHY=true

if curl -s --max-time 3 "http://localhost:52123/docs" &>/dev/null; then
  ok "Backend is running at http://localhost:52123"
else
  warn "Backend did not respond on port 52123"
  HEALTHY=false
fi

if curl -s --max-time 3 "http://localhost:52124/docs" &>/dev/null; then
  ok "Sync microservice is running at http://localhost:52124"
else
  warn "Sync microservice did not respond on port 52124"
  HEALTHY=false
fi

if [[ "$HEALTHY" == false ]]; then
  warn "One or more services failed to start. Check logs above."
  warn "Press Ctrl+C to stop all services."
else
  echo ""
  echo -e "${BOLD}${GREEN}✓ PictoPy dev environment is up!${NC}"
  echo -e "  Press ${BOLD}Ctrl+C${NC} to stop all services."
  echo ""
fi

# Keep alive so logs stream and Ctrl+C triggers cleanup
wait