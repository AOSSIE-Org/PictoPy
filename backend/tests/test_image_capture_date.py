from typing import Any, Dict, Optional

import pytest
from PIL import ExifTags

from app.utils.images import EXIF_IFD_POINTER, _extract_capture_datetime

TAG_IDS = {name: tag_id for tag_id, name in ExifTags.TAGS.items()}
DATE_TIME = TAG_IDS["DateTime"]
DATE_TIME_ORIGINAL = TAG_IDS["DateTimeOriginal"]
DATE_TIME_DIGITIZED = TAG_IDS["DateTimeDigitized"]


class FakeExif(dict):
    """
    Stands in for Pillow's Exif object.

    The distinction that matters: the object itself is IFD0, and the capture
    timestamps live behind a pointer in a separate sub-IFD.
    """

    def __init__(
        self, ifd0: Optional[Dict[int, Any]] = None, sub_ifd: Optional[Dict] = None
    ):
        super().__init__(ifd0 or {})
        self._sub_ifd = sub_ifd or {}

    def get_ifd(self, tag: int) -> Dict[int, Any]:
        return self._sub_ifd if tag == EXIF_IFD_POINTER else {}


class ExplodingExif(FakeExif):
    def get_ifd(self, tag: int) -> Dict[int, Any]:
        raise OSError("corrupt exif")


class TestExtractCaptureDatetime:
    def test_reads_the_sub_ifd(self):
        """
        The regression this guards: getexif() returns IFD0, DateTimeOriginal
        lives in the sub-IFD, so reading only the top level finds nothing and
        every photo falls back to its file mtime.
        """
        exif = FakeExif(sub_ifd={DATE_TIME_ORIGINAL: "2024:07:26 10:30:00"})
        assert _extract_capture_datetime(exif) == "2024:07:26 10:30:00"

    def test_prefers_the_original_over_the_file_timestamp(self):
        exif = FakeExif(
            ifd0={DATE_TIME: "2026:07:26 09:00:00"},
            sub_ifd={DATE_TIME_ORIGINAL: "2024:02:06 10:36:24"},
        )
        assert _extract_capture_datetime(exif) == "2024:02:06 10:36:24"

    def test_prefers_original_over_digitized(self):
        exif = FakeExif(
            sub_ifd={
                DATE_TIME_DIGITIZED: "2024:02:07 11:00:00",
                DATE_TIME_ORIGINAL: "2024:02:06 10:36:24",
            }
        )
        assert _extract_capture_datetime(exif) == "2024:02:06 10:36:24"

    def test_falls_back_through_the_tag_order(self):
        assert (
            _extract_capture_datetime(
                FakeExif(sub_ifd={DATE_TIME_DIGITIZED: "2024:02:07 11:00:00"})
            )
            == "2024:02:07 11:00:00"
        )
        assert (
            _extract_capture_datetime(FakeExif(ifd0={DATE_TIME: "2024:02:08 12:00:00"}))
            == "2024:02:08 12:00:00"
        )

    def test_decodes_bytes_and_strips_nul_padding(self):
        exif = FakeExif(sub_ifd={DATE_TIME_ORIGINAL: b"2024:07:26 10:30:00\x00"})
        assert _extract_capture_datetime(exif) == "2024:07:26 10:30:00"

    @pytest.mark.parametrize(
        "exif",
        [
            None,
            FakeExif(),
            FakeExif(sub_ifd={DATE_TIME_ORIGINAL: ""}),
            FakeExif(sub_ifd={DATE_TIME_ORIGINAL: "   "}),
        ],
    )
    def test_returns_none_without_a_usable_value(self, exif):
        assert _extract_capture_datetime(exif) is None

    def test_survives_a_broken_sub_ifd(self):
        """A corrupt sub-IFD must not lose an otherwise readable IFD0 date."""
        exif = ExplodingExif(ifd0={DATE_TIME: "2024:02:08 12:00:00"})
        assert _extract_capture_datetime(exif) == "2024:02:08 12:00:00"

    def test_plain_dict_without_sub_ifd_support(self):
        """Older Pillow paths hand back a bare mapping."""

        class BareExif(dict):
            pass

        assert (
            _extract_capture_datetime(BareExif({DATE_TIME: "2024:02:08 12:00:00"}))
            == "2024:02:08 12:00:00"
        )
