"""
Memory scoring.

Ranks candidate images by combining signals PictoPy already stores, then
trims the result down to a set worth showing: near-duplicates removed and the
survivors spread across the event's span.

Every signal is normalized to 0-1, weighted, and summed. Weights are
user-adjustable and live in the metadata blob.
"""

import hashlib
import json
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

from app.database.memories import db_get_gps_cell_centre, db_get_gps_histogram
from app.logging.setup_logging import get_logger
from app.schemas.user_preferences import MemoryScoringWeights

logger = get_logger(__name__)

# Saturation points. Beyond these, more of the same signal says nothing extra:
# a photo with six faces is not three times more memorable than one with two.
MAX_NAMED_PEOPLE = 3
MAX_FACES = 4

# Distance from home at which gps_novelty is ~63% saturated.
GPS_NOVELTY_SCALE_KM = 50.0

# Home detection. 0.1 degrees is roughly 11 km; below the floor there is not
# enough geotagged data to call anywhere "home".
HOME_CELL_PRECISION = 1
MIN_IMAGES_FOR_HOME = 20

# Near-duplicate rule. BOTH must hold: visual similarity alone would collapse
# a daily-coffee photo, a revisited viewpoint, or an annual anniversary shot
# into a single survivor. Those are near-identical and genuinely distinct.
# Temporal proximity is necessary, never sufficient.
DUP_COSINE = 0.90
DUP_WINDOW_SECONDS = 120.0

EARTH_RADIUS_KM = 6371.0

# Signals that are meaningful even when zero: a landscape genuinely has no
# faces. The rest distinguish "absent data" from "measured zero" and are
# renormalized out when their source is missing.
ALWAYS_AVAILABLE = frozenset({"favourite", "known_people", "face_presence", "in_album"})


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two coordinates, in kilometres."""
    lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def resolve_weights(stored: Optional[Dict[str, Any]]) -> MemoryScoringWeights:
    """
    Build a normalized weight set from stored preferences.

    Stored values are raw slider positions; the model normalizes them to sum
    to 1.0 and falls back to defaults on anything unusable.
    """
    if not stored:
        return MemoryScoringWeights()
    try:
        return MemoryScoringWeights.model_validate(stored)
    except ValueError as e:
        logger.warning(f"Invalid scoring weights, using defaults: {e}")
        return MemoryScoringWeights()


def scoring_signature(weights: MemoryScoringWeights, version: int) -> str:
    """Fingerprint the scoring inputs so stale memories are detectable."""
    payload = {"version": version, "weights": weights.model_dump()}
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def parse_captured_at(value: Any) -> Optional[datetime]:
    """Parse a stored captured_at value, tolerating trailing Z and bad data."""
    if isinstance(value, datetime):
        return value
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.rstrip("Z"))
    except ValueError:
        return None


def detect_home_location() -> Optional[Tuple[float, float]]:
    """
    Estimate where the user lives, as the densest GPS cell.

    Returns None when the library holds too few geotagged photos to say,
    which correctly disables the gps_novelty signal rather than treating
    every photo as taken at home.
    """
    histogram = db_get_gps_histogram(
        precision=HOME_CELL_PRECISION, min_images=MIN_IMAGES_FOR_HOME
    )
    if not histogram:
        return None

    cell_lat, cell_lon, _ = histogram[0]
    return db_get_gps_cell_centre(cell_lat, cell_lon, HOME_CELL_PRECISION)


def compute_signals(
    row: Dict[str, Any], home: Optional[Tuple[float, float]]
) -> Tuple[Dict[str, float], Set[str]]:
    """
    Turn one image's raw signal row into normalized values.

    Returns the values plus the set of signals that actually have data behind
    them, so the weighted sum can renormalize over what is available.
    """
    values: Dict[str, float] = {}
    available: Set[str] = set(ALWAYS_AVAILABLE)

    values["favourite"] = 1.0 if row.get("isFavourite") else 0.0
    values["in_album"] = 1.0 if row.get("in_album") else 0.0
    values["known_people"] = (
        min(row.get("named_people") or 0, MAX_NAMED_PEOPLE) / MAX_NAMED_PEOPLE
    )
    values["face_presence"] = min(row.get("face_count") or 0, MAX_FACES) / MAX_FACES

    # Semantic signals only exist once the image has been scored against the
    # vocabulary. An unscored image is not a boring image.
    is_scored = bool(row.get("scored_signature"))
    top_semantic = row.get("top_semantic_score")
    top_event = row.get("top_event_score")
    values["semantic_confidence"] = float(top_semantic or 0.0)
    values["event_strength"] = float(top_event or 0.0)
    if is_scored:
        available.add("semantic_confidence")
        available.add("event_strength")

    # Missing GPS is not "at home", so leave the signal unavailable rather
    # than scoring it zero.
    latitude = row.get("latitude")
    longitude = row.get("longitude")
    if latitude is not None and longitude is not None and home is not None:
        distance = haversine_km(latitude, longitude, home[0], home[1])
        values["gps_novelty"] = 1.0 - math.exp(-distance / GPS_NOVELTY_SCALE_KM)
        available.add("gps_novelty")
    else:
        values["gps_novelty"] = 0.0

    return values, available


def composite_score(
    values: Dict[str, float],
    available: Set[str],
    weights: MemoryScoringWeights,
) -> float:
    """
    Weighted sum renormalized over the signals that have data.

    Without renormalizing, an image with no GPS would be penalized purely for
    lacking a sensor reading, which is not a statement about the photo.
    """
    total_weight = 0.0
    total = 0.0
    for name in type(weights).model_fields:
        if name not in available:
            continue
        weight = getattr(weights, name)
        total_weight += weight
        total += weight * values.get(name, 0.0)

    if total_weight <= 0:
        return 0.0
    return total / total_weight


def score_candidates(
    signal_rows: Sequence[Dict[str, Any]],
    weights: MemoryScoringWeights,
    home: Optional[Tuple[float, float]],
    penalized_ids: Optional[Set[str]] = None,
    penalty: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Score every candidate, highest first.

    `penalized_ids` are demoted rather than dropped, for triggers whose pool
    is too small to spare a photo.
    """
    penalized = penalized_ids or set()
    scored: List[Dict[str, Any]] = []

    for row in signal_rows:
        values, available = compute_signals(row, home)
        score = composite_score(values, available, weights)
        if row["id"] in penalized:
            score *= penalty
        scored.append(
            {
                "id": row["id"],
                "score": score,
                "signals": values,
                "captured_at": parse_captured_at(row.get("captured_at")),
                "class_count": row.get("class_count") or 0,
            }
        )

    scored.sort(key=lambda item: -item["score"])
    return scored


def _unit(vector: np.ndarray) -> np.ndarray:
    """Normalize defensively; stored embeddings should already be unit-norm."""
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm > 0 else vector


def suppress_near_duplicates(
    candidates: Sequence[Dict[str, Any]],
    embeddings: Dict[str, np.ndarray],
    cosine_threshold: float = DUP_COSINE,
    window_seconds: float = DUP_WINDOW_SECONDS,
) -> List[Dict[str, Any]]:
    """
    Drop shots that are both visually near-identical and close in time.

    Both conditions are required. Similarity alone would delete the second of
    two annual anniversary photos taken from the same spot; time alone would
    delete a genuinely different frame captured three seconds later.

    Candidates must arrive best-first: the survivor of a duplicate pair is
    whichever was already ranked higher.
    """
    survivors: List[Dict[str, Any]] = []
    survivor_vectors: List[Tuple[np.ndarray, Optional[datetime]]] = []

    for candidate in candidates:
        vector = embeddings.get(candidate["id"])
        timestamp = candidate.get("captured_at")

        # Without an embedding or a timestamp the pair test cannot be
        # satisfied, so the image is not a duplicate. Keep it.
        if vector is not None and timestamp is not None:
            vector = _unit(vector)
            is_duplicate = False
            for kept_vector, kept_time in survivor_vectors:
                if kept_time is None or kept_vector is None:
                    continue
                gap = abs((timestamp - kept_time).total_seconds())
                if gap > window_seconds:
                    continue
                if float(np.dot(kept_vector, vector)) >= cosine_threshold:
                    is_duplicate = True
                    break
            if is_duplicate:
                continue

        survivors.append(candidate)
        survivor_vectors.append(
            (_unit(vector) if vector is not None else None, timestamp)
        )

    return survivors


def _chronological(candidates: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Order a selection for playback. A story has to read forwards."""
    return sorted(
        candidates,
        key=lambda c: (c.get("captured_at") or datetime.min, -c["score"]),
    )


def spread_over_time(
    candidates: Sequence[Dict[str, Any]], target: int
) -> List[Dict[str, Any]]:
    """
    Pick `target` images spread across the event rather than clustered.

    Taking the top N by score alone can return ten frames from one minute of
    a three-day trip. Bucketing the span and taking the best of each bucket
    keeps the story moving.
    """
    if target <= 0:
        return []
    if len(candidates) <= target:
        return _chronological(candidates)

    timed = [c for c in candidates if c.get("captured_at") is not None]
    if len(timed) < target:
        return _chronological(candidates[:target])

    start = min(c["captured_at"] for c in timed)
    end = max(c["captured_at"] for c in timed)
    span = (end - start).total_seconds()

    # No span to spread across; score order picks the set, order does not
    # matter because every timestamp is identical.
    if span <= 0:
        return _chronological(candidates[:target])

    buckets: Dict[int, Dict[str, Any]] = {}
    for candidate in timed:
        offset = (candidate["captured_at"] - start).total_seconds()
        index = min(int(offset / span * target), target - 1)
        # Candidates arrive best-first, so the first to claim a bucket wins.
        buckets.setdefault(index, candidate)

    selected = list(buckets.values())

    # Empty buckets (a quiet stretch of the event) are backfilled by score so
    # the caller still gets the number of photos it asked for.
    if len(selected) < target:
        chosen_ids = {c["id"] for c in selected}
        for candidate in candidates:
            if candidate["id"] in chosen_ids:
                continue
            selected.append(candidate)
            if len(selected) >= target:
                break

    return _chronological(selected)


def aggregate_memory_score(selected: Sequence[Dict[str, Any]]) -> float:
    """
    Score a memory as a whole, for ranking memories against each other.

    Built from its strongest few images, then nudged by size and by how
    varied its content is. Both are memory-level properties: a photo is not
    better for belonging to a bigger set, but a memory is.
    """
    if not selected:
        return 0.0

    top = sorted((c["score"] for c in selected), reverse=True)[:5]
    base = sum(top) / len(top)

    size_boost = 1.0 + 0.15 * (math.log1p(len(selected)) / math.log1p(30))

    class_counts = [c.get("class_count", 0) for c in selected]
    distinct_ratio = (
        min(1.0, (sum(class_counts) / len(class_counts)) / 10.0)
        if class_counts
        else 0.0
    )
    diversity_boost = 1.0 + 0.10 * distinct_ratio

    return base * size_boost * diversity_boost
