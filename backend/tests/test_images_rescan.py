"""
The watcher calls sync-folder on any file change, so the folder walk reruns
constantly over folders that are almost entirely unchanged. These cover the
check that keeps it from rereading and re-thumbnailing every file each time.
"""

import datetime
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Iterator, List

import cv2
import numpy as np
import pytest
from PIL import Image

from app.database.folders import db_create_folders_table
from app.database.images import (
    ImageSyncState,
    db_bulk_insert_images,
    db_create_images_table,
    db_get_images_by_folder_ids,
    db_get_image_sync_state_by_folder_ids,
    db_get_unembedded_images,
    db_get_untagged_images,
)
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.utils.SigLIP import siglip_util_preprocess_image
from app.utils.image_conversion import (
    image_util_normalize_16bit_grayscale,
    image_util_read_bgr,
)
from app.utils.images import (
    EXIF_IFD_POINTER,
    image_util_extract_metadata,
    image_util_generate_thumbnail,
    image_util_is_unchanged,
    image_util_prepare_image_records,
    image_util_process_folder_images,
)


@pytest.fixture(scope="function")
def test_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Point the image/folder DB modules at a fresh tempfile database."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.images.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.folders.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.yolo_mapping.DATABASE_PATH", db_path)

    db_create_YOLO_classes_table()  # mappings (image_classes FK target)
    db_create_folders_table()  # folders (images.folder_id FK target)
    db_create_images_table()

    yield db_path

    os.unlink(db_path)


@pytest.fixture
def folder(test_db: str) -> str:
    """Insert a folder row to satisfy the images.folder_id FK."""
    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO folders (folder_id, folder_path, last_modified_time, AI_Tagging) "
        "VALUES (?, ?, 0, 1)",
        ("folder-1", "/photos"),
    )
    conn.commit()
    conn.close()
    return "folder-1"


def _photo(path, colour=(10, 20, 30)) -> str:
    """Write a real JPEG; the walk opens and verifies every candidate file."""
    Image.new("RGB", (8, 8), colour).save(path, "JPEG")
    return str(path)


def _thumbnail(path) -> str:
    Image.new("RGB", (4, 4), "white").save(path, "JPEG")
    return str(path)


def _state(photo: str, thumbnail: str, **overrides: Any) -> ImageSyncState:
    """The sync state a previous scan would have recorded for an untouched file."""
    stats = os.stat(photo)
    recorded = ImageSyncState(
        thumbnailPath=thumbnail,
        file_size=stats.st_size,
        file_mtime=int(stats.st_mtime),
        date_source=None,
    )
    recorded.update(overrides)  # type: ignore[typeddict-item]
    return recorded


class Test16BitGrayscaleImages:
    @pytest.mark.parametrize("dtype", ["<u2", ">u2"])
    @pytest.mark.parametrize(
        ("pixel", "expected"), [(0, 0), (255, 0), (256, 1), (32768, 128), (65535, 255)]
    )
    def test_normalization_matches_opencv_and_siglip_inputs(
        self, tmp_path: Path, dtype: str, pixel: int, expected: int
    ) -> None:
        image_path = tmp_path / "gray16.tiff"
        Image.fromarray(np.full((16, 16), pixel, dtype=dtype)).save(image_path)

        with Image.open(image_path) as image:
            normalized = image_util_normalize_16bit_grayscale(image)
        assert normalized.mode == "RGB"
        assert np.asarray(normalized).dtype == np.uint8
        assert np.asarray(normalized)[0, 0].tolist() == [expected] * 3

        cv_image = cv2.imread(str(image_path))
        assert cv_image is not None
        assert cv_image[0, 0].tolist() == [expected] * 3
        loaded = image_util_read_bgr(str(image_path))
        assert loaded is not None
        assert loaded[0, 0].tolist() == [expected] * 3

        siglip_input = siglip_util_preprocess_image(str(image_path), 8)
        assert siglip_input is not None
        assert np.allclose(
            siglip_input[:, 0, 0], [expected / 255 * 2 - 1] * 3, atol=1e-6
        )

    def test_16_bit_tiff_falls_back_when_opencv_cannot_decode(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        image_path = tmp_path / "gray16.tiff"
        Image.fromarray(np.full((16, 16), 32768, dtype=np.uint16)).save(image_path)
        monkeypatch.setattr("app.utils.image_conversion.cv2.imread", lambda path: None)

        image = image_util_read_bgr(str(image_path))
        assert image is not None
        assert image[0, 0].tolist() == [128, 128, 128]

    @pytest.mark.parametrize("pixel", [128, 32768, 65535])
    def test_32_bit_tiff_preserves_existing_siglip_conversion(
        self, tmp_path: Path, pixel: int
    ) -> None:
        image_path = tmp_path / "gray32.tiff"
        Image.fromarray(np.full((16, 16), pixel, dtype=np.int32)).save(image_path)

        with Image.open(image_path) as image:
            assert image.mode == "I"
            assert image_util_normalize_16bit_grayscale(image) is image
            expected = image.convert("RGB").getpixel((0, 0))[0]

        siglip_input = siglip_util_preprocess_image(str(image_path), 8)
        assert siglip_input is not None
        assert np.allclose(
            siglip_input[:, 0, 0], [expected / 255 * 2 - 1] * 3, atol=1e-6
        )

    def test_thumbnail_generation_succeeds_for_16_bit_tiff(
        self, tmp_path: Path
    ) -> None:
        image_path = tmp_path / "gray16.tiff"
        thumbnail_path = tmp_path / "gray16.jpg"
        Image.fromarray(np.full((16, 16), 32768, dtype=np.uint16)).save(image_path)

        assert image_util_generate_thumbnail(str(image_path), str(thumbnail_path))
        with Image.open(thumbnail_path) as thumbnail:
            assert thumbnail.convert("RGB").getpixel((0, 0)) == (128, 128, 128)

    def test_normal_indexing_inserts_16_bit_tiff(
        self,
        tmp_path: Path,
        test_db: str,
        folder: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        photos = tmp_path / "photos"
        photos.mkdir()
        thumbnails = tmp_path / "thumbs"
        monkeypatch.setattr("app.utils.images.THUMBNAIL_IMAGES_PATH", str(thumbnails))
        image_path = photos / "gray16.tiff"
        Image.fromarray(np.full((16, 16), 32768, dtype=np.uint16)).save(image_path)

        assert image_util_process_folder_images([(str(photos), folder, False)])
        indexed = db_get_images_by_folder_ids([folder])

        assert len(indexed) == 1
        assert indexed[0][1] == str(image_path)
        assert Path(indexed[0][2]).is_file()
        assert [image["path"] for image in db_get_untagged_images()] == [
            str(image_path)
        ]
        assert [image["path"] for image in db_get_unembedded_images()] == [
            str(image_path)
        ]

    def test_non_16_bit_modes_are_unchanged(self) -> None:
        images = [
            Image.new("RGB", (1, 1)),
            Image.new("RGBA", (1, 1)),
            Image.new("L", (1, 1)),
            Image.new("CMYK", (1, 1)),
            Image.new("P", (1, 1)),
        ]

        assert all(
            image_util_normalize_16bit_grayscale(image) is image for image in images
        )

    def test_animated_gif_keeps_its_palette_frames(self, tmp_path: Path) -> None:
        first = Image.new("P", (2, 2), 0)
        first.putpalette([255, 0, 0, 0, 255, 0] + [0, 0, 0] * 254)
        second = Image.new("P", (2, 2), 1)
        second.putpalette(first.getpalette())
        gif_path = tmp_path / "animated.gif"
        first.save(gif_path, save_all=True, append_images=[second], duration=100)

        with Image.open(gif_path) as gif:
            assert gif.n_frames == 2
            assert image_util_normalize_16bit_grayscale(gif) is gif


class TestIsUnchanged:
    def test_matching_size_and_mtime_is_unchanged(self, tmp_path):
        photo = _photo(tmp_path / "a.jpg")
        thumb = _thumbnail(tmp_path / "thumb.jpg")
        assert image_util_is_unchanged(photo, _state(photo, thumb)) is True

    def test_a_rewritten_file_is_changed(self, tmp_path):
        photo = _photo(tmp_path / "a.jpg")
        thumb = _thumbnail(tmp_path / "thumb.jpg")
        recorded = _state(photo, thumb)

        os.utime(photo, (0, 0))

        assert image_util_is_unchanged(photo, recorded) is False

    def test_a_resized_file_is_changed(self, tmp_path):
        photo = _photo(tmp_path / "a.jpg")
        thumb = _thumbnail(tmp_path / "thumb.jpg")
        recorded = _state(photo, thumb, file_size=999999)
        assert image_util_is_unchanged(photo, recorded) is False

    def test_a_missing_thumbnail_forces_a_reread(self, tmp_path):
        """Skipping means keeping the old thumbnail, so it has to still exist."""
        photo = _photo(tmp_path / "a.jpg")
        recorded = _state(photo, str(tmp_path / "gone.jpg"))
        assert image_util_is_unchanged(photo, recorded) is False

    def test_a_half_written_thumbnail_forces_a_reread(self, tmp_path):
        photo = _photo(tmp_path / "a.jpg")
        truncated = tmp_path / "thumb.jpg"
        truncated.write_bytes(b"")
        assert image_util_is_unchanged(photo, _state(photo, str(truncated))) is False

    def test_a_row_predating_mtime_tracking_is_reread(self, tmp_path):
        """Shipped databases have file_size but no file_mtime; reread them once."""
        photo = _photo(tmp_path / "a.jpg")
        thumb = _thumbnail(tmp_path / "thumb.jpg")
        assert (
            image_util_is_unchanged(photo, _state(photo, thumb, file_mtime=None))
            is False
        )

    @pytest.mark.parametrize(
        "date_source, has_sidecar, expected",
        [
            ("filesystem", False, True),
            ("filesystem", True, False),
            ("exif", True, True),
        ],
    )
    def test_a_late_sidecar_rereads_only_a_filesystem_dated_photo(
        self, tmp_path: Path, date_source: str, has_sidecar: bool, expected: bool
    ) -> None:
        photo = _photo(tmp_path / "a.jpg")
        thumb = _thumbnail(tmp_path / "thumb.jpg")
        if has_sidecar:
            (tmp_path / "a.jpg.supplemental-metadata.json").write_text(
                '{"photoTakenTime": {"timestamp": "1600000000"}}'
            )
        recorded = _state(photo, thumb, date_source=date_source)
        assert image_util_is_unchanged(photo, recorded) is expected

    def test_an_unparseable_exif_date_falls_back_to_the_sidecar(
        self, tmp_path: Path
    ) -> None:
        image = Image.new("RGB", (8, 8))
        exif = image.getexif()
        exif[EXIF_IFD_POINTER] = {0x9003: "0000:00:00 00:00:00"}  # DateTimeOriginal
        image.save(tmp_path / "a.jpg", exif=exif)
        (tmp_path / "a.jpg.supplemental-metadata.json").write_text(
            '{"photoTakenTime": {"timestamp": "1600000000"}}'
        )
        photo = str(tmp_path / "a.jpg")

        metadata = image_util_extract_metadata(photo)
        assert metadata["date_source"] == "sidecar"
        assert metadata["date_created"] == (
            datetime.datetime.fromtimestamp(1600000000).isoformat()
        )
        thumb = _thumbnail(tmp_path / "thumb.jpg")
        recorded = _state(photo, thumb, date_source=metadata["date_source"])
        assert image_util_is_unchanged(photo, recorded) is True

    def test_an_unknown_path_is_changed(self, tmp_path):
        assert image_util_is_unchanged(str(tmp_path / "a.jpg"), None) is False

    def test_a_file_that_vanished_is_changed(self, tmp_path):
        photo = _photo(tmp_path / "a.jpg")
        thumb = _thumbnail(tmp_path / "thumb.jpg")
        recorded = _state(photo, thumb)
        os.unlink(photo)
        assert image_util_is_unchanged(photo, recorded) is False


class TestPrepareImageRecordsSkips:
    """Regenerating a thumbnail per file is the cost this avoids."""

    @pytest.fixture
    def thumbnail_dir(self, tmp_path, monkeypatch) -> str:
        target = tmp_path / "thumbs"
        target.mkdir()
        monkeypatch.setattr("app.utils.images.THUMBNAIL_IMAGES_PATH", str(target))
        return str(target)

    @pytest.fixture
    def counted_thumbnails(self, monkeypatch) -> List[str]:
        """Record every file the run actually regenerated a thumbnail for."""
        generated: List[str] = []

        def spy(image_path: str, thumbnail_path: str, *args, **kwargs):
            generated.append(image_path)
            return image_util_generate_thumbnail(
                image_path, thumbnail_path, *args, **kwargs
            )

        monkeypatch.setattr("app.utils.images.image_util_generate_thumbnail", spy)
        return generated

    def test_an_unchanged_file_produces_no_record_and_no_thumbnail(
        self, tmp_path, thumbnail_dir, counted_thumbnails
    ):
        photo = _photo(tmp_path / "a.jpg")
        thumb = _thumbnail(tmp_path / "existing.jpg")
        known = {os.path.normcase(os.path.abspath(photo)): _state(photo, thumb)}

        records = image_util_prepare_image_records(
            [photo], {str(tmp_path): "folder-1"}, known
        )

        assert records == []
        assert counted_thumbnails == []

    def test_a_changed_file_is_still_processed(
        self, tmp_path, thumbnail_dir, counted_thumbnails
    ):
        photo = _photo(tmp_path / "a.jpg")
        thumb = _thumbnail(tmp_path / "existing.jpg")
        known = {
            os.path.normcase(os.path.abspath(photo)): _state(
                photo, thumb, file_size=12345
            )
        }

        records = image_util_prepare_image_records(
            [photo], {str(tmp_path): "folder-1"}, known
        )

        assert len(records) == 1
        assert counted_thumbnails == [photo]

    def test_only_the_changed_file_is_reread(
        self, tmp_path, thumbnail_dir, counted_thumbnails
    ):
        stale = _photo(tmp_path / "stale.jpg", (1, 2, 3))
        fresh = _photo(tmp_path / "fresh.jpg", (4, 5, 6))
        thumb = _thumbnail(tmp_path / "existing.jpg")
        known = {
            os.path.normcase(os.path.abspath(stale)): _state(stale, thumb),
            os.path.normcase(os.path.abspath(fresh)): _state(
                fresh, thumb, file_mtime=0
            ),
        }

        records = image_util_prepare_image_records(
            [stale, fresh], {str(tmp_path): "folder-1"}, known
        )

        assert [record["path"] for record in records] == [fresh]
        assert counted_thumbnails == [fresh]

    def test_without_known_state_every_file_is_processed(
        self, tmp_path, thumbnail_dir, counted_thumbnails
    ):
        """The default has to stay a full reread, since other callers rely on it."""
        photo = _photo(tmp_path / "a.jpg")

        records = image_util_prepare_image_records([photo], {str(tmp_path): "folder-1"})

        assert len(records) == 1
        assert counted_thumbnails == [photo]


class TestSyncStateQuery:
    def test_no_folders_queries_nothing(self, test_db):
        assert db_get_image_sync_state_by_folder_ids([]) == {}

    def test_size_and_mtime_come_back_off_the_metadata_blob(self, folder, tmp_path):
        path = str(tmp_path / "a.jpg")
        db_bulk_insert_images(
            [
                {
                    "id": "img-1",
                    "path": path,
                    "folder_id": folder,
                    "thumbnailPath": "/thumbs/img-1.jpg",
                    "metadata": json.dumps(
                        {"file_size": 4096, "file_mtime": 1700000000}
                    ),
                    "isTagged": False,
                    "isEmbedded": False,
                    "latitude": None,
                    "longitude": None,
                    "captured_at": None,
                }
            ]
        )

        state = db_get_image_sync_state_by_folder_ids([folder])

        assert state[os.path.normcase(os.path.abspath(path))] == {
            "thumbnailPath": "/thumbs/img-1.jpg",
            "file_size": 4096,
            "file_mtime": 1700000000,
            "date_source": None,
        }

    def test_a_non_finite_size_does_not_abort_the_scan(self, folder, tmp_path):
        """JSON reads 1e309 as inf, and int(inf) raises outside the ValueError family."""
        path = str(tmp_path / "a.jpg")
        db_bulk_insert_images(
            [
                {
                    "id": "img-1",
                    "path": path,
                    "folder_id": folder,
                    "thumbnailPath": "/thumbs/img-1.jpg",
                    "metadata": '{"file_size": 1e309, "file_mtime": 1e309}',
                    "isTagged": False,
                    "isEmbedded": False,
                    "latitude": None,
                    "longitude": None,
                    "captured_at": None,
                }
            ]
        )

        recorded = db_get_image_sync_state_by_folder_ids([folder])[
            os.path.normcase(os.path.abspath(path))
        ]

        assert recorded["file_size"] is None
        assert recorded["file_mtime"] is None

    def test_an_unreadable_blob_leaves_the_file_looking_changed(self, folder, tmp_path):
        path = str(tmp_path / "a.jpg")
        db_bulk_insert_images(
            [
                {
                    "id": "img-1",
                    "path": path,
                    "folder_id": folder,
                    "thumbnailPath": "/thumbs/img-1.jpg",
                    "metadata": "not json",
                    "isTagged": False,
                    "isEmbedded": False,
                    "latitude": None,
                    "longitude": None,
                    "captured_at": None,
                }
            ]
        )

        recorded = db_get_image_sync_state_by_folder_ids([folder])[
            os.path.normcase(os.path.abspath(path))
        ]

        assert recorded["file_size"] is None
        assert recorded["file_mtime"] is None
        assert image_util_is_unchanged(path, recorded) is False


class TestRescanningAFolder:
    """The whole point: the second walk over an untouched folder does no work."""

    @pytest.fixture
    def library(self, tmp_path, test_db, monkeypatch):
        photos = tmp_path / "photos"
        photos.mkdir()
        thumbs = tmp_path / "thumbs"
        thumbs.mkdir()
        monkeypatch.setattr("app.utils.images.THUMBNAIL_IMAGES_PATH", str(thumbs))

        for index in range(5):
            _photo(photos / f"p{index}.jpg", (index * 20, 40, 90))

        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path, last_modified_time, "
            "AI_Tagging) VALUES (?, ?, 0, 1)",
            ("folder-1", str(photos)),
        )
        conn.commit()
        conn.close()
        return photos

    @pytest.fixture
    def generated(self, monkeypatch) -> List[str]:
        collected: List[str] = []

        def spy(image_path: str, thumbnail_path: str, *args, **kwargs):
            collected.append(image_path)
            return image_util_generate_thumbnail(
                image_path, thumbnail_path, *args, **kwargs
            )

        monkeypatch.setattr("app.utils.images.image_util_generate_thumbnail", spy)
        return collected

    def test_second_scan_of_an_untouched_folder_regenerates_nothing(
        self, library, generated
    ):
        folder_data = [(str(library), "folder-1", False)]

        assert image_util_process_folder_images(folder_data) is True
        assert len(generated) == 5

        generated.clear()
        assert image_util_process_folder_images(folder_data) is True
        assert generated == []

    def test_only_a_touched_file_is_reread_on_rescan(self, library, generated):
        folder_data = [(str(library), "folder-1", False)]
        image_util_process_folder_images(folder_data)

        touched = library / "p3.jpg"
        os.utime(touched, (0, 0))

        generated.clear()
        image_util_process_folder_images(folder_data)

        assert generated == [str(touched)]

    def test_rescanning_does_not_churn_image_ids(self, library, generated, test_db):
        """A new id per scan would cascade every face, tag, and album row away."""
        folder_data = [(str(library), "folder-1", False)]
        image_util_process_folder_images(folder_data)

        conn = sqlite3.connect(test_db)
        before = dict(conn.execute("SELECT path, id FROM images").fetchall())
        conn.close()

        image_util_process_folder_images(folder_data)

        conn = sqlite3.connect(test_db)
        after = dict(conn.execute("SELECT path, id FROM images").fetchall())
        conn.close()

        assert before == after

    def test_a_sidecar_copied_in_after_the_photo_is_read(
        self, library: Path, test_db: str
    ) -> None:
        folder_data = [(str(library), "folder-1", False)]
        image_util_process_folder_images(folder_data)
        (library / "p2.jpg.supplemental-metadata.json").write_text(
            '{"photoTakenTime": {"timestamp": "1600000000"}}'
        )
        image_util_process_folder_images(folder_data)

        conn = sqlite3.connect(test_db)
        (metadata,) = conn.execute(
            "SELECT metadata FROM images WHERE path = ?", (str(library / "p2.jpg"),)
        ).fetchone()
        conn.close()
        assert json.loads(metadata)["date_source"] == "sidecar"


class TestExtractMetadataRecordsMtime:
    def test_mtime_is_recorded_in_whole_seconds(self, tmp_path):
        photo = _photo(tmp_path / "a.jpg")
        metadata = image_util_extract_metadata(photo)
        assert metadata["file_mtime"] == int(os.stat(photo).st_mtime)

    def test_a_missing_file_records_no_usable_mtime(self, tmp_path):
        metadata = image_util_extract_metadata(str(tmp_path / "gone.jpg"))
        assert metadata["file_mtime"] == 0
