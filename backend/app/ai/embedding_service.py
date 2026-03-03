"""
EmbeddingService
================
Converts image metadata into a fixed-dimension, L2-normalised float32 numpy
vector suitable for cosine-similarity search.

Design decisions
----------------
* **Fully offline** – only numpy and the Python standard library are used.
* **Fixed vocabulary** – the embedding dimension is determined once at import
  time from the YOLO class list and a set of hard-coded temporal / spatial
  tokens.  No fitting step is required, so new images can be embedded
  incrementally without invalidating old embeddings.
* **Deterministic** – identical metadata always produces an identical vector.
* **Lightweight** – one float32 vector ≈ 163 × 4 = 652 bytes per image.

Embedding layout  (total dimension = EMBEDDING_DIM)
---------------------------------------------------
Slice                 Width  Description
─────────────────     ─────  ──────────────────────────────────────────────
[OFF_OBJ  : +N_OBJ]    80    YOLO object-class relative frequency (≥ 0)
[OFF_TOD  : +4]         4    Time-of-day bins: morning / afternoon / evening / night
[OFF_SEAS : +4]         4    Season bins: spring / summer / autumn / winter
[OFF_DOW  : +7]         7    Day-of-week: Monday … Sunday
[OFF_FLAG : +2]         2    Binary flags: has_faces, has_location
[OFF_FC   : +MAX_FC]   64    Face-cluster presence (binary, zero-padded)
[OFF_SPA  : +2]         2    Normalised latitude and longitude ∈ [−1, 1]
─────────────────     ─────
Total                 163

Query embedding
---------------
`embed_query(text)` tokenises a free-text string and maps recognised
keywords onto the *same* vector space so that cosine similarity can be used
directly between a query and any stored image embedding.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from app.config.settings import MAX_FACE_CLUSTERS
from app.utils.YOLO import class_names as _YOLO_CLASS_NAMES
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Vocabulary and dimension constants
# ---------------------------------------------------------------------------

_OBJ_NAMES: List[str] = [n.lower() for n in _YOLO_CLASS_NAMES]

N_OBJ: int = len(_OBJ_NAMES)  # 80 for standard COCO
N_TOD: int = 4  # time-of-day bins
N_SEASON: int = 4  # season bins
N_DOW: int = 7  # days of the week
N_FLAGS: int = 2  # has_faces, has_location
N_SPATIAL: int = 2  # normalised lat, lon

#: Total number of face-cluster slots encoded; higher cluster IDs are clamped.
MAX_FC: int = MAX_FACE_CLUSTERS

#: Total embedding dimensionality – **must not change** without a full rebuild.
EMBEDDING_DIM: int = N_OBJ + N_TOD + N_SEASON + N_DOW + N_FLAGS + MAX_FC + N_SPATIAL

# Slice offsets (computed once at module load)
_OFF_OBJ: int = 0
_OFF_TOD: int = _OFF_OBJ + N_OBJ
_OFF_SEAS: int = _OFF_TOD + N_TOD
_OFF_DOW: int = _OFF_SEAS + N_SEASON
_OFF_FLAG: int = _OFF_DOW + N_DOW
_OFF_FC: int = _OFF_FLAG + N_FLAGS
_OFF_SPA: int = _OFF_FC + MAX_FC

# ---------------------------------------------------------------------------
# Lookup tables (built once at import time)
# ---------------------------------------------------------------------------

#: Exact YOLO class name → column index
_OBJ_INDEX: Dict[str, int] = {name: i for i, name in enumerate(_OBJ_NAMES)}

#: Multi-word YOLO class names (e.g. "traffic light") → column index
_OBJ_BIGRAMS: Dict[str, int] = {
    name: idx for name, idx in _OBJ_INDEX.items() if " " in name
}

#: Time-of-day keyword → TOD bin index (0=morning … 3=night)
_TOD_MAP: Dict[str, int] = {
    "morning": 0,
    "sunrise": 0,
    "dawn": 0,
    "afternoon": 1,
    "noon": 1,
    "midday": 1,
    "evening": 2,
    "sunset": 2,
    "dusk": 2,
    "twilight": 2,
    "night": 3,
    "midnight": 3,
    "dark": 3,
    "nighttime": 3,
}

#: Season keyword → season bin index (0=spring … 3=winter)
_SEASON_MAP: Dict[str, int] = {
    "spring": 0,
    "springtime": 0,
    "summer": 1,
    "autumn": 2,
    "fall": 2,
    "winter": 3,
    "snowy": 3,
}

#: Day-of-week keyword → weekday() index (0=Monday)
_DOW_MAP: Dict[str, Optional[int]] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
    # Special multi-day tokens handled separately
    "weekday": None,
    "weekend": None,
}

# Months → season (0=spring)
_MONTH_SEASON: Dict[int, int] = {
    12: 3,
    1: 3,
    2: 3,  # winter
    3: 0,
    4: 0,
    5: 0,  # spring
    6: 1,
    7: 1,
    8: 1,  # summer
    9: 2,
    10: 2,
    11: 2,  # autumn
}


def _month_to_season(month: int) -> int:
    return _MONTH_SEASON.get(month, 0)


def _hour_to_tod(hour: int) -> int:
    """Map 24-hour clock to TOD bin (0=morning, 1=afternoon, 2=evening, 3=night)."""
    if 6 <= hour < 12:
        return 0
    if 12 <= hour < 17:
        return 1
    if 17 <= hour < 21:
        return 2
    return 3  # night (21-05)


# ---------------------------------------------------------------------------
# Public module-level helper
# ---------------------------------------------------------------------------


def l2_normalize(vec: np.ndarray) -> np.ndarray:
    """Return an L2-normalised float32 copy; returns the zero vector if norm ≈ 0."""
    norm = float(np.linalg.norm(vec))
    if norm < 1e-9:
        return vec.astype(np.float32)
    return (vec / norm).astype(np.float32)


# ---------------------------------------------------------------------------
# EmbeddingService
# ---------------------------------------------------------------------------


class EmbeddingService:
    """
    Stateless service that converts image metadata records and free-text
    queries into fixed-dimension, L2-normalised float32 numpy vectors.

    Parameters
    ----------
    max_face_clusters :
        Maximum face-cluster index that will be encoded.  Must match the
        ``MAX_FACE_CLUSTERS`` setting used when the embedding table was
        first populated; changing it requires a full index rebuild.
    """

    def __init__(self, max_face_clusters: int = MAX_FC) -> None:
        if max_face_clusters != MAX_FC:
            logger.warning(
                "EmbeddingService initialised with max_face_clusters=%d "
                "but module constant MAX_FC=%d; EMBEDDING_DIM will be wrong.",
                max_face_clusters,
                MAX_FC,
            )
        self._max_fc = max_face_clusters

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_image(self, image_record: Dict[str, Any]) -> np.ndarray:
        """
        Build a float32 embedding vector from *image_record*.

        The dict is expected to contain the keys returned by
        ``db_get_all_images()`` plus an optional ``face_cluster_ids`` key
        injected by :class:`~app.ai.search_service.SearchService`:

        ``id``, ``path``, ``tags`` (list[str] | None),
        ``latitude``, ``longitude``, ``captured_at``,
        ``face_cluster_ids`` (list[int] | None)

        Returns
        -------
        np.ndarray  shape (EMBEDDING_DIM,), dtype=float32, L2-normalised
        """
        vec = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        self._fill_objects(vec, image_record.get("tags") or [])
        self._fill_temporal(vec, image_record.get("captured_at"))
        self._fill_faces(vec, image_record.get("face_cluster_ids") or [])
        self._fill_spatial(
            vec,
            image_record.get("latitude"),
            image_record.get("longitude"),
        )
        return l2_normalize(vec)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Map a free-text query onto the same embedding space.

        Recognised tokens
        -----------------
        * Any YOLO class name (exact or partial / substring match).
        * Multi-word YOLO names such as ``"traffic light"`` (bigram scan).
        * Time-of-day keywords: morning, afternoon, evening, night, …
        * Season keywords: spring, summer, autumn / fall, winter, …
        * Day-of-week names and ``weekday`` / ``weekend`` aggregates.
        * ``face``, ``faces``, ``person``, ``people``, ``portrait``, ``selfie``
          → sets the *has_faces* flag.

        Returns
        -------
        np.ndarray  shape (EMBEDDING_DIM,), dtype=float32, L2-normalised
        """
        vec = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        tokens = query.lower().split()

        # ── Object classes ────────────────────────────────────────────────
        matched: set[int] = set()
        i = 0
        while i < len(tokens):
            # Try two-token bigram first
            if i + 1 < len(tokens):
                bigram = f"{tokens[i]} {tokens[i + 1]}"
                if bigram in _OBJ_BIGRAMS:
                    matched.add(_OBJ_BIGRAMS[bigram])
                    i += 2
                    continue
            tok = tokens[i]
            # Exact match (any length)
            if tok in _OBJ_INDEX:
                matched.add(_OBJ_INDEX[tok])
            elif len(tok) >= 4:
                # Partial substring match only for sufficiently long tokens
                # (avoids "at" → "cat", "park" → "parking meter" false positives).
                # Rule: the token must be a prefix, suffix, or the class name must
                # start with the token (prevents mid-word collisions like "ark").
                for name, idx in _OBJ_INDEX.items():
                    if name.startswith(tok) or tok.startswith(name):
                        matched.add(idx)
            i += 1

        for idx in matched:
            vec[_OFF_OBJ + idx] = 1.0

        # ── Temporal keywords ─────────────────────────────────────────────
        for tok in tokens:
            if tok in _TOD_MAP:
                vec[_OFF_TOD + _TOD_MAP[tok]] = 1.0
            if tok in _SEASON_MAP:
                vec[_OFF_SEAS + _SEASON_MAP[tok]] = 1.0
            dow = _DOW_MAP.get(tok)
            if dow is not None:
                vec[_OFF_DOW + dow] = 1.0
            elif tok == "weekday":
                vec[_OFF_DOW : _OFF_DOW + 5] = 1.0  # Monday–Friday
            elif tok == "weekend":
                vec[_OFF_DOW + 5 : _OFF_DOW + 7] = 1.0  # Saturday–Sunday

        # ── Face hints ────────────────────────────────────────────────────
        _FACE_HINTS = {
            "face",
            "faces",
            "person",
            "people",
            "portrait",
            "selfie",
            "human",
        }
        if _FACE_HINTS.intersection(tokens):
            vec[_OFF_FLAG] = 1.0  # has_faces flag

        return l2_normalize(vec)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fill_objects(self, vec: np.ndarray, tags: Sequence[str]) -> None:
        """Populate the object-class slice from a list of YOLO class names."""
        counts = np.zeros(N_OBJ, dtype=np.float32)
        for tag in tags:
            t = tag.lower().strip()
            if t in _OBJ_INDEX:
                counts[_OBJ_INDEX[t]] += 1.0
        total = counts.sum()
        if total > 0.0:
            counts /= total  # relative frequency in [0, 1]
        vec[_OFF_OBJ : _OFF_OBJ + N_OBJ] = counts

    def _fill_temporal(self, vec: np.ndarray, captured_at: Any) -> None:
        """Decode a datetime value and set TOD / season / day-of-week bits."""
        if captured_at is None:
            return
        try:
            if isinstance(captured_at, str):
                # Tolerate both "YYYY-MM-DD HH:MM:SS" and ISO-8601 with T
                dt = datetime.fromisoformat(captured_at.replace("T", " ").split(".")[0])
            elif isinstance(captured_at, datetime):
                dt = captured_at
            else:
                return
        except (ValueError, TypeError):
            logger.debug("Could not parse captured_at=%r", captured_at)
            return

        vec[_OFF_TOD + _hour_to_tod(dt.hour)] = 1.0
        vec[_OFF_SEAS + _month_to_season(dt.month)] = 1.0
        vec[_OFF_DOW + dt.weekday()] = 1.0

    def _fill_faces(self, vec: np.ndarray, cluster_ids: Sequence[int]) -> None:
        """Set the has_faces flag and per-cluster presence bits."""
        if not cluster_ids:
            return
        vec[_OFF_FLAG] = 1.0  # has_faces
        for cid in cluster_ids:
            if 0 <= cid < self._max_fc:
                vec[_OFF_FC + cid] = 1.0

    def _fill_spatial(
        self,
        vec: np.ndarray,
        lat: Optional[float],
        lon: Optional[float],
    ) -> None:
        """Normalise GPS coordinates to [−1, 1] and store in the spatial slice."""
        if lat is None or lon is None:
            return
        try:
            vec[_OFF_FLAG + 1] = 1.0  # has_location
            vec[_OFF_SPA] = float(lat) / 90.0  # [−90,  90] → [−1, 1]
            vec[_OFF_SPA + 1] = float(lon) / 180.0  # [−180, 180] → [−1, 1]
        except (TypeError, ValueError):
            pass
