import os
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS
from datetime import datetime
from PIL.TiffImagePlugin import IFDRational


def extract_metadata(image_path):
    metadata = {}

    # Check if file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")

    try:
        with Image.open(image_path) as image:
            try:
                # Basic image info
                info_dict = {
                    "image_size": image.size,
                    "image_format": image.format,
                    "image_mode": image.mode,
                }
                metadata.update(info_dict)

                # Extract EXIF data
                exifdata = image.getexif()
                for tag_id in exifdata:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exifdata.get(tag_id)
                    if isinstance(data, (tuple, list)):
                        data = [
                            float(d) if isinstance(d, IFDRational) else d for d in data
                        ]
                    elif isinstance(data, IFDRational):
                        data = float(data)

                    if isinstance(data, bytes):
                        try:
                            data = data.decode("utf-8", errors="ignore")
                        except UnicodeDecodeError:
                            data = "[Unreadable Metadata]"

                    metadata[str(tag).lower().replace(" ", "_")] = data
            except Exception as exif_error:
                print(
                    f"Warning: Failed to extract EXIF data from {image_path}. Error: {exif_error}"
                )

    except FileNotFoundError:
        raise  # Re-raise if file is not found
    except UnidentifiedImageError:
        raise ValueError(f"Invalid image file: {image_path}")
    except OSError as os_error:
        raise OSError(f"Error processing file: {image_path}. {os_error}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error processing {image_path}: {e}")

    # File size extraction
    try:
        metadata["file_size"] = os.path.getsize(image_path)
    except OSError as file_error:
        print(
            f"Warning: Could not retrieve file size for {image_path}. Error: {file_error}"
        )

    # Image creation date
    try:
        creation_time = os.path.getctime(image_path)
        metadata["creation_date"] = datetime.fromtimestamp(creation_time).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except OSError as time_error:
        print(
            f"Warning: Could not retrieve creation date for {image_path}. Error: {time_error}"
        )
    return metadata
