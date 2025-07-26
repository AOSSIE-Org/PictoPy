import os
from PIL import Image
from app.database.folders import get_all_folder_ids
from app.database.images import get_all_images_from_folder_id
from app.config.settings import THUMBNAIL_IMAGES_PATH


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

# This function takes a list of folder paths, iterates through each folder and its files,
# skipping the "PictoPy.thumbnails" directory, and generates thumbnails for supported image files.
# It saves thumbnails in a designated thumbnails folder and collects any errors for invalid paths
# or thumbnail generation failures, returning a list of failed paths and error details.


def generate_thumbnails_for_existing_folders():
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

# This function retrieves all folder IDs from the database, then for each folder,
# it fetches all associated image paths and generates thumbnails for each image
# if a thumbnail does not already exist. Any image paths causing errors during processing
# are recorded and returned. In case of any top-level failure, it returns an empty list.
