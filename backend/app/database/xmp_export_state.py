from typing import List, Optional, Tuple, TypedDict

from app.database.images import _connect


class XmpExportCandidate(TypedDict):
    image_id: str
    path: str
    # Snapshot taken before collecting; recorded on success so a change made
    # during the export leaves the image pending.
    change_count: int
    pending: bool
    digest: Optional[str]
    file_size: Optional[int]
    file_mtime_ns: Optional[int]
    failure_count: int


def _bump(where: str) -> str:
    return (
        "UPDATE image_xmp_state SET change_count = change_count + 1 "
        f"WHERE image_id {where};"
    )


def _width_or_height_changed() -> str:
    # json_valid first: json_extract raises on malformed JSON, which would fail
    # the rescan's UPDATE of that image.
    def dim(row: str, key: str) -> str:
        return (
            f"(CASE WHEN json_valid({row}.metadata) "
            f"THEN json_extract({row}.metadata, '$.{key}') END)"
        )

    return " OR ".join(
        f"{dim('OLD', key)} IS NOT {dim('NEW', key)}" for key in ("width", "height")
    )


# Every write that can change what export would put in an image. Triggers only
# ever UPDATE existing state rows: inserting one while an image is being
# cascade-deleted would violate its foreign key. "UPDATE OF" fires even when
# the value is unchanged, so each column trigger also checks for a real change.
_TRIGGERS: List[Tuple[str, str]] = [
    (
        "xmp_images_insert",
        "AFTER INSERT ON images BEGIN "
        "INSERT OR IGNORE INTO image_xmp_state (image_id) VALUES (NEW.id); END",
    ),
    (
        "xmp_images_favourite",
        "AFTER UPDATE OF isFavourite ON images "
        "WHEN OLD.isFavourite IS NOT NEW.isFavourite "
        f"BEGIN {_bump('= NEW.id')} END",
    ),
    (
        "xmp_images_dimensions",
        "AFTER UPDATE OF metadata ON images "
        f"WHEN {_width_or_height_changed()} "
        f"BEGIN {_bump('= NEW.id')} END",
    ),
    (
        "xmp_image_classes_insert",
        f"AFTER INSERT ON image_classes BEGIN {_bump('= NEW.image_id')} END",
    ),
    (
        "xmp_image_classes_delete",
        f"AFTER DELETE ON image_classes BEGIN {_bump('= OLD.image_id')} END",
    ),
    (
        "xmp_image_classes_update",
        "AFTER UPDATE OF image_id, class_id, score ON image_classes "
        "WHEN OLD.image_id IS NOT NEW.image_id OR OLD.class_id IS NOT NEW.class_id "
        "OR OLD.score IS NOT NEW.score "
        f"BEGIN {_bump('IN (OLD.image_id, NEW.image_id)')} END",
    ),
    (
        "xmp_mappings_rename",
        "AFTER UPDATE OF name ON mappings WHEN OLD.name IS NOT NEW.name BEGIN "
        + _bump(
            "IN (SELECT image_id FROM image_classes "
            "WHERE class_id IN (OLD.class_id, NEW.class_id))"
        )
        + " END",
    ),
    (
        # Deactivated labels keep their rows until the next rescore but are
        # filtered out of the export, so the flag alone changes it.
        "xmp_semantic_labels_active",
        "AFTER UPDATE OF active ON semantic_labels "
        "WHEN OLD.active IS NOT NEW.active BEGIN "
        + _bump("IN (SELECT image_id FROM image_classes WHERE class_id = NEW.class_id)")
        + " END",
    ),
    (
        "xmp_faces_insert",
        "AFTER INSERT ON faces WHEN NEW.image_id IS NOT NULL "
        f"BEGIN {_bump('= NEW.image_id')} END",
    ),
    (
        "xmp_faces_delete",
        "AFTER DELETE ON faces WHEN OLD.image_id IS NOT NULL "
        f"BEGIN {_bump('= OLD.image_id')} END",
    ),
    (
        # Also fired by ON DELETE SET NULL when a cluster is deleted.
        "xmp_faces_update",
        "AFTER UPDATE OF image_id, embeddings, bbox, confidence, cluster_id ON faces "
        "WHEN (OLD.image_id IS NOT NULL OR NEW.image_id IS NOT NULL) AND ("
        "OLD.image_id IS NOT NEW.image_id OR OLD.embeddings IS NOT NEW.embeddings "
        "OR OLD.bbox IS NOT NEW.bbox OR OLD.confidence IS NOT NEW.confidence "
        "OR OLD.cluster_id IS NOT NEW.cluster_id) "
        f"BEGIN {_bump('IN (OLD.image_id, NEW.image_id)')} END",
    ),
    (
        "xmp_face_clusters_rename",
        "AFTER UPDATE OF cluster_name ON face_clusters "
        "WHEN OLD.cluster_name IS NOT NEW.cluster_name BEGIN "
        + _bump(
            "IN (SELECT image_id FROM faces "
            "WHERE cluster_id = NEW.cluster_id AND image_id IS NOT NULL)"
        )
        + " END",
    ),
    (
        "xmp_image_embeddings_insert",
        f"AFTER INSERT ON image_embeddings BEGIN {_bump('= NEW.image_id')} END",
    ),
    (
        "xmp_image_embeddings_delete",
        f"AFTER DELETE ON image_embeddings BEGIN {_bump('= OLD.image_id')} END",
    ),
    (
        "xmp_image_embeddings_update",
        "AFTER UPDATE OF image_id, model_version, embedding, scored_signature "
        "ON image_embeddings WHEN OLD.image_id IS NOT NEW.image_id "
        "OR OLD.model_version IS NOT NEW.model_version "
        "OR OLD.embedding IS NOT NEW.embedding "
        "OR OLD.scored_signature IS NOT NEW.scored_signature "
        f"BEGIN {_bump('IN (OLD.image_id, NEW.image_id)')} END",
    ),
    (
        "xmp_album_images_insert",
        f"AFTER INSERT ON album_images BEGIN {_bump('= NEW.image_id')} END",
    ),
    (
        "xmp_album_images_delete",
        f"AFTER DELETE ON album_images BEGIN {_bump('= OLD.image_id')} END",
    ),
    (
        # Locked albums are left out of the export, so locking changes it too.
        "xmp_albums_update",
        "AFTER UPDATE OF album_name, is_locked ON albums "
        "WHEN OLD.album_name IS NOT NEW.album_name "
        "OR OLD.is_locked IS NOT NEW.is_locked BEGIN "
        + _bump("IN (SELECT image_id FROM album_images WHERE album_id = NEW.album_id)")
        + " END",
    ),
]


def db_create_image_xmp_state_table() -> None:
    """Export state per image, plus the triggers that keep it current.

    Must run after every table the triggers watch exists. Triggers are
    recreated on each start so their definitions follow releases.
    """
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS image_xmp_state (
                image_id TEXT PRIMARY KEY,
                change_count INTEGER NOT NULL DEFAULT 0,
                exported_count INTEGER,
                digest TEXT,
                file_size INTEGER,
                file_mtime_ns INTEGER,
                last_outcome TEXT,
                last_error TEXT,
                failure_count INTEGER NOT NULL DEFAULT 0,
                last_attempt_at DATETIME,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
            )
            """
        )
        # exported_count NULL means never exported; such rows are pending.
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_image_xmp_state_pending
            ON image_xmp_state(image_id)
            WHERE exported_count IS NULL OR change_count > exported_count
            """
        )
        # Images indexed before this table existed start out never exported.
        cursor.execute(
            "INSERT OR IGNORE INTO image_xmp_state (image_id) SELECT id FROM images"
        )
        for name, body in _TRIGGERS:
            cursor.execute(f"DROP TRIGGER IF EXISTS {name}")
            cursor.execute(f"CREATE TRIGGER {name} {body}")
        conn.commit()
    finally:
        conn.close()


_PENDING = "(s.exported_count IS NULL OR s.change_count > s.exported_count)"
_PNG = "lower(i.path) LIKE '%.png'"


def db_get_xmp_export_candidates(
    include_clean: bool = False,
) -> List[XmpExportCandidate]:
    """PNG images whose export is pending; every PNG with include_clean.

    include_clean is for the manual export, which also re-checks files whose
    stat no longer matches what was recorded.
    """
    only_pending = "" if include_clean else f"AND {_PENDING}"
    conn = _connect()
    try:
        rows = conn.execute(
            f"""
            SELECT s.image_id, i.path, s.change_count, {_PENDING}, s.digest,
                   s.file_size, s.file_mtime_ns, s.failure_count
            FROM image_xmp_state s
            JOIN images i ON i.id = s.image_id
            WHERE {_PNG} {only_pending}
            ORDER BY s.image_id
            """
        ).fetchall()
        return [
            {
                "image_id": image_id,
                "path": path,
                "change_count": change_count,
                "pending": bool(pending),
                "digest": digest,
                "file_size": file_size,
                "file_mtime_ns": file_mtime_ns,
                "failure_count": failure_count,
            }
            for (
                image_id,
                path,
                change_count,
                pending,
                digest,
                file_size,
                file_mtime_ns,
                failure_count,
            ) in rows
        ]
    finally:
        conn.close()


class XmpExportCounts(TypedDict):
    total: int
    pending: int
    # Pending images whose last attempt raised; they are retried.
    failed: int
    # Left alone on purpose: unreadable XMP, or a newer PictoPy's data.
    skipped: int


def db_get_xmp_export_counts() -> XmpExportCounts:
    """Where export stands across the library's PNG images."""
    conn = _connect()
    try:
        total, pending, failed, skipped = conn.execute(
            f"""
            SELECT COUNT(*),
                   COALESCE(SUM({_PENDING}), 0),
                   COALESCE(SUM({_PENDING} AND s.last_outcome = 'failed'), 0),
                   COALESCE(SUM(NOT {_PENDING} AND s.last_outcome IN
                       ('unreadable_existing', 'newer_schema')), 0)
            FROM image_xmp_state s
            JOIN images i ON i.id = s.image_id
            WHERE {_PNG}
            """
        ).fetchone()
        return {
            "total": total,
            "pending": pending,
            "failed": failed,
            "skipped": skipped,
        }
    finally:
        conn.close()


def db_record_xmp_export_success(
    image_id: str,
    change_count_seen: int,
    outcome: str,
    digest: Optional[str],
    file_size: Optional[int],
    file_mtime_ns: Optional[int],
) -> None:
    """Mark the image exported as of the change count the export started from."""
    conn = _connect()
    try:
        conn.execute(
            """
            UPDATE image_xmp_state
            SET exported_count = ?, last_outcome = ?, digest = ?,
                file_size = ?, file_mtime_ns = ?, last_error = NULL,
                failure_count = 0, last_attempt_at = CURRENT_TIMESTAMP
            WHERE image_id = ?
            """,
            (change_count_seen, outcome, digest, file_size, file_mtime_ns, image_id),
        )
        conn.commit()
    finally:
        conn.close()


def db_record_xmp_export_failure(image_id: str, error: str) -> None:
    """Leaves exported_count alone, so the image stays pending and is retried."""
    conn = _connect()
    try:
        conn.execute(
            """
            UPDATE image_xmp_state
            SET last_outcome = 'failed', last_error = ?,
                failure_count = failure_count + 1,
                last_attempt_at = CURRENT_TIMESTAMP
            WHERE image_id = ?
            """,
            (error, image_id),
        )
        conn.commit()
    finally:
        conn.close()


def db_refresh_image_file_stat(image_id: str, file_size: int, file_mtime: int) -> None:
    """Record the file's new size after a write so the folder rescan skips it.

    Width and height are untouched, so this does not mark the image dirty.
    """
    conn = _connect()
    try:
        conn.execute(
            """
            UPDATE images
            SET metadata = json_set(metadata, '$.file_size', ?, '$.file_mtime', ?)
            WHERE id = ? AND json_valid(metadata)
            """,
            (file_size, file_mtime, image_id),
        )
        conn.commit()
    finally:
        conn.close()
