from PIL import Image
from PIL.ExifTags import TAGS

# https://thepythoncode.com/article/extracting-image-metadata-in-python
def extract_metadata(image_path):
    metadata = {}

    with Image.open(image_path) as image:
        info_dict = {
            "Filename": image.filename,
            "Image Size": image.size,
            "Image Height": image.height,
            "Image Width": image.width,
            "Image Format": image.format,
            "Image Mode": image.mode,
            "Image is Animated": getattr(image, "is_animated", False),
            "Frames in Image": getattr(image, "n_frames", 1)
        }
        metadata.update(info_dict)

        exifdata = image.getexif()
        for tag_id in exifdata:
            tag = TAGS.get(tag_id, tag_id)
            data = exifdata.get(tag_id)
            if isinstance(data, bytes):
                data = data.decode()
            metadata[tag] = data

    return metadata