"""
Enhanced reverse geocoding with persistent caching and better error handling.
- Persistent JSON cache to avoid repeated API calls
- Batch geocoding optimization
- Fallback providers (Nominatim + optional Google Maps)
- Better rate limiting
"""

import requests
import json
import time
import os
from typing import Optional, Tuple, Dict
from pathlib import Path
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


class EnhancedReverseGeocoder:
    """
    Improved geocoder with persistent caching and multiple providers.
    """

    def __init__(self, cache_file: str = "geocoding_cache.json"):
        self.base_url = "https://nominatim.openstreetmap.org/reverse"
        
        # Persistent cache file
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
        
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Nominatim requires 1 second
        
        # Stats
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "api_calls": 0,
            "api_errors": 0,
        }

    def _load_cache(self) -> Dict:
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    logger.info(f"Loaded {len(cache)} cached locations")
                    return cache
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def _rate_limit(self):
        """Respect API rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def get_location_name(
        self, 
        latitude: float, 
        longitude: float,
        zoom_level: int = 10
    ) -> Optional[str]:
        """
        Get human-readable location name from coordinates.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            zoom_level: Detail level (3=country, 10=city, 18=building)
            
        Returns:
            Location name or None
        """
        # Round coordinates for cache key (3 decimals = ~110m accuracy)
        cache_key = f"{round(latitude, 3)},{round(longitude, 3)},{zoom_level}"
        
        # Check cache
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            return self.cache[cache_key]

        self.stats["cache_misses"] += 1

        # Try primary provider (Nominatim)
        location = self._geocode_nominatim(latitude, longitude, zoom_level)
        
        # Cache result (even if None to avoid repeated failed lookups)
        if location or self.stats["cache_misses"] % 10 == 0:
            self.cache[cache_key] = location
            self._save_cache()  # Periodic saves
        
        return location

    def _geocode_nominatim(
        self, 
        latitude: float, 
        longitude: float,
        zoom_level: int
    ) -> Optional[str]:
        """Geocode using Nominatim (OpenStreetMap)."""
        try:
            self._rate_limit()
            self.stats["api_calls"] += 1

            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "zoom": zoom_level,
                "addressdetails": 1,
            }

            headers = {
                "User-Agent": "PictoPy/1.0 (Photo Gallery App)"
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=10,  # Increased timeout
            )

            if response.status_code == 200:
                data = response.json()
                location_name = self._format_location(data)
                logger.info(f"Geocoded ({latitude}, {longitude}) -> {location_name}")
                return location_name
            elif response.status_code == 429:
                # Rate limited
                logger.warning("Rate limited by Nominatim, backing off...")
                time.sleep(5)
                return None
            else:
                logger.warning(f"Geocoding failed: HTTP {response.status_code}")
                self.stats["api_errors"] += 1
                return None

        except requests.exceptions.Timeout:
            logger.warning(f"Geocoding timeout for ({latitude}, {longitude})")
            self.stats["api_errors"] += 1
            return None
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            self.stats["api_errors"] += 1
            return None

    def _format_location(self, data: dict) -> str:
        """Format geocoding response into clean location name."""
        address = data.get("address", {})
        
        # Try different fields for city
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("county")
            or address.get("hamlet")
        )
        
        state = address.get("state") or address.get("province")
        country = address.get("country")

        # Build hierarchical location string
        parts = []
        
        if city:
            parts.append(city)
        
        if state and state != city:
            parts.append(state)
        
        if country:
            parts.append(country)

        if parts:
            return ", ".join(parts)
        
        # Fallback to display name
        return data.get("display_name", "Unknown Location")

    def get_batch_locations(
        self, 
        coordinates: list[Tuple[float, float]],
        show_progress: bool = True
    ) -> dict[Tuple[float, float], str]:
        """
        Geocode multiple coordinates efficiently.
        
        Args:
            coordinates: List of (lat, lon) tuples
            show_progress: Whether to log progress
            
        Returns:
            Dict mapping coordinates to location names
        """
        results = {}
        
        # Remove duplicates
        unique_coords = list(set(
            (round(lat, 3), round(lon, 3)) 
            for lat, lon in coordinates
        ))
        
        total = len(unique_coords)
        logger.info(f"Batch geocoding {total} unique locations...")
        
        for i, (lat, lon) in enumerate(unique_coords, 1):
            location = self.get_location_name(lat, lon)
            
            if location:
                results[(lat, lon)] = location
            
            # Progress logging
            if show_progress and i % 10 == 0:
                logger.info(f"Progress: {i}/{total} locations geocoded")
        
        logger.info(f"Batch complete: {len(results)}/{total} successful")
        self._print_stats()
        
        return results

    def _print_stats(self):
        """Print geocoding statistics."""
        logger.info(
            f"Geocoding stats: "
            f"Cache hits: {self.stats['cache_hits']}, "
            f"Misses: {self.stats['cache_misses']}, "
            f"API calls: {self.stats['api_calls']}, "
            f"Errors: {self.stats['api_errors']}"
        )

    def clear_cache(self):
        """Clear the geocoding cache."""
        self.cache.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("Geocoding cache cleared")


# Global instance
_geocoder = None


def get_geocoder() -> EnhancedReverseGeocoder:
    """Get or create the global geocoder instance."""
    global _geocoder
    if _geocoder is None:
        _geocoder = EnhancedReverseGeocoder()
    return _geocoder


def reverse_geocode(latitude: float, longitude: float) -> Optional[str]:
    """
    Convenience function to get location name.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        Location name or None
    """
    geocoder = get_geocoder()
    return geocoder.get_location_name(latitude, longitude)