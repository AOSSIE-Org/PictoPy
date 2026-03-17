import os
from app.utils.images import image_util_remove_duplicate_images

def test_remove_duplicate_images(tmp_path):
    file1 = tmp_path / "img1.jpg"
    file1.write_text("data")

    # simulate duplicate reference
    records = [
        {"path": str(file1)},
        {"path": str(file1)},
    ]

    result = image_util_remove_duplicate_images(records)

    assert len(result) == 1
