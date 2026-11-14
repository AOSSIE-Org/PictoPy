import pytest
from app.schemas.album import CreateAlbumRequest

def test_create_album_no_password():
    with pytest.raises(ValueError):
        CreateAlbumRequest(
            name = "ABCD",
            is_locked = True
        )