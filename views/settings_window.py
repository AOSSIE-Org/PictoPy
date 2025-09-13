from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel, QLineEdit, QFileDialog

class SettingsWindow(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("Settings")
        self.setLayout(QVBoxLayout())
        self.setup_ui()

    def setup_ui(self):
        # Add a label and line edit for the media folder
        self.media_folder_label = QLabel("Media Folder:")
        self.layout().addWidget(self.media_folder_label)

        self.media_folder_edit = QLineEdit()
        self.media_folder_edit.setText(self.settings.media_folder)
        self.layout().addWidget(self.media_folder_edit)

        # Add a button to open a file dialog
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_media_folder)
        self.layout().addWidget(self.browse_button)

        # Add auto-detect checkbox
        self.auto_detect_checkbox = QCheckBox("Auto-detect common media folders")
        self.auto_detect_checkbox.setChecked(self.settings.auto_detect_folders)
        self.layout().addWidget(self.auto_detect_checkbox)

        # Add a button to save the settings
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.layout().addWidget(self.save_button)

    def browse_media_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Media Folder", self.settings.media_folder)
        if folder:
            self.media_folder_edit.setText(folder)

    def save_settings(self):
        self.settings.media_folder = self.media_folder_edit.text()
        self.settings.auto_detect_folders = self.auto_detect_checkbox.isChecked()
        self.accept()