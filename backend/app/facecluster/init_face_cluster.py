import os
from app.config.settings import DATABASE_PATH
from app.database.faces import get_all_face_embeddings
from app.facecluster.facecluster import FaceCluster

face_cluster = None


def init_face_cluster(db_path=DATABASE_PATH):
    # Initializes the face_cluster object.
    # - If the object already exists, it returns the existing instance.
    # - If a database exists at the specified path, it loads the FaceCluster from it.
    # - If no database is found, it creates a new FaceCluster instance,
    #   fits it with all available face embeddings, and saves it to the database.
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
    # Returns the global face_cluster instance.
    # If it hasn't been initialized yet, it calls init_face_cluster() to set it up.
    global face_cluster
    if face_cluster is None:
        face_cluster = init_face_cluster()
    return face_cluster
