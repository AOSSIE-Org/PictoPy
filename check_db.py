
import sqlite3
import os

db_path = 'backend/app/database/PictoPy.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]

print("--- Table Summary ---")
for t in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {t}")
    count = cursor.fetchone()[0]
    print(f"{t}: {count} rows")

print("\n--- Folder Details ---")
cursor.execute("SELECT folder_id, folder_path, AI_Tagging, taggingCompleted FROM folders")
folders = cursor.fetchall()
for f in folders:
    print(f"ID: {f[0]}, Path: {f[1]}, AI_Tagging: {f[2]}, taggingCompleted: {f[3]}")

print("\n--- Image Tagging Sample ---")
cursor.execute("SELECT image_id, path, isTagged FROM images LIMIT 5")
images = cursor.fetchall()
for img in images:
    print(f"ID: {img[0]}, Path: {img[1]}, isTagged: {img[2]}")

print("\n--- Face Embeddings Sample ---")
try:
    cursor.execute("SELECT face_id, image_id, cluster_id FROM faces LIMIT 5")
    faces = cursor.fetchall()
    for face in faces:
        print(f"FaceID: {face[0]}, ImageID: {face[1]}, ClusterID: {face[2]}")
except Exception as e:
    print(f"Error querying faces: {e}")

conn.close()
