import os
from PIL import Image, ExifTags
import pytest
from app.utils.images import image_util_generate_thumbnail

def test_thumbnail_preserves_exif_orientation(tmp_path):
    # Create a test image with an EXIF orientation flag (e.g., 6 = rotated 90 degrees CW)
    img_path = str(tmp_path / "test_portrait.jpg")
    thumb_path = str(tmp_path / "test_thumb.jpg")
    
    # Create a simple 200x100 rectangular image (landscape)
    img = Image.new("RGB", (200, 100), color="red")
    
    # Orientation 6 means the camera was rotated 90 degrees CW, so the actual photo should be viewed as 100x200 (portrait)
    exif_dict = {ExifTags.Base.Orientation: 6}
    exif = img.getexif()
    exif.update(exif_dict)
    
    img.save(img_path, format="JPEG", exif=exif)
    
    # Generate thumbnail
    success = image_util_generate_thumbnail(img_path, thumb_path, size=(50, 50))
    assert success
    
    # Verify the thumbnail was properly rotated to 50x100 (which fits into 50x50 so it scales down, width becomes 25, height 50)
    # The original image was 200x100.
    # Exif 6 rotates it 270 degrees, swapping width and height -> effectively 100x200.
    # Thumbnail size is (50, 50). Preserving aspect ratio (100:200 = 1:2), it becomes 25x50.
    
    with Image.open(thumb_path) as thumb:
        # Since it was 100x200 originally (after orientation), the thumbnail (max 50x50) 
        # should be scaled by 50/200 = 0.25 -> 25x50
        assert thumb.size == (25, 50)
