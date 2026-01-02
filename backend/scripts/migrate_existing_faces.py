"""
Migration script to re-process existing photos with face alignment enabled.

This script allows developers who already have uploaded photos to regenerate
face embeddings with the new alignment feature, improving clustering accuracy.

Usage:
    python scripts/migrate_existing_faces.py [--dry-run]
"""

import argparse
import sqlite3
from typing import List, Dict
from app.config.settings import DATABASE_PATH, FACE_ALIGNMENT_ENABLED
from app.models.FaceDetector import FaceDetector
from app.database.connection import get_db_connection
from app.utils.face_clusters import cluster_util_face_clusters_sync
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def get_all_images_with_faces() -> List[Dict]:
    """Get all images that have faces detected."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT i.id, i.path
            FROM images i
            INNER JOIN faces f ON i.id = f.image_id
            ORDER BY i.path
        """)
        
        results = cursor.fetchall()
        images = [{"id": row[0], "path": row[1]} for row in results]
        
        logger.info(f"Found {len(images)} images with faces")
        return images
        
    finally:
        conn.close()


def clear_faces_for_image(image_id: str) -> int:
    """Clear existing face embeddings for an image."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM faces WHERE image_id = ?", (image_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count
        
    finally:
        conn.close()


def migrate_image(face_detector: FaceDetector, image_id: str, image_path: str, dry_run: bool = False) -> bool:
    """
    Re-process a single image with face alignment enabled.
    
    Args:
        face_detector: FaceDetector instance
        image_id: Image ID
        image_path: Path to image file
        dry_run: If True, don't actually modify database
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if dry_run:
            logger.info(f"[DRY RUN] Would re-process: {image_path}")
            return True
        
        # Clear old face embeddings
        deleted = clear_faces_for_image(image_id)
        logger.debug(f"Cleared {deleted} old face(s) for {image_id}")
        
        # Detect faces with new alignment
        result = face_detector.detect_faces(image_id, image_path, forSearch=False)
        
        if result and result['num_faces'] > 0:
            logger.info(f"✓ Re-processed {image_path}: {result['num_faces']} face(s)")
            return True
        else:
            logger.warning(f"⚠ No faces detected in {image_path}")
            return True
            
    except Exception as e:
        logger.error(f"✗ Failed to process {image_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Re-process existing photos with face alignment"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of images to process (for testing)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Face Alignment Migration Script")
    print("=" * 70)
    
    # Check if alignment is enabled
    if not FACE_ALIGNMENT_ENABLED:
        print("\n⚠ WARNING: FACE_ALIGNMENT_ENABLED is False in settings.py")
        print("   This migration will regenerate embeddings WITHOUT alignment.")
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return 1
    else:
        print(f"\n✓ Face alignment is ENABLED")
    
    if args.dry_run:
        print("✓ DRY RUN mode (no changes will be made)")
    
    # Get all images
    images = get_all_images_with_faces()
    
    if not images:
        print("\n✓ No images with faces found. Nothing to migrate.")
        return 0
    
    if args.limit:
        images = images[:args.limit]
        print(f"\n⚠ Limiting to first {args.limit} images")
    
    print(f"\nFound {len(images)} images to process")
    
    if not args.dry_run:
        response = input(f"\nThis will re-generate embeddings for {len(images)} images.\nContinue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return 1
    
    # Initialize face detector
    print("\n" + "=" * 70)
    print("Initializing face detector...")
    face_detector = FaceDetector()
    
    # Process images
    print("=" * 70)
    print("Processing images...")
    print("=" * 70)
    
    success_count = 0
    fail_count = 0
    
    for i, img in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}] Processing: {img['path']}")
        
        if migrate_image(face_detector, img['id'], img['path'], dry_run=args.dry_run):
            success_count += 1
        else:
            fail_count += 1
    
    # Clean up
    face_detector.close()
    
    # Re-cluster if not dry run
    if not args.dry_run and success_count > 0:
        print("\n" + "=" * 70)
        print("Re-clustering faces...")
        print("=" * 70)
        
        try:
            cluster_count = cluster_util_face_clusters_sync(force_full_reclustering=True)
            print(f"✓ Created {cluster_count} clusters")
        except Exception as e:
            print(f"✗ Clustering failed: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total images: {len(images)}")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    
    if args.dry_run:
        print("\n✓ DRY RUN completed. No changes were made.")
        print("  Run without --dry-run to actually migrate.")
    else:
        print(f"\n✓ Migration completed!")
        print(f"  {success_count} images re-processed with face alignment.")
    
    print("=" * 70)
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
