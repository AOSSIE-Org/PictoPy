"""
Location and Datetime Metadata Extraction Utility

This module extracts GPS coordinates and capture datetime from image metadata JSON.
Used by the image upload process to automatically populate location and datetime fields.

Author: PictoPy Team
Date: 2025-12-14
"""

import json
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class MetadataExtractor:
    """
    Extracts location and datetime information from image metadata JSON.

    This class provides utilities to safely parse metadata and extract:
    - GPS coordinates (latitude, longitude)
    - Capture datetime
    """

    def __init__(self):
        """Initialize the metadata extractor."""
        pass

    def extract_gps_coordinates(
        self, metadata: Dict[str, Any]
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Extract GPS coordinates from metadata dictionary.

        Supports multiple metadata structures:
        - Top-level: {"latitude": 28.6, "longitude": 77.2}
        - Nested EXIF: {"exif": {"gps": {"latitude": 28.6, "longitude": 77.2}}}
        - Alternative names: lat, lon, Latitude, Longitude

        Args:
            metadata: Parsed metadata dictionary

        Returns:
            Tuple of (latitude, longitude) or (None, None) if not found

        Validates:
            - Latitude: -90 to 90
            - Longitude: -180 to 180
        """
        latitude = None
        longitude = None

        try:
            if not isinstance(metadata, dict):
                return None, None

            # Method 1: Direct top-level fields
            lat = metadata.get("latitude")
            lon = metadata.get("longitude")

            # Method 2: Check nested 'exif' -> 'gps' structure
            if not lat or not lon:
                exif = metadata.get("exif", {})
                if isinstance(exif, dict):
                    gps = exif.get("gps", {})
                    if isinstance(gps, dict):
                        lat = lat or gps.get("latitude")
                        lon = lon or gps.get("longitude")

            # Method 3: Check alternative field names
            if not lat or not lon:
                lat = lat or metadata.get("lat") or metadata.get("Latitude")
                lon = lon or metadata.get("lon") or metadata.get("Longitude")

            # Validate and convert coordinates
            if lat is not None and lon is not None:
                try:
                    lat = float(lat)
                    lon = float(lon)

                    # Sanity check: valid coordinate ranges
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        latitude = lat
                        longitude = lon
                    else:
                        logger.warning(
                            f"Invalid coordinate range: lat={lat}, lon={lon}"
                        )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not convert coordinates to float: {e}")

        except Exception as e:
            logger.error(f"Unexpected error extracting GPS coordinates: {e}")

        return latitude, longitude

    def extract_datetime(self, metadata: Dict[str, Any]) -> Optional[datetime]:
        """
        Extract capture datetime from metadata dictionary.

        Supports multiple datetime formats and field names:
        - date_created, datetime, date_taken, timestamp, DateTime
        - Nested: exif.datetime, exif.DateTimeOriginal
        - Formats: ISO 8601, EXIF format (YYYY:MM:DD HH:MM:SS), etc.

        Args:
            metadata: Parsed metadata dictionary

        Returns:
            datetime object or None if not found/parseable
        """
        captured_at = None

        try:
            if not isinstance(metadata, dict):
                return None

            # Method 1: Check common top-level field names
            date_str = None
            for field in [
                "date_created",
                "datetime",
                "date_taken",
                "timestamp",
                "DateTime",
            ]:
                if field in metadata:
                    date_str = metadata[field]
                    break

            # Method 2: Check nested 'exif' structure
            if not date_str:
                exif = metadata.get("exif", {})
                if isinstance(exif, dict):
                    date_str = (
                        exif.get("datetime")
                        or exif.get("DateTime")
                        or exif.get("DateTimeOriginal")
                        or exif.get("DateTimeDigitized")
                    )

            # Parse datetime string
            if date_str:
                date_str = str(date_str).strip()

                # Try multiple datetime formats
                datetime_formats = [
                    "%Y-%m-%d %H:%M:%S",  # 2024-01-15 14:30:45
                    "%Y:%m:%d %H:%M:%S",  # 2024:01:15 14:30:45 (EXIF format)
                    "%Y-%m-%dT%H:%M:%S",  # 2024-01-15T14:30:45 (ISO)
                    "%Y-%m-%dT%H:%M:%S.%f",  # 2024-01-15T14:30:45.123456
                    "%Y-%m-%d",  # 2024-01-15
                    "%d/%m/%Y %H:%M:%S",  # 15/01/2024 14:30:45
                    "%d/%m/%Y",  # 15/01/2024
                    "%m/%d/%Y %H:%M:%S",  # 01/15/2024 14:30:45
                    "%m/%d/%Y",  # 01/15/2024
                ]

                # Try ISO format first (handles timezone)
                if "T" in date_str:
                    try:
                        # Remove timezone suffix for simpler parsing
                        date_str_clean = (
                            date_str.replace("Z", "").split("+")[0].split("-")
                        )
                        # Rejoin only date-time parts (not timezone)
                        if len(date_str_clean) >= 3:
                            date_str_clean = "-".join(date_str_clean[:3])
                            captured_at = datetime.fromisoformat(date_str_clean)
                    except Exception:
                        pass

                # Try other formats
                if not captured_at:
                    for fmt in datetime_formats:
                        try:
                            captured_at = datetime.strptime(date_str, fmt)
                            break
                        except (ValueError, TypeError):
                            continue

                if not captured_at:
                    logger.warning(f"Could not parse datetime: {date_str}")

        except Exception as e:
            logger.error(f"Unexpected error extracting datetime: {e}")

        return captured_at

    def extract_all(
        self, metadata_json: str
    ) -> Tuple[Optional[float], Optional[float], Optional[datetime]]:
        """
        Extract GPS coordinates and datetime from metadata JSON string.

        Args:
            metadata_json: JSON string from images.metadata column

        Returns:
            Tuple of (latitude, longitude, captured_at)
        """
        latitude = None
        longitude = None
        captured_at = None

        # Handle null/empty metadata
        if not metadata_json or metadata_json == "null":
            return None, None, None

        try:
            # Parse JSON
            if isinstance(metadata_json, bytes):
                metadata_json = metadata_json.decode("utf-8")

            metadata = json.loads(metadata_json)

            # Extract GPS coordinates
            latitude, longitude = self.extract_gps_coordinates(metadata)

            # Extract datetime
            captured_at = self.extract_datetime(metadata)

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in metadata: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing metadata: {e}")

        return latitude, longitude, captured_at
