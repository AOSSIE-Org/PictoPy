from __future__ import annotations

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances
import sqlite3
import json
from collections import defaultdict
from contextlib import contextmanager
import logging
from typing import Dict, List, Optional, Set, Union, Any, Callable, TypeVar, ParamSpec
from pathlib import Path
import time
from functools import wraps
from numpy.typing import NDArray

from app.config.settings import CLUSTERS_DATABASE_PATH
from app.utils.path_id_mapping import get_path_from_id, get_id_from_path
from app.database.faces import get_face_embeddings, get_all_face_embeddings

# Set up logging
logger = logging.getLogger(__name__)

# Type variables for generic type hints
P = ParamSpec('P')
R = TypeVar('R')

class TTLCache:
    """
    Time-based LRU cache implementation with type safety.
    
    Attributes:
        maxsize: Maximum number of items to store in cache
        ttl: Time-to-live in seconds for cache entries
        cache: Dictionary storing cached values and timestamps
    """
    
    def __init__(self, maxsize: int = 128, ttl: int = 3600) -> None:
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache: Dict[str, tuple[Any, float]] = {}
        
    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        """Create a cached version of the function."""
        
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Create cache key from function arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check if result is cached and not expired
            if key in self.cache:
                result, timestamp = self.cache[key]
                if time.time() - timestamp <= self.ttl:
                    return result
                else:
                    del self.cache[key]
            
            # Compute new result
            result = func(*args, **kwargs)
            
            # Add to cache
            self.cache[key] = (result, time.time())
            
            # Enforce cache size limit
            if len(self.cache) > self.maxsize:
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k][1]
                )
                del self.cache[oldest_key]
            
            return result
        
        def clear_cache() -> None:
            """Clear the cache."""
            self.cache.clear()
            
        wrapper.clear_cache = clear_cache  # type: ignore
        return wrapper

@contextmanager
def database_connection(db_path: Union[str, Path]):
    """
    Context manager for handling database connections.
    
    Args:
        db_path: Path to the SQLite database
        
    Yields:
        sqlite3.Connection: Active database connection
    """
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

class FaceCluster:
    """
    Face clustering implementation with caching and optimized performance.
    
    Attributes:
        eps: DBSCAN epsilon parameter
        min_samples: DBSCAN minimum samples parameter
        metric: Distance metric for clustering
        dbscan: DBSCAN clustering instance
        embeddings: Array of face embeddings
        image_ids: List of image IDs
        labels: Cluster labels
        db_path: Path to the database
    """

    def __init__(
        self,
        eps: float = 0.3,
        min_samples: int = 2,
        metric: str = "cosine",
        db_path: Union[str, Path] = CLUSTERS_DATABASE_PATH
    ) -> None:
        """
        Initialize the face cluster manager.
        
        Args:
            eps: DBSCAN epsilon parameter
            min_samples: DBSCAN minimum samples parameter
            metric: Distance metric for clustering
            db_path: Path to the database
        """
        self.eps = eps
        self.min_samples = min_samples
        self.metric = metric
        logger.debug(f"Initializing DBSCAN with eps={eps}")
        self.dbscan = DBSCAN(
            eps=eps,
            min_samples=min_samples,
            metric=metric,
            n_jobs=-1  # Use all available CPU cores
        )
        self.embeddings: NDArray = np.array([])
        self.image_ids: List[str] = []
        self.labels: Optional[NDArray] = None
        self.db_path = Path(db_path)
        
        # Initialize database
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the database schema if it doesn't exist."""
        with database_connection(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS face_clusters (
                    id INTEGER PRIMARY KEY,
                    image_ids TEXT NOT NULL,
                    labels TEXT NOT NULL
                )
            """)

    def _validate_input(self, embeddings: List[NDArray], image_paths: List[str]) -> None:
        """
        Validate input data for consistency.
        
        Args:
            embeddings: List of face embeddings
            image_paths: List of corresponding image paths
            
        Raises:
            ValueError: If inputs are invalid or inconsistent
        """
        if len(embeddings) != len(image_paths):
            raise ValueError("Number of embeddings must match number of image paths")
        if not all(isinstance(path, str) for path in image_paths):
            raise ValueError("All image paths must be strings")

    def fit(self, embeddings: List[NDArray], image_paths: List[str]) -> Dict[int, List[str]]:
        """
        Fit the clustering model with new data.
        
        Args:
            embeddings: List of face embeddings
            image_paths: List of corresponding image paths
            
        Returns:
            Dict mapping cluster labels to lists of image IDs
        """
        self._validate_input(embeddings, image_paths)
        
        if not embeddings:
            self.embeddings = np.array([])
            self.image_ids = []
            self.labels = None
        else:
            self.embeddings = np.array(embeddings)
            self.image_ids = [get_id_from_path(path) for path in image_paths]
            self.labels = self.dbscan.fit_predict(self.embeddings)

        self._clear_caches()
        return self.get_clusters()

    @TTLCache(maxsize=128, ttl=3600)
    def get_clusters(self) -> Dict[int, List[str]]:
        """
        Get current clustering results with TTL caching.
        
        Returns:
            Dict mapping cluster labels to lists of image IDs
        """
        clusters: Dict[int, Set[str]] = defaultdict(set)
        if self.labels is not None:
            for i, label in enumerate(self.labels):
                clusters[int(label)].add(self.image_ids[i])
        return {k: list(v) for k, v in clusters.items()}

    def add_face(self, embedding: NDArray, image_path: str) -> Dict[int, List[str]]:
        """
        Add a new face embedding to the clusters.
        
        Args:
            embedding: Face embedding vector
            image_path: Path to the image
            
        Returns:
            Updated clustering results
        """
        image_id = get_id_from_path(image_path)
        
        if len(self.embeddings) == 0:
            self.embeddings = np.array([embedding])
            self.image_ids = [image_id]
            self.labels = np.array([-1])
        else:
            # Vectorized distance calculation
            distances = cosine_distances(embedding.reshape(1, -1), self.embeddings)[0]
            nearest_neighbor = np.argmin(distances)
            
            # Determine cluster assignment
            if distances[nearest_neighbor] <= self.eps:
                new_label = self.labels[nearest_neighbor]
            else:
                new_label = max(self.labels) + 1 if len(self.labels) > 0 else 0
            
            # Update state
            self.embeddings = np.vstack([self.embeddings, embedding])
            self.image_ids.append(image_id)
            self.labels = np.append(self.labels, new_label)

        self._clear_caches()
        self.save_to_db()
        return self.get_clusters()

    @TTLCache(maxsize=128, ttl=3600)
    def get_related_images(self, image_id: str) -> List[str]:
        """
        Find related images based on embedding similarity with TTL caching.
        
        Args:
            image_id: ID of the query image
            
        Returns:
            List of related image IDs
        """
        if image_id not in self.image_ids:
            return []

        indices = [i for i, id in enumerate(self.image_ids) if id == image_id]
        embeddings = self.embeddings[indices]

        related_images = set()
        for embedding in embeddings:
            distances = cosine_distances(
                embedding.reshape(1, -1),
                self.embeddings
            )[0]
            for i, distance in enumerate(distances):
                if (
                    self.image_ids[i] != image_id
                    and distance <= self.eps
                ):
                    related_images.add(self.image_ids[i])

        return list(related_images)

    def remove_image(self, image_id: str) -> Dict[int, List[str]]:
        """
        Remove an image and its embeddings from the clusters.
        
        Args:
            image_id: ID of the image to remove
            
        Returns:
            Updated clustering results
        """
        if image_id in self.image_ids:
            # Create mask for filtering
            mask = np.array([id != image_id for id in self.image_ids])
            
            # Update arrays efficiently
            self.embeddings = self.embeddings[mask]
            self.image_ids = list(np.array(self.image_ids)[mask])
            
            if len(self.embeddings) > 0:
                self.labels = self.dbscan.fit_predict(self.embeddings)
            else:
                self.labels = None

        self._clear_caches()
        self.save_to_db()
        return self.get_clusters()

    def _clear_caches(self) -> None:
        """Clear all internal caches."""
        self.get_clusters.clear_cache()  # type: ignore
        self.get_related_images.clear_cache()  # type: ignore

    def save_to_db(self) -> None:
        """Save current state to the database."""
        with database_connection(self.db_path) as conn:
            state = {
                'image_ids': json.dumps(self.image_ids),
                'labels': json.dumps(
                    self.labels.tolist() if self.labels is not None else []
                )
            }
            
            conn.execute("DELETE FROM face_clusters")
            conn.execute(
                """INSERT INTO face_clusters (image_ids, labels)
                   VALUES (:image_ids, :labels)""",
                state
            )

    @classmethod
    def load_from_db(
        cls,
        db_path: Union[str, Path] = CLUSTERS_DATABASE_PATH
    ) -> 'FaceCluster':
        """
        Load clustering state from database.
        
        Args:
            db_path: Path to the database
            
        Returns:
            Initialized FaceCluster instance
        """
        instance = cls(db_path=db_path)
        
        try:
            with database_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT image_ids, labels FROM face_clusters")
                row = cursor.fetchone()

                if row:
                    image_ids, labels = row
                    instance.image_ids = json.loads(image_ids)
                    instance.labels = (
                        np.array(json.loads(labels)) if labels else None
                    )

                    # Load embeddings efficiently
                    embeddings = []
                    for emb in get_all_face_embeddings():
                        if get_id_from_path(emb["image_path"]) in instance.image_ids:
                            embeddings.extend(emb["embeddings"])
                    instance.embeddings = np.array(embeddings)

        except sqlite3.OperationalError as e:
            logger.error(f"Database error: {e}")

        return instance