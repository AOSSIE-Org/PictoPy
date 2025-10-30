# Standard library imports
import sqlite3
from typing import List, Dict, Any
from datetime import datetime, timedelta

# App-specific imports
from app.config.settings import DATABASE_PATH
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def db_get_memories_on_this_day(years_back: int = 5) -> List[Dict[str, Any]]:
    """
    Get images from the same day in previous years.

    Args:
        years_back: Number of years to look back (default: 5)

    Returns:
        List of dictionaries containing memory data grouped by year
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        # Get current month and day
        today = datetime.now()
        current_month = today.month
        current_day = today.day
        current_year = today.year

        # Query images from the same day in previous years
        cursor.execute(
            """
            SELECT 
                i.id,
                i.path,
                i.thumbnailPath,
                i.metadata,
                i.isTagged,
                m.name as tag_name
            FROM images i
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
            WHERE i.metadata IS NOT NULL
            ORDER BY i.metadata
            """
        )

        results = cursor.fetchall()

        # Parse and filter by date
        from app.utils.images import image_util_parse_metadata

        memories_by_year = {}

        for image_id, path, thumbnail_path, metadata, is_tagged, tag_name in results:
            try:
                metadata_dict = image_util_parse_metadata(metadata)
                date_created = metadata_dict.get("date_created")

                if date_created:
                    # Parse the date
                    img_date = datetime.fromisoformat(
                        date_created.replace("Z", "+00:00")
                    )

                    # Check if it's the same month and day, but different year
                    if (
                        img_date.month == current_month
                        and img_date.day == current_day
                        and img_date.year != current_year
                        and current_year - img_date.year <= years_back
                    ):

                        year = img_date.year
                        years_ago = current_year - year

                        if year not in memories_by_year:
                            memories_by_year[year] = {
                                "year": year,
                                "years_ago": years_ago,
                                "date": img_date.strftime("%B %d, %Y"),
                                "images": [],
                            }

                        # Check if image already exists in the list
                        existing_image = next(
                            (
                                img
                                for img in memories_by_year[year]["images"]
                                if img["id"] == image_id
                            ),
                            None,
                        )

                        if existing_image:
                            # Add tag to existing image
                            if tag_name and tag_name not in existing_image["tags"]:
                                existing_image["tags"].append(tag_name)
                        else:
                            # Add new image
                            memories_by_year[year]["images"].append(
                                {
                                    "id": image_id,
                                    "path": path,
                                    "thumbnailPath": thumbnail_path,
                                    "metadata": metadata_dict,
                                    "isTagged": bool(is_tagged),
                                    "tags": [tag_name] if tag_name else [],
                                }
                            )
            except Exception as e:
                logger.error(f"Error parsing image metadata for memories: {e}")
                continue

        # Convert to list and sort by year (most recent first)
        memories_list = sorted(
            memories_by_year.values(), key=lambda x: x["year"], reverse=True
        )

        return memories_list

    except Exception as e:
        logger.error(f"Error getting 'On This Day' memories: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


def db_get_recent_memories(days: int = 30, min_images: int = 5) -> List[Dict[str, Any]]:
    """
    Get recent collections of images grouped by date.

    Args:
        days: Number of days to look back (default: 30)
        min_images: Minimum number of images per day to create a memory (default: 5)

    Returns:
        List of dictionaries containing memory data grouped by date
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        # Calculate the cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)

        cursor.execute(
            """
            SELECT 
                i.id,
                i.path,
                i.thumbnailPath,
                i.metadata,
                i.isTagged,
                m.name as tag_name
            FROM images i
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
            WHERE i.metadata IS NOT NULL
            ORDER BY i.metadata DESC
            """
        )

        results = cursor.fetchall()

        from app.utils.images import image_util_parse_metadata

        memories_by_date = {}

        for image_id, path, thumbnail_path, metadata, is_tagged, tag_name in results:
            try:
                metadata_dict = image_util_parse_metadata(metadata)
                date_created = metadata_dict.get("date_created")

                if date_created:
                    img_date = datetime.fromisoformat(
                        date_created.replace("Z", "+00:00")
                    )

                    # Only include images within the specified days
                    if img_date >= cutoff_date:
                        date_key = img_date.strftime("%Y-%m-%d")

                        if date_key not in memories_by_date:
                            memories_by_date[date_key] = {
                                "date": img_date.strftime("%B %d, %Y"),
                                "iso_date": date_key,
                                "images": [],
                            }

                        existing_image = next(
                            (
                                img
                                for img in memories_by_date[date_key]["images"]
                                if img["id"] == image_id
                            ),
                            None,
                        )

                        if existing_image:
                            if tag_name and tag_name not in existing_image["tags"]:
                                existing_image["tags"].append(tag_name)
                        else:
                            memories_by_date[date_key]["images"].append(
                                {
                                    "id": image_id,
                                    "path": path,
                                    "thumbnailPath": thumbnail_path,
                                    "metadata": metadata_dict,
                                    "isTagged": bool(is_tagged),
                                    "tags": [tag_name] if tag_name else [],
                                }
                            )
            except Exception as e:
                logger.error(f"Error parsing image metadata for recent memories: {e}")
                continue

        # Filter out dates with fewer than min_images and sort by date
        memories_list = [
            memory
            for memory in memories_by_date.values()
            if len(memory["images"]) >= min_images
        ]
        memories_list.sort(key=lambda x: x["iso_date"], reverse=True)

        return memories_list

    except Exception as e:
        logger.error(f"Error getting recent memories: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


def db_get_memories_by_people(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get memories grouped by people (face clusters).

    Args:
        limit: Maximum number of people memories to return (default: 10)

    Returns:
        List of dictionaries containing memory data grouped by person
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        # First, get clusters with enough images
        cursor.execute(
            """
            SELECT 
                c.cluster_id,
                c.cluster_name,
                COUNT(DISTINCT f.image_id) as image_count
            FROM face_clusters c
            JOIN faces f ON c.cluster_id = f.cluster_id
            WHERE c.cluster_name IS NOT NULL AND c.cluster_name != ''
            GROUP BY c.cluster_id
            HAVING image_count >= 3
            ORDER BY image_count DESC, c.cluster_name
            LIMIT ?
            """,
            (limit,),
        )

        clusters = cursor.fetchall()

        if not clusters:
            return []

        # Then get images for each cluster with tags
        cluster_ids = [cluster[0] for cluster in clusters]
        placeholders = ",".join("?" * len(cluster_ids))

        cursor.execute(
            f"""
            SELECT 
                c.cluster_id,
                c.cluster_name,
                i.id,
                i.path,
                i.thumbnailPath,
                i.metadata,
                i.isTagged,
                m.name as tag_name
            FROM face_clusters c
            JOIN faces f ON c.cluster_id = f.cluster_id
            JOIN images i ON f.image_id = i.id
            LEFT JOIN image_classes ic ON i.id = ic.image_id
            LEFT JOIN mappings m ON ic.class_id = m.class_id
            WHERE c.cluster_id IN ({placeholders})
            ORDER BY c.cluster_name, i.id
            """,
            cluster_ids,
        )

        results = cursor.fetchall()

        from app.utils.images import image_util_parse_metadata

        # Create a mapping of cluster_id to image_count
        cluster_counts = {cluster[0]: cluster[2] for cluster in clusters}

        memories_by_person = {}

        for (
            cluster_id,
            cluster_name,
            image_id,
            path,
            thumbnail_path,
            metadata,
            is_tagged,
            tag_name,
        ) in results:
            if cluster_id not in memories_by_person:
                memories_by_person[cluster_id] = {
                    "cluster_id": cluster_id,
                    "person_name": cluster_name,
                    "image_count": cluster_counts.get(cluster_id, 0),
                    "images": [],
                }

            # Check if image already exists in the list
            existing_image = next(
                (
                    img
                    for img in memories_by_person[cluster_id]["images"]
                    if img["id"] == image_id
                ),
                None,
            )

            if existing_image:
                # Add tag to existing image
                if tag_name and tag_name not in existing_image["tags"]:
                    existing_image["tags"].append(tag_name)
            else:
                # Limit images per person to 20
                if len(memories_by_person[cluster_id]["images"]) < 20:
                    metadata_dict = image_util_parse_metadata(metadata)
                    memories_by_person[cluster_id]["images"].append(
                        {
                            "id": image_id,
                            "path": path,
                            "thumbnailPath": thumbnail_path,
                            "metadata": metadata_dict,
                            "isTagged": bool(is_tagged),
                            "tags": [tag_name] if tag_name else [],
                        }
                    )

        # Convert to list and limit to requested number
        memories_list = list(memories_by_person.values())[:limit]

        return memories_list

    except Exception as e:
        logger.error(f"Error getting memories by people: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


def db_get_memories_by_tags(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get memories grouped by common tags/objects.

    Args:
        limit: Maximum number of tag memories to return (default: 10)

    Returns:
        List of dictionaries containing memory data grouped by tag
    """
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                m.name as tag_name,
                m.class_id,
                COUNT(DISTINCT ic.image_id) as image_count,
                i.id,
                i.path,
                i.thumbnailPath,
                i.metadata,
                i.isTagged
            FROM mappings m
            JOIN image_classes ic ON m.class_id = ic.class_id
            JOIN images i ON ic.image_id = i.id
            GROUP BY m.class_id, i.id
            HAVING image_count >= 5
            ORDER BY image_count DESC, m.name
            LIMIT ?
            """,
            (limit * 15,),  # Get more to ensure we have enough after grouping
        )

        results = cursor.fetchall()

        from app.utils.images import image_util_parse_metadata

        memories_by_tag = {}

        for (
            tag_name,
            class_id,
            image_count,
            image_id,
            path,
            thumbnail_path,
            metadata,
            is_tagged,
        ) in results:
            if class_id not in memories_by_tag:
                memories_by_tag[class_id] = {
                    "tag_name": tag_name,
                    "image_count": image_count,
                    "images": [],
                }

            # Limit images per tag to 20
            if len(memories_by_tag[class_id]["images"]) < 20:
                metadata_dict = image_util_parse_metadata(metadata)
                memories_by_tag[class_id]["images"].append(
                    {
                        "id": image_id,
                        "path": path,
                        "thumbnailPath": thumbnail_path,
                        "metadata": metadata_dict,
                        "isTagged": bool(is_tagged),
                        "tags": [tag_name] if tag_name else [],
                    }
                )

        # Convert to list and limit to requested number
        memories_list = list(memories_by_tag.values())[:limit]

        return memories_list

    except Exception as e:
        logger.error(f"Error getting memories by tags: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()
