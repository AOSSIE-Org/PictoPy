from app.utils.images import image_util_is_valid_image


def test_image_util_is_valid_image(tmp_path):
    # Setup valid image (e.g., non-zero size, correct extension)
    valid_img = tmp_path / "valid.jpg"
    valid_img.write_text("dummy content")
    assert image_util_is_valid_image(str(valid_img)) is True

    # Setup valid image with uppercase extension
    valid_img_upper = tmp_path / "VALID.JPG"
    valid_img_upper.write_text("dummy content")
    assert image_util_is_valid_image(str(valid_img_upper)) is True

    # Setup unsupported extension
    invalid_ext = tmp_path / "invalid.txt"
    invalid_ext.write_text("dummy content")
    assert image_util_is_valid_image(str(invalid_ext)) is False

    # Setup zero-byte file
    zero_byte_img = tmp_path / "empty.jpg"
    zero_byte_img.touch()
    assert image_util_is_valid_image(str(zero_byte_img)) is False

    # Missing file
    missing_img = tmp_path / "missing.jpg"
    assert image_util_is_valid_image(str(missing_img)) is False

    # Directory with an image extension
    directory_img = tmp_path / "folder.jpg"
    directory_img.mkdir()
    assert image_util_is_valid_image(str(directory_img)) is False
