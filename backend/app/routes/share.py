from fastapi import APIRouter, Body, HTTPException, Path, status

from app.database.albums import db_get_album, db_get_album_images
from app.logging.setup_logging import get_logger
from app.schemas.share import (
    CreateShareRequest,
    CreateShareResponse,
    ErrorResponse,
    ShareErrorResponseEnvelope,
    GetInterfacesResponse,
    GetSharesResponse,
    Share,
    ShareInterface,
    ShareUrl,
    RevokeShareResponse,
)
from app.share.registry import (
    ShareEntry,
    share_registry_count,
    share_registry_create,
    share_registry_list,
    share_registry_revoke,
)
from app.share.server import share_server_port, share_server_start, share_server_stop
from app.utils.network import network_util_list_candidates

logger = get_logger(__name__)

router = APIRouter()


def _internal_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=ErrorResponse(
            success=False, error="Internal Server Error", message=message
        ).model_dump(),
    )


def _album_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponse(
            success=False,
            error="Album Not Found",
            message="No album exists with the provided ID.",
        ).model_dump(),
    )


def _to_share(entry: ShareEntry, port: int) -> Share:
    album = db_get_album(entry.album_id)
    return Share(
        token=entry.token,
        album_id=entry.album_id,
        # An album deleted while shared leaves the token pointing at nothing;
        # the viewer 404s, so say so here rather than failing the listing.
        album_name=album["album_name"] if album else "(deleted album)",
        image_count=len(db_get_album_images(entry.album_id)),
        port=port,
        created_at=entry.created_at.isoformat(),
        expires_at=entry.expires_at.isoformat() if entry.expires_at else None,
        urls=[
            ShareUrl(
                interface=candidate.interface,
                ip=candidate.ip,
                url=f"http://{candidate.ip}:{port}/s/{entry.token}",
            )
            for candidate in network_util_list_candidates()
        ],
    )


# GET /share/interfaces - Ranked LAN addresses the share could be reached on
@router.get("/interfaces", response_model=GetInterfacesResponse)
def get_interfaces() -> GetInterfacesResponse:
    """
    Candidate addresses, best guess first.

    Machines with virtual adapters routinely surface several, so the caller is
    expected to show this list rather than silently trust the first entry.
    """
    return GetInterfacesResponse(
        success=True,
        data=[
            ShareInterface(
                interface=candidate.interface,
                ip=candidate.ip,
                is_default_route=candidate.is_default_route,
                looks_virtual=candidate.looks_virtual,
                is_up=candidate.is_up,
            )
            for candidate in network_util_list_candidates()
        ],
    )


# GET /share/ - List every active share
@router.get("/", response_model=GetSharesResponse)
def get_shares() -> GetSharesResponse:
    port = share_server_port()
    if port is None:
        return GetSharesResponse(success=True, data=[])
    return GetSharesResponse(
        success=True, data=[_to_share(entry, port) for entry in share_registry_list()]
    )


# POST /share/albums/{album_id} - Start sharing an album over the network
@router.post(
    "/albums/{album_id}",
    response_model=CreateShareResponse,
    responses={code: {"model": ShareErrorResponseEnvelope} for code in [404, 500]},
)
async def create_share(
    album_id: str = Path(...), body: CreateShareRequest = Body(default=None)
) -> CreateShareResponse:
    """
    Issue a share token and make sure the network listener is up.

    An album's local lock is deliberately not consulted: locking protects the
    album inside PictoPy, while sharing carries its own authorization.
    """
    if not db_get_album(album_id):
        raise _album_not_found()

    try:
        port = await share_server_start()
    except OSError as e:
        raise _internal_error(f"Could not start the share server: {e}") from e

    entry = share_registry_create(
        album_id, expires_in_minutes=body.expires_in_minutes if body else None
    )
    logger.info(f"Sharing album {album_id} on port {port}")

    return CreateShareResponse(
        success=True,
        message="Album is now shared on the local network",
        data=_to_share(entry, port),
    )


# DELETE /share/{token} - Stop sharing
@router.delete(
    "/{token}",
    response_model=RevokeShareResponse,
    responses={404: {"model": ShareErrorResponseEnvelope}},
)
async def revoke_share(token: str = Path(...)) -> RevokeShareResponse:
    if not share_registry_revoke(token):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error="Share Not Found",
                message="No active share exists with the provided token.",
            ).model_dump(),
        )

    # Nothing is being served any more, so stop listening rather than leaving a
    # port open on the network.
    if share_registry_count() == 0:
        await share_server_stop()

    return RevokeShareResponse(success=True, message="Share revoked")
