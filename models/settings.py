class Settings:
    def __init__(self):
        # ...existing code...
        self.auto_detect_folders = True

    def to_dict(self):
        return {
            # ...existing code...
            'auto_detect_folders': self.auto_detect_folders
        }

    def from_dict(self, data):
        # ...existing code...
        self.auto_detect_folders = data.get('auto_detect_folders', True)