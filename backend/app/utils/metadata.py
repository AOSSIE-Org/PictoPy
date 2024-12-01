import os
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from PIL.TiffImagePlugin import IFDRational


def extract_metadata(image_path):
    metadata = {}

    with Image.open(image_path) as image:
        info_dict = {
            # "filename": image.filename,
            # "image_is_animated": getattr(image, "is_animated", False),
            # "frames_in_image": getattr(image, "n_frames", 1)
            # "image_height": image.height,
            # "image_width": image.width,
            "image_size": image.size,
            "image_format": image.format,
            "image_mode": image.mode,
        }
        metadata.update(info_dict)

        exifdata = image.getexif()
        for tag_id in exifdata:
            tag = TAGS.get(tag_id, tag_id)
            data = exifdata.get(tag_id)

            if isinstance(data,tuple) or isinstance(data,list) : 
                data = [float(d) if isinstance(d,IFDRational) else d for d in data ]
            elif isinstance(data,IFDRational) : 
                data = float(data)

            if isinstance(data, bytes):
                data = data.decode()
            metadata[str(tag).lower().replace(" ", "_")] = data

    # image file size
    file_size = os.path.getsize(image_path)
    metadata["file_size"] = file_size

    # image creation date
    creation_time = os.path.getctime(image_path)
    creation_date = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S")
    metadata["creation_date"] = creation_date

    return metadata