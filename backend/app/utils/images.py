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
    db_get_images_by_folder_ids,
    db_delete_images_by_ids,
)
from app.models.FaceDetector import FaceDetector
from app.models.ObjectClassifier import ObjectClassifier


def image_util_process_folder_images(folder_data: List[Tuple[str, int, bool]]) -> bool:
    """Main function to process images in multiple folders based on provided folder data.

    Args:
        folder_data: List of tuples containing (folder_path, folder_id, recursive)

    Returns:
        bool: True if all folders processed successfully, False otherwise
    """
    try:
        # Ensure thumbnail directory exists
        os.makedirs(THUMBNAIL_IMAGES_PATH, exist_ok=True)

        all_image_records = []
        all_folder_ids = []

        # Process each folder in the provided data
        for folder_path, folder_id, recursive in folder_data:
            try:
                # Add folder ID to list for obsolete image cleanup
                all_folder_ids.append(folder_id)

                # Step 1: Get all image files from current folder
                image_files = image_util_get_images_from_folder(folder_path, recursive)

                if not image_files:
                    continue  # No images in this folder, continue to next

                # Step 2: Create folder path mapping for this folder
                folder_path_to_id = {os.path.abspath(folder_path): folder_id}

                # Step 3: Prepare image records for this folder
                folder_image_records = image_util_prepare_image_records(image_files, folder_path_to_id)
                all_image_records.extend(folder_image_records)

            except Exception as e:
                print(f"Error processing folder {folder_path}: {e}")
                continue  # Continue with other folders even if one fails

        # Step 4: Remove obsolete images that no longer exist in filesystem
        if all_folder_ids:
            image_util_remove_obsolete_images(all_folder_ids)

        # Step 5: Bulk insert all new records if any exist
        if all_image_records:
            return db_bulk_insert_images(all_image_records)

        return True  # No images to process is not an error
    except Exception as e:
        print(f"Error processing folders: {e}")
        return False


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

            # Step 2: Insert class-image pairs if classes were detected
            if len(classes) > 0:
                # Create image-class pairs
                image_class_pairs = [(image_id, class_id) for class_id in classes]
                print(image_class_pairs)

                # Insert the pairs into the database
                db_insert_image_classes_batch(image_class_pairs)

            # Step 3: Detect faces if "person" class is present
            if classes and 0 in classes and 0 < classes.count(0) < 7:
                face_detector.detect_faces(image_id, image_path)

            # Step 4: Update the image status in the database
            db_update_image_tagged_status(image_id, True)
    finally:
        # Ensure resources are cleaned up
        object_classifier.close()
        face_detector.close()


def image_util_prepare_image_records(image_files: List[str], folder_path_to_id: Dict[str, int]) -> List[Dict]:
    """
    Prepare image records with thumbnails for database insertion.

    Args:
        image_files: List of image file paths
        folder_path_to_id: Dictionary mapping folder paths to IDs

    Returns:
        List of image record dictionaries ready for database insertion
    """
    image_records = []
    for image_path in image_files:
        folder_id = image_util_find_folder_id_for_image(image_path, folder_path_to_id)

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

    return image_records


def image_util_get_images_from_folder(folder_path: str, recursive: bool = True) -> List[str]:
    """Get all image files from a folder.

    Args:
        folder_path: Path to the folder to scan
        recursive: If True, scan subfolders recursively. If False, only scan direct children.

    Returns:
        List of image file paths
    """
    image_files = []

    if recursive:
        # Recursive scan using os.walk
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if image_util_is_valid_image(file_path):
                    image_files.append(file_path)
    else:
        # Non-recursive scan, only direct children
        try:
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path) and image_util_is_valid_image(file_path):
                    image_files.append(file_path)
        except OSError as e:
            print(f"Error reading folder {folder_path}: {e}")

    return image_files


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


def image_util_remove_obsolete_images(folder_id_list: List[int]) -> int:
    """
    Remove obsolete images that no longer exist in the filesystem.

    Args:
        folder_id_list: List of folder IDs to check for obsolete images

    Returns:
        Number of obsolete images removed
    """
    existing_db_images = db_get_images_by_folder_ids(folder_id_list)

    obsolete_images = []
    for image_id, image_path, thumbnail_path in existing_db_images:
        if not os.path.exists(image_path):
            obsolete_images.append(image_id)
            # Also remove thumbnail if it exists
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    os.remove(thumbnail_path)
                    print(f"Removed obsolete thumbnail: {thumbnail_path}")
                except OSError as e:
                    print(f"Error removing thumbnail {thumbnail_path}: {e}")

    if obsolete_images:
        db_delete_images_by_ids(obsolete_images)
        print(f"Removed {len(obsolete_images)} obsolete image(s) from database")

    return len(obsolete_images)


def image_util_create_folder_path_mapping(folder_ids: List[Tuple[int, str]]) -> Dict[str, int]:
    """
    Create a dictionary mapping folder paths to their IDs.

    Args:
        folder_ids: List of tuples containing (folder_id, folder_path)

    Returns:
        Dictionary mapping absolute folder paths to folder IDs
    """
    folder_path_to_id: Dict[str, int] = {}
    for folder_id, folder_path in folder_ids:
        path = os.path.abspath(folder_path)
        folder_path_to_id[path] = folder_id
    return folder_path_to_id


def image_util_find_folder_id_for_image(image_path: str, folder_path_to_id: Dict[str, int]) -> int:
    """
    Find the most specific folder ID for a given image path.

    Args:
        image_path: Path to the image file
        folder_path_to_id: Dictionary mapping folder paths to IDs

    Returns:
        Folder ID if found, None otherwise
    """
    parent_folder = os.path.dirname(image_path)

    current_path = parent_folder
    while current_path:
        if current_path in folder_path_to_id:
            return folder_path_to_id[current_path]
        current_path = os.path.dirname(current_path)

    return None


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
