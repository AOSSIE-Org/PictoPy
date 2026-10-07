import json
from typing import Dict, List, Optional, Tuple, TypedDict, Union

import numpy as np

from app.database.images import SQLITE_ID_CHUNK, _connect
from app.database.semantic_labels import SEMANTIC_CLASS_ID_OFFSET


class ExportedFace(TypedDict):
    embedding: List[float]
    bbox: Optional[Dict[str, Union[int, float]]]
    confidence: Optional[float]
    cluster_name: Optional[str]


class ImageExportData(TypedDict):
    tags: List[str]
    semantic_tags: List[Tuple[str, float]]
    faces: List[ExportedFace]
    embedding_model: Optional[str]
    embedding: Optional[List[float]]
    semantic_signature: Optional[str]
    favourite: bool
    albums: List[str]
    width: Optional[int]
    height: Optional[int]


def _dimensions(metadata_json: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    try:
        metadata = json.loads(metadata_json) if metadata_json else {}
        width, height = int(metadata.get("width") or 0), int(
            metadata.get("height") or 0
        )
    except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
        return None, None
    # 0x0 is what the indexer records when Pillow could not open the file.
    return (width, height) if width and height else (None, None)


def db_get_image_export_data(image_ids: List[str]) -> Dict[str, ImageExportData]:
    """Everything derived for these images, keyed by id; unknown ids are absent."""
    result: Dict[str, ImageExportData] = {}
    if not image_ids:
        return result

    conn = _connect()
    try:
        for start in range(0, len(image_ids), SQLITE_ID_CHUNK):
            chunk = image_ids[start : start + SQLITE_ID_CHUNK]
            marks = ", ".join("?" * len(chunk))

            for image_id, is_favourite, metadata_json in conn.execute(
                f"SELECT id, isFavourite, metadata FROM images WHERE id IN ({marks})",
                chunk,
            ):
                width, height = _dimensions(metadata_json)
                result[image_id] = {
                    "tags": [],
                    "semantic_tags": [],
                    "faces": [],
                    "embedding_model": None,
                    "embedding": None,
                    "semantic_signature": None,
                    "favourite": bool(is_favourite),
                    "albums": [],
                    "width": width,
                    "height": height,
                }

            # Deactivated labels keep their rows until the next rescore; they
            # are no longer part of the vocabulary, so they are not exported.
            for image_id, name, class_id, score in conn.execute(
                f"""
                SELECT ic.image_id, m.name, ic.class_id, ic.score
                FROM image_classes ic
                JOIN mappings m ON m.class_id = ic.class_id
                LEFT JOIN semantic_labels sl ON sl.class_id = ic.class_id
                WHERE ic.image_id IN ({marks})
                  AND (ic.class_id < ? OR sl.active = 1)
                ORDER BY ic.image_id, ic.class_id
                """,
                [*chunk, SEMANTIC_CLASS_ID_OFFSET],
            ):
                if class_id < SEMANTIC_CLASS_ID_OFFSET:
                    result[image_id]["tags"].append(name)
                elif score is not None:
                    result[image_id]["semantic_tags"].append((name, score))

            for image_id, emb, bbox, conf, cluster_name in conn.execute(
                f"""
                SELECT f.image_id, f.embeddings, f.bbox, f.confidence, fc.cluster_name
                FROM faces f
                LEFT JOIN face_clusters fc ON f.cluster_id = fc.cluster_id
                WHERE f.image_id IN ({marks})
                ORDER BY f.image_id, f.face_id
                """,
                chunk,
            ):
                # A face with corrupt JSON must not block exporting the rest.
                try:
                    face: ExportedFace = {
                        "embedding": json.loads(emb),
                        "bbox": json.loads(bbox) if bbox else None,
                        "confidence": conf,
                        "cluster_name": cluster_name,
                    }
                except (json.JSONDecodeError, TypeError):
                    continue
                result[image_id]["faces"].append(face)

            for image_id, model_version, blob, signature in conn.execute(
                f"""
                SELECT image_id, model_version, embedding, scored_signature
                FROM image_embeddings WHERE image_id IN ({marks})
                """,
                chunk,
            ):
                row = result[image_id]
                row["embedding_model"] = model_version
                row["embedding"] = np.frombuffer(blob, dtype=np.float32).tolist()
                row["semantic_signature"] = signature

            # Membership of a locked album is private; it never leaves the DB.
            for image_id, album_name in conn.execute(
                f"""
                SELECT ai.image_id, a.album_name FROM album_images ai
                JOIN albums a ON a.album_id = ai.album_id
                WHERE ai.image_id IN ({marks}) AND IFNULL(a.is_locked, 0) = 0
                ORDER BY ai.image_id, a.album_name
                """,
                chunk,
            ):
                result[image_id]["albums"].append(album_name)
        return result
    finally:
        conn.close()
