"""
The album share server: a second FastAPI app bound to the local network.

Kept separate from the main backend because that one exposes shutdown, delete
and metadata routes that must never leave localhost.
"""
