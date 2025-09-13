from PyQt5.QtWidgets import QMainWindow
from models.folder_detector import CommonFolderDetector

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ...existing initialization code...
        self.folders = []  # Initialize folders list
        self.settings = Settings()  # Assuming Settings is a class that handles your settings
        self.load_folders()
        
    def load_folders(self):
        # ...existing code to load folders...
        
        # Auto-detect common folders if enabled
        if self.settings.auto_detect_folders:
            common_folders = CommonFolderDetector.get_common_folders()
            for folder in common_folders:
                if folder not in self.folders:  # Avoid duplicates
                    self.folders.append(folder)
                    
        # ...existing code to update the UI or perform actions with the loaded folders...

class Settings:
    def __init__(self):
        # ...load your settings here...
        self.auto_detect_folders = True  # Example setting, change as needed

    # ...other settings methods and properties...