import os
import sys  
from typing import Dict

"""
Functions are being used instead of variables to ensure that the values cannot be altered by any means.
"""

def homeDir() -> str:
    """
    Get the home directory path i.e. the directory to scan.
    Handle Mobile (TBI)

    Returns:
        str: Home directory path.
    """
    return os.path.expanduser("~")

def logPath() -> str:
    """
    Log file is created in the user's home directory.

    Returns:
        str: The path to the log file.
    """
    return os.path.join(dataDir(), "log.txt")

def dbPath() -> str:
    """
    Database is created on the user's home directory.

    Returns:
        str: The path to the database file.
    """
    return os.path.join(dataDir(), "database.db")

def dataDir() -> str:
    """
    Data directory is created in the user's home directory.

    Returns:
        str: The path to the data directory.
    """
    directory = os.path.join(os.path.expanduser("~"), ".pictopy")
    os.makedirs(directory, exist_ok=True)
    return directory

def dbSchema() -> Dict:
    """
    Returns the database schema as a string.

    Returns:
        Dict: The database schema.
    """
    return {
      "MEDIA": [
          "mediaID INTEGER PRIMARY KEY AUTOINCREMENT",
          "hash TEXT UNIQUE",
          "path TEXT",
          "directory TEXT",
          "fileType TEXT CHECK(fileType IN ('img', 'vid'))",
          "timeStamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
          "hidden INTEGER",
      ],
      "CLASS": ["classID INTEGER PRIMARY KEY AUTOINCREMENT", "class TEXT UNIQUE"],
      "JUNCTION": [
          "mediaID INTEGER",
          "classID INTEGER",
          "FOREIGN KEY(mediaID) REFERENCES MEDIA(mediaID) ON DELETE CASCADE",
          "FOREIGN KEY(classID) REFERENCES CLASS(classID)",
          "PRIMARY KEY (mediaID, classID)",
      ],
    }
            
def yoloModelPath() -> str:
    """
    Returns the path to the YOLO model.

    Returns:
        str: The path to the YOLO model.
    """
    return "models/yolov8n.onnx"
