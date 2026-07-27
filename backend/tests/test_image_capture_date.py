import datetime
import json
from typing import Any, Dict, Optional

import pytest
from PIL import ExifTags, Image

from app.utils.extract_location_metadata import MetadataExtractor
from app.utils.images import (
    EXIF_IFD_POINTER,
    _extract_capture_datetime,
    image_util_extract_metadata,
)

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


def _write_image(path, exif_date=None):
    image = Image.new("RGB", (4, 4), "white")
    if exif_date:
        exif = image.getexif()
        exif.get_ifd(EXIF_IFD_POINTER)[DATE_TIME_ORIGINAL] = exif_date
        image.save(path, exif=exif)
    else:
        image.save(path)
    return path


def _sidecar(path, exif_date):
    epoch = int(datetime.datetime.strptime(exif_date, "%Y:%m:%d %H:%M:%S").timestamp())
    path.with_name(path.name + ".supplemental-metadata.json").write_text(
        json.dumps({"photoTakenTime": {"timestamp": str(epoch)}}), encoding="utf-8"
    )


class TestDateSource:
    """
    A capture date and a filesystem mtime are different facts. Conflating them
    is what let a bulk copy read as one 40-minute burst of photos on import
    day, which the import-event trigger then curated into a memory.
    """

    def test_exif_date_is_marked_trustworthy(self, tmp_path):
        path = _write_image(tmp_path / "a.jpg", "2024:02:06 10:36:24")
        metadata = image_util_extract_metadata(str(path))
        assert metadata["date_source"] == "exif"
        assert metadata["date_created"] == "2024-02-06T10:36:24"

    def test_sidecar_fills_in_for_a_stripped_export(self, tmp_path):
        path = _write_image(tmp_path / "b.jpg")
        _sidecar(path, "2025:09:13 12:28:39")
        metadata = image_util_extract_metadata(str(path))
        assert metadata["date_source"] == "sidecar"
        assert metadata["date_created"] == "2025-09-13T12:28:39"

    def test_exif_wins_over_the_sidecar(self, tmp_path):
        path = _write_image(tmp_path / "c.jpg", "2024:02:06 10:36:24")
        _sidecar(path, "2025:09:13 12:28:39")
        assert image_util_extract_metadata(str(path))["date_source"] == "exif"

    def test_mtime_is_marked_as_a_guess(self, tmp_path):
        path = _write_image(tmp_path / "d.jpg")
        metadata = image_util_extract_metadata(str(path))
        assert metadata["date_source"] == "filesystem"
        assert metadata["date_created"] is not None

    def test_a_missing_file_has_no_date_source(self, tmp_path):
        metadata = image_util_extract_metadata(str(tmp_path / "gone.jpg"))
        assert metadata["date_source"] == "unknown"


class TestCapturedAtRefusesGuessedDates:
    """
    date_created keeps the mtime so the gallery still has something to show;
    captured_at must not, because every memories query reads it as fact.
    """

    def setup_method(self):
        self.extractor = MetadataExtractor()

    def _captured_at(self, metadata):
        return self.extractor.extract_all(json.dumps(metadata))[2]

    @pytest.mark.parametrize("source", ["exif", "sidecar"])
    def test_keeps_a_real_capture_date(self, source):
        captured_at = self._captured_at(
            {"date_created": "2024-02-06T10:36:24", "date_source": source}
        )
        assert captured_at == datetime.datetime(2024, 2, 6, 10, 36, 24)

    @pytest.mark.parametrize("source", ["filesystem", "unknown"])
    def test_drops_a_guessed_date(self, source):
        assert (
            self._captured_at(
                {"date_created": "2026-07-26T09:00:00", "date_source": source}
            )
            is None
        )

    def test_metadata_predating_the_field_is_still_read(self):
        """Rows written before date_source existed keep working until re-sync."""
        assert self._captured_at(
            {"date_created": "2024-02-06T10:36:24"}
        ) == datetime.datetime(2024, 2, 6, 10, 36, 24)
