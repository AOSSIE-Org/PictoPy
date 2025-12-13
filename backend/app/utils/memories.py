"""
Memory generation utility for clustering photos by date and location.

This module generates memories by:
1. Clustering photos by date similarity (same day, month, year, or "on this day" from past years)
2. Clustering photos by geographic proximity
3. Creating memory objects with representative media subsets
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import math
from app.database.images import db_get_all_images
from app.utils.images import image_util_parse_metadata
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# Constants for clustering
DATE_CLUSTER_THRESHOLD_DAYS = 7  # Photos within 7 days are considered same event
LOCATION_CLUSTER_THRESHOLD_KM = 10  # Photos within 10km are considered same location
REPRESENTATIVE_MEDIA_COUNT = 6  # Number of thumbnails to show per memory


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in kilometers.
    Uses the Haversine formula.
    """
    # Earth radius in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO date string to datetime object."""
    if not date_str:
        return None
    try:
        # Handle ISO format with or without microseconds
        if "T" in date_str:
            date_str = date_str.split("T")[0] + " " + date_str.split("T")[1].split(".")[0]
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        try:
            # Try just date
            return datetime.strptime(date_str.split(" ")[0], "%Y-%m-%d")
        except (ValueError, AttributeError):
            return None


def _format_memory_title(
    memory_type: str, date: Optional[datetime], location: Optional[str]
) -> str:
    """
    Generate a human-readable title for a memory.
    
    Examples:
    - "On this day, 2023"
    - "Trip to Jaipur, 2023"
    - "December 2023"
    - "Summer 2023"
    """
    if memory_type == "on_this_day" and date:
        return f"On this day, {date.year}"
    elif memory_type == "trip" and location and date:
        return f"Trip to {location}, {date.year}"
    elif memory_type == "trip" and date:
        return f"Trip, {date.strftime('%B %Y')}"
    elif memory_type == "date_cluster" and date:
        # Same day
        today = datetime.now()
        if date.date() == today.date():
            return "Today"
        elif date.date() == (today - timedelta(days=1)).date():
            return "Yesterday"
        else:
            return date.strftime("%B %d, %Y")
    elif memory_type == "month_cluster" and date:
        return date.strftime("%B %Y")
    elif memory_type == "year_cluster" and date:
        return str(date.year)
    else:
        return "Memory"


def _get_location_name(lat: float, lon: float) -> str:
    """
    Get a human-readable location name from coordinates.
    For now, returns a simple format. Can be enhanced with reverse geocoding.
    """
    # Simple format: "Location (lat, lon)"
    # In production, this could use a reverse geocoding service
    return f"Location ({lat:.4f}, {lon:.4f})"


def _cluster_by_date(images: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    Cluster images by date similarity.
    Returns list of clusters, each containing images from similar dates.
    """
    # Group by date (same day)
    date_groups = defaultdict(list)
    for img in images:
        metadata = img.get("metadata", {})
        date_str = metadata.get("date_created")
        date = _parse_date(date_str)
        if date:
            date_key = date.date()  # Group by date only
            date_groups[date_key].append(img)

    # Convert to list of clusters
    clusters = []
    for date_key, imgs in date_groups.items():
        if len(imgs) >= 2:  # Only create clusters with 2+ images
            clusters.append(imgs)

    return clusters


def _cluster_by_location(images: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    Cluster images by geographic proximity.
    Uses simple distance-based clustering.
    """
    # Filter images with valid GPS coordinates
    geo_images = []
    for img in images:
        metadata = img.get("metadata", {})
        lat = metadata.get("latitude")
        lon = metadata.get("longitude")
        if lat is not None and lon is not None:
            geo_images.append((img, lat, lon))

    if len(geo_images) < 2:
        return []

    # Simple clustering: group images that are close to each other
    clusters = []
    used = set()

    for i, (img1, lat1, lon1) in enumerate(geo_images):
        if i in used:
            continue

        cluster = [img1]
        used.add(i)

        for j, (img2, lat2, lon2) in enumerate(geo_images):
            if j in used or i == j:
                continue

            distance = _haversine_distance(lat1, lon1, lat2, lon2)
            if distance <= LOCATION_CLUSTER_THRESHOLD_KM:
                cluster.append(img2)
                used.add(j)

        if len(cluster) >= 2:
            clusters.append(cluster)

    return clusters


def _get_on_this_day_memories(images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate "On this day" memories - photos from the same date in past years.
    """
    today = datetime.now()
    memories = []

    # Group images by month-day (ignoring year)
    month_day_groups = defaultdict(list)
    for img in images:
        metadata = img.get("metadata", {})
        date_str = metadata.get("date_created")
        date = _parse_date(date_str)
        if date and date.year < today.year:  # Only past years
            month_day_key = (date.month, date.day)
            month_day_groups[month_day_key].append((img, date))

    # Check if today's month-day matches any past year
    today_key = (today.month, today.day)
    if today_key in month_day_groups:
        past_images = month_day_groups[today_key]
        if len(past_images) >= 2:
            # Get the most recent year's images
            past_images.sort(key=lambda x: x[1], reverse=True)
            images_for_memory = [img for img, _ in past_images[:20]]  # Limit to 20

            # Get representative subset
            representative = images_for_memory[:REPRESENTATIVE_MEDIA_COUNT]

            # Get date range
            dates = [date for _, date in past_images]
            min_date = min(dates)
            max_date = max(dates)

            memory = {
                "id": f"on_this_day_{min_date.year}",
                "title": _format_memory_title("on_this_day", min_date, None),
                "type": "on_this_day",
                "date_range": {
                    "start": min_date.isoformat(),
                    "end": max_date.isoformat(),
                },
                "location": None,
                "media_count": len(images_for_memory),
                "representative_media": [
                    {
                        "id": img["id"],
                        "thumbnailPath": img["thumbnailPath"],
                    }
                    for img in representative
                ],
                "media_ids": [img["id"] for img in images_for_memory],
            }
            memories.append(memory)

    return memories


def _create_memory_from_cluster(
    cluster: List[Dict[str, Any]],
    memory_type: str,
    cluster_id: str,
) -> Dict[str, Any]:
    """
    Create a memory object from a cluster of images.
    """
    if not cluster:
        return None

    # Get dates from cluster
    dates = []
    locations = []
    for img in cluster:
        metadata = img.get("metadata", {})
        date_str = metadata.get("date_created")
        date = _parse_date(date_str)
        if date:
            dates.append(date)

        lat = metadata.get("latitude")
        lon = metadata.get("longitude")
        if lat is not None and lon is not None:
            locations.append((lat, lon))

    # Determine date range
    if dates:
        min_date = min(dates)
        max_date = max(dates)
    else:
        min_date = max_date = datetime.now()

    # Determine location (average if multiple)
    location = None
    if locations:
        avg_lat = sum(lat for lat, _ in locations) / len(locations)
        avg_lon = sum(lon for _, lon in locations) / len(locations)
        location = _get_location_name(avg_lat, avg_lon)

    # Get representative subset
    representative = cluster[:REPRESENTATIVE_MEDIA_COUNT]

    return {
        "id": cluster_id,
        "title": _format_memory_title(memory_type, min_date, location),
        "type": memory_type,
        "date_range": {
            "start": min_date.isoformat(),
            "end": max_date.isoformat(),
        },
        "location": location,
        "media_count": len(cluster),
        "representative_media": [
            {
                "id": img["id"],
                "thumbnailPath": img["thumbnailPath"],
            }
            for img in representative
        ],
        "media_ids": [img["id"] for img in cluster],
    }


def generate_memories() -> List[Dict[str, Any]]:
    """
    Main function to generate all memories from images in the database.
    Returns a list of memory objects.
    """
    try:
        # Get all images from database
        all_images = db_get_all_images()

        if not all_images:
            logger.info("No images found in database")
            return []

        # Parse metadata for all images
        images_with_metadata = []
        for img in all_images:
            metadata = image_util_parse_metadata(img.get("metadata"))
            img["metadata"] = metadata
            images_with_metadata.append(img)

        memories = []

        # 1. Generate "On this day" memories
        on_this_day = _get_on_this_day_memories(images_with_metadata)
        memories.extend(on_this_day)

        # 2. Cluster by location (trips)
        location_clusters = _cluster_by_location(images_with_metadata)
        for idx, cluster in enumerate(location_clusters):
            memory = _create_memory_from_cluster(
                cluster, "trip", f"trip_{idx}"
            )
            if memory:
                memories.append(memory)

        # 3. Cluster by date (same day events)
        date_clusters = _cluster_by_date(images_with_metadata)
        for idx, cluster in enumerate(date_clusters):
            # Skip if already in a location cluster
            cluster_ids = {img["id"] for img in cluster}
            already_in_memory = any(
                any(img_id in m["media_ids"] for img_id in cluster_ids)
                for m in memories
            )
            if not already_in_memory:
                memory = _create_memory_from_cluster(
                    cluster, "date_cluster", f"date_{idx}"
                )
                if memory:
                    memories.append(memory)

        # Sort memories by date (most recent first)
        memories.sort(
            key=lambda m: m["date_range"]["end"], reverse=True
        )

        logger.info(f"Generated {len(memories)} memories")
        return memories

    except Exception as e:
        logger.error(f"Error generating memories: {e}", exc_info=True)
        return []

