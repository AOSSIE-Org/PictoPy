import os
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
    Generates a list of paths to all images in the given directory.

    Args:
        startPath: Path to the directory to search for images.

    Returns:
        A generator that yields paths to all images in the directory.
    """
    for root, dirs, files in os.walk(startPath):
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
        print(path)
        os.remove(path)
