"""
Location and Datetime Metadata Extraction Utility

This module extracts GPS coordinates and capture datetime from image metadata JSON
and populates the dedicated latitude, longitude, and captured_at columns in the database.

Usage:
    python -m app.utils.extract_location_metadata

Author: PictoPy Team
Date: 2025-12-14
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

from app.config.settings import DATABASE_PATH
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
        self.stats = {
            'total': 0,
            'updated': 0,
            'with_location': 0,
            'with_datetime': 0,
            'with_both': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def extract_gps_coordinates(self, metadata: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
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
            lat = metadata.get('latitude')
            lon = metadata.get('longitude')
            
            # Method 2: Check nested 'exif' -> 'gps' structure
            if not lat or not lon:
                exif = metadata.get('exif', {})
                if isinstance(exif, dict):
                    gps = exif.get('gps', {})
                    if isinstance(gps, dict):
                        lat = lat or gps.get('latitude')
                        lon = lon or gps.get('longitude')
            
            # Method 3: Check alternative field names
            if not lat or not lon:
                lat = lat or metadata.get('lat') or metadata.get('Latitude')
                lon = lon or metadata.get('lon') or metadata.get('Longitude')
            
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
                        logger.warning(f"Invalid coordinate range: lat={lat}, lon={lon}")
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
            for field in ['date_created', 'datetime', 'date_taken', 'timestamp', 'DateTime']:
                if field in metadata:
                    date_str = metadata[field]
                    break
            
            # Method 2: Check nested 'exif' structure
            if not date_str:
                exif = metadata.get('exif', {})
                if isinstance(exif, dict):
                    date_str = (
                        exif.get('datetime') or 
                        exif.get('DateTime') or 
                        exif.get('DateTimeOriginal') or
                        exif.get('DateTimeDigitized')
                    )
            
            # Parse datetime string
            if date_str:
                date_str = str(date_str).strip()
                
                # Try multiple datetime formats
                datetime_formats = [
                    '%Y-%m-%d %H:%M:%S',        # 2024-01-15 14:30:45
                    '%Y:%m:%d %H:%M:%S',        # 2024:01:15 14:30:45 (EXIF format)
                    '%Y-%m-%dT%H:%M:%S',        # 2024-01-15T14:30:45 (ISO)
                    '%Y-%m-%dT%H:%M:%S.%f',     # 2024-01-15T14:30:45.123456
                    '%Y-%m-%d',                 # 2024-01-15
                    '%d/%m/%Y %H:%M:%S',        # 15/01/2024 14:30:45
                    '%d/%m/%Y',                 # 15/01/2024
                    '%m/%d/%Y %H:%M:%S',        # 01/15/2024 14:30:45
                    '%m/%d/%Y',                 # 01/15/2024
                ]
                
                # Try ISO format first (handles timezone)
                if 'T' in date_str:
                    try:
                        # Remove timezone suffix for simpler parsing
                        date_str_clean = date_str.replace('Z', '').split('+')[0].split('-')
                        # Rejoin only date-time parts (not timezone)
                        if len(date_str_clean) >= 3:
                            date_str_clean = '-'.join(date_str_clean[:3])
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
    
    def extract_all(self, metadata_json: str) -> Tuple[Optional[float], Optional[float], Optional[datetime]]:
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
        if not metadata_json or metadata_json == 'null':
            return None, None, None
        
        try:
            # Parse JSON
            if isinstance(metadata_json, bytes):
                metadata_json = metadata_json.decode('utf-8')
            
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
    
    def migrate_metadata(self) -> Dict[str, int]:
        """
        Main migration function to populate latitude, longitude, and captured_at
        columns for all images with metadata.
        
        This function:
        1. Connects to the database
        2. Retrieves all images with metadata
        3. Extracts GPS coordinates and datetime
        4. Updates the database with extracted values
        5. Reports statistics
        
        Returns:
            Dictionary with migration statistics
        """
        logger.info("=" * 70)
        logger.info("Starting metadata extraction migration...")
        logger.info("=" * 70)
        
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        try:
            # Fetch all images with metadata
            logger.info("Fetching images from database...")
            cursor.execute("SELECT id, metadata FROM images WHERE metadata IS NOT NULL")
            images = cursor.fetchall()
            
            self.stats['total'] = len(images)
            logger.info(f"Found {self.stats['total']} images with metadata")
            
            if self.stats['total'] == 0:
                logger.warning("No images found with metadata")
                return self.stats
            
            # Process each image
            updates = []
            for image_id, metadata_json in images:
                try:
                    lat, lon, dt = self.extract_all(metadata_json)
                    
                    # Only update if we extracted something
                    if lat is not None or lon is not None or dt is not None:
                        updates.append({
                            'id': image_id,
                            'latitude': lat,
                            'longitude': lon,
                            'captured_at': dt
                        })
                        
                        # Track statistics
                        has_location = lat is not None and lon is not None
                        has_datetime = dt is not None
                        
                        if has_location:
                            self.stats['with_location'] += 1
                        if has_datetime:
                            self.stats['with_datetime'] += 1
                        if has_location and has_datetime:
                            self.stats['with_both'] += 1
                    else:
                        self.stats['skipped'] += 1
                
                except Exception as e:
                    self.stats['errors'] += 1
                    logger.error(f"Error processing image {image_id}: {e}")
            
            # Batch update database
            if updates:
                logger.info(f"Updating {len(updates)} images...")
                
                for update_data in updates:
                    cursor.execute("""
                        UPDATE images 
                        SET latitude = ?, 
                            longitude = ?, 
                            captured_at = ?
                        WHERE id = ?
                    """, (
                        update_data['latitude'],
                        update_data['longitude'],
                        update_data['captured_at'],
                        update_data['id']
                    ))
                
                conn.commit()
                self.stats['updated'] = len(updates)
                logger.info(f"Successfully updated {self.stats['updated']} images")
            
            # Print summary
            self._print_summary()
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            conn.rollback()
            raise
        
        finally:
            conn.close()
        
        return self.stats
    
    def _print_summary(self):
        """Print migration summary statistics."""
        logger.info("\n" + "=" * 70)
        logger.info("METADATA EXTRACTION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total images processed:       {self.stats['total']}")
        logger.info(f"Images updated:               {self.stats['updated']}")
        logger.info(f"Images with location data:    {self.stats['with_location']} ({self._percentage('with_location')}%)")
        logger.info(f"Images with datetime:         {self.stats['with_datetime']} ({self._percentage('with_datetime')}%)")
        logger.info(f"Images with both:             {self.stats['with_both']} ({self._percentage('with_both')}%)")
        logger.info(f"Images skipped (no data):     {self.stats['skipped']}")
        logger.info(f"Errors encountered:           {self.stats['errors']}")
        logger.info("=" * 70)
    
    def _percentage(self, key: str) -> str:
        """Calculate percentage for a statistic."""
        if self.stats['total'] == 0:
            return "0.0"
        return f"{(self.stats[key] / self.stats['total'] * 100):.1f}"


def main():
    """
    Main entry point for the metadata extraction script.
    
    Usage:
        python -m app.utils.extract_location_metadata
    """
    try:
        # Check if database exists
        if not Path(DATABASE_PATH).exists():
            logger.error(f"Database not found at: {DATABASE_PATH}")
            return
        
        # Create extractor and run migration
        extractor = MetadataExtractor()
        stats = extractor.migrate_metadata()
        
        # Exit with appropriate code
        if stats['errors'] > 0:
            logger.warning("Migration completed with errors")
            exit(1)
        else:
            logger.info("✅ Migration completed successfully!")
            exit(0)
    
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
