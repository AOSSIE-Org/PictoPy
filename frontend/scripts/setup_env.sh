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

# Check and install Rust and Cargo
if ! command -v rustc &> /dev/null; then
    echo -e "${RED}Rust is not installed. Installing...${NC}"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
    
    # Add Rust to PATH if not already added
    if ! grep -q ".cargo/bin" ~/.bashrc; then
        echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    fi
    
    # Initialize Rust environment
    source ~/.bashrc
    rustup default stable
    rustup update
else
    echo -e "${GREEN}Rust is already installed. Version: $(rustc --version)${NC}"
    echo -e "${YELLOW}Updating Rust...${NC}"
    rustup update
fi

# Verify Cargo installation
if ! command -v cargo &> /dev/null; then
    echo -e "${RED}Cargo is not installed properly. Reinstalling Rust...${NC}"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path
    source $HOME/.cargo/env
else
    echo -e "${GREEN}Cargo is installed. Version: $(cargo --version)${NC}"
fi

# Check and install Node.js and npm
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed. Installing...${NC}"
    # Install Node.js 18.x
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    
    # Install npm if not installed
    if ! command -v npm &> /dev/null; then
        sudo apt-get install -y npm
    fi
    
    # Install n for Node.js version management
    sudo npm install -g n
    
    # Install and use the stable version
    sudo n stable
    
    # Refresh npm
    sudo npm install -g npm@latest
else
    echo -e "${GREEN}Node.js is already installed. Version: $(node --version)${NC}"
    echo -e "${GREEN}npm version: $(npm --version)${NC}"
    
    # Update npm to latest version
    echo -e "${YELLOW}Updating npm...${NC}"
    sudo npm install -g npm@latest
fi

# Verify all installations
echo -e "\n${YELLOW}Verifying installations...${NC}"
echo -e "${GREEN}Rust version: $(rustc --version)${NC}"
echo -e "${GREEN}Cargo version: $(cargo --version)${NC}"
echo -e "${GREEN}Node.js version: $(node --version)${NC}"
echo -e "${GREEN}npm version: $(npm --version)${NC}"

# Clean up
echo -e "\n${YELLOW}Cleaning up unused files...${NC}"
sudo apt-get clean
sudo rm -rf /var/lib/apt/lists/*

echo -e "${GREEN}All required tools and libraries are installed!${NC}"
echo -e "${YELLOW}Note: You may need to restart your terminal or run 'source ~/.bashrc' to use the installed tools.${NC}"