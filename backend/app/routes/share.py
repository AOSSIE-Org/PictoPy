from typing import Optional

from fastapi import APIRouter, HTTPException, Path, status

from app.database.albums import db_get_album
from app.logging.setup_logging import get_logger
from app.schemas.share import (
    CreateShareRequest,
    CreateShareResponse,
    ErrorResponse,
    GetInterfacesResponse,
    GetSharesResponse,
    RevokeShareResponse,
    Share,
    ShareErrorResponseEnvelope,
    ShareInterface,
)
from app.share.registry import share_registry_list
from app.share.server import share_server_port
from app.utils.network import network_util_list_candidates
from app.utils.share import share_util_create, share_util_describe, share_util_revoke

logger = get_logger(__name__)

router = APIRouter()

_SERVER_ERROR = {500: {"model": ShareErrorResponseEnvelope}}
_NOT_FOUND = {404: {"model": ShareErrorResponseEnvelope}}


def _internal_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=ErrorResponse(
            success=False, error="Internal Server Error", message=message
        ).model_dump(),
    )


def _not_found(error: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponse(success=False, error=error, message=message).model_dump(),
    )


@router.get(
    "/interfaces", response_model=GetInterfacesResponse, responses=_SERVER_ERROR
)
def get_interfaces() -> GetInterfacesResponse:
    """
    Candidate addresses, best guess first.

    Machines with virtual adapters routinely surface several, so the caller is
    expected to show this list rather than silently trust the first entry.
    """
    return GetInterfacesResponse(
        success=True,
        data=[
            ShareInterface(**vars(candidate))
            for candidate in network_util_list_candidates()
        ],
    )


@router.get("/", response_model=GetSharesResponse, responses=_SERVER_ERROR)
def get_shares() -> GetSharesResponse:
    port = share_server_port()
    if port is None:
        return GetSharesResponse(success=True, data=[])
    return GetSharesResponse(
        success=True,
        data=[
            Share(**share_util_describe(entry, port)) for entry in share_registry_list()
        ],
    )


@router.post(
    "/albums/{album_id}",
    response_model=CreateShareResponse,
    responses={**_NOT_FOUND, **_SERVER_ERROR},
)
async def create_share(
    album_id: str = Path(...), body: Optional[CreateShareRequest] = None
) -> CreateShareResponse:
    """
    Issue a share token and make sure the network listener is up.

    An album's local lock is deliberately not consulted: locking protects the
    album inside PictoPy, while sharing carries its own authorization — the
    optional password on this request, which is hashed and never read back.
    """
    if not db_get_album(album_id):
        raise _not_found("Album Not Found", "No album exists with the provided ID.")

    try:
        entry = await share_util_create(
            album_id,
            expires_in_minutes=body.expires_in_minutes if body else None,
            password=body.password if body else None,
        )
    except OSError as e:
        raise _internal_error(f"Could not start the share server: {e}") from e

    port = share_server_port()
    if port is None:
        raise _internal_error("The share server stopped before the share was served.")

    logger.info(f"Sharing album {album_id} on port {port}")
    return CreateShareResponse(
        success=True,
        message="Album is now shared on the local network",
        data=Share(**share_util_describe(entry, port)),
    )


@router.delete(
    "/{token}",
    response_model=RevokeShareResponse,
    responses={**_NOT_FOUND, **_SERVER_ERROR},
)
async def revoke_share(token: str = Path(...)) -> RevokeShareResponse:
    if not await share_util_revoke(token):
        raise _not_found(
            "Share Not Found", "No active share exists with the provided token."
        )
    return RevokeShareResponse(success=True, message="Share revoked")
