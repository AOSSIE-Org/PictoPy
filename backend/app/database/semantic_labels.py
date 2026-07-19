from app.database.images import _connect


def db_create_semantic_labels_table():
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_labels (
                label_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                prompt_template TEXT,
                threshold REAL,
                active BOOLEAN DEFAULT 1
            )
            """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_semantic_labels (
                image_id TEXT,
                label_id INTEGER,
                score REAL NOT NULL,
                PRIMARY KEY (image_id, label_id),
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
                FOREIGN KEY (label_id) REFERENCES semantic_labels(label_id) ON DELETE CASCADE
            )
            """)

        conn.commit()
    finally:
        if conn:
            conn.close()
