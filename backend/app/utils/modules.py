import os
import json
import hashlib
import sqlite3
from typing import List, Dict, Union, Tuple


# TODO:
# recursively look for media in child directories
# implement classifyImg()

def genHash(imgPath: str) -> str:
    """
    Generate a hash for the image file.
    Will serve as unique identifier

    Args:
        imgPath: Path to the image file.

    Returns:
        str: Hash value of the image file.
    """
    with open(imgPath, "rb") as f:
        imgData = f.read()
        return hashlib.md5(imgData).hexdigest()


def classifyImg(imgPath: str) -> str:
    """
    Classify the image using object detection.

    Args:
        imgPath: Path to the image file.

    Returns:
        str: Classification of the image.
    """
    # Object detection (TBI)
    return "thing"  # for demo


def isImg(filePath: str) -> bool:
    """
    Check if the file is an image file.

    Args:
        filePath: Path to the file.

    Returns:
        bool: True if the file is an image file, False otherwise.
    """
    _, fileExtension = os.path.splitext(filePath)
    imgExts = [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".avif", ".tif"]
    return fileExtension.lower() in imgExts


def detectFileWithHash(files: List[str], targetHash: str) -> Union[str, None]:
    """
    Detect a file with a specific hash value.

    Args:
        files: List of file paths.
        targetHash: Hash value to compare with.

    Returns:
        Union[str, None]: Path of the file if found, None otherwise.
    """
    for file in files:
        if not isImg(file):
            continue
        fileHash = genHash(file)
        if fileHash == targetHash:
            return file
    return None
    # File paths can be stored in DB but what if path is changed?
    # we need to keep checking for the path change and update DB (TBI)


def processImgs(conn: sqlite3.Connection, files: List[str]) -> None:
    """
    Process images and insert data into the database.

    Args:
        conn: SQLite database connection.
        files: List of file paths.
    """
    for file in files:
        if not isImg(file):
            continue
        imgHash = genHash(file)
        if hashExist(conn, imgHash):
            continue
        imgClass = classifyImg(file)
        query = f"INSERT OR REPLACE INTO media(hash, imageClass) VALUES('{imgHash}', '{imgClass}')"
        executeQuery(conn, query)


def connectDB(dbPath: str) -> sqlite3.Connection:
    """
    Connect to an SQLite database.

    Args:
        dbPath: Path to the database file.

    Returns:
        sqlite3.Connection: Database connection.
    """
    conn = sqlite3.connect(dbPath)
    return conn


def createTable(conn: sqlite3.Connection, tableID: str, columns: List[str]) -> None:
    """
    Create a table in the database if it doesn't exist.

    Args:
        conn: SQLite database connection.
        tableID: Name of the table.
        columns: List of column names and types.
    """
    cursor = conn.cursor()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {tableID} ({', '.join(columns)})")
    conn.commit()


def executeQuery(conn: sqlite3.Connection, query: str) -> List[Tuple]:
    """
    Execute a SQL query and return the results.

    Args:
        conn: SQLite database connection.
        query: SQL query to execute.

    Returns:
        List[Tuple]: Results of the query.
    """
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()


def closeConnection(conn: sqlite3.Connection) -> None:
    """
    Close the database connection.

    Args:
        conn: SQLite database connection.
    """
    conn.commit()
    conn.close()


def hashExist(conn: sqlite3.Connection, hashValue: str) -> bool:
    """
    Check if a hash value exists in the database.

    Args:
        conn: SQLite database connection.
        hashValue: Hash value to check.

    Returns:
        bool: True if the hash value exists, False otherwise.
    """
    query = f"SELECT EXISTS(SELECT 1 FROM media WHERE hash='{hashValue}')"
    result = executeQuery(conn, query)
    return result[0][0]


def fileByClass(conn: sqlite3.Connection, files: List[str], tableID: str) -> Dict[str, List[str]]:
    """
    Retrieve files classified by class from the database.

    Args:
        conn: SQLite database connection.
        files: List of file paths.
        tableID: Name of the table.

    Returns:
        Dict[str, List[str]]: Dictionary mapping class names to lists of file paths.
    """
    rows = executeQuery(conn, f"SELECT imageClass, hash FROM {tableID}")
    classDict = {}
    for row in rows:
        imageClass = row[0]
        hashValue = row[1]
        if imageClass not in classDict:
            classDict[imageClass] = []
        filePath = detectFileWithHash(files, hashValue)
        if filePath:
            classDict[imageClass].append(filePath)
    return classDict


def classifyPath(dirPath: str, dbPath: str) -> Dict[str, List[str]]:
    """
    Attach class names to the file paths and return a JSON object.

    Args:
        dirPath: Path to the directory containing the images.
        dbPath: Path to the database file.

    Returns:
        Dict[str, List[str]]: Dictionary mapping class names to lists of file paths.
    """

    # Create database and table if they don't exist
    columns = ["hash TEXT PRIMARY KEY", "imageClass TEXT"]
    tableID = "media"
    conn = connectDB(dbPath)
    createTable(conn, tableID, columns)

    # Process images and insert data into the database
    files = [os.path.join(dirPath, file) for file in os.listdir(dirPath)]
    # dbPath = os.path.join(dirPath, "gallery.db") # DB in same dir as images
    processImgs(conn, files)

    # Retrieve files classified by class from the database
    result = json.dumps(fileByClass(conn, files, tableID), indent=2)

    # Close the database connection
    closeConnection(conn)

    return result

# Test case
if __name__ == "__main__":
    print(classifyPath("./.test/", "./.test/gallery.db")) # Just for demo, actual path will be provided by FrontEnd (TBI)

