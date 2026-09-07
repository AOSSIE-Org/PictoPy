"""
Generate the OpenAPI schema and write it to docs/backend/backend_python/openapi.json.

Run this deliberately (e.g. before committing API changes or in CI) instead of
regenerating on every backend startup.

Usage:
    python scripts/generate_openapi.py
"""
import os
import sys

# Ensure backend directory is in sys.path so we can import from main/app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import generate_openapi_json

if __name__ == "__main__":
    generate_openapi_json()