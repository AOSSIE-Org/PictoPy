#!/bin/bash

# Get the directory of the script and resolve the repo root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' 

echo -e "${YELLOW}Starting setup...${NC}"


# Detect OS
if [ -f "/etc/debian_version" ]; then
    echo -e "\e[33mDetected Debian-based Linux. Installing dependencies...\e[0m"
    sudo apt update
    sudo apt install -y \
        libwebkit2gtk-4.1-dev \
        build-essential \
        curl \
        wget \
        file \
        libxdo-dev \
        libssl-dev \
        libayatana-appindicator3-dev \
        librsvg2-dev
elif [ -f "/etc/fedora-release" ] || [ -f "/etc/redhat-release" ]; then
    echo -e "\e[33mDetected Fedora/RedHat-based Linux. Installing dependencies...\e[0m"
    sudo dnf group install -y development-tools
    sudo dnf install -y \
        webkit2gtk4.1-devel \
        openssl-devel \
        curl \
        wget \
        file \
        libxdo-devel \
        libayatana-appindicator-gtk3-devel \
        librsvg2-devel
elif [ -f "/etc/arch-release" ] || [ -f "/etc/manjaro-release" ] || command -v pacman &> /dev/null; then
    echo -e "\e[33mDetected Arch-based Linux. Installing dependencies...\e[0m"
    sudo pacman -Syu --needed --noconfirm \
        webkit2gtk-4.1 \
        base-devel \
        curl \
        wget \
        file \
        xdotool \
        openssl \
        libayatana-appindicator \
        librsvg \
        nodejs \
        npm
else
    echo -e "\e[31mUnsupported OS: $(uname). Please install system dependencies manually.\e[0m"
    exit 1
fi

# Install pyenv if not already installed
if ! command -v pyenv &> /dev/null; then
    echo "Installing pyenv..."
    curl https://pyenv.run | bash
    
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init - bash)"' >> ~/.bashrc

    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
    echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
    echo 'eval "$(pyenv init - bash)"' >> ~/.profile

    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
    echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile
    echo 'eval "$(pyenv init - bash)"' >> ~/.bash_profile

    source ~/.bash_profile

fi

echo "Installing Python 3.12..."
pyenv install 3.12.0
pyenv global 3.12.0

python_version=$(python --version)
echo "Installed: $python_version"


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

. "$HOME/.cargo/env"  

# ---- Install Node.js and npm (if not installed) ----
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed. Installing...${NC}"
    OS_TYPE=$(uname)
    if [ "$OS_TYPE" = "Linux" ]; then
        if [ -f "/etc/debian_version" ]; then
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif [ -f "/etc/fedora-release" ] || [ -f "/etc/redhat-release" ]; then
            curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo -E bash -
            sudo dnf install -y nodejs
        fi
    elif [ "$OS_TYPE" = "Darwin" ]; then
        brew install node
    fi
else
    echo -e "${GREEN}Node.js is installed. Version: $(node --version)${NC}"
    echo -e "${GREEN}npm version: $(npm --version)${NC}"
fi



# ---- Set up the backend ----
echo -e "${YELLOW}Setting up backend...${NC}"
cd "$REPO_ROOT/backend" || { echo -e "${RED}backend directory not found${NC}"; exit 1; }
rm -rf .env
python -m venv .env
source .env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# ---- Set up the sync-microservice ----
echo -e "${YELLOW}Setting up sync-microservice...${NC}"
cd "$REPO_ROOT/sync-microservice" || { echo -e "${RED}sync-microservice directory not found${NC}"; exit 1; }
rm -rf .sync-env
python -m venv .sync-env
source .sync-env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# ---- Set up the frontend ----
echo -e "${YELLOW}Setting up frontend...${NC}"
cd "$REPO_ROOT/frontend" || { echo -e "${RED}frontend directory not found${NC}"; exit 1; }
npm install
cd "$REPO_ROOT/frontend/src-tauri" || { echo -e "${RED}src-tauri directory not found${NC}"; exit 1; }
cargo build || { echo -e "${RED}Cargo build failed in src-tauri. Please check your Tauri setup.${NC}"; exit 1; }
cd "$REPO_ROOT"

echo -e "${GREEN}Setup complete!${NC}, restart the terminal to apply changes."
