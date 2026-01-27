"""
Memory Clustering Algorithm

This module groups images into "memories" based on spatial proximity (location)
and temporal proximity (date/time). Uses DBSCAN for spatial clustering and
date-based grouping for temporal clustering.

A "memory" is a collection of photos taken at the same place around the same time.

Author: PictoPy Team
Date: 2025-12-14
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

import numpy as np
from sklearn.cluster import DBSCAN

from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


# ============================================================================
# City Coordinate Mapping for Reverse Geocoding
# ============================================================================

# Major city coordinates for approximate reverse geocoding
CITY_COORDINATES = {
    # India - Major Cities
    "Jaipur, Rajasthan": (26.9124, 75.7873),
    "Delhi, India": (28.7041, 77.1025),
    "Mumbai, Maharashtra": (19.0760, 72.8777),
    "Bangalore, Karnataka": (12.9716, 77.5946),
    "Kolkata, West Bengal": (22.5726, 88.3639),
    "Chennai, Tamil Nadu": (13.0827, 80.2707),
    "Hyderabad, Telangana": (17.3850, 78.4867),
    "Pune, Maharashtra": (18.5204, 73.8567),
    "Ahmedabad, Gujarat": (23.0225, 72.5714),
    "Goa, India": (15.2993, 74.1240),
    "Agra, Uttar Pradesh": (27.1767, 78.0081),
    "Udaipur, Rajasthan": (24.5854, 73.7125),
    "Jaisalmer, Rajasthan": (26.9157, 70.9083),
    "Varanasi, Uttar Pradesh": (25.3176, 82.9739),
    "Rishikesh, Uttarakhand": (30.0869, 78.2676),
    "Shimla, Himachal Pradesh": (31.1048, 77.1734),
    "Manali, Himachal Pradesh": (32.2432, 77.1892),
    "Darjeeling, West Bengal": (27.0410, 88.2663),
    "Ooty, Tamil Nadu": (11.4102, 76.6950),
    "Coorg, Karnataka": (12.3375, 75.8069),
    # International - Major Tourist Destinations
    "Paris, France": (48.8566, 2.3522),
    "London, UK": (51.5074, -0.1278),
    "New York, USA": (40.7128, -74.0060),
    "Tokyo, Japan": (35.6762, 139.6503),
    "Dubai, UAE": (25.2048, 55.2708),
    "Singapore": (1.3521, 103.8198),
    "Bangkok, Thailand": (13.7563, 100.5018),
    "Bali, Indonesia": (-8.4095, 115.1889),
    "Sydney, Australia": (-33.8688, 151.2093),
    "Rome, Italy": (41.9028, 12.4964),
}


def find_nearest_city(latitude: float, longitude: float, max_distance_km: float = 50.0) -> Optional[str]:
    """
    Find the nearest known city to given coordinates.

    Args:
        latitude: GPS latitude
        longitude: GPS longitude
        max_distance_km: Maximum distance to consider (default: 50km)

    Returns:
        City name if within range, None otherwise
    """
    from math import radians, cos, sin, asin, sqrt

    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km using Haversine formula."""
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        km = 6371 * c  # Radius of Earth in km
        return km

    nearest_city = None
    min_distance = float("inf")

    for city_name, (city_lat, city_lon) in CITY_COORDINATES.items():
        distance = haversine_distance(latitude, longitude, city_lat, city_lon)
        if distance < min_distance and distance <= max_distance_km:
            min_distance = distance
            nearest_city = city_name

    return nearest_city


class MemoryClustering:
    """
    Clusters images into memories based on location and time proximity.

    Algorithm:
    1. Spatial clustering: Group images by GPS coordinates using DBSCAN
    2. Temporal clustering: Within each location cluster, group by date
    3. Memory creation: Generate memory objects with metadata

    Parameters:
        location_radius_km: Maximum distance between photos in the same location (default: 5km)
        date_tolerance_days: Maximum days between photos in the same memory (default: 3)
        min_images_per_memory: Minimum images required to form a memory (default: 2)
    """

    def __init__(
        self,
        location_radius_km: float = 5.0,
        date_tolerance_days: int = 3,
        min_images_per_memory: int = 2,
    ):
        """Initialize the memory clustering algorithm."""
        self.location_radius_km = location_radius_km
        self.date_tolerance_days = date_tolerance_days
        self.min_images_per_memory = min_images_per_memory

        # Convert km to radians for DBSCAN with haversine metric
        # Earth radius in kilometers
        EARTH_RADIUS_KM = 6371.0
        self.location_eps_radians = location_radius_km / EARTH_RADIUS_KM

        logger.info(f"MemoryClustering initialized: radius={location_radius_km}km, date_tolerance={date_tolerance_days}days, min_images={min_images_per_memory}")

    def cluster_memories(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        FLEXIBLE: Cluster ALL images into memories.
        - Has GPS + Date: Cluster by location using DBSCAN, then by date within each location
        - Has GPS only: Cluster by location using DBSCAN
        - Has Date only: Group by month (if ≥5 photos per month)
        - Has neither: Skip (can't create meaningful memory)

        Images work with EITHER date OR location - not both required!

        Args:
            images: List of image dicts with id, path, thumbnailPath,
                   latitude, longitude, captured_at

        Returns:
            List of memories with type='location' or type='date'
        """
        logger.info(f"Starting flexible clustering for {len(images)} images")

        if not images:
            return []

        try:
            # Separate images by what data they have
            gps_images = []
            date_only_images = []
            skipped_count = 0

            for img in images:
                has_gps = img.get("latitude") is not None and img.get("longitude") is not None
                has_date = img.get("captured_at")

                if has_gps:
                    # Has GPS (with or without date) → location-based clustering
                    gps_images.append(img)
                elif has_date:
                    # Has date but no GPS → date-based grouping
                    date_only_images.append(img)
                else:
                    # Has neither GPS nor date → skip
                    skipped_count += 1

            logger.info(f"GPS-based: {len(gps_images)}, Date-only: {len(date_only_images)}, Skipped: {skipped_count}")

            memories = []

            # Process location-based memories (these may also have dates)
            if gps_images:
                location_memories = self._cluster_location_images(gps_images)
                memories.extend(location_memories)

            # Process date-only memories (no GPS)
            if date_only_images:
                date_memories = self._cluster_date_images(date_only_images)
                memories.extend(date_memories)

            # Sort by date descending
            memories.sort(key=lambda m: m.get("date_start") or "", reverse=True)

            logger.info(f"Generated {len(memories)} total memories")
            return memories

        except Exception as e:
            logger.error(f"Clustering failed: {e}", exc_info=True)
            return []

    def _cluster_location_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        SIMPLIFIED: Use existing DBSCAN clustering for GPS images.
        """
        try:
            valid_images = self._filter_valid_images(images)
            if not valid_images:
                return []

            location_clusters = self._cluster_by_location(valid_images)
            memories = []

            for cluster in location_clusters:
                temporal_clusters = self._cluster_by_date(cluster)
                for temp_cluster in temporal_clusters:
                    if len(temp_cluster) >= self.min_images_per_memory:
                        memory = self._create_simple_memory(temp_cluster, memory_type="location")
                        if memory is not None:
                            memories.append(memory)

            return memories
        except Exception as e:
            logger.error(f"Location clustering failed: {e}")
            return []

    def _cluster_date_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        FLEXIBLE: Group date-only images by year-month.
        Uses min_images_per_memory (default: 2) as threshold.
        """
        try:
            # Group by year-month
            monthly_groups = defaultdict(list)

            for img in images:
                captured_at = img.get("captured_at")
                if not captured_at:
                    continue

                # Parse date
                if isinstance(captured_at, str):
                    try:
                        dt = datetime.fromisoformat(captured_at.replace("Z", ""))
                    except (ValueError, AttributeError):
                        continue
                elif isinstance(captured_at, datetime):
                    dt = captured_at
                else:
                    continue

                # Group by year-month
                month_key = dt.strftime("%Y-%m")
                monthly_groups[month_key].append(img)

            # Create memories for months with enough photos (uses min_images_per_memory)
            memories = []
            for month_key, month_images in monthly_groups.items():
                if len(month_images) >= self.min_images_per_memory:
                    memory = self._create_simple_memory(month_images, memory_type="date")
                    if memory:
                        memories.append(memory)

            return memories
        except Exception as e:
            logger.error(f"Date clustering failed: {e}")
            return []

    def _create_simple_memory(self, images: List[Dict[str, Any]], memory_type: str = "location") -> Dict[str, Any]:
        """
        SIMPLIFIED: Create a memory object with minimal fields.
        Ensures all datetime objects are converted to ISO strings.
        """
        try:
            # Convert datetime objects to ISO strings in images
            cleaned_images = []
            for img in images:
                img_copy = img.copy()
                if img_copy.get("captured_at") and isinstance(img_copy["captured_at"], datetime):
                    img_copy["captured_at"] = img_copy["captured_at"].isoformat()
                cleaned_images.append(img_copy)

            # Sort by date
            sorted_images = sorted(cleaned_images, key=lambda x: x.get("captured_at", ""))

            # Get date range
            dates = [img.get("captured_at") for img in sorted_images if img.get("captured_at")]
            if dates:
                if isinstance(dates[0], str):
                    dates = [datetime.fromisoformat(d.replace("Z", "")) for d in dates]
                date_start = min(dates).isoformat()
                date_end = max(dates).isoformat()
                date_obj = min(dates)
            else:
                date_start = date_end = None
                date_obj = None 

            # Simple titles
            if memory_type == "location":
                # Calculate center first
                lats = [img["latitude"] for img in images if img.get("latitude") is not None]
                lons = [img["longitude"] for img in images if img.get("longitude") is not None]
                center_lat = np.mean(lats) if lats else 0
                center_lon = np.mean(lons) if lons else 0

                # Get actual location name using reverse geocoding
                location_name = self._reverse_geocode(center_lat, center_lon)

                # Create title based on date range
                if len(dates) > 1:
                    # Multiple dates: show date range
                    start_date = min(dates)
                    end_date = max(dates)
                    if start_date.strftime("%B %Y") == end_date.strftime("%B %Y"):
                        # Same month: "Jaipur in Nov 2025"
                        title = f"{location_name} in {start_date.strftime('%b %Y')}"
                    else:
                        # Different months: "Jaipur - Nov-Dec 2025" or "Jaipur - Nov 2025 to Jan 2026"
                        if start_date.year == end_date.year:
                            title = f"{location_name} - {start_date.strftime('%b')}-{end_date.strftime('%b %Y')}"
                        else:
                            title = f"{location_name} - {start_date.strftime('%b %Y')} to {end_date.strftime('%b %Y')}"
                else:
                    # Single date or no dates: just the location name
                    title = location_name
            else:
                # Date-based: "Month Year"
                if date_obj:
                    title = date_obj.strftime("%B %Y")
                else:
                    title = "Undated Photos"  
                location_name = ""
                center_lat = 0
                center_lon = 0

            # Create memory - use _generate_memory_id for unique IDs
            memory_id = self._generate_memory_id(center_lat, center_lon, date_obj)

            return {
                "memory_id": memory_id,
                "title": title,
                "description": f"{len(images)} photos",
                "location_name": location_name,
                "date_start": date_start,
                "date_end": date_end,
                "image_count": len(images),
                "images": sorted_images,
                "thumbnail_image_id": sorted_images[0].get("id", ""),
                "center_lat": center_lat,
                "center_lon": center_lon,
                "type": memory_type,  # Add type field
            }
        except Exception as e:
            logger.error(f"Memory creation failed: {e}")
            return None

    def _cluster_gps_based_memories(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cluster images with GPS data into location-based memories.
        This is the original clustering logic.

        Args:
            images: List of images with GPS coordinates

        Returns:
            List of location-based memories
        """
        # Filter images with valid location data
        valid_images = self._filter_valid_images(images)

        if not valid_images:
            logger.warning("No images with valid location data")
            return []

        logger.info(f"Processing {len(valid_images)} GPS images")

        # Step 1: Cluster by location (spatial)
        location_clusters = self._cluster_by_location(valid_images)
        logger.info(f"Created {len(location_clusters)} location clusters")

        # Step 2: Within each location cluster, cluster by date (temporal)
        memories = []
        for location_cluster in location_clusters:
            temporal_clusters = self._cluster_by_date(location_cluster)

            # Step 3: Create memory objects
            for temporal_cluster in temporal_clusters:
                if len(temporal_cluster) >= self.min_images_per_memory:
                    memory = self._create_memory(temporal_cluster)
                    memories.append(memory)

        return memories

    def _cluster_date_based_memories(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cluster images WITHOUT GPS data into date-based memories.
        Groups photos by capture date/time only (screenshots, downloads, edits, etc.)

        Args:
            images: List of images without GPS coordinates

        Returns:
            List of date-based memories
        """
        logger.info(f"Clustering {len(images)} non-GPS images by date")

        # Parse and filter images with valid dates
        valid_images = []
        for img in images:
            img_copy = img.copy()
            captured_at = img_copy.get("captured_at")

            if captured_at:
                if isinstance(captured_at, str):
                    try:
                        captured_at = datetime.fromisoformat(captured_at.replace("Z", ""))
                        img_copy["captured_at"] = captured_at
                    except Exception:
                        # Try alternative formats
                        for fmt in [
                            "%Y-%m-%d %H:%M:%S",
                            "%Y:%m:%d %H:%M:%S",
                            "%Y-%m-%d",
                        ]:
                            try:
                                captured_at = datetime.strptime(captured_at, fmt)
                                img_copy["captured_at"] = captured_at
                                break
                            except Exception:
                                continue
                        else:
                            logger.debug(f"Could not parse date for image {img.get('id')}")
                            continue
                elif isinstance(captured_at, datetime):
                    img_copy["captured_at"] = captured_at

                valid_images.append(img_copy)

        if not valid_images:
            logger.warning("No non-GPS images with valid dates")
            return []

        logger.info(f"Found {len(valid_images)} non-GPS images with valid dates")

        # Sort by date
        valid_images.sort(key=lambda x: x["captured_at"])

        # Group by date tolerance
        clusters = []
        current_cluster = [valid_images[0]]

        for i in range(1, len(valid_images)):
            prev_date = valid_images[i - 1]["captured_at"]
            curr_date = valid_images[i]["captured_at"]

            # Check if within tolerance
            date_diff = abs((curr_date - prev_date).days)

            if date_diff <= self.date_tolerance_days:
                current_cluster.append(valid_images[i])
            else:
                # Create memory from current cluster if it meets min size
                if len(current_cluster) >= self.min_images_per_memory:
                    clusters.append(current_cluster)
                # Start new cluster
                current_cluster = [valid_images[i]]

        # Add last cluster if it meets min size
        if current_cluster and len(current_cluster) >= self.min_images_per_memory:
            clusters.append(current_cluster)

        logger.info(f"Created {len(clusters)} date-based clusters")

        # Create memory objects
        memories = []
        for cluster in clusters:
            memory = self._create_date_based_memory(cluster)
            memories.append(memory)

        return memories

    def _create_date_based_memory(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a date-based memory object for images without GPS.

        Args:
            images: List of image dictionaries in the cluster (no GPS)

        Returns:
            Memory dictionary with metadata
        """
        # Get date range
        dates = [img["captured_at"] for img in images if img.get("captured_at")]
        date_start = min(dates) if dates else None
        date_end = max(dates) if dates else None

        # Generate title for date-based memory
        if date_start:
            if date_start.date() == date_end.date():
                title = date_start.strftime("%B %d, %Y")
            else:
                days = (date_end - date_start).days + 1
                if days <= 7:
                    title = date_start.strftime("%B %d, %Y")
                elif days <= 31:
                    title = date_start.strftime("%B %Y")
                else:
                    title = date_start.strftime("%B - %B %Y") if date_start.month != date_end.month else date_start.strftime("%B %Y")
        else:
            title = "Memories Collection"

        # Generate description
        description = self._generate_description(len(images), date_start, date_end)

        # Select thumbnail (middle image)
        thumbnail_idx = len(images) // 2
        thumbnail_image_id = images[thumbnail_idx]["id"]

        # Create memory ID (use timestamp only)
        memory_id = f"mem_date_{date_start.strftime('%Y%m%d')}" if date_start else f"mem_date_unknown_{hash(tuple(img['id'] for img in images[:5]))}"

        # Convert captured_at datetime objects to ISO strings
        serialized_images = []
        for img in images:
            img_copy = img.copy()
            if img_copy.get("captured_at") and isinstance(img_copy["captured_at"], datetime):
                img_copy["captured_at"] = img_copy["captured_at"].isoformat()
            serialized_images.append(img_copy)

        return {
            "memory_id": memory_id,
            "title": title,
            "description": description,
            "location_name": "Date-Based Memory",  # Identifier for non-GPS memories
            "date_start": date_start.isoformat() if date_start else None,
            "date_end": date_end.isoformat() if date_end else None,
            "image_count": len(images),
            "images": serialized_images,
            "thumbnail_image_id": thumbnail_image_id,
            "center_lat": 0.0,  # No GPS data
            "center_lon": 0.0,  # No GPS data
        }

    def _filter_valid_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter images that have valid location and datetime data.

        Args:
            images: List of image dictionaries

        Returns:
            List of valid images with parsed datetime objects
        """
        valid_images = []

        for img in images:
            try:
                # Check for required fields
                if img.get("latitude") is None or img.get("longitude") is None:
                    continue

                # Parse captured_at if it's a string
                captured_at = img.get("captured_at")
                img_copy = img.copy()

                if captured_at:
                    if isinstance(captured_at, str):
                        try:
                            # SQLite returns ISO format: "YYYY-MM-DDTHH:MM:SS"
                            captured_at = datetime.fromisoformat(captured_at.replace("Z", ""))
                            img_copy["captured_at"] = captured_at
                        except Exception:
                            # Try alternative formats
                            for fmt in [
                                "%Y-%m-%d %H:%M:%S",
                                "%Y:%m:%d %H:%M:%S",
                                "%Y-%m-%d",
                            ]:
                                try:
                                    captured_at = datetime.strptime(captured_at, fmt)
                                    img_copy["captured_at"] = captured_at
                                    break
                                except Exception:
                                    continue
                            else:
                                # Could not parse date, but location is still valid
                                logger.debug(f"Could not parse date for image {img.get('id')}: {captured_at}")
                                # Clear the unparseable string to prevent downstream errors
                                img_copy["captured_at"] = None
                    elif isinstance(captured_at, datetime):
                        img_copy["captured_at"] = captured_at

                valid_images.append(img_copy)

            except Exception as e:
                logger.warning(f"Error filtering image {img.get('id')}: {e}")
                continue

        return valid_images

    def _cluster_by_location(self, images: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Cluster images by geographic location using DBSCAN.

        Args:
            images: List of image dictionaries with latitude/longitude

        Returns:
            List of location clusters (each cluster is a list of images)
        """
        if not images:
            return []

        # Extract coordinates
        coordinates = np.array([[img["latitude"], img["longitude"]] for img in images])

        # Convert to radians for haversine metric
        coordinates_rad = np.radians(coordinates)

        # Apply DBSCAN clustering
        # eps: maximum distance between two samples (in radians for haversine)
        # min_samples: minimum number of samples to form a cluster
        clustering = DBSCAN(
            eps=self.location_eps_radians,
            min_samples=1,  # Even single photos can form a cluster
            metric="haversine",  # Use haversine distance for lat/lon
            algorithm="ball_tree",
        )

        labels = clustering.fit_predict(coordinates_rad)

        # Group images by cluster label
        clusters = defaultdict(list)
        for idx, label in enumerate(labels):
            if label != -1:  # -1 is noise in DBSCAN
                clusters[label].append(images[idx])

        # Noise points (label -1) each become their own cluster
        for idx, label in enumerate(labels):
            if label == -1:
                clusters[f"noise_{idx}"].append(images[idx])

        return list(clusters.values())

    def _cluster_by_date(self, images: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Cluster images by date within a location cluster.

        Groups images that were taken within date_tolerance_days of each other.

        Args:
            images: List of image dictionaries with captured_at datetime

        Returns:
            List of temporal clusters (each cluster is a list of images)
        """
        if not images:
            return []

        # Sort by date
        sorted_images = sorted(
            [img for img in images if img.get("captured_at")],
            key=lambda x: x["captured_at"],
        )

        # Images without dates go into a separate cluster
        no_date_images = [img for img in images if not img.get("captured_at")]

        if not sorted_images:
            return [no_date_images] if no_date_images else []

        # Group by date tolerance
        clusters = []
        current_cluster = [sorted_images[0]]

        for i in range(1, len(sorted_images)):
            prev_date = sorted_images[i - 1]["captured_at"]
            curr_date = sorted_images[i]["captured_at"]

            # Check if within tolerance
            date_diff = abs((curr_date - prev_date).days)

            if date_diff <= self.date_tolerance_days:
                current_cluster.append(sorted_images[i])
            else:
                # Start new cluster
                clusters.append(current_cluster)
                current_cluster = [sorted_images[i]]

        # Add last cluster
        if current_cluster:
            clusters.append(current_cluster)

        # Add no-date images as separate cluster if exists
        if no_date_images:
            clusters.append(no_date_images)

        return clusters

    def _create_memory(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a memory object from a cluster of images.

        Args:
            images: List of image dictionaries in the cluster

        Returns:
            Memory dictionary with metadata
        """
        # Calculate center coordinates
        center_lat = np.mean([img["latitude"] for img in images])
        center_lon = np.mean([img["longitude"] for img in images])

        # Get date range
        dates = [img["captured_at"] for img in images if img.get("captured_at")]
        if dates:
            date_start = min(dates)
            date_end = max(dates)
        else:
            date_start = None
            date_end = None

        # Get location name
        location_name = self._reverse_geocode(center_lat, center_lon)

        # Generate title
        title = self._generate_title(location_name, date_start, len(images))

        # Generate description
        description = self._generate_description(len(images), date_start, date_end)

        # Select thumbnail (first image or middle image)
        thumbnail_idx = len(images) // 2
        thumbnail_image_id = images[thumbnail_idx]["id"]

        # Create memory ID (use timestamp + location hash)
        memory_id = self._generate_memory_id(center_lat, center_lon, date_start)

        # Convert captured_at datetime objects to ISO strings for all images
        serialized_images = []
        for img in images:
            img_copy = img.copy()
            if img_copy.get("captured_at") and isinstance(img_copy["captured_at"], datetime):
                img_copy["captured_at"] = img_copy["captured_at"].isoformat()
            serialized_images.append(img_copy)

        return {
            "memory_id": memory_id,
            "title": title,
            "description": description,
            "location_name": location_name,
            "date_start": date_start.isoformat() if date_start else None,
            "date_end": date_end.isoformat() if date_end else None,
            "image_count": len(images),
            "images": serialized_images,
            "thumbnail_image_id": thumbnail_image_id,
            "center_lat": float(center_lat),
            "center_lon": float(center_lon),
        }

    def _reverse_geocode(self, latitude: float, longitude: float) -> str:
        """
        Convert GPS coordinates to a human-readable location name.

        Uses city coordinate mapping for major cities, falls back to coordinates.

        Args:
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            Location string (e.g., "Jaipur, Rajasthan" or formatted coordinates)
        """
        # Try to find nearest known city
        city_name = find_nearest_city(latitude, longitude, max_distance_km=50.0)

        if city_name:
            logger.debug(f"Mapped coordinates ({latitude:.4f}, {longitude:.4f}) to {city_name}")
            return city_name

        # Fallback: Return formatted coordinates
        return f"{latitude:.4f}°, {longitude:.4f}°"

    def _generate_title(self, location_name: str, date: Optional[datetime], image_count: int) -> str:
        """
        Generate a title for the memory.

        Args:
            location_name: Human-readable location
            date: Date of the memory
            image_count: Number of images

        Returns:
            Title string
        """
        if date:
            month_year = date.strftime("%B %Y")
            return f"{location_name} - {month_year}"
        else:
            return f"{location_name} - {image_count} photos"

    def _generate_description(
        self,
        image_count: int,
        date_start: Optional[datetime],
        date_end: Optional[datetime],
    ) -> str:
        """
        Generate a description for the memory.

        Args:
            image_count: Number of images
            date_start: Start date
            date_end: End date

        Returns:
            Description string
        """
        if date_start and date_end:
            if date_start.date() == date_end.date():
                return f"{image_count} photos from {date_start.strftime('%B %d, %Y')}"
            else:
                days = (date_end - date_start).days + 1
                return f"{image_count} photos over {days} days ({date_start.strftime('%b %d')} - {date_end.strftime('%b %d, %Y')})"
        else:
            return f"{image_count} photos"

    def _generate_memory_id(self, latitude: float, longitude: float, date: Optional[datetime]) -> str:
        """
        Generate a unique ID for the memory.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            date: Date of memory

        Returns:
            Unique memory ID
        """
        # Create hash from location and date
        location_hash = hash((round(latitude, 2), round(longitude, 2)))
        if date:
            date_str = date.strftime("%Y%m%d")
            return f"mem_{date_str}_{abs(location_hash)}"
        else:
            return f"mem_nodate_{abs(location_hash)}"
