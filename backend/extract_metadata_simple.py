#!/usr/bin/env python3
"""
Standalone script to extract location data from metadata and update the database.
"""

import json
import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "app" / "database" / "PictoPy.db"


def extract_and_update():
    """Extract location and datetime from metadata JSON and update database columns."""

    print("=" * 70)
    print("Starting metadata extraction...")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all images with metadata
    cursor.execute("SELECT id, metadata FROM images WHERE metadata IS NOT NULL AND metadata != ''")
    images = cursor.fetchall()

    print(f"\nFound {len(images)} images with metadata")

    updated_count = 0
    location_count = 0
    datetime_count = 0
    both_count = 0

    for image_id, metadata_str in images:
        try:
            # Parse JSON metadata
            metadata = json.loads(metadata_str)

            # Extract values
            latitude = metadata.get("latitude")
            longitude = metadata.get("longitude")
            date_created = metadata.get("date_created")

            has_location = latitude is not None and longitude is not None
            has_datetime = date_created is not None

            if has_location or has_datetime:
                # Update the database
                if has_location and has_datetime:
                    cursor.execute("UPDATE images SET latitude = ?, longitude = ?, captured_at = ? WHERE id = ?", (latitude, longitude, date_created, image_id))
                    both_count += 1
                elif has_location:
                    cursor.execute("UPDATE images SET latitude = ?, longitude = ? WHERE id = ?", (latitude, longitude, image_id))
                    location_count += 1
                elif has_datetime:
                    cursor.execute("UPDATE images SET captured_at = ? WHERE id = ?", (date_created, image_id))
                    datetime_count += 1

                updated_count += 1

                # Show progress every 50 images
                if updated_count % 50 == 0:
                    print(f"  Processed {updated_count} images...")

        except Exception as e:
            print(f"  Error processing image {image_id}: {e}")
            continue

    # Commit changes
    conn.commit()

    # Get final statistics
    cursor.execute("SELECT COUNT(*) FROM images WHERE latitude IS NOT NULL")
    total_with_location = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM images WHERE captured_at IS NOT NULL")
    total_with_datetime = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM images WHERE latitude IS NOT NULL AND captured_at IS NOT NULL")
    total_with_both = cursor.fetchone()[0]

    conn.close()

    # Print summary
    print("\n" + "=" * 70)
    print("METADATA EXTRACTION SUMMARY")
    print("=" * 70)
    print(f"Total images processed:       {len(images)}")
    print(f"Images updated:               {updated_count}")
    print(f"Images with location data:    {total_with_location} ({100 * total_with_location / len(images):.1f}%)")
    print(f"Images with datetime:         {total_with_datetime} ({100 * total_with_datetime / len(images):.1f}%)")
    print(f"Images with both:             {total_with_both} ({100 * total_with_both / len(images):.1f}%)")
    print(f"Images skipped (no data):     {len(images) - updated_count}")
    print("=" * 70)
    print("\n✅ Migration completed successfully!")
    print("\nNext steps:")
    print("  1. Start the backend: .env/bin/python3.12 main.py")
    print("  2. Test API: curl -X POST 'http://localhost:8000/api/memories/generate'")
    print()


if __name__ == "__main__":
    extract_and_update()
