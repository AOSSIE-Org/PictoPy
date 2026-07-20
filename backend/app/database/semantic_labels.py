import json
from typing import List, Tuple

import numpy as np

from app.database.images import _connect
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# YOLO owns mappings class_ids 0-79; semantic labels are allocated from here.
SEMANTIC_CLASS_ID_OFFSET = 1000


def db_create_semantic_labels_table():
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()

        # Migrate the pre-vocabulary shell schema. It shipped with no writer,
        # so the table is guaranteed empty: drop-and-recreate instead of
        # ALTER. image_semantic_labels (also never written) is superseded by
        # image_classes rows + image_classes.score.
        cursor.execute("PRAGMA table_info(semantic_labels)")
        columns = {row[1] for row in cursor.fetchall()}
        if columns and "descriptions" not in columns:
            cursor.execute("DROP TABLE semantic_labels")
        cursor.execute("DROP TABLE IF EXISTS image_semantic_labels")

        # Definition + cache table for the curated vocabulary. class_id is
        # shared with mappings so tag consumers (image_classes joins) treat
        # semantic labels exactly like YOLO classes. descriptions (JSON
        # array) are the source of truth; label_embedding caches their
        # renormalized mean for embedding_model_version.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS semantic_labels (
                class_id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                descriptions TEXT NOT NULL,
                threshold REAL,
                active BOOLEAN DEFAULT 1,
                label_embedding BLOB,
                embedding_model_version TEXT
            )
            """
        )

        # Display cut: tag-list queries join this view instead of
        # image_classes, so chips show all YOLO tags but only the
        # top-SEMANTIC_DISPLAY_TOP_K semantic tags per image. Search
        # matching still uses the full table (stored top-K). Recreated at
        # startup so setting changes apply without re-scoring.
        from app.config.settings import SEMANTIC_DISPLAY_TOP_K

        cursor.execute("DROP VIEW IF EXISTS image_classes_display")
        cursor.execute(
            f"""
            CREATE VIEW image_classes_display AS
            SELECT image_id, class_id FROM (
                SELECT image_id, class_id,
                       ROW_NUMBER() OVER (
                           PARTITION BY image_id ORDER BY score DESC
                       ) AS display_rank
                FROM image_classes WHERE score IS NOT NULL
            ) WHERE display_rank <= {int(SEMANTIC_DISPLAY_TOP_K)}
            UNION ALL
            SELECT image_id, class_id FROM image_classes WHERE score IS NULL
            """
        )

        conn.commit()
    finally:
        if conn:
            conn.close()


def db_upsert_semantic_vocabulary(labels: List[dict]) -> None:
    """Idempotently sync the seed vocabulary into mappings + semantic_labels.

    New labels get mappings rows with class_id >= SEMANTIC_CLASS_ID_OFFSET;
    changed descriptions invalidate the cached label embedding; labels
    missing from the seed are deactivated (rows kept -- image_classes may
    reference them).
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()

        cursor.execute("SELECT class_id, name FROM mappings")
        mapping_by_name = {name: cid for cid, name in cursor.fetchall()}

        cursor.execute(
            "SELECT class_id, name, category, descriptions, threshold, active "
            "FROM semantic_labels"
        )
        existing = {row[1]: row for row in cursor.fetchall()}

        next_id = (
            max(
                [SEMANTIC_CLASS_ID_OFFSET - 1]
                + [
                    cid
                    for cid in mapping_by_name.values()
                    if cid >= SEMANTIC_CLASS_ID_OFFSET
                ]
            )
            + 1
        )

        added = updated = skipped = 0
        seed_names = set()
        for label in labels:
            name = label["name"]
            seed_names.add(name)
            category = label["category"]
            descriptions = json.dumps(label["descriptions"])
            threshold = label.get("threshold")

            if name in existing:
                class_id, _, old_cat, old_desc, old_thr, old_active = existing[name]
                if old_desc != descriptions:
                    # descriptions changed: cached embedding is stale
                    cursor.execute(
                        """
                        UPDATE semantic_labels
                        SET category = ?, descriptions = ?, threshold = ?,
                            active = 1, label_embedding = NULL,
                            embedding_model_version = NULL
                        WHERE class_id = ?
                        """,
                        (category, descriptions, threshold, class_id),
                    )
                    updated += 1
                elif (old_cat, old_thr, bool(old_active)) != (
                    category,
                    threshold,
                    True,
                ):
                    cursor.execute(
                        "UPDATE semantic_labels "
                        "SET category = ?, threshold = ?, active = 1 "
                        "WHERE class_id = ?",
                        (category, threshold, class_id),
                    )
                    updated += 1
                continue

            mapped_id = mapping_by_name.get(name)
            if mapped_id is not None and mapped_id < SEMANTIC_CLASS_ID_OFFSET:
                logger.warning(
                    f"Skipping semantic label '{name}': name already owned by "
                    "a YOLO mapping"
                )
                skipped += 1
                continue

            if mapped_id is None:
                mapped_id = next_id
                next_id += 1
                cursor.execute(
                    "INSERT INTO mappings (class_id, name) VALUES (?, ?)",
                    (mapped_id, name),
                )
                mapping_by_name[name] = mapped_id

            cursor.execute(
                """
                INSERT INTO semantic_labels
                    (class_id, name, category, descriptions, threshold)
                VALUES (?, ?, ?, ?, ?)
                """,
                (mapped_id, name, category, descriptions, threshold),
            )
            added += 1

        deactivated = 0
        for name in set(existing) - seed_names:
            if existing[name][5]:
                cursor.execute(
                    "UPDATE semantic_labels SET active = 0 WHERE name = ?",
                    (name,),
                )
                deactivated += 1

        conn.commit()
        if added or updated or skipped or deactivated:
            logger.info(
                f"Semantic vocabulary sync: {added} added, {updated} updated, "
                f"{deactivated} deactivated, {skipped} skipped"
            )
    finally:
        if conn:
            conn.close()


def db_get_labels_needing_embeddings(
    model_version: str,
) -> List[Tuple[int, List[str]]]:
    """Active labels whose cached embedding is missing or belongs to a
    different checkpoint. Returns (class_id, descriptions) pairs."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT class_id, descriptions FROM semantic_labels
            WHERE active = 1
              AND (label_embedding IS NULL
                   OR IFNULL(embedding_model_version, '') != ?)
            """,
            (model_version,),
        )
        return [
            (class_id, json.loads(descriptions))
            for class_id, descriptions in cursor.fetchall()
        ]
    finally:
        if conn:
            conn.close()


def db_update_label_embeddings(
    rows: List[Tuple[int, np.ndarray, str]],
) -> None:
    """Store computed label embeddings: (class_id, embedding, model_version).

    Same raw-float32 blob format as image_embeddings.embedding.
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.executemany(
            """
            UPDATE semantic_labels
            SET label_embedding = ?, embedding_model_version = ?
            WHERE class_id = ?
            """,
            [
                (
                    np.ascontiguousarray(embedding, dtype=np.float32).tobytes(),
                    model_version,
                    class_id,
                )
                for class_id, embedding, model_version in rows
            ],
        )
        conn.commit()
    finally:
        if conn:
            conn.close()


def db_get_active_label_embeddings(
    model_version: str,
) -> Tuple[List[Tuple[int, str, float]], np.ndarray]:
    """Cached embeddings for active labels on the given checkpoint.

    Returns ([(class_id, category, threshold), ...], matrix [N, D]) for the
    scoring pass, ordered by class_id (the scoring signature hashes the
    matrix, so row order must be deterministic); threshold is None where the
    label has no per-label override.
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT class_id, category, threshold, label_embedding
            FROM semantic_labels
            WHERE active = 1
              AND label_embedding IS NOT NULL
              AND embedding_model_version = ?
            ORDER BY class_id
            """,
            (model_version,),
        )
        rows = cursor.fetchall()
        if not rows:
            return [], np.empty((0, 0), dtype=np.float32)

        meta = [
            (class_id, category, threshold) for class_id, category, threshold, _ in rows
        ]
        matrix = np.vstack(
            [np.frombuffer(blob, dtype=np.float32) for _, _, _, blob in rows]
        )
        return meta, matrix
    finally:
        if conn:
            conn.close()


def db_write_image_semantic_scores(
    batch: List[Tuple[str, List[Tuple[int, float]]]], signature: str
) -> None:
    """Replace each image's semantic tag rows with the given (class_id, score)
    pairs and stamp its scored_signature. YOLO rows (class_id below the
    offset) are never touched."""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        for image_id, pairs in batch:
            cursor.execute(
                "DELETE FROM image_classes " "WHERE image_id = ? AND class_id >= ?",
                (image_id, SEMANTIC_CLASS_ID_OFFSET),
            )
            cursor.executemany(
                "INSERT OR REPLACE INTO image_classes "
                "(image_id, class_id, score) VALUES (?, ?, ?)",
                [(image_id, class_id, score) for class_id, score in pairs],
            )
            cursor.execute(
                "UPDATE image_embeddings SET scored_signature = ? "
                "WHERE image_id = ?",
                (signature, image_id),
            )
        conn.commit()
    finally:
        if conn:
            conn.close()
