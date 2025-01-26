import sqlite3
import json
from app.ner.test import ner_marking
from app.ner.camera import scanned_embeddings
from app.config.settings import NER_DATABASE_PATH,FACES_DATABASE_PATH,IMAGES_DATABASE_PATH
import numpy as np


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

def extract_ner(text):
    conn = sqlite3.connect(NER_DATABASE_PATH)
    cursor = conn.cursor()

    text_to_display = ner_marking(text)  
    store = []

    for name in text_to_display:
        cursor.execute("SELECT embeddings FROM ner_mapping WHERE name = ?", (name,))
        result = cursor.fetchone()  
        if result:
            embeddings = json.loads(result[0])  
            store.append(embeddings)
        else:
            print(f"No embeddings found for name: {name}")

    conn.close()
    return store

def compare_ner(store):
    conn = sqlite3.connect(FACES_DATABASE_PATH)
    cursor = conn.cursor()

    conn2 = sqlite3.connect(IMAGES_DATABASE_PATH)
    cursor2 = conn2.cursor()

    cursor.execute("SELECT id, image_id, embeddings FROM faces")
    rows = cursor.fetchall()

    pathways = []
    for row in rows:

        python_list = json.loads(row[2])
        
        if len(store) == len(python_list):
            python_list = np.array(python_list)
            store = np.array(store)
            concatenated_embedding1 = np.concatenate(python_list)
            concatenated_embedding2 = np.concatenate(store)

            cosine_similarity = np.dot(concatenated_embedding1, concatenated_embedding2) / (np.linalg.norm(concatenated_embedding1) * np.linalg.norm(concatenated_embedding2))
            print(cosine_similarity)

            if 0.5 <= cosine_similarity <= 1:

                cursor2.execute('''
                SELECT path
                FROM image_id_mapping 
                WHERE id = ?
            ''', (row[1],))  
            
                related_data = cursor2.fetchone() 
                pathways.append(related_data[0])

    conn.close()
    conn2.close()            

    return pathways



    