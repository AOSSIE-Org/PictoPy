#!/bin/bash
# Type checking script for CI/CD and local development

set -e

echo "🔍 Running mypy type checker..."

cd "$(dirname "$0")/.."

# Check if mypy is installed
if ! command -v mypy &> /dev/null; then
    echo "❌ mypy not found. Installing..."
    pip install mypy
fi

# Run mypy with configuration
echo "Checking types in app directory..."
mypy app --config-file mypy.ini

echo "✅ Type checking complete!"

# Show summary
echo ""
echo "📊 Summary:"
mypy app --config-file mypy.ini | tail -1
