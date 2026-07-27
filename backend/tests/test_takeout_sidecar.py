import datetime
import json

import pytest

from app.utils.takeout_sidecar import takeout_sidecar_read


def _epoch(text: str) -> str:
    """Sidecars store local-time epochs; build one the reader will echo back."""
    return str(int(datetime.datetime.strptime(text, "%Y:%m:%d %H:%M:%S").timestamp()))


def write_sidecar(image_path, suffix=".supplemental-metadata.json", **payload):
    sidecar = image_path.with_name(image_path.name + suffix)
    sidecar.write_text(json.dumps(payload), encoding="utf-8")
    return sidecar


@pytest.fixture
def image(tmp_path):
    path = tmp_path / "IMG_2988.jpg"
    path.write_bytes(b"not a real jpeg")
    return path


class TestTakeoutSidecarRead:
    def test_reads_the_shutter_time(self, image):
        write_sidecar(
            image, photoTakenTime={"timestamp": _epoch("2025:12:18 21:19:07")}
        )
        assert takeout_sidecar_read(str(image))[0] == "2025:12:18 21:19:07"

    def test_prefers_shutter_time_over_upload_time(self, image):
        """
        creationTime is when Google received the file. On an export of an old
        library that is years after the photo was taken.
        """
        write_sidecar(
            image,
            creationTime={"timestamp": _epoch("2026:07:26 09:00:00")},
            photoTakenTime={"timestamp": _epoch("2024:04:21 18:27:16")},
        )
        assert takeout_sidecar_read(str(image))[0] == "2024:04:21 18:27:16"

    def test_falls_back_to_creation_time(self, image):
        write_sidecar(image, creationTime={"timestamp": _epoch("2024:04:21 18:27:16")})
        assert takeout_sidecar_read(str(image))[0] == "2024:04:21 18:27:16"

    @pytest.mark.parametrize(
        "suffix",
        [".supplemental-metadata.json", ".json", ".supplemental-metadata(1).json"],
    )
    def test_accepts_every_spelling_takeout_has_shipped(self, image, suffix):
        write_sidecar(
            image,
            suffix=suffix,
            photoTakenTime={"timestamp": _epoch("2025:09:13 12:28:39")},
        )
        assert takeout_sidecar_read(str(image))[0] == "2025:09:13 12:28:39"

    def test_reads_coordinates(self, image):
        write_sidecar(image, geoData={"latitude": 28.4504, "longitude": 77.5847})
        _, latitude, longitude = takeout_sidecar_read(str(image))
        assert (latitude, longitude) == (28.4504, 77.5847)

    def test_zero_coordinates_mean_no_location(self, image):
        """Takeout writes 0/0 rather than null, and 0/0 is in the Atlantic."""
        write_sidecar(
            image,
            photoTakenTime={"timestamp": _epoch("2025:09:13 12:28:39")},
            geoData={"latitude": 0.0, "longitude": 0.0},
        )
        assert takeout_sidecar_read(str(image))[1] is None

    def test_falls_back_to_the_original_exif_block(self, image):
        write_sidecar(
            image,
            geoData={"latitude": 0.0, "longitude": 0.0},
            geoDataExif={"latitude": 12.9716, "longitude": 77.5946},
        )
        assert takeout_sidecar_read(str(image))[1] == 12.9716

    def test_ignores_album_metadata_sitting_in_the_same_folder(self, tmp_path):
        """`metadata.json` describes the album, not any one photo."""
        album = tmp_path / "metadata"
        album.write_bytes(b"")
        write_sidecar(album, suffix=".json", entries=[{"title": "Photos from 2025"}])
        assert takeout_sidecar_read(str(album)) == (None, None, None)

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"photoTakenTime": {}},
            {"photoTakenTime": {"timestamp": ""}},
            {"photoTakenTime": {"timestamp": "not-a-number"}},
            {"photoTakenTime": "1734556747"},
        ],
    )
    def test_returns_none_without_a_usable_timestamp(self, image, payload):
        write_sidecar(image, **payload)
        assert takeout_sidecar_read(str(image))[0] is None

    def test_survives_a_corrupt_sidecar(self, image):
        image.with_name(image.name + ".json").write_text("{oh no", encoding="utf-8")
        assert takeout_sidecar_read(str(image)) == (None, None, None)

    def test_returns_none_when_no_sidecar_exists(self, image):
        assert takeout_sidecar_read(str(image)) == (None, None, None)

    def test_does_not_match_a_neighbours_sidecar(self, tmp_path):
        """
        Two files sharing a stem across extensions are different photos; the
        glob fallback must not hand one the other's date.
        """
        png = tmp_path / "IMG_3503.PNG"
        png.write_bytes(b"")
        jpg = tmp_path / "IMG_3503.JPG"
        jpg.write_bytes(b"")
        write_sidecar(jpg, photoTakenTime={"timestamp": _epoch("2026:03:07 22:30:28")})
        assert takeout_sidecar_read(str(png))[0] is None
