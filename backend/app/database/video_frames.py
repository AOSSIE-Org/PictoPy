"""Sampled video keyframes and the tags derived from them.

Frames are deliberately kept out of the images table: they would otherwise
leak into the photo gallery, memories and face clustering. These tables
mirror their image counterparts so the existing tagging passes port over
with the same shapes.
"""

import sqlite3
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.database.images import _connect
from app.database.semantic_labels import SEMANTIC_CLASS_ID_OFFSET
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def db_create_video_frames_tables() -> None:
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()

        # frame_path is nullable so the purge action can drop the JPEGs
        # without destroying the embeddings that depend on them.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS video_frames (
                id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                frame_path TEXT UNIQUE,
                timestamp_sec REAL,
                frame_index INTEGER,
                isEmbedded BOOLEAN DEFAULT 0,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_video_frames_video_id "
            "ON video_frames(video_id)"
        )

        # Same raw-float32 blob format as image_embeddings.embedding.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS video_frame_embeddings (
                frame_id TEXT PRIMARY KEY,
                model_version TEXT NOT NULL,
                embedding BLOB NOT NULL,
                scored_signature TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (frame_id) REFERENCES video_frames(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_video_frame_embeddings_model_version "
            "ON video_frame_embeddings(model_version)"
        )

        # Video-level tags, aggregated from the frames at write time so tag
        # queries stay a plain join. score is NULL for YOLO rows and the best
        # frame's match score for semantic rows, matching image_classes.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS video_classes (
                video_id TEXT,
                class_id INTEGER,
                score REAL,
                frame_count INTEGER,
                PRIMARY KEY (video_id, class_id),
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
                FOREIGN KEY (class_id) REFERENCES mappings(class_id) ON DELETE CASCADE
            )
            """
        )

        # Display cut mirroring image_classes_display: all YOLO tags, but only
        # the top-SEMANTIC_DISPLAY_TOP_K semantic tags per video. Recreated at
        # startup so setting changes apply without re-scoring.
        from app.config.settings import SEMANTIC_DISPLAY_TOP_K

        cursor.execute("DROP VIEW IF EXISTS video_classes_display")
        cursor.execute(
            f"""
            CREATE VIEW video_classes_display AS
            SELECT video_id, class_id FROM (
                SELECT video_id, class_id,
                       ROW_NUMBER() OVER (
                           PARTITION BY video_id ORDER BY score DESC
                       ) AS display_rank
                FROM video_classes WHERE score IS NOT NULL
            ) WHERE display_rank <= {int(SEMANTIC_DISPLAY_TOP_K)}
            UNION ALL
            SELECT video_id, class_id FROM video_classes WHERE score IS NULL
            """
        )

        conn.commit()
    finally:
        if conn:
            conn.close()


def db_get_untagged_videos() -> List[Dict[str, str]]:
    """Videos in AI-tagging-enabled folders that have not been tagged yet."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT v.id, v.path
            FROM videos v
            JOIN folders f ON v.folder_id = f.folder_id
            WHERE f.AI_Tagging = TRUE
              AND v.isTagged = FALSE
            """
        )
        return [{"id": video_id, "path": path} for video_id, path in cursor.fetchall()]
    finally:
        if conn:
            conn.close()


def db_mark_videos_tagged(video_ids: List[str]) -> bool:
    if not video_ids:
        return True

    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in video_ids)
        cursor.execute(
            f"UPDATE videos SET isTagged = 1 WHERE id IN ({placeholders})",
            video_ids,
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error marking videos as tagged: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def db_bulk_insert_video_frames(frame_records: List[dict]) -> bool:
    """Insert sampled frame rows: id, video_id, frame_path, timestamp_sec,
    frame_index."""
    if not frame_records:
        return True

    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO video_frames
                (id, video_id, frame_path, timestamp_sec, frame_index)
            VALUES (:id, :video_id, :frame_path, :timestamp_sec, :frame_index)
            ON CONFLICT(frame_path) DO UPDATE SET
                video_id=excluded.video_id,
                timestamp_sec=excluded.timestamp_sec,
                frame_index=excluded.frame_index
            """,
            frame_records,
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error inserting video frames: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def db_delete_frames_for_videos(video_ids: List[str]) -> bool:
    """Drop a video's frame rows (and, by cascade, their embeddings) so a
    re-tag starts from a clean sample."""
    if not video_ids:
        return True

    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in video_ids)
        cursor.execute(
            f"DELETE FROM video_frames WHERE video_id IN ({placeholders})",
            video_ids,
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error deleting video frames: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def db_get_unembedded_video_frames() -> List[Dict[str, str]]:
    """Frames still needing a SigLIP2 embedding. Purged frames (frame_path
    NULL) are excluded -- there is nothing left on disk to embed."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT vf.id, vf.frame_path
            FROM video_frames vf
            JOIN videos v ON vf.video_id = v.id
            JOIN folders f ON v.folder_id = f.folder_id
            WHERE f.AI_Tagging = TRUE
              AND vf.isEmbedded = FALSE
              AND vf.frame_path IS NOT NULL
            """
        )
        return [
            {"id": frame_id, "frame_path": frame_path}
            for frame_id, frame_path in cursor.fetchall()
        ]
    finally:
        if conn:
            conn.close()


def db_mark_video_frames_embedded(frame_ids: List[str]) -> bool:
    if not frame_ids:
        return True

    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        # Chunked by 500 to stay under SQLite's 999-variable limit, matching
        # db_mark_images_embedded.
        chunk_size = 500
        for i in range(0, len(frame_ids), chunk_size):
            chunk = frame_ids[i : i + chunk_size]
            placeholders = ",".join("?" for _ in chunk)
            cursor.execute(
                f"UPDATE video_frames SET isEmbedded = 1 WHERE id IN ({placeholders})",
                chunk,
            )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error marking video frames as embedded: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def db_upsert_video_frame_embeddings(
    rows: List[Tuple[str, str, np.ndarray]],
) -> None:
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO video_frame_embeddings (frame_id, model_version, embedding)
            VALUES (?, ?, ?)
            ON CONFLICT(frame_id) DO UPDATE SET
                model_version = excluded.model_version,
                embedding = excluded.embedding,
                scored_signature = NULL,
                created_at = CURRENT_TIMESTAMP
            """,
            [
                (
                    frame_id,
                    model_version,
                    np.ascontiguousarray(embedding, dtype=np.float32).tobytes(),
                )
                for frame_id, model_version, embedding in rows
            ],
        )
        conn.commit()
    finally:
        if conn:
            conn.close()


def db_write_video_classes(video_id: str, pairs: List[Tuple[int, int]]) -> None:
    """Replace a video's YOLO tag rows with (class_id, frame_count) pairs.
    Semantic rows (class_id at or above the offset) are never touched."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM video_classes WHERE video_id = ? AND class_id < ?",
            (video_id, SEMANTIC_CLASS_ID_OFFSET),
        )
        cursor.executemany(
            "INSERT OR REPLACE INTO video_classes "
            "(video_id, class_id, score, frame_count) VALUES (?, ?, NULL, ?)",
            [(video_id, class_id, frame_count) for class_id, frame_count in pairs],
        )
        conn.commit()
    finally:
        if conn:
            conn.close()


def db_write_video_semantic_scores(
    video_id: str, pairs: List[Tuple[int, float, int]], signature: str
) -> None:
    """Replace a video's semantic tag rows with (class_id, score, frame_count)
    triples and stamp the signature on every frame of that video. YOLO rows
    are never touched -- mirrors db_write_image_semantic_scores."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM video_classes WHERE video_id = ? AND class_id >= ?",
            (video_id, SEMANTIC_CLASS_ID_OFFSET),
        )
        cursor.executemany(
            "INSERT OR REPLACE INTO video_classes "
            "(video_id, class_id, score, frame_count) VALUES (?, ?, ?, ?)",
            [
                (video_id, class_id, score, frame_count)
                for class_id, score, frame_count in pairs
            ],
        )
        cursor.execute(
            """
            UPDATE video_frame_embeddings SET scored_signature = ?
            WHERE frame_id IN (SELECT id FROM video_frames WHERE video_id = ?)
            """,
            (signature, video_id),
        )
        conn.commit()
    finally:
        if conn:
            conn.close()


def db_get_videos_needing_scoring(
    model_version: str, signature: str, limit: int
) -> List[str]:
    """Videos with at least one frame embedding whose semantic scores are
    missing or computed against another vocabulary/label state."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT vf.video_id
            FROM video_frames vf
            JOIN video_frame_embeddings e ON vf.id = e.frame_id
            WHERE e.model_version = ?
              AND IFNULL(e.scored_signature, '') != ?
            LIMIT ?
            """,
            (model_version, signature, limit),
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        if conn:
            conn.close()


def db_get_frame_embeddings_for_video(video_id: str, model_version: str) -> np.ndarray:
    """All of one video's frame embeddings as an [N, D] matrix."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.embedding
            FROM video_frames vf
            JOIN video_frame_embeddings e ON vf.id = e.frame_id
            WHERE vf.video_id = ? AND e.model_version = ?
            ORDER BY vf.frame_index
            """,
            (video_id, model_version),
        )
        rows = cursor.fetchall()
        if not rows:
            return np.empty((0, 0), dtype=np.float32)
        return np.vstack([np.frombuffer(blob, dtype=np.float32) for (blob,) in rows])
    finally:
        if conn:
            conn.close()


def db_get_all_frame_embeddings(
    model_version: str,
) -> Tuple[List[str], List[float], np.ndarray]:
    """Every frame embedding with its video and timestamp, for semantic
    search. Returns (video_ids, timestamps, matrix) aligned by row."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT vf.video_id, vf.timestamp_sec, e.embedding
            FROM video_frames vf
            JOIN video_frame_embeddings e ON vf.id = e.frame_id
            WHERE e.model_version = ?
            """,
            (model_version,),
        )
        rows = cursor.fetchall()
        if not rows:
            return [], [], np.empty((0, 0), dtype=np.float32)

        video_ids = [row[0] for row in rows]
        timestamps = [row[1] for row in rows]
        matrix = np.vstack([np.frombuffer(row[2], dtype=np.float32) for row in rows])
        return video_ids, timestamps, matrix
    finally:
        if conn:
            conn.close()


def db_get_video_tags(video_ids: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """Display tag names per video. Pass video_ids to restrict, or None for
    every video."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()

        query = """
            SELECT vc.video_id, m.name
            FROM video_classes_display vc
            JOIN mappings m ON vc.class_id = m.class_id
        """
        params: List[str] = []
        if video_ids is not None:
            if not video_ids:
                return {}
            placeholders = ",".join("?" for _ in video_ids)
            query += f" WHERE vc.video_id IN ({placeholders})"
            params = video_ids
        query += " ORDER BY vc.video_id, m.name"

        cursor.execute(query, params)

        tags: Dict[str, List[str]] = {}
        for video_id, name in cursor.fetchall():
            tags.setdefault(video_id, []).append(name)
        return tags
    except sqlite3.Error as e:
        logger.error(f"Error getting video tags: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def db_get_video_ids_by_tag(tag_name: str) -> List[str]:
    """Video IDs carrying a tag. Matches against the full stored tag set, not
    the display cut, so search isn't limited by SEMANTIC_DISPLAY_TOP_K."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT vc.video_id
            FROM video_classes vc
            JOIN mappings m ON vc.class_id = m.class_id
            WHERE LOWER(m.name) = LOWER(?)
            """,
            (tag_name,),
        )
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Error searching videos by tag: {e}")
        raise
    finally:
        if conn:
            conn.close()


def db_clear_frame_paths() -> bool:
    """Forget where the frame JPEGs were, keeping the rows and their
    embeddings so tags and semantic search survive a purge."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE video_frames SET frame_path = NULL WHERE frame_path IS NOT NULL"
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error clearing video frame paths: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
