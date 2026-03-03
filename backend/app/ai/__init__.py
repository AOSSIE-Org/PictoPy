"""
app.ai – offline semantic search subsystem for PictoPy
=======================================================

Components
----------
EmbeddingService    Convert image metadata into fixed-dimension L2-normalised
                    numpy vectors using a vocabulary derived from YOLO class
                    names and hard-coded temporal / spatial tokens.

VectorIndexManager  In-memory cosine-similarity index backed by a flat numpy
                    matrix.  Loaded lazily from the SQLite embedding store on
                    first query; supports incremental add / remove without a
                    full rebuild.

SearchService       High-level façade that wires EmbeddingService and
                    VectorIndexManager together, handles face-cluster
                    enrichment, and returns ranked SearchResult objects.

Typical usage (inside a FastAPI route)
---------------------------------------
    service: SearchService = request.app.state.search_service
    results = service.search("dog at the park", top_k=10)
"""

from app.ai.embedding_service import EmbeddingService
from app.ai.vector_index_manager import VectorIndexManager
from app.ai.search_service import SearchService

__all__ = ["EmbeddingService", "VectorIndexManager", "SearchService"]
