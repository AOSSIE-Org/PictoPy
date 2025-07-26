import os
import uuid
from typing import List, Tuple, Dict
from PIL import Image
from pathlib import Path

from app.config.settings import THUMBNAIL_IMAGES_PATH
from app.database.images import (
    db_bulk_insert_images,
    db_get_untagged_images,
    db_update_image_tagged_status,
    db_insert_image_classes_batch,
)
from app.database.folders import db_get_folder_ids_by_path_prefix
from app.models.FaceDetector import FaceDetector
from app.models.ObjectClassifier import ObjectClassifier


def image_util_is_valid_image(file_path: str) -> bool:
    """Check if the file is a valid image with allowed extensions."""
    # Check file extension first
    allowed_extensions = {".jpg", ".jpeg", ".png"}
    file_extension = Path(file_path).suffix.lower()

    if file_extension not in allowed_extensions:
        return False

    # Then verify it's a valid image
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def image_util_generate_thumbnail(image_path: str, thumbnail_path: str, size: Tuple[int, int] = (200, 200)) -> bool:
    """Generate thumbnail for a single image."""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size)

            # Convert to RGB if the image has an alpha channel or is not RGB
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.save(thumbnail_path, "JPEG")  # Always save thumbnails as JPEG
        return True
    except Exception as e:
        print(f"Error generating thumbnail for {image_path}: {e}")
        return False


def image_util_get_images_from_folder(folder_path: str) -> List[str]:
    """Get all image files from a folder."""
    image_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if image_util_is_valid_image(file_path):
                image_files.append(file_path)
    return image_files


def image_util_process_folder_images(root_folder: str) -> bool:
    """Main function to process images in a folder and its subfolders."""
    try:
        # Ensure thumbnail directory exists
        os.makedirs(THUMBNAIL_IMAGES_PATH, exist_ok=True)

        # Get all folder IDs and create a path -> id mapping
        folder_ids = db_get_folder_ids_by_path_prefix(root_folder)
        if not folder_ids:
            return False

        # Get all image files
        image_files = image_util_get_images_from_folder(root_folder)
        if not image_files:
            return True  # No images to process is not an error

        # Create a dictionary mapping folder paths to their IDs
        folder_path_to_id: Dict[str, int] = {}
        for folder_id in folder_ids:
            path = os.path.abspath(folder_id[1])  # Assuming db_get_folder_ids_by_path_prefix returns (id, path) tuples
            folder_path_to_id[path] = folder_id[0]

        # Prepare image records
        image_records = []
        for image_path in image_files:
            parent_folder = os.path.dirname(image_path)

            # Find the most specific folder ID by checking parent folders
            folder_id = None
            current_path = parent_folder
            while current_path:
                if current_path in folder_path_to_id:
                    folder_id = folder_path_to_id[current_path]
                    break
                current_path = os.path.dirname(current_path)

            if not folder_id:
                continue  # Skip if no matching folder ID found

            image_id = str(uuid.uuid4())
            thumbnail_name = f"thumbnail_{image_id}.jpg"
            thumbnail_path = os.path.join(THUMBNAIL_IMAGES_PATH, thumbnail_name)

            # Generate thumbnail
            if image_util_generate_thumbnail(image_path, thumbnail_path):
                image_records.append(
                    {
                        "id": image_id,
                        "path": image_path,
                        "folder_id": folder_id,
                        "thumbnailPath": thumbnail_path,
                        "metadata": "{}",  # Empty JSON object as default
                        "isTagged": False,
                    }
                )

        # Bulk insert all records
        return db_bulk_insert_images(image_records)
    except Exception as e:
        print(f"Error processing folder {root_folder}: {e}")
        return False


def image_util_classify_and_face_detect_images(untagged_images: List[Dict[str, str]]) -> None:
    """Classify untagged images and detect faces if applicable."""
    object_classifier = ObjectClassifier()
    face_detector = FaceDetector()
    try:
        for image in untagged_images:
            image_path = image["path"]
            image_id = image["id"]

            # Step 1: Get classes
            classes = object_classifier.get_classes(image_path)

            # Step 2: Update the image status in the database
            db_update_image_tagged_status(image_id, True)

            # Step 3: Insert class-image pairs if classes were detected
            if len(classes) > 0:
                # Create image-class pairs
                image_class_pairs = [(image_id, class_id) for class_id in classes]
                print(image_class_pairs)

                # Insert the pairs into the database
                db_insert_image_classes_batch(image_class_pairs)

            # Step 4: Detect faces if "person" class is present
            if classes and 0 in classes and 0 < classes.count(0) < 7:
                face_detector.detect_faces(image_id, image_path)
    finally:
        # Ensure resources are cleaned up
        object_classifier.close()
        face_detector.close()


def image_util_process_untagged_images() -> bool:
    """Process all untagged images in folders with AI tagging enabled."""
    try:
        # Step 1: Get all untagged images and whose corresponding folder has AI tagging enabled
        untagged_images = db_get_untagged_images()
        if not untagged_images:
            return True  # No untagged images to process

        # Step 2: Process each untagged image
        image_util_classify_and_face_detect_images(untagged_images)

        return True
    except Exception as e:
        print(f"Error processing untagged images: {e}")
        return False
