import sqlite3
import json
from app.ner.test import ner_marking
from app.ner.camera import scanned_embeddings
from app.config.settings import NER_DATABASE_PATH


def ner_table():
    conn = sqlite3.connect(NER_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ner_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name STRING,
            embeddings TEXT
        )
        """
    )  
    conn.commit()
    conn.close()

def add_nerdata(text):
    conn = sqlite3.connect(NER_DATABASE_PATH)
    cursor = conn.cursor()
    text_to_display = ner_marking(text)
    for name in text_to_display:
        print(name)
        cursor.execute("SELECT id FROM ner_mapping WHERE name = ?", (name,))
        result = cursor.fetchone()
        if result is None:
            embedding_json = json.dumps(scanned_embeddings(name).tolist())
            cursor.execute(
                "INSERT INTO ner_mapping (name, embeddings) VALUES (?, ?)",
                (name, embedding_json)
            )
    conn.commit()
    conn.close()