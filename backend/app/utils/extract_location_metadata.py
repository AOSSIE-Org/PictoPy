"""
Location and Datetime Metadata Extraction Utility

This module extracts GPS coordinates and capture datetime from image metadata JSON.
Used by the image upload process to automatically populate location and datetime fields.

Author: PictoPy Team
Date: 2025-12-14
"""

import json
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, Iterable

from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)


# Where a metadata date came from. Only the first two are real capture times;
# a filesystem mtime is when the file was written, which for a copied library
# is import day, so it must never reach images.captured_at.
DATE_SOURCE_EXIF = "exif"
DATE_SOURCE_SIDECAR = "sidecar"
DATE_SOURCE_CONTAINER = "container"
DATE_SOURCE_FILESYSTEM = "filesystem"
DATE_SOURCE_UNKNOWN = "unknown"

TRUSTED_DATE_SOURCES = frozenset(
    {DATE_SOURCE_EXIF, DATE_SOURCE_SIDECAR, DATE_SOURCE_CONTAINER}
)


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

    @staticmethod
    def _resolve_coordinate(
        field: str, candidates: Iterable[Any], limit: float
    ) -> Optional[float]:
        """
        Return the first candidate that is usable as a coordinate.

        Candidates are supplied in order of preference and each one is converted
        and range checked in turn. A candidate is skipped when it is absent
        (None or a blank string), cannot be read as a number, or falls outside
        the valid range, so a malformed or out-of-range value in a preferred
        field does not mask a good value in a less preferred one.

        Zero is deliberately kept: it is a real location on the equator and the
        prime meridian, but it is falsy in Python, so an `a or b` fallback chain
        would silently discard it.

        Args:
            field: Field name, used only for log messages
            candidates: Candidate values, in order of preference
            limit: Largest valid magnitude (90 for latitude, 180 for longitude)

        Returns:
            The first usable coordinate, or None if no candidate qualifies
        """
        for value in candidates:
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            # bool is a subclass of int, so float(True) would otherwise pass as 1.0
            if isinstance(value, bool):
                logger.warning(f"Ignoring boolean {field}: {value!r}")
                continue

            try:
                number = float(value)
            except (ValueError, TypeError, OverflowError):
                # OverflowError covers integers too large to become a float,
                # which JSON metadata can carry with no size limit
                logger.warning(f"Ignoring unreadable {field}: {value!r}")
                continue

            # Also rejects NaN, which fails every comparison
            if not -limit <= number <= limit:
                logger.warning(f"Ignoring out-of-range {field}: {number}")
                continue

            return number

        return None

    def extract_gps_coordinates(
        self, metadata: Dict[str, Any]
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Extract GPS coordinates from metadata dictionary.

        Supports multiple metadata structures, checked in order of preference:
        - Top-level: {"latitude": 28.6, "longitude": 77.2}
        - Nested EXIF: {"exif": {"gps": {"latitude": 28.6, "longitude": 77.2}}}
        - Alternative names: lat, lon, Latitude, Longitude

        Latitude and longitude are resolved independently, and each falls
        through to the next source when a value is missing, unreadable or out of
        range, so a coordinate pair may be assembled from two different sources.

        Args:
            metadata: Parsed metadata dictionary

        Returns:
            Tuple of (latitude, longitude), or (None, None) when either half
            cannot be resolved, since one coordinate on its own is not a location

        Validates:
            - Latitude: -90 to 90
            - Longitude: -180 to 180

        Note:
            A coordinate of 0 is a real location, not a missing value, so it is
            kept rather than falling through to the next source.
        """
        latitude = None
        longitude = None

        try:
            if not isinstance(metadata, dict):
                return None, None

            # Nested 'exif' -> 'gps' structure, when the image has one
            exif = metadata.get("exif")
            exif = exif if isinstance(exif, dict) else {}
            gps = exif.get("gps")
            gps = gps if isinstance(gps, dict) else {}

            # Direct top-level fields, then nested EXIF GPS, then the
            # alternative spellings some sources use.
            latitude = self._resolve_coordinate(
                "latitude",
                (
                    metadata.get("latitude"),
                    gps.get("latitude"),
                    metadata.get("lat"),
                    metadata.get("Latitude"),
                ),
                90.0,
            )
            longitude = self._resolve_coordinate(
                "longitude",
                (
                    metadata.get("longitude"),
                    gps.get("longitude"),
                    metadata.get("lon"),
                    metadata.get("Longitude"),
                ),
                180.0,
            )

            # A lone latitude or longitude is not a usable location
            if latitude is None or longitude is None:
                return None, None

        except Exception as e:
            logger.error(f"Unexpected error extracting GPS coordinates: {e}")
            return None, None

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

            # A date the extractor itself guessed from the filesystem is not a
            # capture time. Saying "unknown" is what stops a bulk copy from
            # looking like one long burst of photos on import day.
            source = metadata.get("date_source")
            if source is not None and source not in TRUSTED_DATE_SOURCES:
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
                        except (ValueError, TypeError, OverflowError):
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
