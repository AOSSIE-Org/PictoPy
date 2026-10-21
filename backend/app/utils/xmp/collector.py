import os
from typing import Dict, List

from app.config.settings import DEFAULT_FACENET_MODEL
from app.database.image_export import ImageExportData, db_get_image_export_data

from .schema import EmbeddingRecord, FaceRecord, PictoPyMetadata, SemanticTag

# Only one face embedder ships, so its file name identifies the model.
FACE_EMBEDDING_MODEL = os.path.splitext(os.path.basename(DEFAULT_FACENET_MODEL))[0]


def _to_metadata(data: ImageExportData) -> PictoPyMetadata:
    models: Dict[str, str] = {}
    if data["faces"]:
        models["face_embedding"] = FACE_EMBEDDING_MODEL
    if data["semantic_signature"]:
        models["semantic_vocabulary"] = data["semantic_signature"]

    embedding = (
        EmbeddingRecord(data["embedding_model"], data["embedding"])
        if data["embedding_model"] and data["embedding"] is not None
        else None
    )
    return PictoPyMetadata(
        tags=data["tags"],
        semantic_tags=[SemanticTag(n, s) for n, s in data["semantic_tags"]],
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
        models=models,
        width=data["width"],
        height=data["height"],
    )


def collect_image_metadata(image_ids: List[str]) -> Dict[str, PictoPyMetadata]:
    """What PictoPy has stored for each image, keyed by id; unknown ids are absent."""
    return {
        image_id: _to_metadata(data)
        for image_id, data in db_get_image_export_data(image_ids).items()
    }
