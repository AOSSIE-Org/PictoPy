import os
from typing import Dict, List
from utils import *
from media import *
from flask import Flask, render_template, send_file, request, redirect, url_for, Response, jsonify
from markupsafe import escape
from urllib.parse import unquote

writing = False

def dataDir() -> str:
    """
    Data directory is created on the user's home directory.

    Returns:
        str: The path to the home directory.
    """
    directory = os.path.join(os.path.expanduser("~"), ".pictopy")
    os.makedirs(directory, exist_ok=True)
    return directory 

def dbPath() -> str:
    """
    Database is created on the user's home directory.

    Returns:
        str: The path to the database file.
    """
    return os.path.join(dataDir(), "database.db")

def logPath() -> str:
    """
    Log file is created on the user's home directory.

    Returns:
        str: The path to the log file.
    """
    return os.path.join(dataDir(), "log.txt")

def updateDB(groupBy: str = None) -> None:
    """
    Updates the database schema and populates the media table.
    Populates the media table with paths from the home directory.
    Optionally classifies media by class if specified.
    Cleans the database.

    Args:
        groupBy (str, optional): Specifies whether to classify media by 'class'. Defaults to None.
    """
    writeConn = connectDB(dbPath())
    createSchema(writeConn, 
        {
            "MEDIA": [
                "mediaID INTEGER PRIMARY KEY AUTOINCREMENT", 
                "hash TEXT UNIQUE", 
                "path TEXT",
                "directory TEXT",
                "fileType TEXT CHECK(fileType IN ('img', 'vid'))",
                "timeStamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "hidden INTEGER"
            ],
            "CLASS": [
                "classID INTEGER PRIMARY KEY AUTOINCREMENT", 
                "class TEXT UNIQUE"
            ],
            "JUNCTION": [
                "mediaID INTEGER", 
                "classID INTEGER", 
                "FOREIGN KEY(mediaID) REFERENCES MEDIA(mediaID) ON DELETE CASCADE",
                "FOREIGN KEY(classID) REFERENCES CLASS(classID)",
                "PRIMARY KEY (mediaID, classID)"
            ]
        }
    )

    populateMediaTable(writeConn, mediaPaths(homeDir()))
    if groupBy == "class":
        classifyMedia(writeConn, pathOf("models/yolov8n.onnx"), getUnlinkedMedia(connectDB(dbPath())))
    cleanDB(writeConn)
    closeConnection(writeConn)

def groupPaths(hidden, fileType, groupBy) -> str:
    """
    Groups media paths by directory or class and returns them as JSON.

    Args:
        hidden (int): Specifies whether to include hidden files.
        fileType (str): Specifies the type of files to include ('img' or 'vid').
        groupBy (str): Specifies the grouping method ('directory' or 'class').

    Returns:
        str: JSON created from a list of tuples where each tuple contains a group name and a group of paths.
    """
    global writing
    if not writing:
        writing = True
        updateDB(groupBy)
        writing = False
    
    readConn = connectDB(dbPath())
    if groupBy == "directory":
        result = groupByDir(readConn, hidden, fileType)
    else:
        result = groupByClass(readConn, hidden, fileType)
    closeConnection(readConn)

    return jsonify(result)

def decodeLinkPath(path: str) -> str:
    """
    Decodes a URL-encoded path and attempts to find the corresponding file or directory.
    If the file or directory exists under either the Unix-style path or the relative path,
    it returns the absolute path. Otherwise, it should redirect to the index page.
    
    Args:
        path: The URL-encoded path to decode and locate.

    Returns:
        The absolute path if found, or a redirect to the index page if not.
    """
    path = escape(unquote(path))

    # Convert the path to Windows-style path for checking
    unixPath = f"/{path}"
    if pathExist(unixPath):
        return unixPath

    # Convert the path to Windows-style path for checking
    windowsPath = path.replace('/', '\\')
    if pathExist(windowsPath):
        return windowsPath

    return redirect(url_for('index')) # doesn't reload (TBI)

app = Flask(__name__, template_folder=f"{pathOf('static')}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def staticFile(path):
    return app.send_static_file(pathOf(path))

@app.route('/media/<path:path>')
def sendFile(path):
    return send_file(decodeLinkPath(path))

@app.route('/thumbnail/<path:path>')
def thumbnail(path):
    return getThumbnail(decodeLinkPath(path))

# Sections

@app.route('/<string:fileType>/<string:groupBy>')
def groupMedia(fileType, groupBy):
    if fileType not in ["img", "vid"] or groupBy not in ["class", "directory"]:
        return redirect(url_for('index'))
    return groupPaths(0, fileType, groupBy)

@app.route('/hidden/<string:groupBy>')
def hidden(groupBy):
    if groupBy not in ["class", "directory"]:
        return redirect(url_for('index'))
    return groupPaths(1, "any", groupBy)

@app.route('/trash/<string:groupBy>')
def trash(groupBy):
    if groupBy not in ["class", "directory"]:
        return redirect(url_for('index'))
    return groupPaths(-1, "any", groupBy)

# Buttons

@app.route('/toTrash', methods=['POST'])
def toTrash():
    data = request.get_json().get('selectedMedia', [])
    print(f"Moving files to trash: {data}")
    conn = connectDB(dbPath())
    moveToTrash(conn, data)
    closeConnection(conn)
    return jsonify({"success": True})

@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json().get('selectedMedia', [])
    print(f"Deleting files: {data}")
    conn = connectDB(dbPath())
    deleteFromDB(conn, data)
    closeConnection(conn)
    return jsonify({"success": True})

@app.route('/hide', methods=['POST'])
def hide():
    data = request.get_json().get('selectedMedia', [])
    print(f"Hiding files: {data}")
    conn = connectDB(dbPath())
    toggleVisibility(conn, data, 1)
    closeConnection(conn)
    return jsonify({"success": True})

@app.route('/unhide', methods=['POST'])
def unhide():
    data = request.get_json().get('selectedMedia', [])
    print(f"Unhiding files: {data}")
    conn = connectDB(dbPath())
    toggleVisibility(conn, data, 0)
    closeConnection(conn)
    return jsonify({"success": True})

@app.route('/restore', methods=['POST'])
def restore():
    data = request.get_json().get('selectedMedia', [])
    print(f"Restoring files: {data}")
    conn = connectDB(dbPath())
    toggleVisibility(conn, data, 0)
    closeConnection(conn)
    return jsonify({"success": True})

@app.route('/info/<path:path>')
def info(path):
    conn = connectDB(dbPath())
    info = getInfoByPath(conn, decodeLinkPath(path))
    closeConnection(conn)
    return jsonify(info)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
