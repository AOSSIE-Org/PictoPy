from typing import Optional

from app.database.image_export import db_get_image_export_data

from .schema import EmbeddingRecord, FaceRecord, PictoPyMetadata


def collect_image_metadata(image_id: str) -> Optional[PictoPyMetadata]:
    """Gather what PictoPy has stored for an image, or None if it is unknown."""
    data = db_get_image_export_data(image_id)
    if data is None:
        return None
    embedding = (
        EmbeddingRecord(data["embedding_model"], data["embedding"])
        if data["embedding_model"] and data["embedding"] is not None
        else None
    )
    return PictoPyMetadata(
        tags=data["tags"],
        semantic_tags=data["semantic_tags"],
        faces=[
            FaceRecord(
                embedding=f["embedding"],
                bbox=f["bbox"],
                confidence=f["confidence"],
                cluster_name=f["cluster_name"],
            )
            for f in data["faces"]
        ],
        image_embedding=embedding,
        favourite=data["favourite"],
        albums=data["albums"],
    )
