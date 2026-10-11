import json

import numpy as np
import pytest

from app.database import (
    albums,
    face_clusters,
    faces,
    folders,
    image_embeddings,
    images,
    semantic_labels,
    video_frames,
    videos,
    yolo_mapping,
)
from app.database.image_export import db_get_image_export_data
from app.utils.xmp.collector import collect_image_metadata


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    # Each database module binds DATABASE_PATH at import, so patch them all
    # or a local run would touch the real library.
    db_path = str(tmp_path / "export.sqlite3")
    for module in (
        albums, face_clusters, faces, folders, image_embeddings, images,
        semantic_labels, video_frames, videos, yolo_mapping,
    ):  # fmt: skip
        if hasattr(module, "DATABASE_PATH"):
            monkeypatch.setattr(module, "DATABASE_PATH", db_path)

    yolo_mapping.db_create_YOLO_classes_table()
    folders.db_create_folders_table()
    images.db_create_images_table()
    semantic_labels.db_create_semantic_labels_table()
    face_clusters.db_create_clusters_table()
    videos.db_create_videos_table()
    video_frames.db_create_video_frames_tables()
    faces.db_create_faces_table()
    image_embeddings.db_create_image_embeddings_table()
    albums.db_create_albums_table()
    albums.db_create_album_images_table()
    yield


def _seed(image_id: str = "img1") -> None:
    conn = images._connect()
    conn.execute(
        "INSERT INTO images (id, path, thumbnailPath, metadata, isFavourite) "
        "VALUES (?, '/x.png', '/t.png', '{\"width\": 640, \"height\": 480}', 1)",
        (image_id,),
    )
    conn.executemany(
        "INSERT INTO mappings (class_id, name) VALUES (?, ?)",
        [(1000, "sunset"), (1001, "retired")],
    )
    conn.executemany(
        "INSERT INTO semantic_labels (class_id, name, category, descriptions, active) "
        "VALUES (?, ?, 'scene', '[]', ?)",
        [(1000, "sunset", 1), (1001, "retired", 0)],
    )
    conn.executemany(
        "INSERT INTO image_classes (image_id, class_id, score) VALUES (?, ?, ?)",
        [(image_id, 0, None), (image_id, 1000, 0.4), (image_id, 1001, 0.9)],
    )
    conn.execute(
        "INSERT INTO face_clusters (cluster_id, cluster_name) VALUES ('c1', 'Ann')"
    )
    conn.execute(
        "INSERT INTO faces (image_id, cluster_id, embeddings, confidence, bbox) "
        "VALUES (?, 'c1', ?, 0.9, ?)",
        (image_id, json.dumps([0.5, 1.5]), json.dumps({"x": 1, "y": 2})),
    )
    conn.execute(
        "INSERT INTO faces (image_id, embeddings) VALUES (?, 'not json')", (image_id,)
    )
    conn.execute(
        "INSERT INTO image_embeddings "
        "(image_id, model_version, embedding, scored_signature) VALUES (?, 'm1', ?, 'sig')",
        (image_id, np.array([0.25, 0.5], dtype=np.float32).tobytes()),
    )
    conn.execute("INSERT INTO albums (album_id, album_name) VALUES ('a1', 'Trip')")
    conn.execute(
        "INSERT INTO album_images (album_id, image_id) VALUES ('a1', ?)", (image_id,)
    )
    conn.commit()
    conn.close()


def test_unknown_image_is_absent():
    assert db_get_image_export_data(["nope"]) == {}
    assert collect_image_metadata(["nope"]) == {}


def test_collects_every_section():
    _seed()
    meta = collect_image_metadata(["img1", "nope"])["img1"]
    assert meta.tags == ["person"]
    assert [(t.name, t.score) for t in meta.semantic_tags] == [("sunset", 0.4)]
    # The corrupt face row is skipped, not fatal.
    assert len(meta.faces) == 1
    assert meta.faces[0].cluster_name == "Ann"
    assert meta.faces[0].bbox == {"x": 1, "y": 2}
    assert meta.image_embedding is not None
    assert meta.image_embedding.model_version == "m1"
    assert meta.image_embedding.vector == [0.25, 0.5]
    assert meta.models == {
        "face_embedding": "FaceNet_128D",
        "semantic_vocabulary": "sig",
    }
    assert meta.favourite is True
    assert (meta.width, meta.height) == (640, 480)


def test_locked_albums_are_never_exported():
    _seed()
    assert collect_image_metadata(["img1"])["img1"].albums == ["Trip"]


def test_batches_beyond_one_sqlite_chunk(monkeypatch):
    import app.database.image_export as export_module

    monkeypatch.setattr(export_module, "SQLITE_ID_CHUNK", 1)
    _seed("img1")
    conn = images._connect()
    conn.execute(
        "INSERT INTO images (id, path, thumbnailPath, metadata) "
        "VALUES ('img2', '/y.png', '/u.png', '{}')"
    )
    conn.commit()
    conn.close()
    data = db_get_image_export_data(["img1", "img2"])
    assert set(data) == {"img1", "img2"}
    assert data["img2"]["tags"] == [] and data["img2"]["width"] is None
