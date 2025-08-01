#!/bin/bash

# PictoPy Documentation Setup Script
# This script installs the necessary dependencies for building and serving the documentation

echo "📚 Setting up PictoPy Documentation..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

echo "🐍 Installing documentation dependencies..."

# Install documentation dependencies
if [ -f "docs/requirements.txt" ]; then
    echo "📦 Installing from docs/requirements.txt..."
    pip install -r docs/requirements.txt
elif [ -f "requirements.txt" ]; then
    echo "📦 Installing from requirements.txt..."
    pip install -r requirements.txt
else
    echo "❌ No requirements.txt file found. Installing mkdocs-material directly..."
    pip install mkdocs-material
fi

# Check if installation was successful
if command -v mkdocs &> /dev/null; then
    echo "✅ Documentation dependencies installed successfully!"
    echo ""
    echo "🚀 You can now:"
    echo "   - Build documentation: mkdocs build"
    echo "   - Serve documentation: mkdocs serve"
    echo "   - Access docs at: http://127.0.0.1:8000/"
    echo ""
    echo "📖 For more information, see the documentation setup guide."
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi 