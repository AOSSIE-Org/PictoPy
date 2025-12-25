# Standard library imports
import os
import uuid
import json
import subprocess
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# App-specific imports
from app.config.settings import THUMBNAIL_IMAGES_PATH as THUMBNAIL_DIR
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Supported video extensions
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.wmv', '.flv', '.3gp'}


def video_util_is_valid_video(file_path: str) -> bool:
    """Check if a file is a valid video based on extension."""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in VIDEO_EXTENSIONS


def video_util_get_videos_from_folder(folder_path: str, recursive: bool = True) -> List[str]:
    """Get all video files from a folder."""
    video_files = []
    
    try:
        if recursive:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if video_util_is_valid_video(file_path):
                        video_files.append(file_path)
        else:
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path) and video_util_is_valid_video(file_path):
                    video_files.append(file_path)
    except Exception as e:
        logger.error(f"Error getting videos from folder {folder_path}: {e}")
    
    return video_files


def video_util_extract_metadata(video_path: str) -> Dict[str, Any]:
    """Extract metadata from a video file using ffprobe."""
    metadata = {
        "name": os.path.basename(video_path),
        "file_location": video_path,
        "file_size": 0,
        "duration": None,
        "width": None,
        "height": None,
        "codec": None,
        "date_created": None,
    }
    
    try:
        # Get file size
        metadata["file_size"] = os.path.getsize(video_path)
        
        # Get file modification time as fallback date
        mtime = os.path.getmtime(video_path)
        from datetime import datetime
        metadata["date_created"] = datetime.fromtimestamp(mtime).isoformat()
        
        # Try to use ffprobe for detailed metadata
        try:
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'quiet', '-print_format', 'json',
                    '-show_format', '-show_streams', video_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                probe_data = json.loads(result.stdout)
                
                # Get format info
                if 'format' in probe_data:
                    fmt = probe_data['format']
                    if 'duration' in fmt:
                        metadata["duration"] = float(fmt['duration'])
                    if 'tags' in fmt:
                        tags = fmt['tags']
                        if 'creation_time' in tags:
                            metadata["date_created"] = tags['creation_time']
                
                # Get video stream info
                for stream in probe_data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        metadata["width"] = stream.get('width')
                        metadata["height"] = stream.get('height')
                        metadata["codec"] = stream.get('codec_name')
                        if not metadata["duration"] and 'duration' in stream:
                            metadata["duration"] = float(stream['duration'])
                        break
        except FileNotFoundError:
            logger.warning("ffprobe not found, using basic metadata only")
        except subprocess.TimeoutExpired:
            logger.warning(f"ffprobe timeout for {video_path}")
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse ffprobe output for {video_path}")
            
    except Exception as e:
        logger.error(f"Error extracting video metadata for {video_path}: {e}")
    
    return metadata


def video_util_generate_thumbnail(
    video_path: str, 
    thumbnail_path: str, 
    time_offset: float = 0.1
) -> bool:
    """
    Generate a thumbnail from a video file.
    
    Args:
        video_path: Path to the video file
        thumbnail_path: Path where thumbnail should be saved
        time_offset: Position in video (0.0-1.0) to capture thumbnail from
    """
    try:
        # Ensure thumbnail directory exists
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
        
        # Get video duration first
        duration = None
        try:
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1', video_path
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
        except:
            pass
        
        # Calculate timestamp for thumbnail
        timestamp = "00:00:01"  # Default to 1 second
        if duration:
            seek_time = duration * time_offset
            hours = int(seek_time // 3600)
            minutes = int((seek_time % 3600) // 60)
            seconds = int(seek_time % 60)
            timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Generate thumbnail using ffmpeg
        result = subprocess.run(
            [
                'ffmpeg', '-y', '-ss', timestamp, '-i', video_path,
                '-vframes', '1', '-vf', 'scale=400:-1',
                '-q:v', '2', thumbnail_path
            ],
            capture_output=True,
            timeout=30
        )
        
        if result.returncode == 0 and os.path.exists(thumbnail_path):
            logger.debug(f"Generated thumbnail for {video_path}")
            return True
        else:
            logger.warning(f"Failed to generate thumbnail for {video_path}: {result.stderr.decode()}")
            return False
            
    except FileNotFoundError:
        logger.error("ffmpeg not found. Please install ffmpeg for video thumbnail generation.")
        return False
    except subprocess.TimeoutExpired:
        logger.warning(f"Thumbnail generation timeout for {video_path}")
        return False
    except Exception as e:
        logger.error(f"Error generating thumbnail for {video_path}: {e}")
        return False


def _normalize_path(path: str) -> str:
    """Normalize a path for safe comparison."""
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def _find_matching_folder_id(
    video_path: str,
    folder_path_to_id: Dict[str, str]
) -> Optional[str]:
    """
    Find the most specific (deepest) matching folder ID for a video path.
    
    Uses normalized path comparison to prevent partial matches.
    """
    video_dir = _normalize_path(os.path.dirname(video_path))
    best_match: Optional[str] = None
    best_match_length = -1
    
    for folder_path, folder_id in folder_path_to_id.items():
        normalized_folder = _normalize_path(folder_path)
        
        # Check for exact match or proper subdirectory match
        if video_dir == normalized_folder:
            # Exact match - this is the best possible match
            return folder_id
        elif video_dir.startswith(normalized_folder + os.sep):
            # Proper subdirectory match - track the longest (most specific) match
            if len(normalized_folder) > best_match_length:
                best_match = folder_id
                best_match_length = len(normalized_folder)
    
    return best_match


def video_util_prepare_video_records(
    video_files: List[str],
    folder_path_to_id: Dict[str, str]
) -> List[Dict[str, Any]]:
    """Prepare video records for database insertion."""
    video_records = []
    
    for video_path in video_files:
        try:
            video_id = str(uuid.uuid4())
            
            # Find folder ID using safe path matching
            folder_id = _find_matching_folder_id(video_path, folder_path_to_id)
            
            if folder_id is None:
                logger.warning(f"Could not find folder ID for video: {video_path}")
                continue
            
            # Generate thumbnail path
            thumbnail_filename = f"video_thumb_{video_id}.jpg"
            thumbnail_path = os.path.join(THUMBNAIL_DIR, thumbnail_filename)
            
            # Extract metadata
            metadata = video_util_extract_metadata(video_path)
            
            # Generate thumbnail
            video_util_generate_thumbnail(video_path, thumbnail_path)
            
            video_record = {
                "id": video_id,
                "path": video_path,
                "folder_id": folder_id,
                "thumbnailPath": thumbnail_path if os.path.exists(thumbnail_path) else "",
                "metadata": metadata,  # Will be serialized in db_bulk_insert_videos
                "duration": metadata.get("duration"),
                "width": metadata.get("width"),
                "height": metadata.get("height"),
            }
            
            video_records.append(video_record)
            
        except Exception as e:
            logger.error(f"Error preparing video record for {video_path}: {e}")
    
    return video_records


def video_util_format_duration(seconds: Optional[float]) -> str:
    """Format duration in seconds to HH:MM:SS or MM:SS string."""
    if seconds is None:
        return "00:00"
    
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
