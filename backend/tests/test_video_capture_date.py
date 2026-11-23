import datetime
import struct

import pytest

from app.utils.videos import (
    video_util_extract_metadata,
    video_util_prepare_video_records,
    video_util_source_is_unchanged,
)
from app.utils.video_capture_date import (
    EPOCH_1904,
    QUICKTIME_CREATION_KEY,
    video_capture_date_candidates,
)


def box(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload) + 8) + kind + payload


def mvhd(seconds: int, version: int = 0) -> bytes:
    """Only the header and creation time are read; the rest is padding."""
    stamp = struct.pack(">Q", seconds) if version == 1 else struct.pack(">I", seconds)
    return box(b"mvhd", bytes([version]) + b"\x00\x00\x00" + stamp + b"\x00" * 80)


def keys(names) -> bytes:
    entries = b"".join(
        struct.pack(">I", len(name) + 8) + b"mdta" + name for name in names
    )
    return box(b"keys", b"\x00\x00\x00\x00" + struct.pack(">I", len(names)) + entries)


def ilst(index: int, value: bytes) -> bytes:
    data = box(b"data", struct.pack(">I", 1) + b"\x00" * 4 + value)
    return box(b"ilst", box(struct.pack(">I", index), data))


def meta(names, index: int, value: bytes, iso_style: bool = False) -> bytes:
    """
    QuickTime writes meta as a plain container; ISO prefixes version+flags.

    Both spellings exist in the wild and the good timestamps live in the
    QuickTime-style ones, so the reader has to sniff rather than assume.
    """
    body = box(b"hdlr", b"\x00" * 24) + keys(names) + ilst(index, value)
    return box(b"meta", (b"\x00\x00\x00\x00" if iso_style else b"") + body)


def write_video(path, *children: bytes) -> str:
    path.write_bytes(box(b"ftyp", b"isom") + box(b"moov", b"".join(children)))
    return str(path)


@pytest.fixture
def video(tmp_path):
    return tmp_path / "IMG_0034.MP4"


class TestVideoCaptureDateCandidates:
    def test_reads_the_quicktime_creation_date(self, video):
        path = write_video(
            video,
            mvhd(3_615_000_000),
            meta([QUICKTIME_CREATION_KEY], 1, b"2025-08-07T13:02:02+0530"),
        )
        recorded, _ = video_capture_date_candidates(path)
        assert recorded == "2025-08-07T13:02:02"

    def test_keeps_the_wall_clock_where_it_was_shot(self, video):
        """
        The offset is the whole reason this source is preferred: it yields the
        local time at capture, as EXIF does for a photo. Reading it as UTC put
        every video 5.5 hours early on the user's library.
        """
        path = write_video(
            video, meta([QUICKTIME_CREATION_KEY], 1, b"2025-08-07T13:02:02+0530")
        )
        recorded, _ = video_capture_date_candidates(path)
        assert recorded.endswith("13:02:02")

    def test_reads_an_iso_style_meta_box(self, video):
        path = write_video(
            video,
            meta([QUICKTIME_CREATION_KEY], 1, b"2024-02-06T10:36:24+0000", True),
        )
        assert video_capture_date_candidates(path)[0] == "2024-02-06T10:36:24"

    def test_finds_the_key_among_others(self, video):
        path = write_video(
            video,
            meta(
                [b"com.apple.quicktime.make", QUICKTIME_CREATION_KEY, b"other"],
                2,
                b"2025-08-07T13:02:02+0530",
            ),
        )
        assert video_capture_date_candidates(path)[0] == "2025-08-07T13:02:02"

    def test_movie_header_time_is_converted_from_utc(self, video):
        """
        mvhd counts from 1904 in UTC, unlike every other date in the database.
        Round-tripped rather than recomputed, so the test does not just repeat
        the implementation.
        """
        seconds = 3_615_000_000
        path = write_video(video, mvhd(seconds))

        _, file_created = video_capture_date_candidates(path)

        local = datetime.datetime.fromisoformat(file_created)
        as_utc = local.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        assert as_utc == (EPOCH_1904 + datetime.timedelta(seconds=seconds)).replace(
            tzinfo=None
        )

    def test_reads_a_64_bit_movie_header(self, video):
        path = write_video(video, mvhd(3_615_000_000, version=1))
        assert video_capture_date_candidates(path)[1] is not None

    def test_both_are_returned_together(self, video):
        path = write_video(
            video,
            mvhd(3_615_000_000),
            meta([QUICKTIME_CREATION_KEY], 1, b"2025-08-07T13:02:02+0530"),
        )
        recorded, file_created = video_capture_date_candidates(path)
        assert recorded is not None and file_created is not None

    @pytest.mark.parametrize(
        "seconds, reason",
        [
            (0, "clock never set"),
            (1_000, "1904, which is not a capture date"),
            (4_294_967_295, "the year 2040, from a clock set wrong"),
        ],
    )
    def test_implausible_header_times_are_refused(self, video, seconds, reason):
        path = write_video(video, mvhd(seconds))
        assert video_capture_date_candidates(path)[1] is None, reason

    def test_a_file_without_moov_says_nothing(self, video):
        video.write_bytes(box(b"ftyp", b"isom") + box(b"mdat", b"\x00" * 32))
        assert video_capture_date_candidates(str(video)) == (None, None)

    def test_a_movie_header_alone_leaves_the_capture_time_unknown(self, video):
        path = write_video(video, mvhd(3_615_000_000))
        assert video_capture_date_candidates(path)[0] is None

    @pytest.mark.parametrize(
        "content",
        [b"", b"not a video at all", b"\x00\x00\x00\x08moov", b"\xff" * 64],
    )
    def test_survives_anything_that_is_not_a_container(self, video, content):
        video.write_bytes(content)
        assert video_capture_date_candidates(str(video)) == (None, None)

    def test_a_missing_file_says_nothing(self, tmp_path):
        assert video_capture_date_candidates(str(tmp_path / "gone.mp4")) == (None, None)

    def test_an_unparseable_creation_string_is_refused(self, video):
        path = write_video(video, meta([QUICKTIME_CREATION_KEY], 1, b"whenever"))
        assert video_capture_date_candidates(path)[0] is None


# ##############################
# How videos choose a capture date
# ##############################


def sidecar_for(path, exif_date: str):
    epoch = int(datetime.datetime.strptime(exif_date, "%Y:%m:%d %H:%M:%S").timestamp())
    path.with_name(path.name + ".supplemental-metadata.json").write_text(
        f'{{"photoTakenTime": {{"timestamp": "{epoch}"}}}}', encoding="utf-8"
    )


class TestVideoDateResolution:
    """
    Sources ranked by what each actually claims, not by convenience. A file's
    mtime is the weakest of all - a plain copy overwrites it, which is how
    1107 videos came to be stamped with their import date.
    """

    QUICKTIME = b"2025-08-07T13:02:02+0530"

    def test_the_quicktime_time_wins(self, video):
        write_video(
            video,
            mvhd(3_615_000_000),
            meta([QUICKTIME_CREATION_KEY], 1, self.QUICKTIME),
        )
        sidecar_for(video, "2020:01:01 00:00:00")

        metadata = video_util_extract_metadata(str(video))

        assert metadata["date_created"] == "2025-08-07T13:02:02"
        assert metadata["date_source"] == "container"

    def test_a_sidecar_outranks_the_movie_header(self, video):
        """
        photoTakenTime is when it was shot; the movie header is when this file
        was written, which a re-encode or a trim overwrites.
        """
        write_video(video, mvhd(3_615_000_000))
        sidecar_for(video, "2025:12:18 21:19:07")

        metadata = video_util_extract_metadata(str(video))

        assert metadata["date_created"] == "2025-12-18T21:19:07"
        assert metadata["date_source"] == "sidecar"

    def test_the_movie_header_is_the_last_real_source(self, video):
        write_video(video, mvhd(3_615_000_000))
        metadata = video_util_extract_metadata(str(video))
        assert metadata["date_source"] == "container"

    def test_mtime_is_marked_as_a_guess(self, video):
        video.write_bytes(box(b"ftyp", b"isom"))
        metadata = video_util_extract_metadata(str(video))
        assert metadata["date_source"] == "filesystem"
        assert metadata["date_created"] == metadata["file_modified"]

    def test_the_mtime_is_recorded_separately(self, video):
        """
        date_created used to double as the mtime record, so a real capture
        date could not live there without making every video look modified.
        """
        write_video(video, meta([QUICKTIME_CREATION_KEY], 1, self.QUICKTIME))
        metadata = video_util_extract_metadata(str(video))

        assert metadata["file_modified"] != metadata["date_created"]
        assert video_util_source_is_unchanged(str(video), metadata)

    def test_a_row_without_a_recorded_mtime_counts_as_changed(self, video):
        """Rows predating this read once, so their dates get corrected."""
        write_video(video, mvhd(3_615_000_000))
        stale = video_util_extract_metadata(str(video))
        stale.pop("file_modified")

        assert not video_util_source_is_unchanged(str(video), stale)

    def test_a_guessed_date_never_becomes_captured_at(self, video, tmp_path):
        video.write_bytes(box(b"ftyp", b"isom"))
        records = video_util_prepare_video_records([str(video)], {str(tmp_path): 1})
        assert records[0]["captured_at"] is None

    def test_a_real_date_becomes_captured_at(self, video, tmp_path):
        write_video(video, meta([QUICKTIME_CREATION_KEY], 1, self.QUICKTIME))
        records = video_util_prepare_video_records([str(video)], {str(tmp_path): 1})
        assert records[0]["captured_at"] == "2025-08-07T13:02:02"
