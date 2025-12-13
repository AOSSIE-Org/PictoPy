"""
Enhanced Memory generation algorithm.
Groups photos by date and location to create automatic memories.
Improvements: adaptive clustering, duplicate prevention, better trip detection, seasonal memories.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
import math

from app.database.images import db_get_all_images
from app.database.memories import (
    db_insert_memory,
    db_insert_memory_images,
    db_clear_all_memories,
)
from app.utils.geocoding import get_geocoder
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


class MemoryGenerator:
    """Enhanced memory generator with better accuracy and features."""

    # Dynamic clustering based on photo density
    MIN_PHOTOS_FOR_MEMORY = 5  # Increased from 3 for better quality
    TRIP_MIN_DAYS = 1  # Allow single-day trips
    TRIP_MAX_DAYS = 30
    TRIP_MAX_GAP_DAYS = 3  # Allow 3-day gaps in trips
    
    # Adaptive location clustering
    URBAN_RADIUS_KM = 20
    SUBURBAN_RADIUS_KM = 50
    RURAL_RADIUS_KM = 100
    DEFAULT_RADIUS_KM = 50  # Fallback
    
    REPRESENTATIVE_PHOTOS_COUNT = 6  # Increased from 5

    def __init__(self):
        self.memories_created = 0
        self.stats = {
            "on_this_day": 0,
            "trip": 0,
            "location": 0,
            "month_highlight": 0,
            "seasonal": 0,
        }
        self.geocoder = get_geocoder()
        self.location_cache = {}
        self.used_photo_ids: Set[str] = set()  # Prevent duplicates

    def generate_all_memories(self, force_regenerate: bool = False) -> Dict[str, Any]:
        """
        Generate all types of memories from existing photos.
        
        Args:
            force_regenerate: If True, clear existing memories first
            
        Returns:
            Dictionary with generation statistics
        """
        logger.info("Starting enhanced memory generation...")

        if force_regenerate:
            db_clear_all_memories()
            self.used_photo_ids.clear()
            logger.info("Cleared existing memories")

        # Get all images with metadata
        all_images = db_get_all_images()
        logger.info(f"Found {len(all_images)} images to process")

        if not all_images:
            return {
                "memories_created": 0,
                "message": "No images found to generate memories",
                "stats": self.stats,
            }

        # Parse and filter images with dates
        photos_with_dates = self._parse_photos(all_images)
        logger.info(f"Parsed {len(photos_with_dates)} photos with valid dates")

        # Generate memories in priority order (most specific to most general)
        self._generate_on_this_day_memories(photos_with_dates)
        self._generate_trip_memories(photos_with_dates)
        self._generate_seasonal_memories(photos_with_dates)
        self._generate_location_memories(photos_with_dates)
        self._generate_monthly_highlights(photos_with_dates)

        return {
            "memories_created": self.memories_created,
            "message": f"Successfully generated {self.memories_created} memories",
            "stats": self.stats,
        }

    def _parse_photos(self, images: List[Dict]) -> List[Dict]:
        """Parse images and extract relevant metadata."""
        parsed_photos = []

        for img in images:
            metadata = img.get("metadata", {})
            date_str = metadata.get("date_created")

            if not date_str:
                continue

            try:
                # Parse date (handle various formats)
                photo_date = self._parse_date(date_str)
                
                lat = metadata.get("latitude")
                lon = metadata.get("longitude")
                
                # Get location name if coordinates exist
                location_name = metadata.get("location")
                if not location_name and lat and lon:
                    # Use geocoding to get location name
                    cache_key = f"{round(lat, 2)},{round(lon, 2)}"
                    if cache_key in self.location_cache:
                        location_name = self.location_cache[cache_key]
                    else:
                        location_name = self.geocoder.get_location_name(lat, lon)
                        if location_name:
                            self.location_cache[cache_key] = location_name
                
                # Determine location type for adaptive clustering
                location_type = self._determine_location_type(location_name)
                
                parsed_photos.append({
                    "id": img["id"],
                    "path": img["path"],
                    "thumbnail": img["thumbnailPath"],
                    "date": photo_date,
                    "latitude": lat,
                    "longitude": lon,
                    "location": location_name,
                    "location_type": location_type,
                    "metadata": metadata,
                })

            except Exception as e:
                logger.debug(f"Could not parse date for image {img['id']}: {e}")
                continue

        return parsed_photos

    def _determine_location_type(self, location_name: Optional[str]) -> str:
        """Determine if location is urban, suburban, or rural."""
        if not location_name:
            return "unknown"
        
        location_lower = location_name.lower()
        
        # Major cities
        urban_keywords = [
            "city", "mumbai", "delhi", "bangalore", "chennai", "kolkata",
            "hyderabad", "pune", "ahmedabad", "new york", "london", 
            "paris", "tokyo", "dubai"
        ]
        
        # Smaller cities/towns
        suburban_keywords = ["town", "suburb", "township"]
        
        if any(keyword in location_lower for keyword in urban_keywords):
            return "urban"
        elif any(keyword in location_lower for keyword in suburban_keywords):
            return "suburban"
        else:
            return "rural"

    def _get_adaptive_radius(self, location_type: str) -> float:
        """Get clustering radius based on location type."""
        radius_map = {
            "urban": self.URBAN_RADIUS_KM,
            "suburban": self.SUBURBAN_RADIUS_KM,
            "rural": self.RURAL_RADIUS_KM,
            "unknown": self.DEFAULT_RADIUS_KM,
        }
        return radius_map.get(location_type, self.DEFAULT_RADIUS_KM)

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string in various formats."""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y:%m:%d %H:%M:%S",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # If all fail, try ISO format
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

    def _generate_on_this_day_memories(self, photos: List[Dict]):
        """
        Enhanced 'On This Day' with flexible date matching (±3 days).
        """
        today = datetime.now()
        day_groups = defaultdict(list)
        
        for photo in photos:
            if photo["id"] in self.used_photo_ids:
                continue
                
            photo_date = photo["date"]
            
            # Check if within ±3 days of today (any past year)
            if photo_date.year < today.year:
                day_diff = abs((today.replace(year=photo_date.year) - photo_date).days)
                if day_diff <= 3:
                    years_ago = today.year - photo_date.year
                    day_groups[years_ago].append(photo)

        # Create memory for each past year group
        for years_ago, year_photos in day_groups.items():
            if len(year_photos) >= self.MIN_PHOTOS_FOR_MEMORY:
                title = f"On This Day {years_ago} {'Year' if years_ago == 1 else 'Years'} Ago"
                
                if self._create_memory(
                    title=title,
                    memory_type="on_this_day",
                    photos=year_photos,
                ):
                    self.stats["on_this_day"] += 1
                    for p in year_photos:
                        self.used_photo_ids.add(p["id"])

    def _generate_trip_memories(self, photos: List[Dict]):
        """
        Improved trip detection with gap tolerance and adaptive clustering.
        """
        available_photos = [p for p in photos if p["id"] not in self.used_photo_ids]
        photos_sorted = sorted(available_photos, key=lambda x: x["date"])

        i = 0
        while i < len(photos_sorted):
            trip_photos = [photos_sorted[i]]
            trip_start = photos_sorted[i]
            last_photo_date = photos_sorted[i]["date"]
            
            j = i + 1
            while j < len(photos_sorted):
                current_photo = photos_sorted[j]
                days_since_start = (current_photo["date"] - trip_start["date"]).days
                days_since_last = (current_photo["date"] - last_photo_date).days

                if days_since_start <= self.TRIP_MAX_DAYS:
                    if days_since_last <= self.TRIP_MAX_GAP_DAYS:
                        if self._is_same_location_cluster_adaptive(trip_start, current_photo):
                            trip_photos.append(current_photo)
                            last_photo_date = current_photo["date"]
                            j += 1
                        else:
                            break
                    else:
                        break
                else:
                    break

            # Create trip memory if criteria met
            if len(trip_photos) >= self.MIN_PHOTOS_FOR_MEMORY:
                duration_days = (trip_photos[-1]["date"] - trip_photos[0]["date"]).days
                
                if duration_days >= self.TRIP_MIN_DAYS or len(trip_photos) >= 10:
                    location = self._get_location_name(trip_photos)
                    year = trip_photos[0]["date"].year
                    month = trip_photos[0]["date"].strftime("%B")
                    
                    # Better title generation
                    if duration_days >= 7:
                        title = f"Week in {location}" if location else f"{month} {year} Adventure"
                    elif duration_days >= 3:
                        title = f"Weekend at {location}" if location else f"{month} {year} Getaway"
                    else:
                        title = f"Day Trip to {location}" if location else f"{month} {year} Outing"
                    
                    if self._create_memory(
                        title=title,
                        memory_type="trip",
                        photos=trip_photos,
                    ):
                        self.stats["trip"] += 1
                        for p in trip_photos:
                            self.used_photo_ids.add(p["id"])

            i = j if j > i + 1 else i + 1

    def _generate_seasonal_memories(self, photos: List[Dict]):
        """
        Generate seasonal memories (Spring, Summer, Fall, Winter).
        """
        available_photos = [p for p in photos if p["id"] not in self.used_photo_ids]
        season_groups = defaultdict(list)
        
        for photo in available_photos:
            year = photo["date"].year
            month = photo["date"].month
            
            # Determine season
            if month in [3, 4, 5]:
                season = "Spring"
            elif month in [6, 7, 8]:
                season = "Summer"
            elif month in [9, 10, 11]:
                season = "Fall"
            else:
                season = "Winter"
            
            season_groups[(year, season)].append(photo)

        # Create memories for seasons with enough photos
        for (year, season), season_photos in season_groups.items():
            if len(season_photos) >= self.MIN_PHOTOS_FOR_MEMORY * 2:
                location = self._get_most_common_location(season_photos)
                title = f"{season} {year}" + (f" at {location}" if location else "")
                
                if self._create_memory(
                    title=title,
                    memory_type="seasonal",
                    photos=season_photos,
                ):
                    self.stats["seasonal"] += 1
                    for p in season_photos:
                        self.used_photo_ids.add(p["id"])

    def _generate_location_memories(self, photos: List[Dict]):
        """Enhanced location memories with adaptive clustering."""
        available_photos = [
            p for p in photos 
            if p["id"] not in self.used_photo_ids 
            and p.get("latitude") 
            and p.get("longitude")
        ]
        
        if not available_photos:
            logger.info("No photos with location data available for location memories")
            return
        
        location_groups = self._cluster_by_location_adaptive(available_photos)

        for location_name, location_photos in location_groups.items():
            if len(location_photos) >= self.MIN_PHOTOS_FOR_MEMORY * 2:
                dates = [p["date"] for p in location_photos]
                start_date = min(dates)
                end_date = max(dates)
                
                visit_count = len(set(d.date() for d in dates))
                
                if visit_count >= 10:
                    title = f"Favorite Spot: {location_name}"
                else:
                    title = f"Moments at {location_name}"
                
                if self._create_memory(
                    title=title,
                    memory_type="location",
                    photos=location_photos,
                ):
                    self.stats["location"] += 1
                    for p in location_photos:
                        self.used_photo_ids.add(p["id"])

    def _generate_monthly_highlights(self, photos: List[Dict]):
        """Generate monthly highlights for remaining photos."""
        available_photos = [p for p in photos if p["id"] not in self.used_photo_ids]
        month_groups = defaultdict(list)
        
        for photo in available_photos:
            key = (photo["date"].year, photo["date"].month)
            month_groups[key].append(photo)

        for (year, month), month_photos in month_groups.items():
            if len(month_photos) >= self.MIN_PHOTOS_FOR_MEMORY * 3:
                month_name = datetime(year, month, 1).strftime("%B")
                
                if self._create_memory(
                    title=f"{month_name} {year} Highlights",
                    memory_type="month_highlight",
                    photos=month_photos,
                ):
                    self.stats["month_highlight"] += 1
                    for p in month_photos:
                        self.used_photo_ids.add(p["id"])

    def _cluster_by_location_adaptive(self, photos: List[Dict]) -> Dict[str, List[Dict]]:
        """Adaptive location clustering based on location type."""
        location_groups = defaultdict(list)
        
        for photo in photos:
            lat = photo.get("latitude")
            lon = photo.get("longitude")
            
            if not (lat and lon):
                continue
            
            found_cluster = False
            
            for cluster_name, cluster_photos in location_groups.items():
                representative = cluster_photos[0]
                
                if self._is_same_location_cluster_adaptive(photo, representative):
                    location_groups[cluster_name].append(photo)
                    found_cluster = True
                    break

            if not found_cluster:
                location_name = photo.get("location", f"Location {len(location_groups) + 1}")
                location_groups[location_name].append(photo)

        logger.info(f"Created {len(location_groups)} location clusters")
        return location_groups

    def _is_same_location_cluster_adaptive(self, photo1: Dict, photo2: Dict) -> bool:
        """Check if two photos are in same location using adaptive radius."""
        lat1, lon1 = photo1.get("latitude"), photo1.get("longitude")
        lat2, lon2 = photo2.get("latitude"), photo2.get("longitude")

        if not all([lat1, lon1, lat2, lon2]):
            return False

        # Use the more restrictive radius
        radius1 = self._get_adaptive_radius(photo1.get("location_type", "unknown"))
        radius2 = self._get_adaptive_radius(photo2.get("location_type", "unknown"))
        radius = min(radius1, radius2)

        distance = self._calculate_distance(lat1, lon1, lat2, lon2)
        return distance <= radius

    def _is_same_location_cluster(self, photo1: Dict, photo2: Dict) -> bool:
        """Backward compatible method using default radius."""
        lat1, lon1 = photo1.get("latitude"), photo1.get("longitude")
        lat2, lon2 = photo2.get("latitude"), photo2.get("longitude")

        if not all([lat1, lon1, lat2, lon2]):
            return False

        distance = self._calculate_distance(lat1, lon1, lat2, lon2)
        return distance <= self.DEFAULT_RADIUS_KM

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in km (Haversine formula)."""
        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _get_location_name(self, photos: List[Dict]) -> Optional[str]:
        """Get location name from photos (prioritize named locations)."""
        for photo in photos:
            if photo.get("location"):
                return photo["location"]
        return None

    def _get_most_common_location(self, photos: List[Dict]) -> Optional[str]:
        """Get most common location from photo list."""
        locations = [p.get("location") for p in photos if p.get("location")]
        if not locations:
            return None
        
        from collections import Counter
        return Counter(locations).most_common(1)[0][0]

    def _create_memory(self, title: str, memory_type: str, photos: List[Dict]) -> bool:
        """Create and save a memory to the database."""
        if not photos:
            return False

        memory_id = str(uuid.uuid4())
        
        # Sort photos by date
        photos_sorted = sorted(photos, key=lambda x: x["date"])
        
        # Get date range
        start_date = photos_sorted[0]["date"].isoformat()
        end_date = photos_sorted[-1]["date"].isoformat()

        # Get location info
        location = self._get_location_name(photos)
        lat = photos_sorted[0].get("latitude")
        lon = photos_sorted[0].get("longitude")

        # Select representative photos
        representative_photos = self._select_representative_photos(photos_sorted)
        representative_ids = [p["id"] for p in representative_photos]

        # Insert memory
        success = db_insert_memory(
            memory_id=memory_id,
            title=title,
            memory_type=memory_type,
            start_date=start_date,
            end_date=end_date,
            location=location,
            latitude=lat,
            longitude=lon,
            cover_image_id=representative_ids[0] if representative_ids else None,
            total_photos=len(photos),
        )

        if success:
            # Link all photos to memory
            all_photo_ids = [p["id"] for p in photos_sorted]
            db_insert_memory_images(memory_id, all_photo_ids, representative_ids)
            
            self.memories_created += 1
            logger.info(f"Created memory: {title} ({len(photos)} photos)")
            return True

        return False

    def _select_representative_photos(self, photos: List[Dict]) -> List[Dict]:
        """
        Smart selection of representative photos.
        Evenly distributed across the time period.
        """
        if len(photos) <= self.REPRESENTATIVE_PHOTOS_COUNT:
            return photos

        # Evenly spaced selection
        step = len(photos) / self.REPRESENTATIVE_PHOTOS_COUNT
        selected = []
        
        for i in range(self.REPRESENTATIVE_PHOTOS_COUNT):
            idx = int(i * step)
            if idx < len(photos):
                selected.append(photos[idx])

        return selected[:self.REPRESENTATIVE_PHOTOS_COUNT]