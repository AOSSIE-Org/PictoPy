
import os
import sqlite3
from sqlite3 import IntegrityError
from typing import Dict, List, Generator
from utils.fs import genHash, isImg, imgPaths, homeDir, detectFileWithHash
from utils.db import connectDB, createTable, executeQuery, closeConnection, groupByclasses, hashExist
from utils.createDB import  createSchema, classesExist
from yolov8 import detectedClass


def processImgs(conn: sqlite3.Connection, files: Generator[str, None, None]) -> None:
    for file in files:
        imgHash = genHash(file)
        try:
            imgClass = detectedClass(file)
            _, imageID = executeQuery(conn, f"INSERT INTO IMAGES(hash, path) VALUES('{imgHash}', '{file}')", 1)

            for className in imgClass:
                try:
                    _, classID = executeQuery(conn, f"INSERT INTO CLASS(class) VALUES('{className}')", 1)
                except IntegrityError:
                    classID = executeQuery(conn, f"SELECT classID FROM CLASS WHERE class = '{className}'")[0][0]
                
                executeQuery(conn, f"INSERT OR IGNORE INTO JUNCTION(imageID, classID) VALUES('{imageID}', '{classID}')")

        except IntegrityError:
            executeQuery(conn, f"UPDATE IMAGES SET path = '{file}' WHERE hash = '{imgHash}'")


#NN
def fileByClass(conn: sqlite3.Connection, files: Generator[str, None, None], tableID: str) -> Dict[str, List[str]]:
    rows = executeQuery(conn, f"SELECT imageClass, hash FROM {tableID}")
    classDict = {}
    for row in rows:
        imageClass, hashValue = row
        if imageClass not in classDict:
            classDict[imageClass] = []
        filePath = detectFileWithHash(files, hashValue)
        if filePath:
            classDict[imageClass].append(filePath)
    return classDict

def classifyPath() -> Dict[str, List[str]]:
    """
    Classify images in the home directory and store the results in the database.

    Returns:
        Dict[str, List[str]]: Dictionary mapping class names to lists of file paths.
    """
    dbPath = os.path.join(homeDir(), ".pictopy.db")
    conn = connectDB(dbPath)
    # columns = ["hash TEXT PRIMARY KEY", "imageClass TEXT"]
    # tableID = "media"
    # createTable(conn, tableID, columns)
    createSchema(conn)

    files = imgPaths(homeDir())
    processImgs(conn, files)

    # Re-create the generator since it would be exhausted
    files = imgPaths(homeDir())  
    # Retrieve files classified by class from the database
    # result = fileByClass(conn, files, tableID)
    result = groupByclasses(conn)

    closeConnection(conn)

    return result


# Test case
if __name__ == "__main__":
    print(classifyPath())

# periodically run the object detection function and compare it with DB