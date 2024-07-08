import os
import sys
import hashlib
from typing import Generator, Union, Tuple

def genHash(imgPath: str) -> str:
    """
    Generates a hash of the image file.

    Args:
        imgPath: Path to the image file.

    Returns:
        A hexadecimal string representing the hash of the image file.
    """
    with open(imgPath, "rb") as f:
        imgData = f.read()
        return hashlib.md5(imgData).hexdigest()


def isImg(filePath: str) -> bool:
    """
    Checks if the file is an image.

    Args:
        filePath: Path to the file.

    Returns:
        True if the file is an image, False otherwise.
    """
    _, fileExtension = os.path.splitext(filePath)
    imgExts = [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".avif"]
    return fileExtension.lower() in imgExts


def imgPaths(startPath: str) -> Generator[str, None, None]:
    """
    Generate path to all images in the given directory and it's subdirectories.
    Ignore hidden directories.

    Args:
        startPath: Path to the directory to search for images.

    Returns:
        A generator that yields paths to all images in the directory.
    """
    for root, dirs, files in os.walk(startPath):
        for dir_name in list(dirs):  # Convert dirs to a list to avoid RuntimeError
            if dir_name.startswith('.'):
                dirs.remove(dir_name)
        
        for file in files:
            if isImg(file):
                yield os.path.join(root, file)
                

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

def deleteFile(paths: Tuple[str]) -> None:
    """
    Delete files by path.

    Args:
        paths: A tuple of paths to delete.
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
