#!/bin/bash

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



# ---- Set up the backend ----
echo -e "${YELLOW}Setting up backend...${NC}"
cd ../backend
python -m venv .env
source .env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..

# ---- Set up the sync-microservice ----
echo -e "${YELLOW}Setting up sync-microservice...${NC}"
cd sync-microservice
python -m venv .sync-env
source .sync-env/bin/activate
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
