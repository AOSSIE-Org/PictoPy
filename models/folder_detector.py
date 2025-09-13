import os
from pathlib import Path

class CommonFolderDetector:
    @staticmethod
    def get_common_folders():
        """Returns a list of common folder paths that typically contain media files"""
        common_folders = []
        home = Path.home()

        # Windows common folders
        windows_folders = {
            'Downloads': home / 'Downloads',
            'Pictures': home / 'Pictures',
            'Videos': home / 'Videos',
            'Desktop': home / 'Desktop',
            'Documents': home / 'Documents'
        }

        # Add existing folders to the list
        for name, path in windows_folders.items():
            if path.exists() and path.is_dir():
                common_folders.append(str(path))

        # Check for Screenshots folder in Pictures
        screenshots_folder = windows_folders['Pictures'] / 'Screenshots'
        if screenshots_folder.exists() and screenshots_folder.is_dir():
            common_folders.append(str(screenshots_folder))

        return common_folders
