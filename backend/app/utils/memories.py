import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import math

from app.database.images import db_get_all_images
from app.database.memories import db_insert_memory, db_delete_all_memories
from app.utils.images import image_util_parse_metadata
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate
        
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def get_location_name(latitude: float, longitude: float) -> str:
    """
    Generate a simple location name from coordinates.
    In production, this would use reverse geocoding API.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        Location name string
    """
    # Simple location naming based on coordinates
    # In production, use services like OpenStreetMap Nominatim or Google Geocoding API
    lat_dir = "N" if latitude >= 0 else "S"
    lon_dir = "E" if longitude >= 0 else "W"
    return f"Location {abs(latitude):.2f}°{lat_dir}, {abs(longitude):.2f}°{lon_dir}"


def cluster_images_by_location(images: List[Dict], distance_threshold_km: float = 5.0) -> List[List[Dict]]:
    """
    Cluster images by geographic proximity.
    
    Args:
        images: List of image dictionaries with metadata
        distance_threshold_km: Maximum distance for images to be in same cluster
        
    Returns:
        List of image clusters
    """
    if not images:
        return []
    
    # Filter images with location data
    images_with_location = [
        img for img in images
        if img.get('metadata', {}).get('latitude') is not None
        and img.get('metadata', {}).get('longitude') is not None
    ]
    
    if not images_with_location:
        return []
    
    clusters = []
    used_indices = set()
    
    for i, img in enumerate(images_with_location):
        if i in used_indices:
            continue
        
        cluster = [img]
        used_indices.add(i)
        
        img_lat = img['metadata']['latitude']
        img_lon = img['metadata']['longitude']
        
        for j, other_img in enumerate(images_with_location):
            if j in used_indices:
                continue
            
            other_lat = other_img['metadata']['latitude']
            other_lon = other_img['metadata']['longitude']
            
            distance = calculate_distance(img_lat, img_lon, other_lat, other_lon)
            
            if distance <= distance_threshold_km:
                cluster.append(other_img)
                used_indices.add(j)
        
        if len(cluster) >= 3:  # Minimum 3 images for a location-based memory
            clusters.append(cluster)
    
    return clusters


def create_on_this_day_memories() -> List[Dict[str, Any]]:
    """
    Create 'On This Day' memories for images from previous years on the same date.
    
    Returns:
        List of memory dictionaries
    """
    memories = []
    today = datetime.now()
    
    # Get all images
    all_images = db_get_all_images()
    
    # Group images by date
    images_by_date: Dict[str, List[Dict]] = defaultdict(list)
    
    for img in all_images:
        metadata = image_util_parse_metadata(img.get('metadata', {}))
        date_created = metadata.get('date_created')
        
        if date_created:
            try:
                img_date = datetime.fromisoformat(date_created.replace('Z', '+00:00'))
                # Create key as month-day
                date_key = f"{img_date.month:02d}-{img_date.day:02d}"
                images_by_date[date_key].append({
                    **img,
                    'metadata': metadata,
                    'parsed_date': img_date
                })
            except (ValueError, AttributeError):
                continue
    
    # Check for images from 1-5 years ago on this date
    today_key = f"{today.month:02d}-{today.day:02d}"
    
    if today_key in images_by_date:
        images_on_this_day = images_by_date[today_key]
        
        # Group by year
        years_ago_groups: Dict[int, List[Dict]] = defaultdict(list)
        
        for img in images_on_this_day:
            img_year = img['parsed_date'].year
            years_diff = today.year - img_year
            
            if 1 <= years_diff <= 5:  # 1 to 5 years ago
                years_ago_groups[years_diff].append(img)
        
        # Create memories for each year
        for years_ago, images in years_ago_groups.items():
            if len(images) >= 2:  # At least 2 images
                image_ids = [img['id'] for img in images]
                representative_image = images[0]
                
                year_text = f"{years_ago} year{'s' if years_ago > 1 else ''}"
                
                memory = {
                    "memory_id": str(uuid.uuid4()),
                    "title": f"On This Day - {year_text} Ago",
                    "memory_type": "on_this_day",
                    "date_range_start": images[0]['parsed_date'].isoformat(),
                    "date_range_end": images[0]['parsed_date'].isoformat(),
                    "image_ids": json.dumps(image_ids),
                    "representative_image_id": representative_image['id'],
                    "created_at": datetime.now().isoformat(),
                    "year": images[0]['parsed_date'].year,
                }
                
                memories.append(memory)
    
    return memories


def create_trip_memories() -> List[Dict[str, Any]]:
    """
    Create trip memories based on location clustering and date proximity.
    
    Returns:
        List of memory dictionaries
    """
    memories = []
    
    # Get all images
    all_images = db_get_all_images()
    
    # Filter images with dates and locations
    images_with_data = []
    for img in all_images:
        metadata = image_util_parse_metadata(img.get('metadata', {}))
        date_created = metadata.get('date_created')
        
        if (date_created and 
            metadata.get('latitude') is not None and 
            metadata.get('longitude') is not None):
            try:
                img_date = datetime.fromisoformat(date_created.replace('Z', '+00:00'))
                images_with_data.append({
                    **img,
                    'metadata': metadata,
                    'parsed_date': img_date
                })
            except (ValueError, AttributeError):
                continue
    
    if not images_with_data:
        return memories
    
    # Sort by date
    images_with_data.sort(key=lambda x: x['parsed_date'])
    
    # Group images by date proximity (within 7 days)
    date_groups = []
    current_group = []
    
    for img in images_with_data:
        if not current_group:
            current_group = [img]
        else:
            last_date = current_group[-1]['parsed_date']
            current_date = img['parsed_date']
            
            if (current_date - last_date).days <= 7:
                current_group.append(img)
            else:
                if len(current_group) >= 5:  # At least 5 images
                    date_groups.append(current_group)
                current_group = [img]
    
    if len(current_group) >= 5:
        date_groups.append(current_group)
    
    # For each date group, cluster by location
    for date_group in date_groups:
        location_clusters = cluster_images_by_location(date_group, distance_threshold_km=10.0)
        
        for cluster in location_clusters:
            if len(cluster) >= 5:  # At least 5 images for a trip
                # Calculate average location
                avg_lat = sum(img['metadata']['latitude'] for img in cluster) / len(cluster)
                avg_lon = sum(img['metadata']['longitude'] for img in cluster) / len(cluster)
                
                location_name = get_location_name(avg_lat, avg_lon)
                
                dates = [img['parsed_date'] for img in cluster]
                start_date = min(dates)
                end_date = max(dates)
                
                # Create title
                year = start_date.year
                month_name = start_date.strftime('%B')
                
                title = f"Trip to {location_name}"
                if (end_date - start_date).days <= 1:
                    title = f"{location_name}, {month_name} {year}"
                else:
                    title = f"{location_name}, {month_name} {year}"
                
                image_ids = [img['id'] for img in cluster]
                
                memory = {
                    "memory_id": str(uuid.uuid4()),
                    "title": title,
                    "memory_type": "trip",
                    "date_range_start": start_date.isoformat(),
                    "date_range_end": end_date.isoformat(),
                    "location_name": location_name,
                    "latitude": avg_lat,
                    "longitude": avg_lon,
                    "image_ids": json.dumps(image_ids),
                    "representative_image_id": cluster[0]['id'],
                    "created_at": datetime.now().isoformat(),
                    "year": year,
                }
                
                memories.append(memory)
    
    return memories


def generate_memories() -> int:
    """
    Generate all memories and store them in the database.
    Clears existing memories and creates new ones.
    
    Returns:
        Number of memories created
    """
    logger.info("Starting memory generation...")
    
    # Clear existing memories
    db_delete_all_memories()
    
    memories = []
    
    # Generate different types of memories
    try:
        on_this_day_memories = create_on_this_day_memories()
        memories.extend(on_this_day_memories)
        logger.info(f"Created {len(on_this_day_memories)} 'On This Day' memories")
    except Exception as e:
        logger.error(f"Error creating 'On This Day' memories: {e}")
    
    try:
        trip_memories = create_trip_memories()
        memories.extend(trip_memories)
        logger.info(f"Created {len(trip_memories)} trip memories")
    except Exception as e:
        logger.error(f"Error creating trip memories: {e}")
    
    # Insert memories into database
    for memory in memories:
        try:
            db_insert_memory(memory)
        except Exception as e:
            logger.error(f"Error inserting memory: {e}")
    
    logger.info(f"Memory generation complete. Created {len(memories)} memories")
    return len(memories)
