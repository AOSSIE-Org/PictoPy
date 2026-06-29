#!/bin/bash

# =============================================================================
# PictoPy Dev Setup & Launch Script
# Supports: Linux (Debian/Ubuntu/Arch) and macOS
# Usage: bash dev-setup.sh
# =============================================================================

set -e  # exit on error

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ── Helpers ───────────────────────────────────────────────────────────────────
ok()   { echo -e "${GREEN}✓${NC} $1"; }
skip() { echo -e "${CYAN}→${NC} $1 (already installed, skipping)"; }
info() { echo -e "${BLUE}▸${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }
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

# ── Get script directory (root of PictoPy) ────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/backend"
SYNC_DIR="$SCRIPT_DIR/sync-microservice"

# ── Validate we are in the PictoPy root ───────────────────────────────────────
if [[ ! -d "$FRONTEND_DIR" || ! -d "$BACKEND_DIR" || ! -d "$SYNC_DIR" ]]; then
  fail "Please run this script from the root of the PictoPy repository."
fi

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
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
  elif [[ "$OS" == "arch" ]]; then
    sudo pacman -S --noconfirm nodejs npm
  else
    warn "Cannot auto-install Node.js on this OS. Please install it manually from https://nodejs.org"
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
    libwebkit2gtk-4.1-dev
    libappindicator3-dev
    librsvg2-dev
    patchelf
    libglib2.0-dev
    libgl1-mesa-glx
    pkg-config
    build-essential
    curl
    wget
    file
    libxdo-dev
    libssl-dev
    libayatana-appindicator3-dev
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
  sudo pacman -S --needed --noconfirm webkit2gtk base-devel curl wget file openssl appmenu-gtk-module gtk3 libappindicator-gtk3 librsvg libvips
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
    # Use x86_64 if not Apple Silicon
    [[ "$(uname -m)" != "arm64" ]] && MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
  else
    MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
  fi
  curl -fsSL "$MINICONDA_URL" -o /tmp/miniconda.sh
  bash /tmp/miniconda.sh -b -p "$HOME/miniconda3"
  rm /tmp/miniconda.sh
  export PATH="$HOME/miniconda3/bin:$PATH"
  conda init bash 2>/dev/null || true
  ok "Miniconda installed"
  warn "You may need to restart your terminal after setup for conda to work globally."
fi

# Make sure conda is available in this shell session
CONDA_BIN=$(conda info --base 2>/dev/null)/bin/conda
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

info "Backend: installing Python dependencies..."
# Check if deps are already installed by testing a key package
if conda run -p "$BACKEND_ENV" python -c "import fastapi" &>/dev/null; then
  skip "Backend Python packages"
else
  conda run -p "$BACKEND_ENV" pip install -r "$BACKEND_DIR/requirements.txt"
  ok "Backend Python packages installed"
fi

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

info "Sync microservice: installing Python dependencies..."
if conda run -p "$SYNC_ENV" python -c "import fastapi" &>/dev/null; then
  skip "Sync microservice Python packages"
else
  conda run -p "$SYNC_ENV" pip install -r "$SYNC_DIR/requirements.txt"
  ok "Sync microservice Python packages installed"
fi

# =============================================================================
# PHASE 3 — LAUNCH ALL SERVICES
# =============================================================================
header "Phase 3: Launching All Services"

# Store background process PIDs for cleanup
PIDS=()

# Cleanup on Ctrl+C or exit
cleanup() {
  echo ""
  warn "Shutting down all services..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  ok "All services stopped. Goodbye!"
  exit 0
}
trap cleanup SIGINT SIGTERM

# ── Launch Backend ────────────────────────────────────────────────────────────
info "Starting backend on port 52123..."
(
  cd "$BACKEND_DIR"
  conda run -p "$BACKEND_ENV" fastapi dev --port 52123 2>&1 | \
    while IFS= read -r line; do echo -e "${GREEN}[BACKEND]${NC}   $line"; done
) &
PIDS+=($!)

# ── Launch Sync Microservice ──────────────────────────────────────────────────
info "Starting sync microservice on port 52124..."
(
  cd "$SYNC_DIR"
  conda run -p "$SYNC_ENV" fastapi dev --port 52124 2>&1 | \
    while IFS= read -r line; do echo -e "${YELLOW}[SYNC]${NC}      $line"; done
) &
PIDS+=($!)

# ── Launch Frontend ───────────────────────────────────────────────────────────
info "Starting Tauri frontend..."
(
  cd "$FRONTEND_DIR"
  npm run tauri dev 2>&1 | \
    while IFS= read -r line; do echo -e "${BLUE}[FRONTEND]${NC}  $line"; done
) &
PIDS+=($!)

# =============================================================================
# PHASE 4 — HEALTH CHECK
# =============================================================================
header "Phase 4: Health Check"

info "Waiting 10 seconds for services to start..."
sleep 10

# Check backend
if curl -s "http://localhost:52123" &>/dev/null || curl -s "http://localhost:52123/docs" &>/dev/null; then
  ok "Backend is running at http://localhost:52123"
else
  warn "Backend may still be starting up — check [BACKEND] logs above"
fi

# Check sync microservice
if curl -s "http://localhost:52124" &>/dev/null || curl -s "http://localhost:52124/docs" &>/dev/null; then
  ok "Sync microservice is running at http://localhost:52124"
else
  warn "Sync microservice may still be starting — check [SYNC] logs above"
fi

echo ""
echo -e "${BOLD}${GREEN}✓ PictoPy dev environment is up!${NC}"
echo -e "  Press ${BOLD}Ctrl+C${NC} to stop all services."
echo ""

# Keep script alive so logs keep streaming and Ctrl+C works
wait