from fastapi import FastAPI, HTTPException
from typing import List, Dict, Optional
from models import SmartAlbum, Photo
from pydantic import BaseModel
from ai_stub import refresh_album_contents

app = FastAPI(title="PictoPy Albums API")

# In-memory stores (replace with DB in production)
albums: Dict[str, SmartAlbum] = {}
photos: Dict[str, Photo] = {
    "p1": Photo(id="p1", url="http://example.com/cat.jpg", tags=["cat", "pet"], faces=0),
    "p2": Photo(id="p2", url="http://example.com/dog.jpg", tags=["dog", "pet"], faces=0),
    "p3": Photo(id="p3", url="http://example.com/person1.jpg", tags=["person"], faces=1),
    "p4": Photo(id="p4", url="http://example.com/person2.jpg", tags=["person", "smile"], faces=2),
}


class AlbumCreate(BaseModel):
    name: str
    type: str
    photos: Optional[List[str]] = []
    auto_update: Optional[bool] = False


class AlbumUpdate(BaseModel):
    name: Optional[str]
    type: Optional[str]
    photos: Optional[List[str]]
    auto_update: Optional[bool]


@app.get("/albums", response_model=List[SmartAlbum])
def list_albums():
    return list(albums.values())


@app.post("/albums", response_model=SmartAlbum, status_code=201)
def create_album(body: AlbumCreate):
    album = SmartAlbum(name=body.name, type=body.type, photos=body.photos or [], auto_update=body.auto_update)
    albums[album.id] = album
    return album


@app.patch("/albums/{album_id}", response_model=SmartAlbum)
def update_album(album_id: str, body: AlbumUpdate):
    if album_id not in albums:
        raise HTTPException(status_code=404, detail="Album not found")
    album = albums[album_id]
    update_data = body.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(album, k, v)
    albums[album_id] = album
    return album


@app.delete("/albums/{album_id}", status_code=204)
def delete_album(album_id: str):
    if album_id not in albums:
        raise HTTPException(status_code=404, detail="Album not found")
    del albums[album_id]
    return None


@app.post("/albums/{album_id}/refresh", response_model=SmartAlbum)
def refresh_album(album_id: str):
    if album_id not in albums:
        raise HTTPException(status_code=404, detail="Album not found")
    album = albums[album_id]
    new_photo_ids = refresh_album_contents(album, photos)
    album.photos = new_photo_ids
    albums[album_id] = album
    return album


@app.get("/photos", response_model=List[Photo])
def list_photos():
    return list(photos.values())


@app.get("/photos/{photo_id}", response_model=Photo)
def get_photo(photo_id: str):
    if photo_id not in photos:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photos[photo_id]
