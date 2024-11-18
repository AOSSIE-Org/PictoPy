#!/bin/bash


RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' 

# Update packages
echo -e "${YELLOW}Updating package lists...${NC}"
sudo apt-get update -y

# Required packages
packages=(
    curl
    build-essential
    libgtk-3-dev
    libwebkit2gtk-4.0-dev
    libappindicator3-dev
    wget
    xz-utils
    libssl-dev
    libglib2.0-dev
    libgirepository1.0-dev
    pkg-config
    software-properties-common
    libjavascriptcoregtk-4.0-dev
    libjavascriptcoregtk-4.1-dev
    libsoup-3.0-dev
    libwebkit2gtk-4.1-dev
    librsvg2-dev
    file 
)

# check and install required packages
echo -e "${YELLOW}Checking and installing required packages...${NC}"
for package in "${packages[@]}"; do
    if dpkg -l | grep -q "^ii\s\+$package"; then
        echo -e "${GREEN}$package is already installed.${NC}"
    else
        echo -e "${RED}$package is not installed. Installing...${NC}"
        sudo apt-get install -y "$package"
    fi
done

# Check and install Rust
if ! command -v rustc &> /dev/null; then
    echo -e "${RED}Rust is not installed. Installing...${NC}"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
else
    echo -e "${GREEN}Rust is already installed. Version: $(rustc --version)${NC}"
fi

# Check and install Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed. Installing...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    echo -e "${GREEN}Node.js is already installed. Version: $(node --version)${NC}"
fi

# Clean up
echo -e "${YELLOW}Cleaning up unused files...${NC}"
sudo apt-get clean
sudo rm -rf /var/lib/apt/lists/*

echo -e "${GREEN}All required tools and libraries are installed!${NC}"
