import os
from PIL import Image


def generate_thumbnails_for_folders(folder_paths: list):
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"]
    failed_paths = []

    for folder_path in folder_paths:
        if not os.path.isdir(folder_path):
            failed_paths.append(
                {
                    "folder_path": folder_path,
                    "error": "Invalid folder path",
                    "message": "The provided path is not a valid directory",
                }
            )
            continue

        for root, _, files in os.walk(folder_path):
            # Skip the "PictoPy.thumbnails" folder
            if "PictoPy.thumbnails" in root:
                continue

            # Create the "PictoPy.thumbnails" folder inside the current directory (`root`)
            thumbnail_folder = os.path.join(root, "PictoPy.thumbnails")
            os.makedirs(thumbnail_folder, exist_ok=True)

            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file_path)[1].lower()
                if file_extension in image_extensions:
                    try:
                        # Create a unique thumbnail name based on the file name
                        thumbnail_name = file
                        thumbnail_path = os.path.join(thumbnail_folder, thumbnail_name)

                        # Skip if the thumbnail already exists
                        if os.path.exists(thumbnail_path):
                            continue

                        # Generate the thumbnail
                        img = Image.open(file_path)
                        img.thumbnail((400, 400))
                        img.save(thumbnail_path)
                    except Exception as e:
                        failed_paths.append(
                            {
                                "folder_path": folder_path,
                                "file": file_path,
                                "error": "Thumbnail generation error",
                                "message": f"Error processing file {file}: {str(e)}",
                            }
                        )

    return failed_paths
