import os
import sys
import hashlib
from typing import Generator, Union, List

def genHash(path: str) -> str:
    """
    Generates a hash of file.

    Args:
        path: Path to the file.

    Returns:
        A hexadecimal string representing the hash of the file.
    """
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def checkExtension(filePath: str, extensions: List[str]) -> bool:
    """
    Checks if the file has one of the specified extensions.

    Args:
        filePath: Path to the file.
        extensions: List of allowed extensions.

    Returns:
        True if the file has one of the extensions, False otherwise.
    """
    _, fileExtension = os.path.splitext(filePath)
    return fileExtension.lower() in extensions

def mediaPaths(startPath: str) -> Generator[tuple[str, str, str], None, None]:
    """
    Generate paths to all images and videos in the given directory and its subdirectories.
    Ignore hidden directories.

    Args:
        startPath: Path to the directory to search for images and videos.

    Yields:
        Tuple containing (file path, file type ('img' or 'vid'), root directory path).
    """
    for root, dirs, files in os.walk(startPath):
        for dir_name in list(dirs):  # Convert dirs to a list to avoid RuntimeError
            if dir_name.startswith(('.', 'AppData')):
                dirs.remove(dir_name)
        
        for file in files:
            fileType = None
            if checkExtension(file, [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".avif"]):
                fileType = "img"
            elif checkExtension(file, [".mp4", ".mkv", ".webm"]):
                fileType = "vid"
            if fileType:
                yield os.path.join(root, file), fileType, root
                

# NN
def detectFileWithHash(files: Generator[str, None, None], targetHash: str) -> Union[str, None]:
    """
    Detect a file with a specific hash value from a generator.

    Args:
        files: Generator yielding file paths.
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


def homeDir() -> str:
    """
    Get the home directory path.
    Handle Android (TBI)

    Returns:
        str: Home directory path.
    """
    return os.path.expanduser("~")

def deleteFile(paths: List[str]) -> None:
    """
    Delete files by path.

    Args:
        paths: A list of paths to delete.
    """
    for path in paths:
        try:
            os.remove(path)
        except Exception as e:
            print(f"ERROR: {e}")
            pass

def pathExist(path: str) -> bool:
    """
    Check if a file or directory exists.

    Args:
        path: Path to the file or directory.

    Returns:
        bool: True if the file or directory exists, False otherwise.
    """
    return os.path.exists(path)

def pathOf(path) -> str:
    """
    When packaging the app using pyinstaller sys._MEIPASS/<file>/ will be available instead of <file>/.
    Depending on environment path of models will be returned.

    Args:
        path: Path to the model file.

    Returns:
        str: Path to the model file.
    """
    if pathExist(path):
        return path
    return f"{sys._MEIPASS}/{path}" 
