"""
The only routes reachable from the network. Everything here is unauthenticated
apart from the token in the path, so keep the surface exactly this small.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Path, Request, Response, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.logging.setup_logging import get_logger
from app.share.media import (
    share_media_album_name,
    share_media_image_ids,
    share_media_resolve_path,
)
from app.share.registry import (
    ShareEntry,
    share_registry_get,
    share_registry_is_throttled,
    share_registry_is_unlocked,
    share_registry_unlock,
)

logger = get_logger(__name__)

router = APIRouter()

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)

# Scoped to the share's own path so one album's unlock is never sent to another,
# and left as a session cookie so closing the browser ends the visit.
_UNLOCK_COOKIE = "pictopy_share_unlock"


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


def _is_unlocked(request: Request, entry: ShareEntry) -> bool:
    return share_registry_is_unlocked(entry, request.cookies.get(_UNLOCK_COOKIE))


def _to_album(token: str) -> RedirectResponse:
    """See-other, so refreshing the album does not repost the password."""
    return RedirectResponse(f"/s/{token}", status_code=status.HTTP_303_SEE_OTHER)


def _unlock_page(
    request: Request,
    token: str,
    error: Optional[str] = None,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    """
    The gate a visitor meets before the album exists to them.

    It names nothing about the album — not the title, not the photo count — so a
    link that leaks tells its finder only that some album is being shared.
    """
    return templates.TemplateResponse(
        request,
        "unlock.html",
        {"token": token, "error": error},
        status_code=status_code,
    )


@router.get("/s/{token}", response_class=HTMLResponse)
def view_share(request: Request, token: str = Path(...)) -> HTMLResponse:
    entry = _require_share(token)
    if not _is_unlocked(request, entry):
        return _unlock_page(request, entry.token)

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


@router.post("/s/{token}/unlock")
def unlock_share(
    request: Request, token: str = Path(...), password: str = Form(...)
) -> Response:
    entry = _require_share(token)
    if not entry.is_protected:
        return _to_album(entry.token)

    # Advisory only: the refusal itself is enforced inside the registry, this
    # just tells the visitor which of the two refusals they are looking at.
    throttled = share_registry_is_throttled(entry)
    cookie = share_registry_unlock(entry, password)
    if cookie is None:
        message = (
            "Too many attempts. Wait half a minute and try again."
            if throttled
            else "That password is not right."
        )
        return _unlock_page(request, entry.token, message, status.HTTP_401_UNAUTHORIZED)

    response = _to_album(entry.token)
    response.set_cookie(
        _UNLOCK_COOKIE,
        cookie,
        path=f"/s/{entry.token}",
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/s/{token}/thumb/{image_id}")
def share_thumbnail(
    request: Request, token: str = Path(...), image_id: str = Path(...)
) -> FileResponse:
    entry = _require_share(token)
    if not _is_unlocked(request, entry):
        raise _not_found()
    path = share_media_resolve_path(entry.album_id, image_id, thumbnail=True)
    if path is None:
        raise _not_found()
    return FileResponse(path)


@router.get("/s/{token}/photo/{image_id}")
def share_photo(
    request: Request, token: str = Path(...), image_id: str = Path(...)
) -> FileResponse:
    entry = _require_share(token)
    if not _is_unlocked(request, entry):
        raise _not_found()
    path = share_media_resolve_path(entry.album_id, image_id, thumbnail=False)
    if path is None:
        raise _not_found()
    return FileResponse(path)
