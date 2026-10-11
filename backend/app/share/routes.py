"""
The only routes reachable from the network. Everything here is unauthenticated
apart from the token in the path, so keep the surface exactly this small.
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
from email.utils import formatdate, parsedate_to_datetime
from typing import Dict, Optional

from fastapi import APIRouter, Form, HTTPException, Path, Request, Response, status
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
)
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
from app.utils.xmp import open_without_pictopy

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


# Bump when the bytes served for an unchanged file change (a new strip rule),
# so browsers stop reusing copies made under the old rule.
_PHOTO_VARIANT = "photo-v1"
# Browsers keep their copy but must ask before each use, so revoking or
# expiring a share also stops cached photos from showing. The question costs
# a bodiless 304, never a re-download.
_CACHE_CONTROL = "private, no-cache"


def _validators(stat: os.stat_result, variant: str) -> Dict[str, str]:
    seed = f"{stat.st_mtime_ns}-{stat.st_size}-{variant}".encode()
    return {
        "ETag": f'"{hashlib.sha256(seed).hexdigest()[:32]}"',
        "Last-Modified": formatdate(stat.st_mtime, usegmt=True),
        "Cache-Control": _CACHE_CONTROL,
    }


def _is_not_modified(request: Request, validators: Dict[str, str]) -> bool:
    # RFC 9110: If-None-Match wins; If-Modified-Since only applies without it.
    if_none_match = request.headers.get("if-none-match")
    if if_none_match is not None:
        etag = validators["ETag"]
        candidates = (c.strip() for c in if_none_match.split(","))
        return any(c in ("*", etag, f"W/{etag}") for c in candidates)

    if_modified_since = request.headers.get("if-modified-since")
    if if_modified_since is None:
        return False
    try:
        since = parsedate_to_datetime(if_modified_since)
        modified = parsedate_to_datetime(validators["Last-Modified"])
    except (TypeError, ValueError):
        return False
    return since.tzinfo is not None and modified <= since


def _media_response(request: Request, path: str, *, variant: str) -> Response:
    """Serve a shared file with revalidation; photos lose PictoPy's metadata."""
    try:
        validators = _validators(os.stat(path), variant)
    except OSError:
        raise _not_found()
    # Answered only here, after the share has been re-authorized: a revoked
    # share gets a 404, not a 304 that would keep a cached copy alive.
    if _is_not_modified(request, validators):
        return Response(status_code=304, headers=validators)

    if variant == _PHOTO_VARIANT:
        # Exported PictoPy metadata carries face embeddings and names; guests
        # get the photo without it. Streamed, so memory does not grow with
        # file size.
        try:
            stream = open_without_pictopy(path)
        except OSError:
            raise _not_found()
        if stream is not None:
            return StreamingResponse(
                stream.chunks,
                media_type=mimetypes.guess_type(path)[0] or "application/octet-stream",
                headers={
                    **_validators(stream.source_stat, variant),
                    "Content-Length": str(stream.length),
                },
            )
    return FileResponse(path, headers=validators)


@router.get("/s/{token}/thumb/{image_id}")
def share_thumbnail(
    request: Request, token: str = Path(...), image_id: str = Path(...)
) -> Response:
    entry = _require_share(token)
    if not _is_unlocked(request, entry):
        raise _not_found()
    path = share_media_resolve_path(entry.album_id, image_id, thumbnail=True)
    if path is None:
        raise _not_found()
    return _media_response(request, path, variant="thumb")


@router.get("/s/{token}/photo/{image_id}")
def share_photo(
    request: Request, token: str = Path(...), image_id: str = Path(...)
) -> Response:
    entry = _require_share(token)
    if not _is_unlocked(request, entry):
        raise _not_found()
    path = share_media_resolve_path(entry.album_id, image_id, thumbnail=False)
    if path is None:
        raise _not_found()
    return _media_response(request, path, variant=_PHOTO_VARIANT)
