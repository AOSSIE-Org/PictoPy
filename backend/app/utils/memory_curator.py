"""
Memory curation.

Turns the photo library into persisted, ranked memories. Three triggers
produce candidate sets; each set is scored, deduplicated and written to the
memories table.

- anniversary:    photos from this calendar date in previous years
- import_event:   a burst of photos that hangs together in time and place
- semantic_event: photos SigLIP2 recognises as one occasion
"""

import hashlib
import json
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from app.config.settings import (
    SIGLIP2_ACTIVE_CHECKPOINT,
    SIGLIP2_SCORING_METADATA,
)
from app.database.image_embeddings import (
    db_get_embedding_sample,
    db_get_embeddings_for_image_ids,
)
from app.database.memories import (
    db_delete_stale_memories,
    db_finish_memory_run,
    db_get_anniversary_candidates,
    db_get_event_label_hits,
    db_get_event_labels,
    db_get_images_in_period,
    db_get_memory_ids_for_cluster,
    db_get_memory_image_ids_by_dedupe_key,
    db_get_memory_images,
    db_get_recently_used_image_ids,
    db_get_scoring_signals,
    db_get_top_memory_label,
    db_get_recent_dated_images,
    db_start_memory_run,
    db_update_memory_scores,
    db_upsert_memory,
)
from app.database.metadata import db_get_metadata
from app.logging.setup_logging import get_logger
from app.schemas.user_preferences import MemoriesPreferences
from app.utils.memory_scoring import (
    aggregate_memory_score,
    cohesion_baseline,
    detect_home_location,
    mean_pairwise_cohesion,
    parse_captured_at,
    score_candidates,
    spread_over_time,
    suppress_near_duplicates,
    trim_incoherent,
)

logger = get_logger(__name__)

# Bumped when curation changes in a way that makes existing memories stale.
GENERATOR_VERSION = 2

# --- Anniversary -----------------------------------------------------------

# EXIF timestamps carry the camera's local time, so a photo taken near
# midnight abroad lands on the neighbouring date.
ANNIVERSARY_DAY_WINDOW = 1

# A wall of "4 years ago", "5 years ago", "6 years ago" is noise.
MAX_ANNIVERSARY_MEMORIES = 2

# --- Import event ----------------------------------------------------------

# A gap this long, or a jump this far, ends an event. Temporal segmentation
# rather than DBSCAN over coordinates: clustering by location alone collapses
# a year of at-home photos into one blob.
IMPORT_GAP_HOURS = 8.0
IMPORT_JUMP_KM = 40.0
IMPORT_MAX_SPAN_DAYS = 14
MAX_IMPORT_MEMORIES = 3

# Cap the pool so a first import of a huge library does not stall the worker.
IMPORT_CANDIDATE_LIMIT = 5000

# --- Semantic event --------------------------------------------------------

EVENT_GAP_HOURS = 36.0
EVENT_MIN_IMAGES = 6

# A label counts for an image when it is among the strongest few that image
# matched, and the image ranks in the upper half of everything that label
# matched. Ranks, not scores: SigLIP2 puts "mehndi" at 0.78 and "holi" at
# 0.0003 on the same library, so no absolute cut can serve both.
EVENT_LABEL_TOP_N = 2
EVENT_LABEL_PERCENTILE = 0.50

# Visual cohesion is the real discriminator, but only as a margin above what
# this library already scores. SigLIP2 embeddings occupy a narrow cone: a
# random handful of unrelated photos scores ~0.58 mean pairwise cosine, so an
# absolute gate anywhere near that rejects nothing at all. Real occurrences
# measured +0.31 to +0.35 above baseline; random groups measure +0.00.
EVENT_COHESION_MARGIN = 0.15

# Enough to characterize the library without loading every embedding.
COHESION_SAMPLE_SIZE = 500

# A label may name a memory once it covers this much of it. Both bounds are
# needed: the share alone lets a pair of matches name a whole holiday, the
# count alone lets one stray match name thirty photos.
TITLE_MIN_SHARE = 0.15
TITLE_MIN_IMAGES = 2

# Two labels covering the same weekend are one occasion, not two.
EVENT_MERGE_OVERLAP = 0.60

# An anniversary of a semantic event is only worth surfacing as such if it is
# imminent; otherwise it is a rediscovery and surfaces today.
EVENT_ANNIVERSARY_LOOKAHEAD_DAYS = 3
MAX_SEMANTIC_MEMORIES = 3

# --- Shared ----------------------------------------------------------------

# Images used recently are demoted for anniversaries (a sparse calendar date
# cannot spare photos) and excluded outright elsewhere (those pools are large).
RECENT_USE_WINDOW_DAYS = 30
RECENT_USE_PENALTY = 0.35

# Stand-ins for a memory nothing recognised. A bare date is a poor title for
# something whose whole job is to invite a second look, and there is no
# captioning model here to write a real one. The date is not lost: it moves to
# the subtitle, which the cards and the story viewer both render.
GENERIC_TITLES_ONE_DAY = (
    "Remember this day?",
    "Revisit this day",
    "A day worth keeping",
    "Spotlight on a day",
    "Look back on this day",
)
GENERIC_TITLES_MANY_DAYS = (
    "Remember these days?",
    "Revisit these moments",
    "Days worth keeping",
    "A few days to remember",
    "Look back on these days",
)

# Labels whose title-cased form reads wrong.
EVENT_DISPLAY_NAMES = {
    "valentines day": "Valentine's Day",
    "new year": "New Year",
    "lunar new year": "Lunar New Year",
    "eid": "Eid",
    "bbq": "BBQ",
}


def memory_curator_get_preferences() -> MemoriesPreferences:
    """
    Read memories preferences from the metadata blob.

    Read-only by design: db_update_metadata rewrites the whole blob, so a write
    from the curator process would clobber a concurrent settings save.
    """
    metadata = db_get_metadata() or {}
    stored = (metadata.get("user_preferences") or {}).get("memories") or {}
    try:
        return MemoriesPreferences.model_validate(stored)
    except ValueError as e:
        logger.warning(f"Invalid memories preferences, using defaults: {e}")
        return MemoriesPreferences()


def memory_curator_params_signature(preferences: MemoriesPreferences) -> str:
    """Fingerprint the inputs that determine curation output."""
    payload = {
        "version": GENERATOR_VERSION,
        "min_images": preferences.min_images,
        "max_images": preferences.max_images,
        "weights": preferences.weights.model_dump(),
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _active_model_version() -> str:
    return SIGLIP2_SCORING_METADATA[SIGLIP2_ACTIVE_CHECKPOINT]["model_version"]


def _anniversary_window(reference: date) -> List[str]:
    """Build the MM-DD strings matched by an anniversary lookup."""
    offsets = range(-ANNIVERSARY_DAY_WINDOW, ANNIVERSARY_DAY_WINDOW + 1)
    return sorted({(reference + timedelta(days=o)).strftime("%m-%d") for o in offsets})


def _display_event_name(label: str) -> str:
    return EVENT_DISPLAY_NAMES.get(label, label.title())


def _generic_title(dedupe_key: str, start: datetime, end: datetime) -> str:
    """
    Name a memory no label described well enough to name.

    Picked from the dedupe key, not at random: a rebuild must not rename a
    memory the user has already been shown. Singular or plural to match the
    span, so a fortnight does not get called a day.
    """
    pool = (
        GENERIC_TITLES_ONE_DAY
        if start.date() == end.date()
        else GENERIC_TITLES_MANY_DAYS
    )
    digest = hashlib.sha256(dedupe_key.encode("utf-8")).digest()
    return pool[digest[0] % len(pool)]


def _format_period_label(start: datetime, end: datetime) -> str:
    """
    Name a span by its dates.

    Several bursts in one month would otherwise all be titled "July 2026",
    which reads as duplicates in the grid.
    """
    if start.date() == end.date():
        return start.strftime("%d %B %Y").lstrip("0")
    if (start.year, start.month) == (end.year, end.month):
        return (
            f"{start.strftime('%d').lstrip('0')}–"
            f"{end.strftime('%d').lstrip('0')} {start.strftime('%B %Y')}"
        )
    if start.year == end.year:
        return (
            f"{start.strftime('%d %b').lstrip('0')} – "
            f"{end.strftime('%d %b').lstrip('0')} {start.year}"
        )
    return f"{start.strftime('%b %Y')} – {end.strftime('%b %Y')}"


def _haversine_km(a: Dict[str, Any], b: Dict[str, Any]) -> Optional[float]:
    """Distance between two image rows, or None if either lacks GPS."""
    from app.utils.memory_scoring import haversine_km

    if (
        a.get("latitude") is None
        or a.get("longitude") is None
        or b.get("latitude") is None
        or b.get("longitude") is None
    ):
        return None
    return haversine_km(a["latitude"], a["longitude"], b["latitude"], b["longitude"])


class _CurationContext:
    """Inputs shared by every trigger within a single run."""

    def __init__(
        self,
        reference: date,
        preferences: MemoriesPreferences,
        params_signature: str,
    ):
        self.reference = reference
        self.run_date = reference.isoformat()
        self.preferences = preferences
        self.params_signature = params_signature
        self.weights = preferences.weights
        self.home = detect_home_location()
        self.model_version = _active_model_version()
        self.recently_used = db_get_recently_used_image_ids(
            RECENT_USE_WINDOW_DAYS, self.run_date
        )
        # What "similar" already means in this library, so cohesion can be
        # expressed as a margin over it rather than an absolute cosine.
        self.cohesion_baseline = cohesion_baseline(
            db_get_embedding_sample(self.model_version, COHESION_SAMPLE_SIZE)
        )


def _build_memory(
    context: _CurationContext,
    *,
    image_ids: Sequence[str],
    dedupe_key: str,
    event_type: str,
    title: str,
    subtitle: Optional[str],
    surface_date: str,
    hard_exclude_recent: bool,
    trim_outliers: bool = False,
    rename: Optional[Callable[[List[str]], Tuple[str, Optional[str]]]] = None,
) -> bool:
    """
    Score, trim and persist one candidate set. Returns whether it qualified.

    Shared by all three triggers: they differ only in how candidates are
    found, not in how they are ranked.
    """
    preferences = context.preferences
    candidate_ids = list(image_ids)

    if hard_exclude_recent:
        # A memory's own photos are not "already used" as far as that memory
        # is concerned; excluding them would rebuild it from the leftovers.
        own = db_get_memory_image_ids_by_dedupe_key(dedupe_key)
        blocked = context.recently_used - own
        candidate_ids = [i for i in candidate_ids if i not in blocked]
    if len(candidate_ids) < preferences.min_images:
        return False

    signal_rows = db_get_scoring_signals(candidate_ids)
    if len(signal_rows) < preferences.min_images:
        return False

    scored = score_candidates(
        signal_rows,
        context.weights,
        context.home,
        penalized_ids=None if hard_exclude_recent else context.recently_used,
        penalty=RECENT_USE_PENALTY,
    )

    embeddings = db_get_embeddings_for_image_ids(
        [c["id"] for c in scored], context.model_version
    )
    deduplicated = suppress_near_duplicates(scored, embeddings)
    if len(deduplicated) < preferences.min_images:
        return False

    # Time and place said these belong together; this asks whether they look
    # like it. Only for triggers that segment on the clock — an anniversary
    # spans years and is not supposed to be visually of a piece.
    if trim_outliers:
        deduplicated = trim_incoherent(deduplicated, embeddings, preferences.min_images)

    selected = spread_over_time(deduplicated, preferences.max_images)
    if len(selected) < preferences.min_images:
        return False

    # Name it after what survived. Titling the candidate set instead lets a
    # photo that was just trimmed for not belonging still vote on the label.
    if rename is not None:
        title, subtitle = rename([c["id"] for c in selected])

    cover = max(selected, key=lambda c: c["score"])
    timestamps = [c["captured_at"] for c in selected if c.get("captured_at")]

    db_upsert_memory(
        {
            "memory_id": str(uuid.uuid4()),
            "dedupe_key": dedupe_key,
            "event_type": event_type,
            "status": "complete",
            "title": title,
            "subtitle": subtitle,
            "surface_date": surface_date,
            "period_start": min(timestamps).isoformat() if timestamps else None,
            "period_end": max(timestamps).isoformat() if timestamps else None,
            "cover_image_id": cover["id"],
            "image_count": len(selected),
            "score": aggregate_memory_score(selected),
            # Kept for debugging why a given photo made the cut. Not shown.
            "signals": cover["signals"],
            "params_signature": context.params_signature,
        },
        [
            (candidate["id"], order, candidate["score"])
            for order, candidate in enumerate(selected)
        ],
    )
    return True


# ##############################
# Trigger 1: anniversary
# ##############################


def _curate_anniversaries(context: _CurationContext) -> int:
    """Build memories from photos taken on this date in previous years."""
    reference = context.reference
    candidates = db_get_anniversary_candidates(
        _anniversary_window(reference), reference.year - 1
    )
    if not candidates:
        return 0

    by_year: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for image in candidates:
        capture_year = image.get("capture_year")
        if capture_year is not None:
            by_year[capture_year].append(image)

    qualifying = [
        (year, images)
        for year, images in by_year.items()
        if len(images) >= context.preferences.min_images
    ]
    # Prefer the years with the most to show, then the most recent.
    qualifying.sort(key=lambda pair: (-len(pair[1]), -pair[0]))

    generated = 0
    for year, images in qualifying[:MAX_ANNIVERSARY_MEMORIES]:
        try:
            years_ago = reference.year - year
            # Taken from the photos themselves, not rebuilt from the reference
            # date: Feb 29 has no counterpart in a non-leap source year.
            timestamps = [
                parse_captured_at(image.get("captured_at")) for image in images
            ]
            timestamps = [t for t in timestamps if t is not None]
            subtitle = min(timestamps).strftime("%B %Y") if timestamps else str(year)

            if _build_memory(
                context,
                image_ids=[image["id"] for image in images],
                dedupe_key=f"anniv:{reference.strftime('%m-%d')}:{year}",
                event_type="anniversary",
                title=(
                    "1 year ago today"
                    if years_ago == 1
                    else f"{years_ago} years ago today"
                ),
                subtitle=subtitle,
                surface_date=reference.isoformat(),
                # A sparse calendar date cannot spare photos, so reuse is a
                # penalty rather than an exclusion.
                hard_exclude_recent=False,
            ):
                generated += 1
        except Exception:
            logger.error(
                f"Failed to curate anniversary memory for {year}", exc_info=True
            )

    return generated


# ##############################
# Trigger 2: import event
# ##############################


def segment_by_time_and_place(
    images: Sequence[Dict[str, Any]],
    gap_hours: float = IMPORT_GAP_HOURS,
    jump_km: float = IMPORT_JUMP_KM,
) -> List[List[Dict[str, Any]]]:
    """
    Split chronologically ordered images into events.

    A long pause or a big move ends the current event. O(n log n), and unlike
    spatial clustering it distinguishes two separate trips to the same place.
    """
    timed = [i for i in images if parse_captured_at(i.get("captured_at"))]
    if not timed:
        return []

    timed.sort(key=lambda i: parse_captured_at(i.get("captured_at")))

    segments: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = [timed[0]]

    for previous, image in zip(timed, timed[1:]):
        gap = (
            parse_captured_at(image["captured_at"])
            - parse_captured_at(previous["captured_at"])
        ).total_seconds() / 3600.0
        distance = _haversine_km(previous, image)
        moved = distance is not None and distance > jump_km

        if gap > gap_hours or moved:
            segments.append(current)
            current = []
        current.append(image)

    segments.append(current)
    return segments


def _span_days(segment: Sequence[Dict[str, Any]]) -> float:
    timestamps = [parse_captured_at(i.get("captured_at")) for i in segment]
    timestamps = [t for t in timestamps if t is not None]
    if len(timestamps) < 2:
        return 0.0
    return (max(timestamps) - min(timestamps)).total_seconds() / 86400.0


def _curate_import_events(context: _CurationContext) -> int:
    """Build memories from bursts of photos not yet used by any memory."""
    images = db_get_recent_dated_images(IMPORT_CANDIDATE_LIMIT)
    if len(images) < context.preferences.min_images:
        return 0

    segments = [
        segment
        for segment in segment_by_time_and_place(images)
        if len(segment) >= context.preferences.min_images
        and _span_days(segment) <= IMPORT_MAX_SPAN_DAYS
    ]
    if not segments:
        return 0

    # Most recent first. Ranking by size would let the same few large events
    # hold the cap forever and never surface a newly imported trip.
    segments.sort(
        key=lambda s: max(
            parse_captured_at(i.get("captured_at")) or datetime.min for i in s
        ),
        reverse=True,
    )

    generated = 0
    for segment in segments[:MAX_IMPORT_MEMORIES]:
        try:
            image_ids = [image["id"] for image in segment]
            timestamps = [
                parse_captured_at(image.get("captured_at")) for image in segment
            ]
            timestamps = [t for t in timestamps if t is not None]
            if not timestamps:
                continue

            start, end = min(timestamps), max(timestamps)
            period_label = _format_period_label(start, end)

            dedupe_key = f"import:{start.date()}..{end.date()}"

            # Name it after what the AI recognised, when it recognised
            # anything; otherwise a stand-in, with the dates as the subtitle.
            # Deferred until the set is final, so a photo trimmed for not
            # belonging cannot name the rest.
            def name_from_labels(
                selected_ids: List[str],
                dedupe_key: str = dedupe_key,
                period_label: str = period_label,
                start: datetime = start,
                end: datetime = end,
            ) -> Tuple[str, Optional[str]]:
                top_label = db_get_top_memory_label(
                    selected_ids,
                    EVENT_LABEL_TOP_N,
                    EVENT_LABEL_PERCENTILE,
                    TITLE_MIN_SHARE,
                    TITLE_MIN_IMAGES,
                )
                if top_label is None:
                    return _generic_title(dedupe_key, start, end), period_label
                return _display_event_name(top_label[1]), period_label

            if _build_memory(
                context,
                image_ids=image_ids,
                dedupe_key=dedupe_key,
                event_type="import_event",
                title=period_label,
                subtitle=None,
                surface_date=context.run_date,
                hard_exclude_recent=True,
                trim_outliers=True,
                rename=name_from_labels,
            ):
                generated += 1
        except Exception:
            logger.error("Failed to curate import event memory", exc_info=True)

    return generated


# ##############################
# Trigger 3: semantic event
# ##############################


def group_event_occurrences(
    hits: Sequence[Dict[str, Any]], gap_hours: float = EVENT_GAP_HOURS
) -> List[Dict[str, Any]]:
    """
    Turn per-image event-label hits into discrete occurrences.

    Each label's hits are split wherever they stop being contemporaneous, so
    three separate birthdays become three occurrences rather than one.
    """
    by_label: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for hit in hits:
        timestamp = parse_captured_at(hit.get("captured_at"))
        if timestamp is None:
            continue
        by_label[hit["class_id"]].append({**hit, "timestamp": timestamp})

    occurrences: List[Dict[str, Any]] = []
    for class_id, label_hits in by_label.items():
        label_hits.sort(key=lambda h: h["timestamp"])
        current: List[Dict[str, Any]] = [label_hits[0]]

        for previous, hit in zip(label_hits, label_hits[1:]):
            gap = (hit["timestamp"] - previous["timestamp"]).total_seconds() / 3600.0
            if gap > gap_hours:
                occurrences.append(_make_occurrence(class_id, current))
                current = []
            current.append(hit)

        occurrences.append(_make_occurrence(class_id, current))

    return occurrences


def _make_occurrence(class_id: int, hits: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    # Percentile within the label, not the raw score: raw scores from
    # different labels are not on the same scale and cannot be averaged.
    scores = [h.get("label_rank") or 0.0 for h in hits]
    timestamps = [h["timestamp"] for h in hits]
    return {
        "class_id": class_id,
        "image_ids": [h["image_id"] for h in hits],
        "scores": scores,
        "mean_score": sum(scores) / len(scores) if scores else 0.0,
        "peak_score": max(scores) if scores else 0.0,
        "total_score": sum(scores),
        "start": min(timestamps),
        "end": max(timestamps),
    }


def passes_coherence_gate(
    occurrence: Dict[str, Any],
    embeddings: Dict[str, np.ndarray],
    baseline: Optional[float],
    min_images: int = EVENT_MIN_IMAGES,
) -> bool:
    """
    Decide whether an occurrence is really one event.

    Label agreement got these photos this far; whether they look like one
    occasion is what decides it. Measured as a margin over `baseline`, the
    library's own mean pairwise cosine — an absolute cosine says nothing when
    every embedding already points broadly the same way.
    """
    if len(occurrence["image_ids"]) < min_images:
        return False

    vectors = [
        embeddings[image_id]
        for image_id in occurrence["image_ids"]
        if image_id in embeddings
    ]
    cohesion = mean_pairwise_cohesion(vectors)
    # Without embeddings, or before the library has been characterized, the
    # visual test cannot run. The label ranks already had to pass, so accept
    # rather than silently dropping everything.
    if cohesion is None or baseline is None:
        return True

    return cohesion >= baseline + EVENT_COHESION_MARGIN


def merge_overlapping_occurrences(
    occurrences: Sequence[Dict[str, Any]],
    overlap_ratio: float = EVENT_MERGE_OVERLAP,
) -> List[Dict[str, Any]]:
    """
    Fold occurrences covering the same stretch of time into one memory.

    A wedding weekend can fire "wedding" and "mehndi"; that is one occasion
    with two labels, not two memories over the same photos.
    """
    ordered = sorted(occurrences, key=lambda o: o["start"])
    merged: List[Dict[str, Any]] = []

    for occurrence in ordered:
        target = None
        for candidate in merged:
            overlap = (
                min(candidate["end"], occurrence["end"])
                - max(candidate["start"], occurrence["start"])
            ).total_seconds()
            if overlap <= 0:
                continue
            shorter = min(
                (candidate["end"] - candidate["start"]).total_seconds(),
                (occurrence["end"] - occurrence["start"]).total_seconds(),
            )
            # Two instants at the same moment are the same occasion.
            if shorter <= 0 or overlap / shorter >= overlap_ratio:
                target = candidate
                break

        if target is None:
            merged.append({**occurrence, "class_ids": [occurrence["class_id"]]})
            continue

        target["image_ids"] = list(
            dict.fromkeys([*target["image_ids"], *occurrence["image_ids"]])
        )
        target["start"] = min(target["start"], occurrence["start"])
        target["end"] = max(target["end"], occurrence["end"])
        target["class_ids"].append(occurrence["class_id"])
        # Primary label is whichever contributed more total confidence.
        if occurrence["total_score"] > target["total_score"]:
            target["class_id"] = occurrence["class_id"]
            target["total_score"] = occurrence["total_score"]

    return merged


def _curate_semantic_events(context: _CurationContext) -> int:
    """Build memories from photos SigLIP2 recognises as one occasion."""
    labels = db_get_event_labels()
    if not labels:
        return 0

    label_names = {label["class_id"]: label["name"] for label in labels}
    hits = db_get_event_label_hits(
        list(label_names), EVENT_LABEL_TOP_N, EVENT_LABEL_PERCENTILE
    )
    if not hits:
        return 0

    occurrences = group_event_occurrences(hits)
    if not occurrences:
        return 0

    # One embedding fetch for every image under consideration, rather than
    # one per occurrence.
    all_ids = sorted({i for o in occurrences for i in o["image_ids"]})
    embeddings = db_get_embeddings_for_image_ids(all_ids, context.model_version)

    coherent = [
        o
        for o in occurrences
        if passes_coherence_gate(o, embeddings, context.cohesion_baseline)
    ]
    if not coherent:
        return 0

    merged = merge_overlapping_occurrences(coherent)
    merged.sort(key=lambda o: -len(o["image_ids"]))

    generated = 0
    for occurrence in merged[:MAX_SEMANTIC_MEMORIES]:
        try:
            start, end = occurrence["start"], occurrence["end"]

            # Pull in the unlabeled candids between the recognised shots;
            # they are what turn a label dump into a story.
            expansion = db_get_images_in_period(
                start.isoformat(),
                end.isoformat(),
                exclude_ids=occurrence["image_ids"],
            )
            image_ids = [
                *occurrence["image_ids"],
                *[image["id"] for image in expansion],
            ]

            label = label_names.get(occurrence["class_id"], "event")
            if _build_memory(
                context,
                image_ids=image_ids,
                dedupe_key=f"semantic:{occurrence['class_id']}:{start.date()}",
                event_type="semantic_event",
                title=_display_event_name(label),
                subtitle=start.strftime("%B %Y"),
                surface_date=_semantic_surface_date(context.reference, start),
                hard_exclude_recent=True,
            ):
                generated += 1
        except Exception:
            logger.error("Failed to curate semantic event memory", exc_info=True)

    return generated


def _semantic_surface_date(reference: date, event_start: datetime) -> str:
    """
    Surface on the event's upcoming anniversary, else today.

    An anniversary within the next few days is worth waiting for; anything
    else is a rediscovery and should show now.
    """
    try:
        anniversary = event_start.date().replace(year=reference.year)
    except ValueError:
        # Feb 29 in a non-leap reference year.
        return reference.isoformat()

    delta = (anniversary - reference).days
    if 0 <= delta <= EVENT_ANNIVERSARY_LOOKAHEAD_DAYS:
        return anniversary.isoformat()
    return reference.isoformat()


# ##############################
# Entry point
# ##############################


def memory_curator_rescore(memory_ids: Sequence[str]) -> int:
    """
    Re-score existing memories in place. Returns the number updated.

    Membership stays fixed: only the per-image scores, the cover and the
    memory's own score move. Naming a face changes a scoring input for photos
    that are already curated, and those memories cannot be rebuilt from
    scratch anyway, since their images no longer appear in any candidate pool.
    Rescoring keeps the ranking honest without reshuffling something the user
    may already have watched.
    """
    if not memory_ids:
        return 0

    preferences = memory_curator_get_preferences()
    weights = preferences.weights
    home = detect_home_location()

    updated = 0
    for memory_id in memory_ids:
        try:
            images = db_get_memory_images(memory_id)
            if not images:
                continue

            scored = score_candidates(
                db_get_scoring_signals([image["id"] for image in images]),
                weights,
                home,
            )
            if not scored:
                continue

            cover = max(scored, key=lambda c: c["score"])
            db_update_memory_scores(
                memory_id,
                [(c["id"], c["score"]) for c in scored],
                cover["id"],
                aggregate_memory_score(scored),
            )
            updated += 1
        except Exception:
            logger.error(f"Failed to rescore memory {memory_id}", exc_info=True)

    logger.info(f"Rescored {updated} memories")
    return updated


def memory_curator_rescore_for_cluster(cluster_id: str) -> int:
    """Rescore every memory containing a face from the given cluster."""
    return memory_curator_rescore(db_get_memory_ids_for_cluster(cluster_id))


def memory_curator_run(
    reference_date: Optional[str] = None,
    force: bool = False,
    trigger: str = "manual",
) -> int:
    """
    Run curation for a date and return the number of memories written.

    Records the run in memory_runs so an interrupted pass is detectable, and
    never raises: callers are import hooks and background tasks where a
    curation failure must not fail the surrounding work.
    """
    reference = date.fromisoformat(reference_date) if reference_date else date.today()
    run_date = reference.isoformat()

    preferences = memory_curator_get_preferences()
    if not preferences.enabled and not force:
        logger.info("Memories are disabled; skipping curation")
        return 0

    params_signature = memory_curator_params_signature(preferences)
    db_start_memory_run(run_date, params_signature)
    logger.info(f"Curating memories for {run_date} (trigger={trigger}, force={force})")

    try:
        # Before anything is built: drop memories the library has outgrown.
        # A re-sync that corrects capture dates leaves them stranded, and
        # their photos are candidates again once they are gone. Housekeeping,
        # so failing it must not cost the run the memories it came to make.
        try:
            stale = db_delete_stale_memories()
            if stale:
                logger.info(f"Dropped {stale} memories whose capture dates moved")
        except Exception:
            logger.error("Failed to drop stale memories", exc_info=True)

        context = _CurationContext(reference, preferences, params_signature)

        generated = 0
        for name, curate in (
            ("anniversary", _curate_anniversaries),
            ("semantic_event", _curate_semantic_events),
            ("import_event", _curate_import_events),
        ):
            try:
                produced = curate(context)
                generated += produced
                logger.info(f"{name}: {produced} memories")
            except Exception:
                # One failing trigger must not cost the others their output.
                logger.error(f"{name} curation failed", exc_info=True)
            # Later triggers must not reuse what an earlier one just claimed.
            context.recently_used = db_get_recently_used_image_ids(
                RECENT_USE_WINDOW_DAYS, run_date
            )

        db_finish_memory_run(run_date, "complete", generated)
        logger.info(f"Curation complete for {run_date}: {generated} memories")
        return generated
    except Exception as e:
        logger.error(f"Curation failed for {run_date}", exc_info=True)
        db_finish_memory_run(run_date, "failed", 0, str(e))
        return 0
