"""
The only routes reachable from the network. Everything here is unauthenticated
apart from the token in the path, so keep the surface exactly this small.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Path, Request, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.logging.setup_logging import get_logger
from app.share.media import (
    share_media_album_name,
    share_media_image_ids,
    share_media_resolve_path,
)
from app.share.registry import ShareEntry, share_registry_get

logger = get_logger(__name__)

router = APIRouter()

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


def _not_found() -> HTTPException:
    """
    One shape for every failure.

    A revoked token, an expired one and a token that never existed must be
    indistinguishable, or the response becomes an oracle for guessing.
    """
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


def _require_share(token: str) -> ShareEntry:
    entry = share_registry_get(token)
    if entry is None:
        raise _not_found()
    return entry


@router.get("/s/{token}", response_class=HTMLResponse)
def view_share(request: Request, token: str = Path(...)) -> HTMLResponse:
    entry = _require_share(token)

    album_name = share_media_album_name(entry.album_id)
    if album_name is None:
        # The album was deleted while shared; the token is now meaningless.
        raise _not_found()

    return templates.TemplateResponse(
        request,
        "album.html",
        {
            "album_name": album_name,
            "token": entry.token,
            "image_ids": share_media_image_ids(entry.album_id),
            # The page reformats this into the viewer's own locale.
            "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
        },
    )


@router.get("/s/{token}/thumb/{image_id}")
def share_thumbnail(token: str = Path(...), image_id: str = Path(...)) -> FileResponse:
    entry = _require_share(token)
    path = share_media_resolve_path(entry.album_id, image_id, thumbnail=True)
    if path is None:
        raise _not_found()
    return FileResponse(path)


@router.get("/s/{token}/photo/{image_id}")
def share_photo(token: str = Path(...), image_id: str = Path(...)) -> FileResponse:
    entry = _require_share(token)
    path = share_media_resolve_path(entry.album_id, image_id, thumbnail=False)
    if path is None:
        raise _not_found()
    return FileResponse(path)
