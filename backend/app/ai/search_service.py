"""
SearchService
=============
High-level orchestration of :class:`~app.ai.embedding_service.EmbeddingService`
and :class:`~app.ai.vector_index_manager.VectorIndexManager`.

Responsibilities
----------------
* Index a single image (generate embedding → persist to DB → update in-memory
  index) with automatic face-cluster enrichment.
* Bulk-index all tagged images that are not yet in the embedding store, i.e.
  only new images are processed on startup – **no recomputation**.
* Accept a free-text query and return a ranked list of :class:`SearchResult`
  objects enriched with path / thumbnail / tag data.
* Remove an image from the index when it is deleted from the library.

Usage (inside a FastAPI route handler)
---------------------------------------
    service: SearchService = request.app.state.search_service
    results = service.search("dog at the park", top_k=10)

Thread safety
-------------
``SearchService`` is thread-safe: all mutations delegate to the
``VectorIndexManager``'s internal RLock, and DB writes are atomic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.ai.embedding_service import EmbeddingService, EMBEDDING_DIM
from app.ai.vector_index_manager import VectorIndexManager
from app.database.embeddings import (
    db_upsert_embedding,
    db_delete_embedding,
    db_get_indexed_image_ids,
)
from app.database.images import db_get_all_images, db_get_images_by_ids
from app.database.faces import db_get_faces_by_image_id
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class SearchResult:
    """A single ranked result returned by :py:meth:`SearchService.search`."""

    image_id: str
    score: float
    path: str = ""
    thumbnail_path: str = ""
    tags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# SearchService
# ---------------------------------------------------------------------------


class SearchService:
    """
    Façade that couples :class:`EmbeddingService` and :class:`VectorIndexManager`.

    Parameters
    ----------
    embedding_service :
        Pre-constructed service (injected for testability).  Defaults to a
        fresh ``EmbeddingService()`` instance.
    index_manager :
        Pre-constructed manager.  Defaults to a new ``VectorIndexManager``
        sized to ``EMBEDDING_DIM``.
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        index_manager: Optional[VectorIndexManager] = None,
    ) -> None:
        self._embed = embedding_service or EmbeddingService()
        self._index = index_manager or VectorIndexManager(embedding_dim=EMBEDDING_DIM)

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_image(self, image_record: Dict[str, Any]) -> None:
        """
        Embed *image_record* and persist / update the index.

        The face-cluster IDs are fetched from the database automatically
        if they are not already present in *image_record* under the key
        ``face_cluster_ids``.

        Parameters
        ----------
        image_record :
            Dict with at minimum ``id``, ``tags``, ``captured_at``,
            ``latitude``, ``longitude``.  Matches the shape returned by
            :func:`~app.database.images.db_get_all_images`.
        """
        enriched = _enrich_with_faces(image_record)
        embedding = self._embed.embed_image(enriched)
        db_upsert_embedding(enriched["id"], embedding)
        self._index.add_or_update(enriched["id"], embedding)
        logger.debug("Indexed image %s", enriched["id"])

    def index_all(
        self,
        *,
        force: bool = False,
        images: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """
        Index all tagged images that do not yet have a stored embedding.

        Parameters
        ----------
        force :
            If ``True``, re-embed and overwrite every image even if already
            indexed.  Useful after a settings change (e.g. ``MAX_FACE_CLUSTERS``).
        images :
            Pre-fetched image records.  Fetched from the DB when ``None``.

        Returns
        -------
        int
            Number of images actually (re-)indexed in this call.
        """
        if images is None:
            images = db_get_all_images(tagged=True)

        already_indexed: set[str] = set() if force else set(db_get_indexed_image_ids())

        count = 0
        for record in images:
            iid = record.get("id")
            if not iid:
                continue
            if not force and iid in already_indexed:
                continue
            try:
                self.index_image(record)
                count += 1
            except Exception:
                logger.exception("Failed to index image %s", iid)

        if count:
            logger.info("Indexed %d new image(s)", count)
        else:
            logger.debug("index_all: no new images to index")
        return count

    def remove_image(self, image_id: str) -> None:
        """
        Remove an image from both the persistent embedding store and the
        in-memory index.

        Should be called whenever an image is deleted from the library so
        it no longer appears in search results.
        """
        db_delete_embedding(image_id)
        self._index.remove(image_id)
        logger.debug("Removed image %s from semantic index", image_id)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 20,
        min_score: float = 0.05,
    ) -> List[SearchResult]:
        """
        Perform a semantic search across all indexed images.

        Parameters
        ----------
        query :
            Free-text query (e.g. ``"dog at the park"``, ``"evening sunset"``,
            ``"person in summer"``).
        top_k :
            Maximum number of results to return.
        min_score :
            Cosine-similarity threshold.  Keeps only results with
            ``score >= min_score``.

        Returns
        -------
        list of :class:`SearchResult` ordered by descending similarity score.
        """
        query = query.strip()
        if not query:
            return []

        query_vec = self._embed.embed_query(query)
        raw = self._index.search(query_vec, top_k=top_k, min_score=min_score)
        if not raw:
            return []

        # Batch-fetch path / thumbnail / tags for the matched IDs
        id_set = {iid for iid, _ in raw}
        path_map = _build_path_map(id_set)

        results: List[SearchResult] = []
        for image_id, score in raw:
            info = path_map.get(image_id, {})
            results.append(
                SearchResult(
                    image_id=image_id,
                    score=round(score, 4),
                    path=info.get("path", ""),
                    thumbnail_path=info.get("thumbnailPath", ""),
                    tags=info.get("tags") or [],
                )
            )
        return results

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def index_size(self) -> int:
        """Number of images currently held in the in-memory index."""
        return self._index.size

    @property
    def is_index_loaded(self) -> bool:
        """``True`` once the index has been populated from the database."""
        return self._index.is_loaded


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _enrich_with_faces(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add ``face_cluster_ids`` to *record* unless already present.

    Fetches from the database; silently returns an empty list on error.
    """
    if "face_cluster_ids" in record:
        return record
    try:
        faces = db_get_faces_by_image_id(record["id"])
        cluster_ids = [
            f["cluster_id"] for f in faces if f.get("cluster_id") is not None
        ]
    except Exception:
        logger.debug("Could not fetch face clusters for image %s", record.get("id"))
        cluster_ids = []
    return {**record, "face_cluster_ids": cluster_ids}


def _build_path_map(image_ids: set) -> Dict[str, Dict]:
    """
    Batch-fetch {id, path, thumbnailPath, tags} for a set of image IDs.

    Returns an empty dict on DB error so callers degrade gracefully.
    """
    try:
        records = db_get_images_by_ids(list(image_ids))
        return {r["id"]: r for r in records}
    except Exception:
        logger.exception("Failed to fetch path map for search results")
        return {}
