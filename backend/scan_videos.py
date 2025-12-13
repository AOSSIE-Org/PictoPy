#!/usr/bin/env python3
"""Script to scan existing folders for videos and add them to the database."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.folders import db_get_all_folder_details
from app.utils.videos import (
    video_util_get_videos_from_folder,
    video_util_prepare_video_records,
)
from app.database.videos import db_bulk_insert_videos
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def scan_existing_folders_for_videos():
    """Scan all existing folders for videos and add them to the database."""
    try:
        folders = db_get_all_folder_details()
        logger.info(f"Found {len(folders)} folders to scan for videos")
        
        total_videos_inserted = 0
        
        for folder_id, folder_path, *_ in folders:
            logger.info(f"Scanning folder: {folder_path}")
            
            if not os.path.exists(folder_path):
                logger.warning(f"Folder no longer exists: {folder_path}")
                continue
            
            video_files = video_util_get_videos_from_folder(folder_path, recursive=True)
            
            if video_files:
                logger.info(f"Found {len(video_files)} videos in {folder_path}")
                
                folder_path_to_id = {folder_path: folder_id}
                video_records = video_util_prepare_video_records(video_files, folder_path_to_id)
                
                if video_records:
                    # db_bulk_insert_videos returns actual inserted count
                    inserted_count = db_bulk_insert_videos(video_records)
                    if inserted_count > 0:
                        total_videos_inserted += inserted_count
                        logger.info(
                            f"Successfully inserted {inserted_count} videos from {folder_path} "
                            f"({len(video_records) - inserted_count} duplicates skipped)"
                        )
                    elif inserted_count == 0 and len(video_records) > 0:
                        logger.info(f"All {len(video_records)} videos from {folder_path} already exist in database")
            else:
                logger.info(f"No videos found in {folder_path}")
        
        logger.info(f"Video scan complete. Total videos inserted: {total_videos_inserted}")
        return total_videos_inserted
        
    except Exception as e:
        logger.error(f"Error scanning folders for videos: {e}")
        import traceback
        traceback.print_exc()
        return 0


if __name__ == "__main__":
    print("Scanning existing folders for videos...")
    count = scan_existing_folders_for_videos()
    print(f"Scan complete. Inserted {count} new videos to the database.")
