"""
Memory Clustering Algorithm

This module groups images into "memories" based on spatial proximity (location)
and temporal proximity (date/time). Uses DBSCAN for spatial clustering and 
date-based grouping for temporal clustering.

A "memory" is a collection of photos taken at the same place around the same time.

Author: PictoPy Team
Date: 2025-12-14
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

import numpy as np
from sklearn.cluster import DBSCAN

from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


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
        min_images_per_memory: int = 2
    ):
        """Initialize the memory clustering algorithm."""
        self.location_radius_km = location_radius_km
        self.date_tolerance_days = date_tolerance_days
        self.min_images_per_memory = min_images_per_memory
        
        # Convert km to degrees for DBSCAN
        # Approximate: 1 degree latitude ≈ 111 km
        self.location_eps_degrees = location_radius_km / 111.0
        
        logger.info(f"MemoryClustering initialized: radius={location_radius_km}km, "
                   f"date_tolerance={date_tolerance_days}days, "
                   f"min_images={min_images_per_memory}")
    
    def cluster_memories(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main entry point: Cluster images into memories.
        
        Args:
            images: List of image dictionaries with fields:
                - id: Image ID
                - path: File path
                - thumbnailPath: Thumbnail path
                - latitude: GPS latitude (required)
                - longitude: GPS longitude (required)
                - captured_at: Capture datetime (ISO string or datetime object)
                - metadata: Additional metadata dict
                
        Returns:
            List of memory dictionaries with fields:
                - memory_id: Unique memory identifier
                - title: Memory title (e.g., "Trip to Paris")
                - description: Memory description
                - location_name: Human-readable location
                - date_start: Start date (ISO string)
                - date_end: End date (ISO string)
                - image_count: Number of images in memory
                - images: List of image objects
                - thumbnail_image_id: ID of representative image
                - center_lat: Center latitude of cluster
                - center_lon: Center longitude of cluster
        """
        logger.info(f"Starting memory clustering for {len(images)} images")
        
        if not images:
            logger.warning("No images provided for clustering")
            return []
        
        # Filter images with valid location data
        valid_images = self._filter_valid_images(images)
        
        if not valid_images:
            logger.warning("No images with valid location data")
            return []
        
        logger.info(f"Found {len(valid_images)} images with valid location data")
        
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
        
        logger.info(f"Generated {len(memories)} memories")
        
        # Sort memories by date (most recent first)
        memories.sort(key=lambda m: m['date_start'] if m['date_start'] else '', reverse=True)
        
        return memories
    
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
                if not img.get('latitude') or not img.get('longitude'):
                    continue
                
                # Parse captured_at if it's a string
                captured_at = img.get('captured_at')
                img_copy = img.copy()
                
                if captured_at:
                    if isinstance(captured_at, str):
                        try:
                            # SQLite returns ISO format: "YYYY-MM-DDTHH:MM:SS"
                            captured_at = datetime.fromisoformat(captured_at.replace('Z', ''))
                            img_copy['captured_at'] = captured_at
                        except Exception as e:
                            # Try alternative formats
                            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y:%m:%d %H:%M:%S', '%Y-%m-%d']:
                                try:
                                    captured_at = datetime.strptime(captured_at, fmt)
                                    img_copy['captured_at'] = captured_at
                                    break
                                except Exception:
                                    continue
                            else:
                                # Could not parse date, but location is still valid
                                logger.debug(f"Could not parse date for image {img.get('id')}: {captured_at}")
                    elif isinstance(captured_at, datetime):
                        img_copy['captured_at'] = captured_at
                
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
        coordinates = np.array([
            [img['latitude'], img['longitude']]
            for img in images
        ])
        
        # Apply DBSCAN clustering
        # eps: maximum distance between two samples (in degrees)
        # min_samples: minimum number of samples to form a cluster
        clustering = DBSCAN(
            eps=self.location_eps_degrees,
            min_samples=1,  # Even single photos can form a cluster
            metric='haversine',  # Use haversine distance for lat/lon
            algorithm='ball_tree'
        )
        
        # Convert to radians for haversine
        coordinates_rad = np.radians(coordinates)
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
            [img for img in images if img.get('captured_at')],
            key=lambda x: x['captured_at']
        )
        
        # Images without dates go into a separate cluster
        no_date_images = [img for img in images if not img.get('captured_at')]
        
        if not sorted_images:
            return [no_date_images] if no_date_images else []
        
        # Group by date tolerance
        clusters = []
        current_cluster = [sorted_images[0]]
        
        for i in range(1, len(sorted_images)):
            prev_date = sorted_images[i-1]['captured_at']
            curr_date = sorted_images[i]['captured_at']
            
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
        center_lat = np.mean([img['latitude'] for img in images])
        center_lon = np.mean([img['longitude'] for img in images])
        
        # Get date range
        dates = [img['captured_at'] for img in images if img.get('captured_at')]
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
        thumbnail_image_id = images[thumbnail_idx]['id']
        
        # Create memory ID (use timestamp + location hash)
        memory_id = self._generate_memory_id(center_lat, center_lon, date_start)
        
        # Convert captured_at datetime objects to ISO strings for all images
        serialized_images = []
        for img in images:
            img_copy = img.copy()
            if img_copy.get('captured_at') and isinstance(img_copy['captured_at'], datetime):
                img_copy['captured_at'] = img_copy['captured_at'].isoformat()
            serialized_images.append(img_copy)
        
        return {
            'memory_id': memory_id,
            'title': title,
            'description': description,
            'location_name': location_name,
            'date_start': date_start.isoformat() if date_start else None,
            'date_end': date_end.isoformat() if date_end else None,
            'image_count': len(images),
            'images': serialized_images,
            'thumbnail_image_id': thumbnail_image_id,
            'center_lat': float(center_lat),
            'center_lon': float(center_lon)
        }
    
    def _reverse_geocode(self, latitude: float, longitude: float) -> str:
        """
        Convert GPS coordinates to a human-readable location name.
        
        This is a simple implementation. For production, consider using:
        - Geopy with Nominatim
        - Google Maps Geocoding API
        - Mapbox Geocoding API
        
        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            
        Returns:
            Location string (e.g., "Paris, France")
        """
        # Simple placeholder implementation
        # Returns coordinates formatted as location
        return f"{latitude:.4f}°, {longitude:.4f}°"
    
    def _generate_title(
        self,
        location_name: str,
        date: Optional[datetime],
        image_count: int
    ) -> str:
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
        date_end: Optional[datetime]
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
    
    def _generate_memory_id(
        self,
        latitude: float,
        longitude: float,
        date: Optional[datetime]
    ) -> str:
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
            date_str = date.strftime('%Y%m%d')
            return f"mem_{date_str}_{abs(location_hash)}"
        else:
            return f"mem_nodate_{abs(location_hash)}"
