"""To be decided
Check if DB file exists
If it doesn't create it
check if it contain all classes
if not add them according to their indexs
if conflit occurs delete DB and recreate
"""

import sqlite3
from utils import createTable, executeQuery
from typing import List, Tuple

def createSchema(conn: sqlite3.Connection) -> None:
    """Creates tables for MEDIA, JUNCTION, and CLASS in the database.

    Args:
        conn: A sqlite3.Connection object.
    """
    createTable(conn, "MEDIA", [
        "imageID INTEGER PRIMARY KEY AUTOINCREMENT", 
        "hash TEXT UNIQUE", 
        "path TEXT", 
        "hidden INTEGER"
    ])
    createTable(conn, "CLASS", [
        "classID INTEGER PRIMARY KEY AUTOINCREMENT", 
        "class TEXT UNIQUE"
    ])
    createTable(conn, "JUNCTION", [
        "imageID INTEGER", 
        "classID INTEGER", 
        "FOREIGN KEY(imageID) REFERENCES MEDIA(imageID) ON DELETE CASCADE",
        "FOREIGN KEY(classID) REFERENCES CLASS(classID)",
        "PRIMARY KEY (imageID, classID)"
    ])


# NN
def classesExist(conn: sqlite3.Connection, classes: List[str]) -> bool:
    """Checks if all classes already exist in the CLASS table.

    Args:
        conn: A sqlite3.Connection object.
        classes: A list of class names to check.

    Returns:
        bool: True if all classes exist in the CLASS table, False otherwise.
    """
    result = executeQuery(conn, "SELECT class FROM CLASS ORDER BY classID")
    existing_classes = [row[0] for row in result]
    return existing_classes == classes
