from contextlib import ExitStack
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterator, List, Optional, Sequence
from unittest.mock import patch

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
            "captured_at": (T0 + timedelta(hours=hash(image_id) % 24)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
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

    def capture(memory, images):
        upserts.append({"memory": memory, "images": images})
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
        m("db_get_top_event_label", return_value=top_event_label)
        m("db_get_embeddings_for_image_ids", return_value=embeddings or {})
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

        def flaky(memory, images):
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

    def test_falls_back_to_the_dates_without_a_recognised_event(self):
        pool = make_images("misc", 6, step=timedelta(minutes=20))
        upserts = of_type(run_curator(uncurated=pool), "import_event")
        assert upserts[0]["memory"]["title"] == "26 July 2024"

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
    def _occurrence(self, count=8, score=0.6):
        return memory_curator.group_event_occurrences(
            event_hits(1001, count, score=score)
        )[0]

    def test_accepts_a_coherent_occurrence(self):
        occurrence = self._occurrence()
        assert memory_curator.passes_coherence_gate(
            occurrence, coherent_embeddings(event_hits(1001, 8))
        )

    def test_rejects_too_few_images(self):
        occurrence = self._occurrence(count=3)
        assert not memory_curator.passes_coherence_gate(occurrence, {})

    @pytest.mark.parametrize("score", [0.2, 0.24])
    def test_rejects_weak_mean_score(self, score):
        occurrence = self._occurrence(score=score)
        assert not memory_curator.passes_coherence_gate(occurrence, {})

    def test_rejects_when_no_image_scores_strongly(self):
        """Uniformly middling scores mean the label never really fired."""
        occurrence = self._occurrence(score=0.3)
        assert occurrence["mean_score"] >= memory_curator.EVENT_MEAN_SCORE
        assert not memory_curator.passes_coherence_gate(occurrence, {})

    def test_rejects_visually_incoherent_photos(self):
        """The gate that stops 'picnic' matching three unrelated lawn shots."""
        hits = event_hits(1001, 8)
        occurrence = memory_curator.group_event_occurrences(hits)[0]
        scattered = {
            hit["image_id"]: SCATTER_BASIS[i % len(SCATTER_BASIS)]
            for i, hit in enumerate(hits)
        }
        assert not memory_curator.passes_coherence_gate(occurrence, scattered)

    def test_accepts_when_embeddings_are_unavailable(self):
        """Score gates already passed; do not drop everything for want of vectors."""
        assert memory_curator.passes_coherence_gate(self._occurrence(), {})


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
