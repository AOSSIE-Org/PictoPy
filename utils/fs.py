import os
import sys
import xxhash
import mmap
from typing import Generator, Union, List
from markupsafe import escape
from urllib.parse import unquote

def genHash(path: str) -> str:
    """
    Generates a fast, non-cryptographic hash of a file using xxHash 
    And memory mapping making file's content to be accessible as if 
    it were part of the program's memory, but it's actually stored on disk. 
    Why hash and not uuid?
    Hashes are based on content and not on name/path.

    Args:
        path: Path to the file.

    Returns:
        A hexadecimal string representing the hash of the file.
    """
    try:
        hash_xx = xxhash.xxh64()
        with open(path, "rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                hash_xx.update(mm)
        return hash_xx.hexdigest()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

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
    windowsPath = path.replace("/", "\\")
    if pathExist(windowsPath):
        return windowsPath
