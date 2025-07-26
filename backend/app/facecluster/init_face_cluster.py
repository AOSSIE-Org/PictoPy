import os
from app.config.settings import DATABASE_PATH
from app.database.faces import get_all_face_embeddings
from app.facecluster.facecluster import FaceCluster

face_cluster = None


def init_face_cluster(db_path=DATABASE_PATH):
    """
    Initialize the face clustering system.

    Loads existing face clusters from the database if the database file exists.
    Otherwise, creates a new FaceCluster instance, loads all face embeddings,
    fits the clustering model with those embeddings, and saves the state to the database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        The initialized FaceCluster instance.
    """
    global face_cluster
    if face_cluster is not None:
        return face_cluster

    if os.path.exists(db_path):
        print("Loading existing face clusters from database...", flush=True)
        face_cluster = FaceCluster.load_from_db(db_path)
    else:
        print("Creating new face clusters database...")
        face_cluster = FaceCluster(db_path=db_path)

        all_embeddings = get_all_face_embeddings()
        if all_embeddings:
            embeddings = [e["embeddings"][0] for e in all_embeddings]
            image_paths = [e["image_path"] for e in all_embeddings]
            face_cluster.fit(embeddings, image_paths)
        else:
            print("No face embeddings found. Creating empty clusters.", flush=True)
            face_cluster.fit([], [])

        face_cluster.save_to_db()

    return face_cluster


def get_face_cluster():
    """
    Retrieve the global face cluster instance.

    If the face cluster is not yet initialized, this function initializes it by
    calling init_face_cluster(). Otherwise, it returns the existing instance.

    Returns:
        The global FaceCluster instance.
    """
    global face_cluster
    if face_cluster is None:
        face_cluster = init_face_cluster()
    return face_cluster
