#!/bin/sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Remove images in the output directory
echo -e "${CYAN}Removing old images from output directory...${NC}"
rm .images/output/*

sleep 4

# Display system information
echo -e "${BLUE}Fetching system information...${NC}"
fastfetch

sleep 4

# Display size of the dataset
echo -e "
${YELLOW}============
Size of dataset
============
${NC}"
echo "
$ du -sh .images
"
du -sh .images

sleep 4

# prepare environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run main.py and measure time
echo -e "
${YELLOW}============
Running main.py
============
${NC}"
echo -e "${CYAN}Scanning the whole Drive...${NC}"
time python main.py

sleep 4

# Display DB schema
echo -e "
${YELLOW}============
DB schema:
============
${NC}"
sqlite3 ~/.pictopy.db .schema

sleep 4

# Testing message
echo -e "
${RED}=========
Image output here is only for testing purposes, won't be created in production, thus saving time
=========${NC}"

