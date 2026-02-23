import numpy as np
from app.utils.face_clusters import cluster_util_cluster_all_face_embeddings


def test_dbscan_clusters_two_groups(monkeypatch):
    """
    Ensure clustering groups similar embeddings together.
    """

    cluster_1 = np.array([[1, 0, 0], [0.98, 0.02, 0]])
    cluster_2 = np.array([[0, 1, 0], [0.02, 0.99, 0]])

    embeddings = np.vstack([cluster_1, cluster_2])

    fake_faces = [
        {
            "face_id": i + 1,
            "embeddings": embeddings[i],
            "cluster_name": None,
        }
        for i in range(len(embeddings))
    ]

    def mock_get_all_faces():
        return fake_faces

    monkeypatch.setattr(
        "app.utils.face_clusters.db_get_all_faces_with_cluster_names",
        mock_get_all_faces,
    )

    results = cluster_util_cluster_all_face_embeddings(
        eps=0.3, min_samples=1, similarity_threshold=0.5
    )

    assert len(results) == 4

    cluster_ids = set([r.cluster_uuid for r in results])
    assert len(cluster_ids) == 2


def test_clustering_skips_invalid_embeddings(monkeypatch):
    """
    Ensure invalid embeddings (zero vector) are skipped.
    """

    valid_embedding = np.array([1, 0, 0])
    invalid_embedding = np.array([0, 0, 0])

    fake_faces = [
        {"face_id": 1, "embeddings": valid_embedding, "cluster_name": None},
        {"face_id": 2, "embeddings": invalid_embedding, "cluster_name": None},
    ]

    def mock_get_all_faces():
        return fake_faces

    monkeypatch.setattr(
        "app.utils.face_clusters.db_get_all_faces_with_cluster_names",
        mock_get_all_faces,
    )

    results = cluster_util_cluster_all_face_embeddings(
        eps=0.5, min_samples=1, similarity_threshold=0.5
    )

    assert len(results) == 1