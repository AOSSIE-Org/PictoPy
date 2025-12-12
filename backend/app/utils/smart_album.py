from typing import List, Dict
from app.database.smart_album import (
    db_create_smart_album,
    db_get_smart_album_by_id,
    db_get_all_smart_albums,
    db_add_images_to_smart_album,
    db_get_images_for_smart_album,
    db_find_images_by_criteria,
    db_delete_smart_album,
    db_update_smart_album,
    db_create_smart_albums_table,
    db_clear_smart_album_images,
)

from app.utils.YOLO import class_names
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


class SmartAlbumService:
    """Service for managing smart albums."""

    @staticmethod
    def initialize():
        """Initialize the smart albums table"""
        try:
            db_create_smart_albums_table()
            logger.info("Smart albums table initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize smart albums table: {e}")
            raise

    @staticmethod
    def create_object_based_album(
        album_name: str, object_classes: List[str], auto_update: bool = True
    ) -> str:
        """Create a smart album based on object detection criteria.

        Args:
            album_name:Name of the smart album.(e.g., "DOGS", "CATS_AND_CARS")
            object_classes: List of object class names (e.g., ["dog", "cat"])
            auto_update: Whether to auto-add new matching images

        returns:
            album_id: UUID of the created album

        """
        # Validate class names
        invalid_classes = [cls for cls in object_classes if cls not in class_names]
        if invalid_classes:
            raise ValueError(f"Invalid object classes: {invalid_classes}")

        # Convert class names to class IDs
        class_ids = [i for i, name in enumerate(class_names) if name in object_classes]
        criteria = {
            "type": "object",
            "class_names": object_classes,
            "class_ids": class_ids,
        }

        album_id = db_create_smart_album(
            album_name=album_name,
            album_type="object",
            criteria=criteria,
            auto_update=auto_update,
        )

        # Populate album with existing images
        SmartAlbumService.refresh_album(album_id)

        logger.info(f"Created smart album '{album_name}' with ID {album_id}")
        return album_id

    @staticmethod
    def create_face_based_album(
        album_name: str, face_id: str, auto_update: bool = True
    ) -> str:
        """Create a smart album for a specific face.
        Args:
            album_name: Name of the smart album (e.g., "John_Doe")
            face_id: ID of the face to include in the album
            auto_update: Whether to auto-add new matching images

        returns:
            album_id: UUID of the created album
        """
        criteria = {"type": "face", "face_id": face_id}

        album_id = db_create_smart_album(
            album_name=album_name,
            album_type="face",
            criteria=criteria,
            auto_update=auto_update,
        )

        SmartAlbumService.refresh_album(album_id)
        logger.info(f"Created face-based smart album '{album_name}' with ID {album_id}")
        return album_id

    @staticmethod
    def create_predefined_album() -> Dict[str, str]:
        """
        Create common smart albums automatically.

        returns:
            A dictionary of album names to their IDs.
        """

        predefined = {
            "People": ["person"],
            "Animals": [
                "dog",
                "cat",
                "bird",
                "horse",
                "sheep",
                "cow",
                "elephant",
                "bear",
                "zebra",
                "giraffe",
            ],
            "Pets": ["dog", "cat", "bird"],
            "Vehicles": [
                "car",
                "motorcycle",
                "airplane",
                "bus",
                "train",
                "truck",
                "boat",
            ],
            "Food": [
                "pizza",
                "donut",
                "cake",
                "apple",
                "sandwich",
                "orange",
                "broccoli",
                "carrot",
                "hot dog",
                "banana",
            ],
            "Electronics": [
                "tv",
                "laptop",
                "mouse",
                "remote",
                "keyboard",
                "cell phone",
            ],
            "Sports": [
                "sports ball",
                "baseball bat",
                "baseball glove",
                "skateboard",
                "surfboard",
                "tennis racket",
            ],
            "Furniture": ["chair", "couch", "bed", "dining table"],
        }

        created_albums = {}

        for album_name, object_classes in predefined.items():
            try:
                album_id = SmartAlbumService.create_object_based_album(
                    album_name=album_name,
                    object_classes=object_classes,
                    auto_update=True,
                )
                created_albums[album_name] = album_id
                logger.info(f"Created predefined album: {album_name}")
            except Exception as e:
                logger.error(f"Failed to create album {album_name}: {e}")

        return created_albums

    @staticmethod
    def refresh_album(album_id: str) -> None:
        """Refresh the smart album by adding images that match its criteria.

        Args:
            album_id: UUID of the smart album to refresh
        """
        album = db_get_smart_album_by_id(album_id)
        if not album:
            raise ValueError(f"Smart album with ID {album_id} does not exist.")

        # Clear existing images first
        db_clear_smart_album_images(album_id)

        # Find matching images
        matching_images_ids = db_find_images_by_criteria(album["criteria"])

        if matching_images_ids:
            db_add_images_to_smart_album(album_id, matching_images_ids)

        logger.info(
            f"Refreshed album {album['album_name']}: {len(matching_images_ids)} images"
        )
        return len(matching_images_ids)

    @staticmethod
    def refresh_all_albums() -> Dict[str, int]:
        """Refresh all smart albums in the database.

        Returns:
            A dictionary mapping album IDs to the number of images added.
        """
        albums = db_get_all_smart_albums()
        results = {}
        for album in albums:
            if album.get("auto_update"):
                try:
                    count = SmartAlbumService.refresh_album(album["album_id"])
                    results[album["album_id"]] = count
                except Exception as e:
                    logger.error(f"Failed to refresh album {album['album_id']}: {e}")
                    results[album["album_id"]] = 0
        return results

    @staticmethod
    def get_available_object_classes() -> List[str]:
        """Get the list of available object classes for smart albums.

        Returns:
            List of object class names.
        """
        return list(class_names)

    @staticmethod
    def get_album_statistics() -> Dict:
        """Get statistics about smart albums."""
        albums = db_get_all_smart_albums()
        stats = {
            "total_albums": len(albums),
            "object_albums": sum(1 for a in albums if a["album_type"] == "object"),
            "face_albums": sum(1 for a in albums if a["album_type"] == "face"),
            "auto_update_enabled": sum(1 for a in albums if a.get("auto_update")),
            "total_images_in_albums": sum(a.get("image_count", 0) for a in albums),
        }
        return stats

    @staticmethod
    def get_album_images(
        album_id: str, limit: int = None, offset: int = 0
    ) -> List[Dict]:
        """Get images from a smart album with pagination.

        Args:
            album_id: UUID of the smart album
            limit: Maximum number of images to return
            offset: Number of images to skip

        Returns:
            List of image dictionaries
        """
        try:
            images = db_get_images_for_smart_album(album_id, limit=limit, offset=offset)
            logger.info(f"Retrieved {len(images)} images from album {album_id}")
            return images
        except Exception as e:
            logger.error(f"Failed to get images for album {album_id}: {e}")
            raise

    @staticmethod
    def update_album(
        album_id: str, album_name: str = None, auto_update: bool = None
    ) -> None:
        """Update smart album properties.

        Args:
            album_id: UUID of the smart album
            album_name: New name for the album (optional)
            auto_update: New auto-update setting (optional)
        """
        if album_name is None and auto_update is None:
            raise ValueError("At least one field must be provided for update")

        try:
            db_update_smart_album(
                album_id, album_name=album_name, auto_update=auto_update
            )
            logger.info(f"Updated smart album {album_id}")
        except Exception as e:
            logger.error(f"Failed to update album {album_id}: {e}")
            raise

    @staticmethod
    def delete_album(album_id: str) -> None:
        """Delete a smart album (images are preserved in the library).

        Args:
            album_id: UUID of the smart album to delete
        """
        try:
            album = db_get_smart_album_by_id(album_id)
            if not album:
                raise ValueError(f"Smart album with ID {album_id} does not exist")

            db_delete_smart_album(album_id)
            logger.info(f"Deleted smart album '{album['album_name']}' ({album_id})")
        except Exception as e:
            logger.error(f"Failed to delete album {album_id}: {e}")
            raise
