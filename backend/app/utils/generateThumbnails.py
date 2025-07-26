import os
from PIL import Image
from app.database.folders import get_all_folder_ids
from app.database.images import get_all_images_from_folder_id
from app.config.settings import THUMBNAIL_IMAGES_PATH


def generate_thumbnails_for_folders(folder_paths: list):
    """
    Generate thumbnails (400x400 max) for all supported image files
    found in the given list of folder paths. Thumbnails are saved in
    a 'PictoPy.thumbnails' directory under THUMBNAIL_IMAGES_PATH.
    Skips folders named 'PictoPy.thumbnails' to avoid recursion.
    Returns a list of failed paths with error details.
    """
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
            thumbnail_folder = os.path.join(THUMBNAIL_IMAGES_PATH, "PictoPy.thumbnails")

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


def generate_thumbnails_for_existing_folders():
    """
    Retrieve all folder IDs from the database, then generate thumbnails
    (max 400x400) for all images in those folders. Thumbnails are saved
    in the 'PictoPy.thumbnails' folder under THUMBNAIL_IMAGES_PATH.
    Skips existing thumbnails. Returns a list of image paths for which
    thumbnail generation failed.
    """
    try:
        folder_ids = get_all_folder_ids()
        thumbnail_folder = os.path.join(THUMBNAIL_IMAGES_PATH, "PictoPy.thumbnails")
        failed_paths = []
        for folder_id in folder_ids:
            try:
                curr_image_paths = get_all_images_from_folder_id(folder_id)
                for image_path in curr_image_paths:
                    if not os.path.exists(image_path):
                        continue

                    image_name = os.path.basename(image_path)
                    thumbnail_path = os.path.join(thumbnail_folder, image_name)

                    if os.path.exists(thumbnail_path):
                        continue

                    img = Image.open(image_path)
                    img.thumbnail((400, 400))
                    img.save(thumbnail_path)
            except Exception:
                failed_paths.append(image_path)

        return failed_paths

    except Exception:
        return []
