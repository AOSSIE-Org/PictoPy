import json
import uuid
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import math

from app.database.images import db_get_all_images
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def extract_gps_from_metadata(metadata: Dict[str, Any]) -> tuple:
    """Extract GPS coordinates from image metadata."""
    try:
        if "gpsinfo" in metadata or "GPS" in str(metadata):
            # Try to extract GPS data from various EXIF formats
            gps_data = metadata.get("gpsinfo", {})
            
            if isinstance(gps_data, dict):
                lat = gps_data.get("latitude") or gps_data.get("2")
                lon = gps_data.get("longitude") or gps_data.get("4")
                
                if lat and lon:
                    return (float(lat), float(lon))
        
        return (None, None)
    except Exception as e:
        logger.warning(f"Error extracting GPS: {e}")
        return (None, None)


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates in kilometers using Haversine formula."""
    if None in [lat1, lon1, lat2, lon2]:
        return float('inf')
    
    R = 6371  # Earth radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def parse_date_from_metadata(metadata: Dict[str, Any]) -> datetime:
    """Extract date from metadata."""
    try:
        # Try various date fields
        date_fields = ['datetime', 'datetimeoriginal', 'creation_date', 'date_taken']
        
        for field in date_fields:
            if field in metadata:
                date_str = metadata[field]
                if isinstance(date_str, str):
                    try:
                        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                        except ValueError:
                            continue
        
        # Fallback to creation_date if available
        if 'creation_date' in metadata:
            return datetime.fromisoformat(metadata['creation_date'])
            
        return datetime.now()
    except Exception as e:
        logger.warning(f"Error parsing date: {e}")
        return datetime.now()


def generate_on_this_day_memories() -> List[Dict[str, Any]]:
    """Generate 'On This Day' memories for past years."""
    memories = []
    images = db_get_all_images()
    
    if not images:
        return memories
    
    today = datetime.now()
    current_month_day = (today.month, today.day)
    
    # Group images by year for this month/day
    images_by_year = defaultdict(list)
    
    for image in images:
        try:
            metadata = image.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            
            image_date = parse_date_from_metadata(metadata)
            
            # Check if it's within 3 days of today's date in a previous year
            if (abs(image_date.month - today.month) == 0 and 
                abs(image_date.day - today.day) <= 3 and 
                image_date.year < today.year):
                
                years_ago = today.year - image_date.year
                images_by_year[years_ago].append({
                    "id": image["id"],
                    "path": image["path"],
                    "date": image_date,
                    "metadata": metadata
                })
        except Exception as e:
            logger.warning(f"Error processing image for on-this-day: {e}")
            continue
    
    # Create memories for each year
    for years_ago, year_images in images_by_year.items():
        if len(year_images) >= 1:  # At least 1 image
            year_images.sort(key=lambda x: x["date"])
            
            memory_id = str(uuid.uuid4())
            start_date = year_images[0]["date"]
            end_date = year_images[-1]["date"]
            
            memory = {
                "id": memory_id,
                "title": f"On This Day {years_ago} Year{'s' if years_ago > 1 else ''} Ago",
                "description": f"You had {len(year_images)} moment{'s' if len(year_images) > 1 else ''} on this day in {start_date.year}",
                "memory_type": "on_this_day",
                "date_range_start": start_date.isoformat(),
                "date_range_end": end_date.isoformat(),
                "image_count": len(year_images),
                "cover_image_id": year_images[0]["id"],
                "image_ids": [img["id"] for img in year_images],
                "created_at": datetime.now().isoformat()
            }
            
            memories.append(memory)
    
    return memories


def generate_location_based_memories() -> List[Dict[str, Any]]:
    """Generate memories based on location clustering."""
    memories = []
    images = db_get_all_images()
    
    if not images:
        return memories
    
    # Extract images with GPS data
    images_with_gps = []
    for image in images:
        try:
            metadata = image.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            
            lat, lon = extract_gps_from_metadata(metadata)
            if lat and lon:
                image_date = parse_date_from_metadata(metadata)
                images_with_gps.append({
                    "id": image["id"],
                    "path": image["path"],
                    "lat": lat,
                    "lon": lon,
                    "date": image_date,
                    "metadata": metadata
                })
        except Exception as e:
            logger.warning(f"Error processing image for location memory: {e}")
            continue
    
    if len(images_with_gps) < 5:
        return memories
    
    # Simple clustering by distance (5km radius)
    clusters = []
    used_images = set()
    
    for img in images_with_gps:
        if img["id"] in used_images:
            continue
        
        cluster = [img]
        used_images.add(img["id"])
        
        for other_img in images_with_gps:
            if other_img["id"] in used_images:
                continue
            
            distance = calculate_distance(
                img["lat"], img["lon"],
                other_img["lat"], other_img["lon"]
            )
            
            if distance <= 5:  # 5km radius
                cluster.append(other_img)
                used_images.add(other_img["id"])
        
        if len(cluster) >= 5:
            clusters.append(cluster)
    
    # Create memories for each cluster
    for cluster in clusters:
        cluster.sort(key=lambda x: x["date"])
        
        start_date = cluster[0]["date"]
        end_date = cluster[-1]["date"]
        
        # Estimate location name (simplified)
        avg_lat = sum(img["lat"] for img in cluster) / len(cluster)
        avg_lon = sum(img["lon"] for img in cluster) / len(cluster)
        location_name = f"Location ({avg_lat:.2f}, {avg_lon:.2f})"
        
        memory_id = str(uuid.uuid4())
        memory = {
            "id": memory_id,
            "title": f"Trip to {location_name}",
            "description": f"{len(cluster)} photos from {start_date.strftime('%B %Y')}",
            "memory_type": "location_trip",
            "date_range_start": start_date.isoformat(),
            "date_range_end": end_date.isoformat(),
            "location": location_name,
            "latitude": avg_lat,
            "longitude": avg_lon,
            "image_count": len(cluster),
            "cover_image_id": cluster[0]["id"],
            "image_ids": [img["id"] for img in cluster],
            "created_at": datetime.now().isoformat()
        }
        
        memories.append(memory)
    
    return memories


def generate_all_memories() -> List[Dict[str, Any]]:
    """Generate all types of memories."""
    all_memories = []
    
    logger.info("Generating on-this-day memories...")
    on_this_day = generate_on_this_day_memories()
    all_memories.extend(on_this_day)
    
    logger.info("Generating location-based memories...")
    location_memories = generate_location_based_memories()
    all_memories.extend(location_memories)
    
    logger.info(f"Generated {len(all_memories)} total memories")
    return all_memories
