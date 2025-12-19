#!/usr/bin/env python3
"""
Script to clean up old soft-deleted images.
Run this script periodically to permanently delete images that have been
soft deleted for more than 30 days.
"""

import os
import sys

from app.database.images import db_permanently_delete_old_images
from app.logging.setup_logging import get_logger

# Add project root to PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = get_logger(__name__)


def main():
    """Clean up old soft-deleted images."""
    try:
        logger.info("Starting cleanup of old soft-deleted images")
        deleted_count = db_permanently_delete_old_images(days=30)

        if deleted_count > 0:
            logger.info("Successfully cleaned up %s old images", deleted_count)
            print(
                f"Cleaned up {deleted_count} images that were deleted more than 30 days ago"
            )
        else:
            logger.info("No old images to clean up")
            print("No images to clean up")

    except Exception as e:
        logger.error("Error during cleanup: %s", e)
        print(f"Error during cleanup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
