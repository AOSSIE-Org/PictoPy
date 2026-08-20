from contextlib import ExitStack
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterator, List, Optional, Sequence
from unittest.mock import patch
from zlib import crc32

import numpy as np
import pytest

from app.schemas.user_preferences import MemoriesPreferences
from app.utils import memory_curator

# Captured before the autouse fixture below replaces the module attribute, so
# the preference-loading logic itself stays testable.
real_get_preferences = memory_curator.memory_curator_get_preferences

T0 = datetime(2024, 7, 26, 10, 0, 0)
REFERENCE = "2026-07-26"

# One shared direction stands in for a visually consistent set. Scattered sets
# use mutually orthogonal basis vectors: with N distinct directions the mean
# cosine to the centroid is 1/sqrt(N), so eight of them land well under the
# gate while two would not.
COHERENT = np.eye(8, dtype=np.float32)[0]
SCATTER_BASIS = np.eye(8, dtype=np.float32)

# What a random pair of photos in this library already scores, measured on the
# real one. Every cohesion test is a margin over it, so a run that reads no
# baseline at all judges nothing - which is why it is stubbed rather than left
# to whatever embeddings happen to be in the database.
LIBRARY_BASELINE = 0.58


def library_sample(pairwise: float = LIBRARY_BASELINE, count: int = 4) -> List[Any]:
    """
    Stand-in for the library's own embeddings, with an exact pairwise cosine.

    Each vector is `sqrt(1-p)` along its own axis plus `sqrt(p)` along one they
    share, so every pair scores exactly `pairwise` and the unit length holds.
    """
    vectors = []
    for index in range(count):
        vector = np.zeros(count + 1, dtype=np.float32)
        vector[index] = np.sqrt(1.0 - pairwise)
        vector[count] = np.sqrt(pairwise)
        vectors.append(vector)
    return vectors


# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(autouse=True)
def stub_run_bookkeeping() -> Iterator[None]:
    """Silence the memory_runs writes; the DB tests cover those."""
    with (
        patch.object(memory_curator, "db_start_memory_run", return_value=True),
        patch.object(memory_curator, "db_finish_memory_run", return_value=True),
    ):
        yield


@pytest.fixture(autouse=True)
def stub_preferences() -> Iterator[None]:
    with patch.object(
        memory_curator,
        "memory_curator_get_preferences",
        return_value=MemoriesPreferences(min_images=3),
    ):
        yield


def make_images(
    prefix: str,
    count: int,
    start: datetime = T0,
    step: timedelta = timedelta(minutes=30),
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> List[Dict[str, Any]]:
    return [
        {
            "id": f"{prefix}-{i}",
            "path": f"/photos/{prefix}-{i}.jpg",
            "thumbnailPath": f"/thumbs/{prefix}-{i}.jpg",
            "captured_at": (start + step * i).strftime("%Y-%m-%d %H:%M:%S"),
            "latitude": latitude,
            "longitude": longitude,
            "isFavourite": False,
        }
        for i in range(count)
    ]


def make_anniversary_images(year: int, count: int, month_day: str = "07-26"):
    images = [
        {
            **image,
            "captured_at": f"{year}-{month_day} 1{i}:00:00",
            "capture_year": year,
        }
        for i, image in enumerate(make_images(str(year), count))
    ]
    return images


def signals_for(image_ids: Sequence[str]) -> List[Dict[str, Any]]:
    """Minimal signal rows: every candidate is equally unremarkable."""
    return [
        {
            "id": image_id,
            "isFavourite": False,
            "in_album": False,
            "named_people": 0,
            "face_count": 1,
            "top_semantic_score": None,
            "top_event_score": None,
            "class_count": 1,
            "scored_signature": None,
            "latitude": None,
            "longitude": None,
            # Spread timestamps so time-bucketing has something to work with.
            # crc32, not hash(): str hashing is salted per process, so the
            # spread - and anything ordered by it - would differ every run.
            "captured_at": (
                T0 + timedelta(hours=crc32(image_id.encode()) % 24)
            ).strftime("%Y-%m-%d %H:%M:%S"),
        }
        for image_id in image_ids
    ]


def run_curator(
    *,
    anniversary: Optional[List[Dict[str, Any]]] = None,
    uncurated: Optional[List[Dict[str, Any]]] = None,
    event_labels: Optional[List[Dict[str, Any]]] = None,
    event_hits: Optional[List[Dict[str, Any]]] = None,
    expansion: Optional[List[Dict[str, Any]]] = None,
    top_event_label: Optional[Any] = None,
    embeddings: Optional[Dict[str, np.ndarray]] = None,
    cohesion_sample: Optional[Sequence[Any]] = None,
    video_candidates: Optional[List[Dict[str, Any]]] = None,
    video_signals: Optional[List[Dict[str, Any]]] = None,
    recently_used: Optional[set] = None,
    own_images: Optional[set] = None,
    signals: Any = signals_for,
    upsert_side_effect: Optional[Any] = None,
    mocks: Optional[Dict[str, Any]] = None,
    **run_kwargs: Any,
) -> List[Dict[str, Any]]:
    """
    Run curation against stubbed data sources and return upserted memories.

    Every trigger is stubbed to produce nothing unless the caller supplies
    input for it, so each test exercises one path. Pass `mocks` to receive the
    patched objects for call-count assertions.
    """
    upserts: List[Dict[str, Any]] = []
    collected = mocks if mocks is not None else {}

    def capture(memory, images, videos=()):
        upserts.append({"memory": memory, "images": images, "videos": list(videos)})
        return memory["memory_id"]

    pool = uncurated or []

    with ExitStack() as stack:

        def m(name, **kw):
            mock = stack.enter_context(patch.object(memory_curator, name, **kw))
            collected[name] = mock
            return mock

        m("detect_home_location", return_value=None)
        m("db_get_recently_used_image_ids", return_value=set(recently_used or []))
        m("db_get_anniversary_candidates", return_value=anniversary or [])
        m("db_get_recent_dated_images", return_value=pool)
        m("db_get_memory_image_ids_by_dedupe_key", return_value=set(own_images or []))
        m("db_get_event_labels", return_value=event_labels or [])
        m("db_get_event_label_hits", return_value=event_hits or [])
        m("db_get_images_in_period", return_value=expansion or [])
        m(
            "db_get_top_memory_label",
            **(
                {"side_effect": top_event_label}
                if callable(top_event_label)
                else {"return_value": top_event_label}
            ),
        )
        m("db_get_embeddings_for_image_ids", return_value=embeddings or {})
        # Unstubbed this reads the real database, which on a developer machine
        # is their photo library and in CI is empty - and an empty sample means
        # no baseline, which makes the cohesion gate accept everything.
        m(
            "db_get_embedding_sample",
            return_value=(
                library_sample() if cohesion_sample is None else list(cohesion_sample)
            ),
        )
        m("db_get_video_candidates_in_period", return_value=video_candidates or [])
        m("db_get_video_scoring_signals", return_value=video_signals or [])
        m("db_get_scoring_signals", side_effect=signals)
        m(
            "db_upsert_memory",
            side_effect=upsert_side_effect or capture,
        )
        run_kwargs.setdefault("reference_date", REFERENCE)
        memory_curator.memory_curator_run(**run_kwargs)

    return upserts


def of_type(upserts: List[Dict[str, Any]], event_type: str) -> List[Dict[str, Any]]:
    return [u for u in upserts if u["memory"]["event_type"] == event_type]


# ##############################
# Helpers
# ##############################


class TestAnniversaryWindow:
    def test_spans_a_day_either_side(self):
        assert memory_curator._anniversary_window(date(2026, 7, 26)) == [
            "07-25",
            "07-26",
            "07-27",
        ]

    @pytest.mark.parametrize(
        "reference, expected",
        [
            (date(2026, 1, 1), ["01-01", "01-02", "12-31"]),  # year boundary
            (date(2026, 3, 1), ["02-28", "03-01", "03-02"]),  # non-leap February
            (date(2024, 3, 1), ["02-29", "03-01", "03-02"]),  # leap February
        ],
    )
    def test_handles_calendar_edges(self, reference, expected):
        assert memory_curator._anniversary_window(reference) == expected


class TestDisplayNames:
    @pytest.mark.parametrize(
        "label, expected",
        [
            ("diwali", "Diwali"),
            ("durga puja", "Durga Puja"),
            ("wedding", "Wedding"),
            ("ganesh chaturthi", "Ganesh Chaturthi"),
            ("valentines day", "Valentine's Day"),  # apostrophe needs an override
            ("new year", "New Year"),
            ("eid", "Eid"),
        ],
    )
    def test_renders_readable_titles(self, label, expected):
        assert memory_curator._display_event_name(label) == expected


class TestGenericTitle:
    """
    A memory nothing recognised still has to invite a second look, and there
    is no captioning model here to write it a real title.
    """

    ONE_DAY = (datetime(2026, 7, 11, 15, 0), datetime(2026, 7, 11, 23, 0))
    MANY_DAYS = (datetime(2026, 7, 17, 22, 0), datetime(2026, 7, 18, 10, 0))

    def test_is_stable_for_a_given_memory(self):
        """A rebuild must not rename a memory the user has already seen."""
        first = memory_curator._generic_title("import:a..a", *self.ONE_DAY)
        second = memory_curator._generic_title("import:a..a", *self.ONE_DAY)
        assert first == second

    def test_differs_between_memories(self):
        titles = {
            memory_curator._generic_title(f"import:{i}", *self.ONE_DAY)
            for i in range(40)
        }
        assert len(titles) == len(memory_curator.GENERIC_TITLES_ONE_DAY)

    def test_a_single_day_reads_singular(self):
        assert (
            memory_curator._generic_title("import:a..a", *self.ONE_DAY)
            in memory_curator.GENERIC_TITLES_ONE_DAY
        )

    def test_a_span_reads_plural(self):
        """A fortnight should not be called a day."""
        assert (
            memory_curator._generic_title("import:a..b", *self.MANY_DAYS)
            in memory_curator.GENERIC_TITLES_MANY_DAYS
        )


class TestParamsSignature:
    def test_is_stable_for_equal_preferences(self):
        first = memory_curator.memory_curator_params_signature(MemoriesPreferences())
        second = memory_curator.memory_curator_params_signature(MemoriesPreferences())
        assert first == second

    @pytest.mark.parametrize(
        "overrides",
        [{"min_images": 9}, {"max_images": 12}, {"weights": {"favourite": 0.9}}],
    )
    def test_changes_when_scoring_inputs_change(self, overrides):
        baseline = memory_curator.memory_curator_params_signature(MemoriesPreferences())
        changed = memory_curator.memory_curator_params_signature(
            MemoriesPreferences(**overrides)
        )
        assert baseline != changed

    def test_ignores_delivery_only_preferences(self):
        """Muting the story audio must not invalidate every existing memory."""
        baseline = memory_curator.memory_curator_params_signature(MemoriesPreferences())
        changed = memory_curator.memory_curator_params_signature(
            MemoriesPreferences(story_music_enabled=True, notifications_enabled=False)
        )
        assert baseline == changed


# ##############################
# Trigger 1: anniversary
# ##############################


class TestAnniversaryCuration:
    def test_builds_one_memory_per_qualifying_year(self):
        candidates = make_anniversary_images(2024, 4) + make_anniversary_images(2023, 5)
        upserts = of_type(run_curator(anniversary=candidates), "anniversary")

        assert {u["memory"]["dedupe_key"] for u in upserts} == {
            "anniv:07-26:2024",
            "anniv:07-26:2023",
        }
        assert all(u["memory"]["status"] == "complete" for u in upserts)

    def test_skips_years_below_the_minimum(self):
        candidates = make_anniversary_images(2024, 4) + make_anniversary_images(2023, 2)
        upserts = of_type(run_curator(anniversary=candidates), "anniversary")
        assert [u["memory"]["dedupe_key"] for u in upserts] == ["anniv:07-26:2024"]

    def test_caps_the_number_of_anniversary_memories(self):
        candidates = (
            make_anniversary_images(2024, 6)
            + make_anniversary_images(2023, 5)
            + make_anniversary_images(2022, 4)
        )
        upserts = of_type(run_curator(anniversary=candidates), "anniversary")

        assert len(upserts) == memory_curator.MAX_ANNIVERSARY_MEMORIES
        # The years with the most to show win.
        assert {u["memory"]["dedupe_key"] for u in upserts} == {
            "anniv:07-26:2024",
            "anniv:07-26:2023",
        }

    def test_no_candidates_produces_no_memories(self):
        assert of_type(run_curator(), "anniversary") == []

    @pytest.mark.parametrize(
        "year, expected_title",
        [(2025, "1 year ago today"), (2024, "2 years ago today")],
    )
    def test_titles_singular_and_plural_years(self, year, expected_title):
        upserts = of_type(
            run_curator(anniversary=make_anniversary_images(year, 4)), "anniversary"
        )
        assert upserts[0]["memory"]["title"] == expected_title

    def test_subtitle_comes_from_the_photos(self):
        """Anniversaries are named by the year they recall, not by exact dates."""
        upserts = of_type(
            run_curator(anniversary=make_anniversary_images(2024, 4)), "anniversary"
        )
        assert upserts[0]["memory"]["subtitle"] == "July 2024"

    def test_leap_day_reference_does_not_crash_on_non_leap_source_years(self):
        """Feb 29 has no counterpart in 2023, so the date must come from EXIF."""
        candidates = make_anniversary_images(2023, 4, month_day="02-28")
        upserts = of_type(
            run_curator(anniversary=candidates, reference_date="2024-02-29"),
            "anniversary",
        )
        assert len(upserts) == 1
        assert upserts[0]["memory"]["subtitle"] == "February 2023"

    def test_recently_used_images_are_demoted_not_dropped(self):
        """A sparse calendar date cannot spare photos, so reuse is a penalty."""
        candidates = make_anniversary_images(2024, 5)
        upserts = of_type(
            run_curator(anniversary=candidates, recently_used={"2024-0"}),
            "anniversary",
        )
        assert len(upserts[0]["images"]) == 5

    def test_a_failing_year_does_not_abort_the_rest(self):
        candidates = make_anniversary_images(2024, 6) + make_anniversary_images(2023, 5)
        seen: List[str] = []

        def flaky(memory, images, videos=()):
            seen.append(memory["dedupe_key"])
            if memory["dedupe_key"] == "anniv:07-26:2024":
                raise RuntimeError("boom")
            return memory["memory_id"]

        run_curator(anniversary=candidates, upsert_side_effect=flaky)
        assert len(seen) == 2


# ##############################
# Trigger 2: import event
# ##############################


class TestSegmentByTimeAndPlace:
    def test_a_continuous_burst_is_one_segment(self):
        images = make_images("a", 6, step=timedelta(minutes=20))
        assert len(memory_curator.segment_by_time_and_place(images)) == 1

    @pytest.mark.parametrize(
        "gap_hours, expected_segments",
        [(7, 1), (9, 2)],  # threshold is 8 hours
    )
    def test_splits_on_a_long_pause(self, gap_hours, expected_segments):
        first = make_images("a", 3, step=timedelta(minutes=10))
        second = make_images(
            "b", 3, start=T0 + timedelta(hours=gap_hours), step=timedelta(minutes=10)
        )
        segments = memory_curator.segment_by_time_and_place(first + second)
        assert len(segments) == expected_segments

    @pytest.mark.parametrize(
        "longitude, expected_segments",
        # 77.6 -> 78.2 is ~65 km at this latitude; 77.7 is ~11 km.
        [(77.7, 1), (78.2, 2)],
    )
    def test_splits_on_a_large_move(self, longitude, expected_segments):
        first = make_images(
            "a", 3, step=timedelta(minutes=10), latitude=12.97, longitude=77.6
        )
        second = make_images(
            "b",
            3,
            start=T0 + timedelta(hours=1),
            step=timedelta(minutes=10),
            latitude=12.97,
            longitude=longitude,
        )
        segments = memory_curator.segment_by_time_and_place(first + second)
        assert len(segments) == expected_segments

    def test_images_without_timestamps_are_ignored(self):
        images = make_images("a", 3) + [
            {"id": "undated", "captured_at": None, "latitude": None, "longitude": None}
        ]
        segments = memory_curator.segment_by_time_and_place(images)
        assert sum(len(s) for s in segments) == 3

    def test_empty_input(self):
        assert memory_curator.segment_by_time_and_place([]) == []


class TestImportEventCuration:
    def test_builds_a_memory_from_a_burst(self):
        pool = make_images("trip", 6, step=timedelta(minutes=20))
        upserts = of_type(run_curator(uncurated=pool), "import_event")

        assert len(upserts) == 1
        assert upserts[0]["memory"]["dedupe_key"].startswith("import:2024-07-26")

    def test_separate_bursts_become_separate_memories(self):
        pool = make_images("day1", 4, step=timedelta(minutes=20)) + make_images(
            "day2", 4, start=T0 + timedelta(days=2), step=timedelta(minutes=20)
        )
        upserts = of_type(run_curator(uncurated=pool), "import_event")
        assert len(upserts) == 2

    def test_rejects_bursts_below_the_minimum(self):
        pool = make_images("tiny", 2, step=timedelta(minutes=20))
        assert of_type(run_curator(uncurated=pool), "import_event") == []

    def test_rejects_a_span_longer_than_the_limit(self):
        """A slow trickle never breaks the gap rule, but is not one event."""
        # 60 photos, 7 hours apart: no gap exceeds 8 hours, so this stays a
        # single segment, but it spans ~17 days and must still be rejected.
        pool = make_images("long", 60, step=timedelta(hours=7))
        segments = memory_curator.segment_by_time_and_place(pool)
        assert len(segments) == 1
        assert memory_curator._span_days(segments[0]) > (
            memory_curator.IMPORT_MAX_SPAN_DAYS
        )
        assert of_type(run_curator(uncurated=pool), "import_event") == []

    def test_names_the_memory_after_a_recognised_event(self):
        pool = make_images("party", 6, step=timedelta(minutes=20))
        upserts = of_type(
            run_curator(uncurated=pool, top_event_label=(1003, "birthday", 4.2)),
            "import_event",
        )
        assert upserts[0]["memory"]["title"] == "Birthday"
        assert upserts[0]["memory"]["subtitle"] == "26 July 2024"

    def test_falls_back_to_a_stand_in_without_a_recognised_event(self):
        """
        A bare date is a poor title for something meant to invite a second
        look. The date is not lost - it becomes the subtitle.
        """
        pool = make_images("misc", 6, step=timedelta(minutes=20))
        upserts = of_type(run_curator(uncurated=pool), "import_event")

        memory = upserts[0]["memory"]
        assert memory["title"] in memory_curator.GENERIC_TITLES_ONE_DAY
        assert memory["subtitle"] == "26 July 2024"

    def test_recently_used_images_are_excluded_outright(self):
        """The import pool is large, so there is no reason to repeat photos."""
        pool = make_images("trip", 6, step=timedelta(minutes=20))
        upserts = of_type(
            run_curator(uncurated=pool, recently_used={"trip-0", "trip-1"}),
            "import_event",
        )
        assert len(upserts) == 1
        assert "trip-0" not in {image_id for image_id, _, _ in upserts[0]["images"]}

    def test_caps_the_number_of_import_memories(self):
        pool: List[Dict[str, Any]] = []
        for day in range(6):
            pool += make_images(
                f"d{day}",
                4,
                start=T0 + timedelta(days=day * 2),
                step=timedelta(minutes=20),
            )
        upserts = of_type(run_curator(uncurated=pool), "import_event")
        assert len(upserts) == memory_curator.MAX_IMPORT_MEMORIES


# ##############################
# Trigger 3: semantic event
# ##############################


def event_hits(
    class_id: int,
    count: int,
    start: datetime = T0,
    step: timedelta = timedelta(minutes=30),
    score: float = 0.6,
    prefix: str = "e",
) -> List[Dict[str, Any]]:
    return [
        {
            "image_id": f"{prefix}{class_id}-{i}",
            "class_id": class_id,
            "score": score,
            "label_rank": score,
            "captured_at": (start + step * i).strftime("%Y-%m-%d %H:%M:%S"),
            "latitude": None,
            "longitude": None,
        }
        for i in range(count)
    ]


def coherent_embeddings(hits: Sequence[Dict[str, Any]]) -> Dict[str, np.ndarray]:
    return {hit["image_id"]: COHERENT for hit in hits}


class TestGroupEventOccurrences:
    def test_contemporaneous_hits_form_one_occurrence(self):
        occurrences = memory_curator.group_event_occurrences(event_hits(1001, 6))
        assert len(occurrences) == 1
        assert len(occurrences[0]["image_ids"]) == 6

    @pytest.mark.parametrize(
        "gap_hours, expected", [(35, 1), (37, 2)]  # threshold is 36 hours
    )
    def test_splits_distant_hits(self, gap_hours, expected):
        # The gap is measured from the end of the first run, which itself
        # spans an hour at three hits every 30 minutes.
        first_run_span = timedelta(hours=1)
        hits = event_hits(1001, 3) + event_hits(
            1001,
            3,
            start=T0 + first_run_span + timedelta(hours=gap_hours),
            prefix="later",
        )
        assert len(memory_curator.group_event_occurrences(hits)) == expected

    def test_different_labels_are_grouped_separately(self):
        hits = event_hits(1001, 3) + event_hits(1002, 3)
        occurrences = memory_curator.group_event_occurrences(hits)
        assert {o["class_id"] for o in occurrences} == {1001, 1002}

    def test_hits_without_timestamps_are_dropped(self):
        hits = event_hits(1001, 3) + [
            {"image_id": "x", "class_id": 1001, "score": 0.9, "captured_at": None}
        ]
        occurrences = memory_curator.group_event_occurrences(hits)
        assert "x" not in occurrences[0]["image_ids"]


class TestCoherenceGate:
    """
    Cohesion is judged as a margin over the library's own baseline. SigLIP2
    embeddings sit in a narrow cone, so an absolute cosine says nothing: a
    random handful of unrelated photos already scores ~0.58 mean pairwise.
    """

    BASELINE = 0.58

    def _occurrence(self, count=8):
        return memory_curator.group_event_occurrences(event_hits(1001, count))[0]

    def test_accepts_a_coherent_occurrence(self):
        occurrence = self._occurrence()
        assert memory_curator.passes_coherence_gate(
            occurrence, coherent_embeddings(event_hits(1001, 8)), self.BASELINE
        )

    def test_rejects_too_few_images(self):
        occurrence = self._occurrence(count=3)
        assert not memory_curator.passes_coherence_gate(occurrence, {}, self.BASELINE)

    def test_rejects_visually_incoherent_photos(self):
        """The gate that stops 'picnic' matching three unrelated lawn shots."""
        hits = event_hits(1001, 8)
        occurrence = memory_curator.group_event_occurrences(hits)[0]
        scattered = {
            hit["image_id"]: SCATTER_BASIS[i % len(SCATTER_BASIS)]
            for i, hit in enumerate(hits)
        }
        assert not memory_curator.passes_coherence_gate(
            occurrence, scattered, self.BASELINE
        )

    def test_a_group_no_tighter_than_the_library_is_rejected(self):
        """
        The regression the margin exists for: photos exactly as similar as any
        random pair are not an occasion, however high the raw cosine reads.
        """
        hits = event_hits(1001, 8)
        occurrence = memory_curator.group_event_occurrences(hits)[0]
        embeddings = coherent_embeddings(hits)
        assert not memory_curator.passes_coherence_gate(occurrence, embeddings, 1.0)

    def test_accepts_when_embeddings_are_unavailable(self):
        """Label ranks already passed; do not drop everything for want of vectors."""
        assert memory_curator.passes_coherence_gate(
            self._occurrence(), {}, self.BASELINE
        )

    def test_accepts_when_the_library_has_no_baseline_yet(self):
        occurrence = self._occurrence()
        embeddings = coherent_embeddings(event_hits(1001, 8))
        assert memory_curator.passes_coherence_gate(occurrence, embeddings, None)


class TestMergeOverlappingOccurrences:
    def _occurrence(self, class_id, start, count, total_score=1.0):
        occurrence = memory_curator.group_event_occurrences(
            event_hits(class_id, count, start=start, prefix=f"c{class_id}")
        )[0]
        occurrence["total_score"] = total_score
        return occurrence

    def test_merges_labels_covering_the_same_span(self):
        """A wedding weekend firing 'wedding' and 'mehndi' is one occasion."""
        wedding = self._occurrence(1001, T0, 6, total_score=5.0)
        mehndi = self._occurrence(1002, T0 + timedelta(minutes=10), 6, total_score=2.0)

        merged = memory_curator.merge_overlapping_occurrences([wedding, mehndi])

        assert len(merged) == 1
        assert set(merged[0]["class_ids"]) == {1001, 1002}
        # Primary label is whichever carried more confidence.
        assert merged[0]["class_id"] == 1001

    def test_keeps_separate_occasions_apart(self):
        first = self._occurrence(1001, T0, 6)
        second = self._occurrence(1002, T0 + timedelta(days=30), 6)
        assert len(memory_curator.merge_overlapping_occurrences([first, second])) == 2

    def test_stronger_label_wins_regardless_of_order(self):
        weak = self._occurrence(1001, T0, 6, total_score=1.0)
        strong = self._occurrence(1002, T0 + timedelta(minutes=5), 6, total_score=9.0)
        merged = memory_curator.merge_overlapping_occurrences([weak, strong])
        assert merged[0]["class_id"] == 1002

    def test_empty_input(self):
        assert memory_curator.merge_overlapping_occurrences([]) == []


class TestSemanticEventCuration:
    LABELS = [
        {"class_id": 1001, "name": "wedding"},
        {"class_id": 1002, "name": "diwali"},
    ]

    def test_builds_a_memory_from_a_coherent_occurrence(self):
        hits = event_hits(1001, 8)
        upserts = of_type(
            run_curator(
                event_labels=self.LABELS,
                event_hits=hits,
                embeddings=coherent_embeddings(hits),
            ),
            "semantic_event",
        )

        assert len(upserts) == 1
        memory = upserts[0]["memory"]
        assert memory["title"] == "Wedding"
        assert memory["dedupe_key"] == "semantic:1001:2024-07-26"

    def test_produces_nothing_without_event_labels(self):
        assert (
            of_type(run_curator(event_hits=event_hits(1001, 8)), "semantic_event") == []
        )

    def test_produces_nothing_when_the_gate_rejects(self):
        hits = event_hits(1001, 8)
        scattered = {
            hit["image_id"]: SCATTER_BASIS[i % len(SCATTER_BASIS)]
            for i, hit in enumerate(hits)
        }
        upserts = run_curator(
            event_labels=self.LABELS, event_hits=hits, embeddings=scattered
        )
        assert of_type(upserts, "semantic_event") == []

    def test_pulls_in_unlabeled_photos_from_the_same_span(self):
        """The candids between recognised shots are what make it a story."""
        hits = event_hits(1001, 8)
        expansion = make_images("candid", 4, start=T0 + timedelta(minutes=15))
        upserts = of_type(
            run_curator(
                event_labels=self.LABELS,
                event_hits=hits,
                embeddings=coherent_embeddings(hits),
                expansion=expansion,
            ),
            "semantic_event",
        )
        selected = {image_id for image_id, _, _ in upserts[0]["images"]}
        assert any(image_id.startswith("candid") for image_id in selected)

    def test_surfaces_today_for_a_rediscovery(self):
        """An event six months away is not an anniversary worth waiting for."""
        hits = event_hits(1001, 8, start=datetime(2024, 1, 15, 10, 0))
        upserts = of_type(
            run_curator(
                event_labels=self.LABELS,
                event_hits=hits,
                embeddings=coherent_embeddings(hits),
            ),
            "semantic_event",
        )
        assert upserts[0]["memory"]["surface_date"] == REFERENCE

    def test_surfaces_on_an_imminent_anniversary(self):
        hits = event_hits(1001, 8, start=datetime(2023, 7, 27, 10, 0))
        upserts = of_type(
            run_curator(
                event_labels=self.LABELS,
                event_hits=hits,
                embeddings=coherent_embeddings(hits),
            ),
            "semantic_event",
        )
        assert upserts[0]["memory"]["surface_date"] == "2026-07-27"


class TestSemanticSurfaceDate:
    @pytest.mark.parametrize(
        "event_start, expected",
        [
            (datetime(2023, 7, 26, 10, 0), "2026-07-26"),  # today
            (datetime(2023, 7, 28, 10, 0), "2026-07-28"),  # in two days
            (datetime(2023, 7, 31, 10, 0), "2026-07-26"),  # too far ahead
            (datetime(2023, 7, 20, 10, 0), "2026-07-26"),  # already passed
        ],
    )
    def test_picks_anniversary_or_today(self, event_start, expected):
        assert (
            memory_curator._semantic_surface_date(date(2026, 7, 26), event_start)
            == expected
        )

    def test_leap_day_event_falls_back_to_today(self):
        assert (
            memory_curator._semantic_surface_date(
                date(2026, 3, 1), datetime(2024, 2, 29, 10, 0)
            )
            == "2026-03-01"
        )


# ##############################
# Run orchestration
# ##############################


class TestOutlierTrimming:
    """
    Time and place said these photos belong together; cohesion asks whether
    they look like it. An afternoon at the beach and two screenshots taken
    that evening are indistinguishable on the clock alone.
    """

    def embeddings_for(self, images, outliers=()):
        """Outliers get their own orthogonal direction; the rest share one."""
        spare = iter(SCATTER_BASIS[1:])
        return {
            image["id"]: (next(spare) if image["id"] in outliers else COHERENT)
            for image in images
        }

    def test_import_events_drop_what_does_not_belong(self):
        images = make_images("burst", 9, step=timedelta(minutes=20))
        outliers = {"burst-7", "burst-8"}
        upserts = run_curator(
            uncurated=images, embeddings=self.embeddings_for(images, outliers)
        )

        kept = {image_id for image_id, _, _ in upserts[0]["images"]}
        assert kept.isdisjoint(outliers)
        assert kept

    def test_the_title_is_decided_after_trimming(self):
        """
        A photo trimmed for not belonging must not still vote on the label.
        Titling the candidate set kept a beach afternoon named "Surfing" when
        the two screenshots that outvoted "beach" were no longer in it.
        """
        images = make_images("burst", 9, step=timedelta(minutes=20))
        outliers = {"burst-7", "burst-8"}
        seen = {}

        def label(image_ids, *args):
            seen["ids"] = set(image_ids)
            return (1001, "beach", 1.0)

        run_curator(
            uncurated=images,
            embeddings=self.embeddings_for(images, outliers),
            top_event_label=label,
        )

        assert seen["ids"].isdisjoint(outliers)

    def test_anniversaries_keep_everything(self):
        """
        An anniversary spans years by design. Photos from this date across
        three of them are not supposed to look like one another, and trimming
        on cohesion would gut exactly the memory the trigger exists to make.
        """
        images = make_anniversary_images(2024, 9)
        outliers = {"2024-7", "2024-8"}
        upserts = run_curator(
            anniversary=images, embeddings=self.embeddings_for(images, outliers)
        )

        kept = {
            image_id for image_id, _, _ in of_type(upserts, "anniversary")[0]["images"]
        }
        assert outliers <= kept


class TestVideoGuardrails:
    """
    A story is mostly stills. Clips are punctuation, and the guardrails are
    what stop a memory turning into a playlist.
    """

    @pytest.mark.parametrize(
        "photos, expected",
        [(0, 0), (4, 1), (7, 1), (9, 1), (18, 2), (27, 3), (30, 3), (100, 3)],
    )
    def test_quota_scales_with_the_memory(self, photos, expected):
        assert memory_curator.video_quota(photos) == expected

    def clip(self, clip_id, score, duration):
        return {"id": clip_id, "score": score, "duration": duration}

    def test_takes_the_best_clips_first(self):
        chosen = memory_curator.select_videos_within_budget(
            [self.clip("a", 0.2, 5), self.clip("b", 0.9, 5), self.clip("c", 0.5, 5)],
            quota=2,
            budget_seconds=30.0,
        )
        assert [c["id"] for c in chosen] == ["b", "c"]

    def test_the_budget_outranks_the_quota(self):
        """
        Three clips at the per-clip limit would outlast the photos between
        them, so the seconds budget is the binding constraint, not the count.
        """
        chosen = memory_curator.select_videos_within_budget(
            [self.clip(str(i), 0.9 - i * 0.1, 14.0) for i in range(3)],
            quota=3,
            budget_seconds=30.0,
        )
        assert len(chosen) == 2

    def test_a_shorter_clip_still_fits_after_a_long_one(self):
        chosen = memory_curator.select_videos_within_budget(
            [self.clip("long", 0.9, 28.0), self.clip("short", 0.5, 2.0)],
            quota=3,
            budget_seconds=30.0,
        )
        assert [c["id"] for c in chosen] == ["long", "short"]

    def test_a_quota_of_zero_takes_nothing(self):
        chosen = memory_curator.select_videos_within_budget(
            [self.clip("a", 0.9, 1.0)], quota=0, budget_seconds=30.0
        )
        assert chosen == []

    def test_shortest_wins_a_tie(self):
        chosen = memory_curator.select_videos_within_budget(
            [self.clip("long", 0.5, 12.0), self.clip("short", 0.5, 3.0)],
            quota=1,
            budget_seconds=30.0,
        )
        assert chosen[0]["id"] == "short"


class TestVideoCuration:
    def candidates(self, count, duration=5.0):
        return [
            {
                "id": f"vid-{i}",
                "path": f"/videos/{i}.mp4",
                "thumbnailPath": None,
                "captured_at": (T0 + timedelta(minutes=5 + i)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "duration": duration,
                "isFavourite": False,
            }
            for i in range(count)
        ]

    def signals(self, count):
        return [
            {
                "id": f"vid-{i}",
                "media_type": "video",
                "isFavourite": False,
                "scored_signature": "sig",
                "top_semantic_score": 0.5,
                "top_event_score": 0.5,
                "latitude": None,
                "longitude": None,
                "captured_at": (T0 + timedelta(minutes=5 + i)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
            for i in range(count)
        ]

    def test_clips_join_a_memory(self):
        upserts = run_curator(
            uncurated=make_images("trip", 9, step=timedelta(minutes=20)),
            video_candidates=self.candidates(3),
            video_signals=self.signals(3),
        )
        assert len(upserts[0]["videos"]) == 1
        assert upserts[0]["memory"]["video_count"] == 1

    def test_the_preference_turns_them_off(self):
        with patch.object(
            memory_curator,
            "memory_curator_get_preferences",
            return_value=MemoriesPreferences(min_images=3, include_videos=False),
        ):
            upserts = run_curator(
                uncurated=make_images("trip", 9, step=timedelta(minutes=20)),
                video_candidates=self.candidates(3),
                video_signals=self.signals(3),
            )
        assert upserts[0]["videos"] == []

    def test_a_failure_choosing_clips_still_leaves_a_memory(self):
        """A story of photos is still a story."""
        with patch.object(
            memory_curator,
            "db_get_video_candidates_in_period",
            side_effect=Exception("no videos table"),
        ):
            upserts = run_curator(
                uncurated=make_images("trip", 9, step=timedelta(minutes=20))
            )
        assert upserts and upserts[0]["videos"] == []

    def test_clips_share_the_sort_order_sequence(self):
        upserts = run_curator(
            uncurated=make_images("trip", 9, step=timedelta(minutes=20)),
            video_candidates=self.candidates(1),
            video_signals=self.signals(1),
        )
        orders = [entry[1] for entry in upserts[0]["images"]] + [
            entry[1] for entry in upserts[0]["videos"]
        ]
        assert sorted(orders) == list(range(len(orders)))


class TestRunOrchestration:
    def test_returns_the_number_of_memories_written(self):
        with patch.object(memory_curator, "db_finish_memory_run") as finish:
            run_curator(anniversary=make_anniversary_images(2024, 5))
        assert finish.call_args[0][1] == "complete"
        assert finish.call_args[0][2] == 1

    def test_one_failing_trigger_does_not_cost_the_others(self):
        with patch.object(
            memory_curator, "_curate_semantic_events", side_effect=Exception("boom")
        ):
            upserts = run_curator(anniversary=make_anniversary_images(2024, 5))
        assert len(of_type(upserts, "anniversary")) == 1

    def test_run_reports_failure_without_raising(self):
        with (
            patch.object(
                memory_curator, "detect_home_location", side_effect=Exception("db down")
            ),
            patch.object(memory_curator, "db_finish_memory_run") as finish,
        ):
            generated = memory_curator.memory_curator_run(reference_date=REFERENCE)

        assert generated == 0
        assert finish.call_args[0][1] == "failed"

    def test_stale_memories_are_dropped_before_anything_is_built(self):
        """
        Their photos become candidates again only once the stale memory is
        gone, so the order matters, not just the call.
        """
        order: List[str] = []
        with (
            patch.object(
                memory_curator,
                "db_delete_stale_memories",
                side_effect=lambda: order.append("prune") or 0,
            ),
            patch.object(
                memory_curator,
                "db_get_anniversary_candidates",
                side_effect=lambda *a, **k: order.append("curate") or [],
            ),
        ):
            memory_curator.memory_curator_run(reference_date=REFERENCE)

        assert order[0] == "prune"

    def test_a_failing_prune_does_not_stop_the_run(self):
        with patch.object(
            memory_curator, "db_delete_stale_memories", side_effect=Exception("locked")
        ):
            upserts = run_curator(anniversary=make_anniversary_images(2024, 5))
        assert len(of_type(upserts, "anniversary")) == 1

    def test_empty_memories_are_pruned_with_the_configured_min_images(self):
        """
        Images deleted out from under a memory (a folder removal, say) leave
        it with nothing to show; this is what makes it stop surfacing.
        """
        with patch.object(memory_curator, "db_prune_empty_memories") as prune:
            run_curator(anniversary=make_anniversary_images(2024, 5))
        prune.assert_called_once_with(3)  # stub_preferences sets min_images=3

    def test_a_failing_empty_prune_does_not_stop_the_run(self):
        with patch.object(
            memory_curator, "db_prune_empty_memories", side_effect=Exception("locked")
        ):
            upserts = run_curator(anniversary=make_anniversary_images(2024, 5))
        assert len(of_type(upserts, "anniversary")) == 1

    def test_recently_used_is_refreshed_between_triggers(self):
        """Later triggers must not reuse what an earlier one just claimed."""
        mocks: Dict[str, Any] = {}
        run_curator(anniversary=make_anniversary_images(2024, 5), mocks=mocks)
        # Once when the context is built, then once after each of the three
        # triggers, so each sees what its predecessors consumed.
        assert mocks["db_get_recently_used_image_ids"].call_count == 4


# ##############################
# Enablement
# ##############################


class TestEnablement:
    def test_disabled_preferences_skip_curation(self):
        with (
            patch.object(
                memory_curator,
                "memory_curator_get_preferences",
                return_value=MemoriesPreferences(enabled=False),
            ),
            patch.object(memory_curator, "db_get_anniversary_candidates") as candidates,
        ):
            assert memory_curator.memory_curator_run() == 0
            candidates.assert_not_called()

    def test_declining_a_run_closes_a_claim_someone_else_made(self):
        """
        The route claims the run before handing off. If the preference is
        turned off in between, nobody else would ever close that row.
        """
        with (
            patch.object(
                memory_curator,
                "memory_curator_get_preferences",
                return_value=MemoriesPreferences(enabled=False),
            ),
            patch.object(
                memory_curator,
                "db_get_memory_run",
                return_value={"run_date": REFERENCE, "status": "running"},
            ),
            patch.object(memory_curator, "db_finish_memory_run") as finish,
        ):
            memory_curator.memory_curator_run(reference_date=REFERENCE)

        # Failed, not complete: re-enabling must still be able to generate today.
        finish.assert_called_once_with(REFERENCE, "failed", 0, "Memories are disabled")

    def test_declining_a_run_nobody_claimed_writes_nothing(self):
        with (
            patch.object(
                memory_curator,
                "memory_curator_get_preferences",
                return_value=MemoriesPreferences(enabled=False),
            ),
            patch.object(memory_curator, "db_get_memory_run", return_value=None),
            patch.object(memory_curator, "db_finish_memory_run") as finish,
        ):
            memory_curator.memory_curator_run(reference_date=REFERENCE)

        finish.assert_not_called()

    def test_force_overrides_the_disabled_flag(self):
        with patch.object(
            memory_curator,
            "memory_curator_get_preferences",
            return_value=MemoriesPreferences(enabled=False, min_images=3),
        ):
            upserts = run_curator(
                anniversary=make_anniversary_images(2024, 4), force=True
            )
        assert len(of_type(upserts, "anniversary")) == 1

    @pytest.mark.parametrize(
        "metadata",
        [
            None,
            {},
            {"user_preferences": {}},
            {"user_preferences": {"memories": {"min_images": 999}}},  # out of range
            {"user_preferences": {"memories": {"min_images": 40, "max_images": 10}}},
        ],
    )
    def test_missing_or_invalid_stored_preferences_fall_back_to_defaults(
        self, metadata
    ):
        with patch.object(memory_curator, "db_get_metadata", return_value=metadata):
            preferences = real_get_preferences()

        assert preferences.min_images == 5
        assert preferences.max_images == 30

    def test_stored_preferences_are_honoured(self):
        with patch.object(
            memory_curator,
            "db_get_metadata",
            return_value={"user_preferences": {"memories": {"min_images": 8}}},
        ):
            assert real_get_preferences().min_images == 8


class TestImportIdempotency:
    """
    The candidate pool must not depend on what is already curated. Defining it
    as "images not yet in a memory" makes every regeneration rebuild a memory
    from its own complement, so counts alternate and the contents swap wholesale.
    """

    def test_regenerating_reproduces_the_same_memory(self):
        pool = make_images("trip", 12, step=timedelta(minutes=20))

        first = of_type(run_curator(uncurated=pool), "import_event")
        # Second run sees the first run's images already curated.
        own = {entry[0] for entry in first[0]["images"]}
        second = of_type(
            run_curator(uncurated=pool, recently_used=own, own_images=own),
            "import_event",
        )

        assert [e[0] for e in second[0]["images"]] == [e[0] for e in first[0]["images"]]
        assert second[0]["memory"]["dedupe_key"] == first[0]["memory"]["dedupe_key"]

    def test_a_memory_may_reuse_its_own_photos(self):
        """Its own images are not 'already used' as far as that memory goes."""
        pool = make_images("trip", 8, step=timedelta(minutes=20))
        own = {f"trip-{i}" for i in range(8)}

        upserts = of_type(
            run_curator(uncurated=pool, recently_used=own, own_images=own),
            "import_event",
        )

        assert len(upserts) == 1
        assert len(upserts[0]["images"]) == 8

    def test_other_memories_photos_stay_excluded(self):
        pool = make_images("trip", 10, step=timedelta(minutes=20))
        upserts = of_type(
            run_curator(uncurated=pool, recently_used={"trip-0", "trip-1"}),
            "import_event",
        )

        selected = {entry[0] for entry in upserts[0]["images"]}
        assert "trip-0" not in selected and "trip-1" not in selected

    def test_most_recent_segments_win_the_cap(self):
        """A newly imported trip must not lose its slot to older, larger ones."""
        pool: List[Dict[str, Any]] = []
        for day, size in ((0, 30), (10, 25), (20, 20), (40, 6)):
            pool += make_images(
                f"d{day}",
                size,
                start=T0 + timedelta(days=day),
                step=timedelta(minutes=10),
            )
        upserts = of_type(run_curator(uncurated=pool), "import_event")

        assert len(upserts) == memory_curator.MAX_IMPORT_MEMORIES
        # d40 is the newest and smallest; it must still be included.
        keys = {u["memory"]["dedupe_key"] for u in upserts}
        assert any((T0 + timedelta(days=40)).strftime("%Y-%m-%d") in k for k in keys)


class TestPeriodLabels:
    @pytest.mark.parametrize(
        "start, end, expected",
        [
            (datetime(2026, 7, 26, 9), datetime(2026, 7, 26, 18), "26 July 2026"),
            (datetime(2026, 7, 17, 9), datetime(2026, 7, 18, 9), "17–18 July 2026"),
            (datetime(2026, 7, 30, 9), datetime(2026, 8, 2, 9), "30 Jul – 2 Aug 2026"),
            (datetime(2025, 12, 30), datetime(2026, 1, 2), "Dec 2025 – Jan 2026"),
        ],
    )
    def test_labels_a_span_by_its_dates(self, start, end, expected):
        assert memory_curator._format_period_label(start, end) == expected

    def test_import_titles_do_not_collide_within_a_month(self):
        """Three bursts in one month must not all be titled "July 2026"."""
        pool = make_images(
            "a", 8, start=datetime(2026, 7, 5, 9), step=timedelta(minutes=20)
        )
        pool += make_images(
            "b", 8, start=datetime(2026, 7, 18, 9), step=timedelta(minutes=20)
        )
        pool += make_images(
            "c", 8, start=datetime(2026, 7, 25, 9), step=timedelta(minutes=20)
        )

        upserts = of_type(
            run_curator(uncurated=pool, reference_date="2026-07-27"), "import_event"
        )
        titles = [u["memory"]["title"] for u in upserts]
        assert len(set(titles)) == len(titles), titles
