
import sqlite3
import os

db_path = 'backend/app/database/PictoPy.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]

print("--- Row Counts ---")
for t in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {t}")
    count = cursor.fetchone()[0]
    print(f"{t}: {count}")

print("\n--- Folder Config ---")
cursor.execute("SELECT folder_path, AI_Tagging FROM folders")
for row in cursor.fetchall():
    print(f"Path: {row[0]}, AI_Tagging: {row[1]}")

conn.close()
