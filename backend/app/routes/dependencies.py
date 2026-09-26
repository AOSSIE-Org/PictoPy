"""Dependencies shared by the route modules."""

from fastapi import Request
from starlette.datastructures import State


def get_state(request: Request) -> State:
    """Application state, which is where the shared executors live."""
    return request.app.state
