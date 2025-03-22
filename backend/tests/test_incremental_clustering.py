import time
import numpy as np
import logging
import os
import sys
# Remove the Path import since it's unused

# First add the project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Then import the project modules
from app.facecluster.facecluster import FaceCluster
from app.database.faces import cleanup_face_embeddings, create_faces_table

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def test_incremental_clustering_performance():
    """Test the performance of incremental clustering vs. full reclustering"""
    # Initialize database tables
    create_faces_table()
    cleanup_face_embeddings()

    # Test configuration
    test_config = {
        "num_images": 100,
        "faces_per_image": 3,
        "embedding_size": 128,
        "batch_size": 10,
    }

    # Generate test data
    total_faces = test_config["num_images"] * test_config["faces_per_image"]
    logger.info(f"Generating {total_faces} random face embeddings...")

    all_embeddings = [
        np.random.rand(test_config["embedding_size"]).astype(np.float32)
        for _ in range(total_faces)
    ]

    all_paths = [
        f"test_image_{i}.jpg"
        for i in range(test_config["num_images"])
        for _ in range(test_config["faces_per_image"])
    ]

    # Test incremental clustering
    logger.info("\n===== Testing Incremental Clustering =====")
    face_cluster = FaceCluster()

    start_time = time.perf_counter()

    # Process in batches to simulate real usage
    batch_size = test_config["batch_size"]
    for i in range(0, len(all_embeddings), batch_size):
        batch_embeddings = all_embeddings[i : i + batch_size]
        batch_paths = all_paths[i : i + batch_size]

        if i % 50 == 0 and i > 0:
            logger.info(f"Processed {i} embeddings...")

        face_cluster.add_faces_batch(batch_embeddings, batch_paths)

    incremental_time = time.perf_counter() - start_time

    # Get final clusters
    clusters = face_cluster.get_clusters()
    num_clusters = len([c for c in clusters.keys() if c != -1])

    logger.info(f"Incremental clustering completed in {incremental_time:.2f} seconds")
    logger.info(f"Found {num_clusters} clusters")

    # Test full reclustering (traditional approach)
    logger.info("\n===== Testing Full Reclustering Approach =====")

    # Reset
    cleanup_face_embeddings()
    face_cluster = FaceCluster()

    start_time = time.perf_counter()

    # Add embeddings one by one, forcing full reclustering each time
    for i, (embedding, path) in enumerate(zip(all_embeddings, all_paths)):
        if i % 50 == 0 and i > 0:
            logger.info(f"Processed {i} embeddings...")

        # Simulate the old approach by directly calling DBSCAN each time
        face_cluster.embeddings = np.array(all_embeddings[: i + 1])
        face_cluster.image_ids = [p.split("/")[-1] for p in all_paths[: i + 1]]
        # Use the fit method instead which should run DBSCAN internally
        face_cluster.fit(all_embeddings[: i + 1], all_paths[: i + 1])

    full_recluster_time = time.perf_counter() - start_time

    # Compare results
    logger.info("\n===== Performance Comparison =====")
    logger.info(f"Incremental clustering: {incremental_time:.2f} seconds")
    logger.info(f"Full reclustering: {full_recluster_time:.2f} seconds")
    logger.info(f"Speedup: {full_recluster_time/incremental_time:.2f}x faster")


if __name__ == "__main__":
    test_incremental_clustering_performance()

