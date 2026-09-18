import os
import pytest
from typing import List, Tuple
from app.utils.watcher import watcher_util_find_closest_parent_folder

FolderIdPath = Tuple[str, str]

def test_watcher_find_closest_parent_folder():
    # Helper to create expected output format
    def match(folder_id: str, path: str):
        return (folder_id, os.path.abspath(path))

    # Our watched folders
    watched_folders: List[FolderIdPath] = [
        ("root_d", "D:\\"),
        ("root_x", "X:\\"),
        ("sub_x", "X:\\subfolder"),
        ("normal", "C:\\Photos"),
    ]

    # Test cases: (file_path, expected_match_id, expected_match_path)
    test_cases = [
        # Normal folder cases
        ("C:\\Photos\\image.jpg", "normal", "C:\\Photos"),
        ("C:\\Photos\\nested\\image.jpg", "normal", "C:\\Photos"),
        ("C:\\Photos", "normal", "C:\\Photos"),

        # Drive root cases
        ("X:\\image.jpg", "root_x", "X:\\"),
        ("D:\\another_image.jpg", "root_d", "D:\\"),
        
        # Drive root nested file
        ("D:\\nested\\image.jpg", "root_d", "D:\\"),
        
        # Drive root itself
        ("D:\\", "root_d", "D:\\"),
        
        # Sibling-prefix rejection (must NOT match)
        ("C:\\PhotosBackup\\image.jpg", None, None),
        ("C:\\Photos_old", None, None),
        
        # Nested folders pick longest match
        ("X:\\subfolder\\image.jpg", "sub_x", "X:\\subfolder"),
        ("X:\\subfolder\\nested\\image.jpg", "sub_x", "X:\\subfolder"),
        
        # Unrelated path
        ("C:\\OtherFolder\\image.jpg", None, None),
    ]

    for file_path, expected_id, expected_path in test_cases:
        expected = (expected_id, os.path.abspath(expected_path)) if expected_id else None
        
        # Some paths might need os.path.abspath explicitly if not provided that way
        file_path_abs = os.path.abspath(file_path)
        
        result = watcher_util_find_closest_parent_folder(file_path_abs, watched_folders)
        
        assert result == expected, f"Failed for {file_path}. Expected {expected}, got {result}"
