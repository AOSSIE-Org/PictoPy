"""
VectorIndexManager
==================
Maintains an in-memory numpy matrix of L2-normalised image embeddings and
performs fast cosine-similarity search via a bulk matrix–vector product.

Key design properties
---------------------
*  **Lazy loading** – the index is populated from the SQLite embedding store
   on the first query; startup is therefore instant regardless of library size.
*  **Persistent backing store** – embeddings survive restarts without
   recomputation; only newly added images are embedded.
*  **Incremental updates** – :py:meth:`add_or_update` and :py:meth:`remove`
   keep the in-memory matrix in sync with live changes without a full rebuild.
*  **Thread-safe** – all public methods acquire a reentrant lock.
*  **Memory-efficient** – float32 storage; 10 000 images × 163 dims ≈ 6.5 MB.
*  **O(N) search** via ``matrix @ query_vec`` with ``np.argpartition`` for
   cheap top-k extraction (no sorting of the full array).
"""

from __future__ import annotations

import threading
from typing import Dict, List, Tuple

import numpy as np

from app.database.embeddings import db_get_all_embeddings
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


class VectorIndexManager:
    """
    Thread-safe in-memory flat vector index.

    Parameters
    ----------
    embedding_dim :
        Expected dimensionality of every embedding.  Vectors with a
        different dimension are rejected with a warning.
    """

    def __init__(self, embedding_dim: int) -> None:
        self._dim = embedding_dim
        self._lock = threading.RLock()

        # Core state – populated lazily via ensure_loaded()
        self._image_ids: List[str] = []
        self._id_to_row: Dict[str, int] = {}
        self._matrix: np.ndarray = np.empty((0, self._dim), dtype=np.float32)
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Index lifecycle
    # ------------------------------------------------------------------

    def ensure_loaded(self) -> None:
        """
        Load all stored embeddings from SQLite into RAM (idempotent).

        Thread-safe; subsequent calls are no-ops once loading has completed.
        """
        with self._lock:
            if self._loaded:
                return
            self._do_rebuild()

    def rebuild(self) -> None:
        """
        Force a full reload from the database, discarding any in-memory state.

        Should be called after a bulk re-indexing operation to ensure the
        in-memory matrix accurately reflects the persisted embeddings.
        """
        with self._lock:
            self._loaded = False
            self._do_rebuild()

    def _do_rebuild(self) -> None:
        """Internal rebuild – **must** be called while holding *self._lock*."""
        rows = db_get_all_embeddings()

        ids: List[str] = []
        vecs: List[np.ndarray] = []

        for image_id, vec in rows:
            if vec.shape[0] != self._dim:
                logger.warning(
                    "Skipping embedding for %s: dim %d ≠ expected %d",
                    image_id,
                    vec.shape[0],
                    self._dim,
                )
                continue
            ids.append(image_id)
            vecs.append(vec)

        self._image_ids = ids
        self._id_to_row = {iid: idx for idx, iid in enumerate(ids)}
        self._matrix = (
            np.stack(vecs, axis=0).astype(np.float32)
            if vecs
            else np.empty((0, self._dim), dtype=np.float32)
        )
        self._loaded = True
        logger.debug(
            "Vector index (re)loaded: %d embeddings, dim=%d",
            len(ids),
            self._dim,
        )

    # ------------------------------------------------------------------
    # Incremental updates
    # ------------------------------------------------------------------

    def add_or_update(self, image_id: str, embedding: np.ndarray) -> None:
        """
        Add a new embedding or overwrite an existing one.

        Parameters
        ----------
        image_id :
            Must match the primary key used in ``image_embeddings``.
        embedding :
            1-D float32 array of length *embedding_dim*.

        Raises
        ------
        ValueError
            If ``embedding.shape[0]`` does not equal the index dimension.
        """
        if embedding.shape[0] != self._dim:
            raise ValueError(
                f"Embedding dim {embedding.shape[0]} ≠ index dim {self._dim}"
            )
        vec_row = embedding.astype(np.float32).reshape(1, -1)

        with self._lock:
            self.ensure_loaded()
            if image_id in self._id_to_row:
                # In-place update (O(1))
                self._matrix[self._id_to_row[image_id]] = vec_row
            else:
                # Append row (amortised O(1) via np.vstack)
                row_idx = len(self._image_ids)
                self._image_ids.append(image_id)
                self._id_to_row[image_id] = row_idx
                if self._matrix.shape[0] > 0:
                    self._matrix = np.vstack([self._matrix, vec_row])
                else:
                    self._matrix = vec_row

    def remove(self, image_id: str) -> None:
        """
        Remove an image from the in-memory index.

        Silently ignores *image_id* values not present in the index.
        O(N) due to the index compaction step; acceptable for deletions.
        """
        with self._lock:
            self.ensure_loaded()
            if image_id not in self._id_to_row:
                return
            row = self._id_to_row.pop(image_id)
            self._image_ids.pop(row)
            self._matrix = np.delete(self._matrix, row, axis=0)
            # Rebuild the dense mapping after the row shift
            self._id_to_row = {iid: idx for idx, iid in enumerate(self._image_ids)}

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query_vec: np.ndarray,
        top_k: int = 20,
        min_score: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """
        Return ``(image_id, cosine_similarity)`` pairs sorted by descending score.

        Cosine similarity is computed as a single ``matrix @ query_vec``
        product (O(N·D)).  Top-k extraction uses ``np.argpartition`` to
        avoid a full sort when k ≪ N.

        Parameters
        ----------
        query_vec :
            L2-normalised 1-D float32 array produced by
            :py:meth:`~app.ai.embedding_service.EmbeddingService.embed_query`.
        top_k :
            Maximum number of results to return.
        min_score :
            Cosine similarity threshold.  Results below this value are
            excluded from the returned list.

        Returns
        -------
        list of (image_id, score) tuples, highest score first.
        """
        with self._lock:
            self.ensure_loaded()
            n = self._matrix.shape[0]
            if n == 0:
                return []

            q = query_vec.astype(np.float32)
            scores: np.ndarray = self._matrix @ q  # shape (N,)

            k = min(top_k, n)
            # Partial sort: cheaply find the top-k indices
            top_indices = np.argpartition(scores, -k)[-k:]
            # Sort those k indices by score (descending)
            top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

            results: List[Tuple[str, float]] = []
            for idx in top_indices:
                score = float(scores[idx])
                if score >= min_score:
                    results.append((self._image_ids[idx], score))
            return results

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Number of embeddings currently held in memory."""
        with self._lock:
            return len(self._image_ids)

    @property
    def is_loaded(self) -> bool:
        with self._lock:
            return self._loaded

    def indexed_ids(self) -> List[str]:
        """Return a snapshot of all image_ids currently in the index."""
        with self._lock:
            self.ensure_loaded()
            return list(self._image_ids)
