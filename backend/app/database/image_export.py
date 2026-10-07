import json
from typing import Dict, List, Optional, TypedDict, Union

import numpy as np

from app.database.images import _connect
from app.database.semantic_labels import SEMANTIC_CLASS_ID_OFFSET


class ExportedFace(TypedDict):
    embedding: List[float]
    bbox: Optional[Dict[str, Union[int, float]]]
    confidence: Optional[float]
    cluster_name: Optional[str]


class ImageExportData(TypedDict):
    tags: List[str]
    semantic_tags: List[str]
    faces: List[ExportedFace]
    embedding_model: Optional[str]
    embedding: Optional[List[float]]
    favourite: bool
    albums: List[str]


def db_get_image_export_data(image_id: str) -> Optional[ImageExportData]:
    """Everything derived for one image, read in one connection for XMP export."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT isFavourite FROM images WHERE id = ?", (image_id,)
        ).fetchone()
        if row is None:
            return None

        tag_rows = conn.execute(
            """
            SELECT m.name, ic.class_id FROM image_classes ic
            JOIN mappings m ON m.class_id = ic.class_id
            WHERE ic.image_id = ? ORDER BY ic.class_id
            """,
            (image_id,),
        ).fetchall()

        faces: List[ExportedFace] = []
        for emb, bbox, conf, cluster_name in conn.execute(
            """
            SELECT f.embeddings, f.bbox, f.confidence, fc.cluster_name
            FROM faces f LEFT JOIN face_clusters fc ON f.cluster_id = fc.cluster_id
            WHERE f.image_id = ? ORDER BY f.face_id
            """,
            (image_id,),
        ):
            # A face with corrupt JSON must not block exporting the rest.
            try:
                faces.append(
                    {
                        "embedding": json.loads(emb),
                        "bbox": json.loads(bbox) if bbox else None,
                        "confidence": conf,
                        "cluster_name": cluster_name,
                    }
                )
            except (json.JSONDecodeError, TypeError):
                continue

        emb_row = conn.execute(
            "SELECT model_version, embedding FROM image_embeddings WHERE image_id = ?",
            (image_id,),
        ).fetchone()

        albums = conn.execute(
            """
            SELECT a.album_name FROM album_images ai
            JOIN albums a ON a.album_id = ai.album_id
            WHERE ai.image_id = ? ORDER BY a.album_name
            """,
            (image_id,),
        ).fetchall()

        return {
            "tags": [n for n, cid in tag_rows if cid < SEMANTIC_CLASS_ID_OFFSET],
            "semantic_tags": [
                n for n, cid in tag_rows if cid >= SEMANTIC_CLASS_ID_OFFSET
            ],
            "faces": faces,
            "embedding_model": emb_row[0] if emb_row else None,
            "embedding": (
                np.frombuffer(emb_row[1], dtype=np.float32).tolist()
                if emb_row
                else None
            ),
            "favourite": bool(row[0]),
            "albums": [a[0] for a in albums],
        }
    finally:
        conn.close()
