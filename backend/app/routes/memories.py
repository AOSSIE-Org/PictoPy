"""
Memories API Routes

This module provides REST API endpoints for the Memories feature, which groups
photos by location and time into meaningful collections.

Endpoints:
- POST /api/memories/generate - Generate memories from all images with location data
- GET /api/memories/timeline - Get memories from past N days
- GET /api/memories/on-this-day - Get photos from this date in previous years
- GET /api/memories/locations - Get all unique locations where photos were taken

Author: PictoPy Team
Date: 2025-12-14
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database.images import (
    db_get_images_with_location,
    db_get_images_by_date_range,
    db_get_images_by_year_month,
)
from app.utils.memory_clustering import MemoryClustering
from app.logging.setup_logging import get_logger

# Initialize router and logger
router = APIRouter(prefix="/api/memories", tags=["memories"])
logger = get_logger(__name__)


# Response Models


class MemoryImage(BaseModel):
    """Image within a memory."""

    id: str
    path: str
    thumbnailPath: str
    latitude: Optional[float]
    longitude: Optional[float]
    captured_at: Optional[str]
    isFavourite: Optional[bool] = False  # Add favorite status


class Memory(BaseModel):
    """Memory object containing grouped images."""

    memory_id: str
    title: str
    description: str
    location_name: str
    date_start: Optional[str]
    date_end: Optional[str]
    image_count: int
    images: List[MemoryImage]
    thumbnail_image_id: str
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None
    type: Literal["location", "date"]  # Memory clustering type


class GenerateMemoriesResponse(BaseModel):
    """Response for generate memories endpoint."""

    success: bool
    message: str
    memory_count: int
    image_count: int
    memories: List[Memory]


class TimelineResponse(BaseModel):
    """Response for timeline endpoint."""

    success: bool
    date_range: Dict[str, str]
    memory_count: int
    memories: List[Memory]


class OnThisDayResponse(BaseModel):
    """Response for on-this-day endpoint."""

    success: bool
    today: str
    years: List[int]
    image_count: int
    images: List[MemoryImage]


class LocationCluster(BaseModel):
    """Location cluster with photo count."""

    location_name: str
    center_lat: float
    center_lon: float
    image_count: int
    sample_images: List[MemoryImage]


class LocationsResponse(BaseModel):
    """Response for locations endpoint."""

    success: bool
    location_count: int
    locations: List[LocationCluster]


# API Endpoints


@router.post("/generate")
def generate_memories(
    location_radius_km: float = Query(
        5.0, ge=0.1, le=100, description="Location clustering radius in km"
    ),
    date_tolerance_days: int = Query(
        3, ge=1, le=30, description="Date tolerance in days"
    ),
    min_images: int = Query(2, ge=1, le=10, description="Minimum images per memory"),
):
    """
    SIMPLIFIED: Generate memories from ALL images.
    - GPS images → location-based memories
    - Non-GPS images → monthly date-based memories

    Returns simple breakdown: {location_count, date_count, total}
    """
    try:
        logger.info(
            f"Generating memories: radius={location_radius_km}km, date_tolerance={date_tolerance_days}days, min_images={min_images}"
        )

        # Fetch ALL images
        from app.database.images import db_get_all_images_for_memories

        images = db_get_all_images_for_memories()

        if not images:
            return {
                "data": {
                    "memory_count": 0,
                    "image_count": 0,
                    "memories": [],
                },
                "success": True,
                "message": "No images found",
            }

        logger.info(f"Processing {len(images)} images")

        # Cluster into memories
        clustering = MemoryClustering(
            location_radius_km=location_radius_km,
            date_tolerance_days=date_tolerance_days,
            min_images_per_memory=min_images,
        )

        memories = clustering.cluster_memories(images)

        # Calculate breakdown
        location_count = sum(1 for m in memories if m.get("type") == "location")
        date_count = sum(1 for m in memories if m.get("type") == "date")

        logger.info(
            f"Generated {len(memories)} memories (location: {location_count}, date: {date_count})"
        )

        return {
            "data": {
                "memory_count": len(memories),
                "image_count": len(images),
                "memories": memories,
            },
            "success": True,
            "message": f"{len(memories)} memories ({location_count} location, {date_count} date)",
        }

    except Exception:
        logger.error("Error generating memories", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate memories")


@router.get("/timeline")
def get_timeline(
    days: int = Query(365, ge=1, le=3650, description="Number of days to look back"),
    location_radius_km: float = Query(
        5.0, ge=0.1, le=100, description="Location clustering radius in km"
    ),
    date_tolerance_days: int = Query(
        3, ge=1, le=30, description="Date tolerance in days"
    ),
):
    """
    Get memories from the past N days as a timeline.

    This endpoint:
    1. Calculates date range (today - N days to today)
    2. Fetches images within that date range
    3. Clusters them into memories
    4. Returns timeline of memories

    Args:
        days: Number of days to look back (default: 365 = 1 year)
        location_radius_km: Location clustering radius (default: 5km)
        date_tolerance_days: Date tolerance for temporal clustering (default: 3)

    Returns:
        TimelineResponse with memories ordered by date

    Raises:
        HTTPException: If database query fails
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Getting timeline from {start_date.date()} to {end_date.date()}")

        # Fetch images within date range
        images = db_get_images_by_date_range(start_date, end_date)

        if not images:
            return {
                "data": {
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                    },
                    "memory_count": 0,
                    "memories": [],
                },
                "success": True,
                "message": "No images found in date range",
            }

        logger.info(f"Found {len(images)} images in date range")

        # Cluster into memories
        clustering = MemoryClustering(
            location_radius_km=location_radius_km,
            date_tolerance_days=date_tolerance_days,
            min_images_per_memory=1,  # Allow single images in timeline
        )

        memories = clustering.cluster_memories(images)

        return {
            "data": {
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "memory_count": len(memories),
                "memories": memories,
            },
            "success": True,
            "message": f"Found {len(memories)} memories",
        }

    except Exception:
        logger.error("Error getting timeline", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get timeline")


@router.get("/on-this-day")
def get_on_this_day():
    """
    Get photos taken on this date in previous years.

    This endpoint:
    1. Gets current month and day
    2. Searches for images from this month-day in all previous years
    3. Groups by year
    4. Returns images sorted by year (most recent first)

    Returns:
        OnThisDayResponse with images from this date in previous years

    Raises:
        HTTPException: If database query fails
    """
    try:
        today = datetime.now()
        current_month = today.month
        current_day = today.day

        logger.info(f"Getting 'On This Day' for {today.strftime('%B %d')}")

        # Search for images from this month-day in past years
        # Go back 10 years maximum
        all_images = []
        years_found = []

        for year_offset in range(1, 11):  # 1-10 years ago
            target_year = today.year - year_offset

            try:
                images = db_get_images_by_year_month(target_year, current_month)

                # Filter to specific day - parse each image defensively
                day_images = []
                for img in images:
                    captured_at_str = img.get("captured_at")
                    if not captured_at_str:
                        continue

                    try:
                        # Strip trailing Z and parse ISO format
                        captured_at_str = captured_at_str.rstrip("Z")
                        captured_dt = datetime.fromisoformat(captured_at_str)

                        # Only include if day matches
                        if captured_dt.day == current_day:
                            day_images.append(img)
                    except (ValueError, TypeError, AttributeError):
                        # Skip images with malformed dates
                        logger.debug(
                            f"Skipping image with invalid date: {captured_at_str}"
                        )
                        continue

                if day_images:
                    all_images.extend(day_images)
                    years_found.append(target_year)
                    logger.info(f"Found {len(day_images)} images from {target_year}")

            except Exception as e:
                logger.warning(f"Error querying year {target_year}: {e}")
                continue

        # Sort by year (most recent first)
        def parse_captured_at(img):
            """Safely parse captured_at date, return datetime.min on failure."""
            captured_at = img.get("captured_at")
            if not captured_at:
                return datetime.min
            try:

                if isinstance(captured_at, str):
                    captured_at = captured_at.rstrip("Z")
                return datetime.fromisoformat(captured_at)
            except (ValueError, TypeError, AttributeError):
                return datetime.min

        all_images.sort(key=parse_captured_at, reverse=True)

        return {
            "data": {
                "today": today.strftime("%B %d"),
                "years": sorted(years_found, reverse=True),
                "image_count": len(all_images),
                "images": all_images,
            },
            "success": True,
            "message": f"Found {len(all_images)} images from {len(years_found)} years",
        }

    except Exception:
        logger.error("Error getting 'On This Day'", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get 'On This Day'")


@router.get("/locations")
def get_locations(
    location_radius_km: float = Query(
        5.0, ge=0.1, le=100, description="Location clustering radius in km"
    ),
    max_sample_images: int = Query(
        5, ge=1, le=20, description="Max sample images per location"
    ),
):
    """
    Get all unique locations where photos were taken.

    This endpoint:
    1. Fetches all images with GPS coordinates
    2. Clusters them by location
    3. Returns location clusters with photo counts
    4. Includes sample images for each location

    Args:
        location_radius_km: Location clustering radius (default: 5km)
        max_sample_images: Maximum sample images per location (default: 5)

    Returns:
        LocationsResponse with list of location clusters

    Raises:
        HTTPException: If database query fails
    """
    try:
        logger.info(f"Getting locations with radius={location_radius_km}km")

        # Fetch all images with location data
        images = db_get_images_with_location()

        if not images:
            return {
                "data": {"location_count": 0, "locations": []},
                "success": True,
                "message": "No images with location data",
            }

        logger.info(f"Found {len(images)} images with location data")

        # Cluster by location only (no date clustering)
        clustering = MemoryClustering(
            location_radius_km=location_radius_km,
            date_tolerance_days=3,
            min_images_per_memory=1,
        )

        # Get location clusters using public API
        location_clusters = clustering.cluster_by_location_only(images)

        # Create location cluster objects
        locations = []
        for cluster_images in location_clusters:
            if not cluster_images:
                continue

            # Calculate center
            center_lat = sum(img["latitude"] for img in cluster_images) / len(
                cluster_images
            )
            center_lon = sum(img["longitude"] for img in cluster_images) / len(
                cluster_images
            )

            # Get location name
            location_name = clustering._reverse_geocode(center_lat, center_lon)

            # Get sample images (up to max_sample_images)
            sample_images = cluster_images[:max_sample_images]

            locations.append(
                LocationCluster(
                    location_name=location_name,
                    center_lat=center_lat,
                    center_lon=center_lon,
                    image_count=len(cluster_images),
                    sample_images=sample_images,
                )
            )

        # Sort by image count (most photos first)
        locations.sort(key=lambda loc: loc.image_count, reverse=True)

        return {
            "data": {
                "location_count": len(locations),
                "locations": locations,
            },
            "success": True,
            "message": f"Found {len(locations)} locations",
        }

    except Exception:
        logger.error("Error getting locations", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get locations")
