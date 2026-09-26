"""
The share FastAPI application.

Separate from the main backend app on purpose: this one is bound to 0.0.0.0 and
anything mounted here is reachable by every device that can route to this
machine. Add routes only when they are meant to be public.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.share.routes import router as share_routes


def create_share_app() -> FastAPI:
    # No CORS middleware: the main app allows every origin, and inheriting that
    # here would let any page on the network read a share through a browser.
    # The interactive docs would also enumerate the surface, so they stay off.
    app = FastAPI(
        title="PictoPy Share",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.include_router(share_routes)
    return app
