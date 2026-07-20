from app.database.images import _connect


def db_create_semantic_labels_table():
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()

        # A semantic_labels table from another schema version (no label_id column)
        # breaks the image_semantic_labels FK with "foreign key mismatch" on any
        # cascading delete. Both tables hold derived data, so rebuild them.
        cols = [r[1] for r in cursor.execute("PRAGMA table_info(semantic_labels)")]
        if cols and "label_id" not in cols:
            cursor.execute("DROP TABLE IF EXISTS image_semantic_labels")
            cursor.execute("DROP TABLE semantic_labels")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS semantic_labels (
                label_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                prompt_template TEXT,
                threshold REAL,
                active BOOLEAN DEFAULT 1
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS image_semantic_labels (
                image_id TEXT,
                label_id INTEGER,
                score REAL NOT NULL,
                PRIMARY KEY (image_id, label_id),
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
                FOREIGN KEY (label_id) REFERENCES semantic_labels(label_id) ON DELETE CASCADE
            )
            """
        )

        conn.commit()
    finally:
        if conn:
            conn.close()
