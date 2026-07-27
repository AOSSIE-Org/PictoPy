from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import numpy as np
import pytest

from app.schemas.user_preferences import MemoryScoringWeights
from app.utils import memory_scoring
from app.utils.memory_scoring import (
    aggregate_memory_score,
    cohesion_baseline,
    composite_score,
    compute_signals,
    detect_home_location,
    haversine_km,
    mean_pairwise_cohesion,
    parse_captured_at,
    resolve_weights,
    score_candidates,
    scoring_signature,
    spread_over_time,
    suppress_near_duplicates,
    trim_incoherent,
)

WEIGHTS = MemoryScoringWeights()
HOME = (12.9716, 77.5946)  # Bengaluru
T0 = datetime(2024, 7, 26, 10, 0, 0)


def make_row(**overrides: Any) -> Dict[str, Any]:
    """A signal row for an image with nothing going for it."""
    row: Dict[str, Any] = {
        "id": "img-0",
        "isFavourite": False,
        "in_album": False,
        "named_people": 0,
        "face_count": 0,
        "top_semantic_score": None,
        "top_event_score": None,
        "class_count": 0,
        "scored_signature": None,
        "latitude": None,
        "longitude": None,
        "captured_at": None,
    }
    row.update(overrides)
    return row


def score_row(**overrides: Any) -> float:
    values, available = compute_signals(make_row(**overrides), HOME)
    return composite_score(values, available, WEIGHTS)


def candidate(
    image_id: str, score: float = 1.0, captured_at: Optional[datetime] = T0
) -> Dict[str, Any]:
    return {"id": image_id, "score": score, "captured_at": captured_at}


# ##############################
# Haversine
# ##############################


class TestHaversine:
    @pytest.mark.parametrize(
        "a, b, expected_km, tolerance",
        [
            ((12.9716, 77.5946), (12.9716, 77.5946), 0, 1),  # same point
            ((12.9716, 77.5946), (19.0760, 72.8777), 845, 30),  # Bengaluru-Mumbai
            ((48.8566, 2.3522), (51.5074, -0.1278), 344, 20),  # Paris-London
            ((0.0, 0.0), (0.0, 180.0), 20015, 50),  # antipodal on the equator
        ],
    )
    def test_matches_known_distances(self, a, b, expected_km, tolerance):
        assert abs(haversine_km(*a, *b) - expected_km) <= tolerance

    def test_is_symmetric(self):
        forward = haversine_km(12.9716, 77.5946, 48.8566, 2.3522)
        backward = haversine_km(48.8566, 2.3522, 12.9716, 77.5946)
        assert forward == pytest.approx(backward)


# ##############################
# Weights
# ##############################


class TestResolveWeights:
    @pytest.mark.parametrize("stored", [None, {}, {"unknown_signal": 0.5}])
    def test_falls_back_to_defaults(self, stored):
        assert resolve_weights(stored).favourite == pytest.approx(0.22)

    def test_normalizes_a_partial_set(self):
        weights = resolve_weights({"favourite": 1.0})
        total = sum(
            getattr(weights, name) for name in MemoryScoringWeights.model_fields
        )
        assert total == pytest.approx(1.0)

    @pytest.mark.parametrize("bad", [{"favourite": -0.1}, {"favourite": 1.5}])
    def test_rejects_out_of_range_and_uses_defaults(self, bad):
        assert resolve_weights(bad).favourite == pytest.approx(0.22)

    def test_all_zero_falls_back_to_defaults(self):
        zeroed = {name: 0.0 for name in MemoryScoringWeights.model_fields}
        assert resolve_weights(zeroed).favourite == pytest.approx(0.22)


class TestScoringSignature:
    def test_is_stable_for_equivalent_weight_sets(self):
        """Signature must depend on the values, not on how they were built."""
        first = scoring_signature(MemoryScoringWeights(), 1)
        # Same values, supplied explicitly and in a different key order.
        explicit = scoring_signature(
            MemoryScoringWeights.model_validate(
                {"in_album": 0.08, "favourite": 0.22, "gps_novelty": 0.10}
            ),
            1,
        )
        # Doubling every weight normalizes back to the same distribution.
        doubled = scoring_signature(
            MemoryScoringWeights.model_validate(
                {
                    name: field.default * 2
                    for name, field in MemoryScoringWeights.model_fields.items()
                }
            ),
            1,
        )
        assert first == explicit == doubled

    def test_changes_with_version_and_weights(self):
        baseline = scoring_signature(MemoryScoringWeights(), 1)
        assert scoring_signature(MemoryScoringWeights(), 2) != baseline
        assert scoring_signature(MemoryScoringWeights(favourite=0.9), 1) != baseline


# ##############################
# Signal normalization
# ##############################


class TestComputeSignals:
    @pytest.mark.parametrize(
        "named_people, expected",
        [(0, 0.0), (1, 1 / 3), (3, 1.0), (7, 1.0)],  # saturates at 3
    )
    def test_known_people_saturates(self, named_people, expected):
        values, _ = compute_signals(make_row(named_people=named_people), HOME)
        assert values["known_people"] == pytest.approx(expected)

    @pytest.mark.parametrize(
        "face_count, expected",
        [(0, 0.0), (2, 0.5), (4, 1.0), (12, 1.0)],  # saturates at 4
    )
    def test_face_presence_saturates(self, face_count, expected):
        values, _ = compute_signals(make_row(face_count=face_count), HOME)
        assert values["face_presence"] == pytest.approx(expected)

    def test_gps_novelty_grows_with_distance(self):
        near, _ = compute_signals(make_row(latitude=12.98, longitude=77.60), HOME)
        far, _ = compute_signals(make_row(latitude=48.85, longitude=2.35), HOME)
        assert near["gps_novelty"] < far["gps_novelty"] <= 1.0

    def test_gps_novelty_at_home_is_zero(self):
        values, _ = compute_signals(make_row(latitude=HOME[0], longitude=HOME[1]), HOME)
        assert values["gps_novelty"] == pytest.approx(0.0)

    @pytest.mark.parametrize(
        "row, signal",
        [
            ({"latitude": None, "longitude": None}, "gps_novelty"),
            ({"scored_signature": None}, "semantic_confidence"),
            ({"scored_signature": None}, "event_strength"),
        ],
    )
    def test_missing_sources_are_unavailable(self, row, signal):
        _, available = compute_signals(make_row(**row), HOME)
        assert signal not in available

    def test_no_home_makes_gps_unavailable_even_with_coordinates(self):
        _, available = compute_signals(make_row(latitude=12.98, longitude=77.60), None)
        assert "gps_novelty" not in available

    @pytest.mark.parametrize(
        "signal", ["favourite", "known_people", "face_presence", "in_album"]
    )
    def test_zero_valued_signals_stay_available(self, signal):
        """A landscape genuinely has no faces; that is data, not absence."""
        _, available = compute_signals(make_row(), HOME)
        assert signal in available


# ##############################
# Composite score
# ##############################


class TestCompositeScore:
    def test_availability_renormalization(self):
        """
        The invariant that makes renormalization worth having: an image with
        no GPS must score exactly as an otherwise identical image sitting at
        home. Missing a sensor reading is not a demerit.
        """
        no_gps = score_row()
        at_home = score_row(latitude=HOME[0], longitude=HOME[1])
        assert no_gps == pytest.approx(at_home)

    def test_unscored_image_is_not_penalized_against_a_scored_zero(self):
        unscored = score_row()
        scored_zero = score_row(scored_signature="sig", top_semantic_score=0.0)
        assert unscored == pytest.approx(scored_zero)

    def test_travel_beats_staying_home(self):
        assert score_row(latitude=48.85, longitude=2.35) > score_row(
            latitude=HOME[0], longitude=HOME[1]
        )

    @pytest.mark.parametrize(
        "overrides",
        [
            {"isFavourite": True},
            {"in_album": True},
            {"named_people": 2},
            {"face_count": 3},
            {"scored_signature": "sig", "top_event_score": 0.9},
        ],
    )
    def test_every_signal_raises_the_score(self, overrides):
        assert score_row(**overrides) > score_row()

    def test_score_stays_within_bounds(self):
        best = score_row(
            isFavourite=True,
            in_album=True,
            named_people=5,
            face_count=9,
            scored_signature="sig",
            top_semantic_score=1.0,
            top_event_score=1.0,
            latitude=48.85,
            longitude=2.35,
        )
        assert 0.0 <= score_row() <= best <= 1.0

    def test_no_available_signals_scores_zero(self):
        assert composite_score({}, set(), WEIGHTS) == 0.0


class TestScoreCandidates:
    def test_orders_by_score_descending(self):
        rows = [
            make_row(id="dull"),
            make_row(id="favourite", isFavourite=True),
            make_row(id="album", in_album=True),
        ]
        ranked = score_candidates(rows, WEIGHTS, HOME)
        assert ranked[0]["id"] == "favourite"
        assert ranked[-1]["id"] == "dull"

    def test_penalizes_without_dropping(self):
        rows = [make_row(id="a", isFavourite=True), make_row(id="b", in_album=True)]
        ranked = score_candidates(
            rows, WEIGHTS, HOME, penalized_ids={"a"}, penalty=0.35
        )
        assert {c["id"] for c in ranked} == {"a", "b"}
        assert ranked[0]["id"] == "b"

    def test_carries_signals_and_timestamps_through(self):
        rows = [make_row(id="a", captured_at="2024-07-26 10:00:00")]
        ranked = score_candidates(rows, WEIGHTS, HOME)
        assert ranked[0]["captured_at"] == T0
        assert "favourite" in ranked[0]["signals"]


# ##############################
# Near-duplicate suppression
# ##############################


class TestSuppressNearDuplicates:
    SIMILAR = np.array([0.9999, 0.0141], dtype=np.float32)  # cosine ~0.9999
    BASE = np.array([1.0, 0.0], dtype=np.float32)
    DIFFERENT = np.array([0.0, 1.0], dtype=np.float32)  # orthogonal

    def _run(self, second_vector, second_time):
        embeddings = {"a": self.BASE, "b": second_vector}
        candidates = [candidate("a"), candidate("b", captured_at=second_time)]
        return [c["id"] for c in suppress_near_duplicates(candidates, embeddings)]

    @pytest.mark.parametrize(
        "similar, delta, expected, reason",
        [
            (True, timedelta(seconds=2), ["a"], "burst frame"),
            (True, timedelta(seconds=60), ["a"], "rapid-fire shutter"),
            # Both conditions are required, which is the whole point:
            (True, timedelta(minutes=30), ["a", "b"], "same view, later that day"),
            (True, timedelta(days=1), ["a", "b"], "morning coffee every day"),
            (True, timedelta(days=365), ["a", "b"], "annual anniversary photo"),
            (False, timedelta(seconds=2), ["a", "b"], "subject moved"),
            (False, timedelta(days=365), ["a", "b"], "unrelated"),
        ],
    )
    def test_duplicate_requires_similarity_and_proximity(
        self, similar, delta, expected, reason
    ):
        vector = self.SIMILAR if similar else self.DIFFERENT
        assert self._run(vector, T0 + delta) == expected, reason

    @pytest.mark.parametrize("delta_seconds", [119, 121])
    def test_time_window_boundary(self, delta_seconds):
        survivors = self._run(self.SIMILAR, T0 + timedelta(seconds=delta_seconds))
        assert survivors == (["a"] if delta_seconds <= 120 else ["a", "b"])

    def test_cosine_threshold_boundary(self):
        # Just under the threshold: kept despite being seconds apart.
        below = np.array([0.88, np.sqrt(1 - 0.88**2)], dtype=np.float32)
        assert self._run(below, T0 + timedelta(seconds=1)) == ["a", "b"]

    def test_keeps_images_with_no_embedding(self):
        candidates = [candidate("a"), candidate("missing")]
        survivors = suppress_near_duplicates(candidates, {"a": self.BASE})
        assert [c["id"] for c in survivors] == ["a", "missing"]

    def test_keeps_images_with_no_timestamp(self):
        """Without a time the pair test cannot be satisfied, so keep it."""
        embeddings = {"a": self.BASE, "b": self.SIMILAR}
        candidates = [candidate("a"), candidate("b", captured_at=None)]
        survivors = suppress_near_duplicates(candidates, embeddings)
        assert [c["id"] for c in survivors] == ["a", "b"]

    def test_higher_ranked_candidate_survives(self):
        embeddings = {"low": self.BASE, "high": self.SIMILAR}
        candidates = [
            candidate("high", score=0.9),
            candidate("low", score=0.1, captured_at=T0 + timedelta(seconds=1)),
        ]
        survivors = suppress_near_duplicates(candidates, embeddings)
        assert [c["id"] for c in survivors] == ["high"]

    def test_empty_input(self):
        assert suppress_near_duplicates([], {}) == []


# ##############################
# Time spreading
# ##############################


class TestSpreadOverTime:
    def test_returns_everything_when_under_target(self):
        candidates = [candidate(f"i{n}") for n in range(3)]
        assert len(spread_over_time(candidates, 10)) == 3

    @pytest.mark.parametrize(
        "count, target",
        [
            (3, 10),  # under target, early return
            (6, 4),  # bucketed
            (3, 3),  # exactly at target
        ],
    )
    def test_output_is_always_chronological(self, count, target):
        """
        A story has to read forwards, whichever path selected the images.
        Candidates arrive best-first, so score order is the wrong order out.
        """
        candidates = [
            candidate(f"i{n}", score=1.0 - n / 10, captured_at=T0 - timedelta(days=n))
            for n in range(count)
        ]
        selected = spread_over_time(candidates, target)
        timestamps = [c["captured_at"] for c in selected]
        assert timestamps == sorted(timestamps)

    def test_undated_images_sort_first_without_crashing(self):
        candidates = [
            candidate("dated", captured_at=T0),
            candidate("undated", captured_at=None),
        ]
        assert len(spread_over_time(candidates, 5)) == 2

    def test_samples_across_the_span_not_one_clump(self):
        """Ten frames from one minute of a three-day trip is a bad story."""
        clumped = [
            candidate(f"clump{n}", score=1.0, captured_at=T0 + timedelta(seconds=n))
            for n in range(20)
        ]
        spread = [
            candidate(f"late{n}", score=0.5, captured_at=T0 + timedelta(days=n))
            for n in range(1, 4)
        ]
        selected = spread_over_time(clumped + spread, 4)

        assert len(selected) == 4
        # The later days are represented despite scoring lower.
        assert any(c["id"].startswith("late") for c in selected)

    def test_result_is_chronological(self):
        candidates = [
            candidate(f"i{n}", score=1.0 - n / 10, captured_at=T0 + timedelta(days=n))
            for n in range(6)
        ]
        selected = spread_over_time(candidates, 4)
        timestamps = [c["captured_at"] for c in selected]
        assert timestamps == sorted(timestamps)

    def test_backfills_when_buckets_are_empty(self):
        candidates = [
            candidate(f"i{n}", score=1.0, captured_at=T0 + timedelta(seconds=n))
            for n in range(10)
        ]
        assert len(spread_over_time(candidates, 5)) == 5

    def test_zero_span_falls_back_to_score_order(self):
        candidates = [candidate(f"i{n}", score=1.0 - n / 10) for n in range(6)]
        selected = spread_over_time(candidates, 3)
        assert [c["id"] for c in selected] == ["i0", "i1", "i2"]

    @pytest.mark.parametrize("target", [0, -1])
    def test_non_positive_target_returns_nothing(self, target):
        assert spread_over_time([candidate("a")], target) == []


# ##############################
# Memory-level score
# ##############################


class TestAggregateMemoryScore:
    def test_empty_set_scores_zero(self):
        assert aggregate_memory_score([]) == 0.0

    def test_stronger_images_score_higher(self):
        weak = [{"score": 0.2, "class_count": 1} for _ in range(5)]
        strong = [{"score": 0.8, "class_count": 1} for _ in range(5)]
        assert aggregate_memory_score(strong) > aggregate_memory_score(weak)

    def test_larger_memories_get_a_modest_boost(self):
        small = [{"score": 0.5, "class_count": 1} for _ in range(5)]
        large = [{"score": 0.5, "class_count": 1} for _ in range(25)]
        assert aggregate_memory_score(large) > aggregate_memory_score(small)

    def test_more_varied_content_scores_higher(self):
        plain = [{"score": 0.5, "class_count": 1} for _ in range(10)]
        varied = [{"score": 0.5, "class_count": 9} for _ in range(10)]
        assert aggregate_memory_score(varied) > aggregate_memory_score(plain)

    def test_uses_the_best_images_not_the_average(self):
        """A few standouts should not be diluted by a long tail."""
        with_tail = [{"score": 0.9, "class_count": 1} for _ in range(5)] + [
            {"score": 0.0, "class_count": 1} for _ in range(5)
        ]
        without_tail = [{"score": 0.9, "class_count": 1} for _ in range(5)]
        assert aggregate_memory_score(with_tail) >= aggregate_memory_score(without_tail)


# ##############################
# Home detection
# ##############################


class TestDetectHomeLocation:
    def test_returns_the_centre_of_the_densest_cell(self):
        histogram: List[Any] = [(13.0, 77.6, 400), (48.9, 2.4, 20)]
        with (
            patch.object(
                memory_scoring, "db_get_gps_histogram", return_value=histogram
            ),
            patch.object(
                memory_scoring, "db_get_gps_cell_centre", return_value=HOME
            ) as centre,
        ):
            assert detect_home_location() == HOME
        centre.assert_called_once_with(13.0, 77.6, memory_scoring.HOME_CELL_PRECISION)

    def test_returns_none_below_the_geotag_floor(self):
        """Too little GPS data disables the signal rather than guessing."""
        with patch.object(memory_scoring, "db_get_gps_histogram", return_value=[]):
            assert detect_home_location() is None

    def test_applies_the_minimum_image_threshold(self):
        with patch.object(
            memory_scoring, "db_get_gps_histogram", return_value=[]
        ) as histogram:
            detect_home_location()
        assert (
            histogram.call_args.kwargs["min_images"]
            == memory_scoring.MIN_IMAGES_FOR_HOME
        )


# ##############################
# Timestamp parsing
# ##############################


class TestParseCapturedAt:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("2024-07-26 10:00:00", T0),
            ("2024-07-26T10:00:00Z", T0),
            (T0, T0),
            ("not-a-date", None),
            ("", None),
            (None, None),
            (12345, None),
        ],
    )
    def test_parses_or_returns_none(self, value, expected):
        assert parse_captured_at(value) == expected


# ##############################
# Cohesion
# ##############################


CONE_HALF_ANGLE = 1.1  # radians; wide enough to separate, narrow enough to
# keep every pair's cosine positive


def cone_vector(position: float) -> np.ndarray:
    """
    A unit vector at `position` (0..1) across a narrow cone.

    Mimics how SigLIP2 actually distributes embeddings: everything points
    broadly the same way, so cosines are high even between unrelated images
    and only *differences* in cosine carry information.
    """
    tilt = CONE_HALF_ANGLE * position
    return np.array(
        [np.cos(tilt), np.sin(tilt) * 0.6, np.sin(tilt) * 0.8], dtype=np.float32
    )


class TestMeanPairwiseCohesion:
    def test_identical_vectors_are_perfectly_cohesive(self):
        v = np.array([1.0, 0.0], dtype=np.float32)
        assert mean_pairwise_cohesion([v, v, v]) == pytest.approx(1.0)

    def test_orthogonal_vectors_score_zero(self):
        a = np.array([1.0, 0.0], dtype=np.float32)
        b = np.array([0.0, 1.0], dtype=np.float32)
        assert mean_pairwise_cohesion([a, b]) == pytest.approx(0.0, abs=1e-6)

    def test_does_not_drift_with_group_size(self):
        """
        The reason this exists rather than cohesion to the centroid: each
        image contributes 1/k of the centroid it is then measured against, so
        centroid cohesion rewards small groups for being small. Same spread,
        different k, must read the same.
        """
        rng = np.random.default_rng(3)

        def average(k: int) -> float:
            return float(
                np.mean(
                    [
                        mean_pairwise_cohesion([cone_vector(p) for p in rng.random(k)])
                        for _ in range(60)
                    ]
                )
            )

        assert abs(average(4) - average(20)) < 0.03

    @pytest.mark.parametrize("count", [0, 1])
    def test_needs_a_pair(self, count: int):
        assert mean_pairwise_cohesion([cone_vector(0.0)] * count) is None

    def test_normalizes_unnormalized_input(self):
        a = np.array([3.0, 0.0], dtype=np.float32)
        b = np.array([10.0, 0.0], dtype=np.float32)
        assert mean_pairwise_cohesion([a, b]) == pytest.approx(1.0)


class TestCohesionBaseline:
    def test_reports_what_unrelated_photos_already_score(self):
        """
        Measured against the user's library this sits near 0.59, which is why
        the old absolute gate of 0.55 could never reject anything.
        """
        sample = [cone_vector(i / 39) for i in range(40)]
        baseline = cohesion_baseline(sample)
        assert baseline is not None
        assert 0.0 < baseline < 1.0

    def test_a_coherent_group_sits_above_the_baseline(self):
        sample = [cone_vector(i / 39) for i in range(40)]
        tight = [cone_vector(0.05 + i * 0.002) for i in range(8)]
        assert mean_pairwise_cohesion(tight) > cohesion_baseline(sample)


class TestTrimIncoherent:
    def group(self, tight: int, outliers: int) -> tuple:
        candidates, embeddings = [], {}
        for i in range(tight):
            key = f"in-{i}"
            candidates.append(candidate(key))
            embeddings[key] = cone_vector(0.05 + i * 0.01)
        for i in range(outliers):
            key = f"out-{i}"
            candidates.append(candidate(key))
            embeddings[key] = cone_vector(0.85 + i * 0.03)
        return candidates, embeddings

    def test_drops_the_photo_that_does_not_belong(self):
        """
        The case this was built for: an afternoon at the beach plus two
        screenshots taken that evening. The clock cannot tell them apart.
        """
        candidates, embeddings = self.group(tight=9, outliers=2)
        kept = {c["id"] for c in trim_incoherent(candidates, embeddings, min_keep=5)}
        assert kept == {f"in-{i}" for i in range(9)}

    def test_a_varied_but_related_group_survives_intact(self):
        """
        A day out legitimately varies — the drive to the beach is not the
        beach. An absolute floor would throw the drive away; the group's own
        spread keeps it.
        """
        candidates, embeddings = [], {}
        for i in range(10):
            key = f"img-{i}"
            candidates.append(candidate(key))
            embeddings[key] = cone_vector(0.02 + i * 0.055)
        kept = trim_incoherent(candidates, embeddings, min_keep=5)
        assert len(kept) == 10

    def test_a_tight_group_does_not_trim_its_own_tail(self):
        """Without the margin floor, 2 MADs out of a near-identical burst
        still deletes photos."""
        candidates, embeddings = self.group(tight=10, outliers=0)
        assert len(trim_incoherent(candidates, embeddings, min_keep=5)) == 10

    def test_never_trims_below_min_keep(self):
        candidates, embeddings = self.group(tight=6, outliers=2)
        kept = trim_incoherent(candidates, embeddings, min_keep=8)
        assert len(kept) == 8

    def test_two_equal_clusters_are_left_alone(self):
        """
        Half the group cannot be "the outliers". Two occasions got merged, and
        trimming is the wrong tool for that — the cap is what says so.
        """
        candidates, embeddings = self.group(tight=5, outliers=5)
        assert len(trim_incoherent(candidates, embeddings, min_keep=3)) == 10

    def test_images_without_embeddings_are_kept(self):
        """Missing data is not a verdict — the same rule dedup follows."""
        candidates, embeddings = self.group(tight=9, outliers=2)
        candidates.append(candidate("unknown"))
        kept = {c["id"] for c in trim_incoherent(candidates, embeddings, min_keep=5)}
        assert "unknown" in kept

    def test_too_few_embeddings_to_judge_leaves_the_group_alone(self):
        candidates, embeddings = self.group(tight=9, outliers=2)
        sparse = {k: v for k, v in list(embeddings.items())[:2]}
        assert len(trim_incoherent(candidates, sparse, min_keep=5)) == len(candidates)
