#!/bin/bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' 

echo -e "${YELLOW}Starting setup...${NC}"

OS_TYPE=$(uname)

if [ "$OS_TYPE" = "Linux" ]; then
    if command -v apt-get &> /dev/null; then
        echo -e "${YELLOW}Detected Linux with apt-get. Installing dependencies...${NC}"
        apt-get update

        echo "deb http://archive.ubuntu.com/ubuntu jammy main universe multiverse" | tee /etc/apt/sources.list.d/ubuntu-jammy.list
        echo "deb http://security.ubuntu.com/ubuntu jammy-security main universe multiverse" | tee -a /etc/apt/sources.list.d/ubuntu-jammy-security.list

        apt-get install -y \
            curl build-essential libgtk-3-dev libwebkit2gtk-4.0-dev libappindicator3-dev git \
            wget xz-utils libssl-dev libglib2.0-dev libgirepository1.0-dev pkg-config \
            software-properties-common libjavascriptcoregtk-4.0-dev libjavascriptcoregtk-4.1-dev \
            libsoup-3.0-dev libwebkit2gtk-4.1-dev librsvg2-dev file libglib2.0-dev libgl1-mesa-glx \
        
    else
        echo -e "${RED}apt-get not found on Linux. Please install the following dependencies manually:${NC}"
        echo -e "  curl, build-essential, libgtk-3-dev, libwebkit2gtk-4.0-dev, libappindicator3-dev,"
        echo -e "  wget, xz-utils, libssl-dev, libglib2.0-dev, libgirepository1.0-dev, pkg-config,"
        echo -e "  software-properties-common, libjavascriptcoregtk-4.0-dev, libjavascriptcoregtk-4.1-dev,"
        echo -e "  libsoup-3.0-dev, libwebkit2gtk-4.1-dev, librsvg2-dev, file, libgl1-mesa-glx"
        echo -e "${RED}Also please install Rust from https://rustup.rs${NC}"
        exit 1
    fi

elif [ "$OS_TYPE" = "Darwin" ]; then
    echo -e "${YELLOW}Detected macOS. Installing dependencies using Homebrew...${NC}"
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}Homebrew is not installed. Please install it from https://brew.sh${NC}"
        exit 1
    fi
    brew update
    brew install \
    curl \
    git \
    cmake \
    pkg-config \
    gtk+3 \
    webkit2gtk \
    libappindicator \
    wget \
    xz \
    openssl@3 \
    glib \
    gobject-introspection \
    gtk-mac-integration \
    javascriptcoregtk \
    webkit2gtk-4.1 \
    libsoup \
    librsvg \
    gcc

    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    source "$HOME/.cargo/env"

    xcode-select --install

    brew tap homebrew/cask
    brew install --cask xquartz

    brew install gtk+3 --with-jasper --with-quartz-relocation

else
    echo -e "${RED}Unsupported OS: $OS_TYPE. Please install system dependencies manually.${NC}"
    exit 1
fi

# Install pyenv if not already installed
if ! command -v pyenv &> /dev/null; then
    echo "Installing pyenv..."
    curl https://pyenv.run | bash
    
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
fi

echo "Installing Python 3.12..."
pyenv install 3.12.0
pyenv global 3.12.0

python_version=$(python --version)
echo "Installed: $python_version"

pip install ruff black pre-commit mypy


# ---- Install Rust (if not already installed) ----
if ! command -v rustc &> /dev/null; then
    echo -e "${RED}Rust is not installed. Installing...${NC}"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
    rustup default stable
    rustup update
else
    echo -e "${GREEN}Rust is installed. Version: $(rustc --version)${NC}"
    echo -e "${YELLOW}Updating Rust...${NC}"
    rustup update
fi

# ---- Install Node.js and npm (if not installed) ----
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed. Installing...${NC}"
    if [ "$OS_TYPE" = "Linux" ]; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | -E bash -
        apt-get install -y nodejs
    elif [ "$OS_TYPE" = "Darwin" ]; then
        brew install node
    fi
else
    echo -e "${GREEN}Node.js is installed. Version: $(node --version)${NC}"
    echo -e "${GREEN}npm version: $(npm --version)${NC}"
fi

$HOME/.cargo/env

# ---- Set up the backend ----
echo -e "${YELLOW}Setting up backend...${NC}"
cd backend
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..

# ---- Set up the frontend ----
echo -e "${YELLOW}Setting up frontend...${NC}"
cd frontend
npm install
cd src-tauri || { echo -e "${RED}src-tauri directory not found${NC}"; exit 1; }
cargo build || { echo -e "${RED}Cargo build failed in src-tauri. Please check your Tauri setup.${NC}"; exit 1; }
cd ../../

echo -e "${GREEN}Setup complete!${NC}, restart the terminal to apply changes."
