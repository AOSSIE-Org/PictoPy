import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances
import sqlite3
import json
from collections import defaultdict
from app.config.settings import CLUSTERS_DATABASE_PATH
from app.utils.path_id_mapping import get_path_from_id, get_id_from_path
from app.database.faces import get_face_embeddings, get_all_face_embeddings


class FaceCluster:
    def __init__(
        self, eps=0.3, min_samples=2, metric="cosine", db_path=CLUSTERS_DATABASE_PATH
    ):
        self.eps = eps
        self.min_samples = min_samples
        self.metric = metric
        # print("DBSCAN Eps: ", eps)
        self.dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric=metric)
        self.embeddings = np.array([])
        self.image_ids = []
        self.labels = None
        self.db_path = db_path

    def fit(self, embeddings, image_paths):
        if not embeddings or len(embeddings) == 0:
            self.embeddings = np.array([])
            self.image_ids = []
            self.labels = None
        else:
            self.embeddings = np.array(embeddings)
            self.image_ids = [get_id_from_path(path) for path in image_paths]
            self.labels = self.dbscan.fit_predict(self.embeddings)
        return self.get_clusters()

    def get_clusters(self):
        clusters = defaultdict(set)
        if self.labels is not None:
            for i, label in enumerate(self.labels):
                clusters[int(label)].add(self.image_ids[i])
        return {k: list(v) for k, v in clusters.items()}

    def get_all_clusters(self):
        clusters = self.get_clusters()
        result = {}
        for label, image_ids in clusters.items():
            result[label] = [get_path_from_id(image_id) for image_id in image_ids]
        return result

    def add_face(self, embedding, image_path):
        image_id = get_id_from_path(image_path)
        if len(self.embeddings) == 0:
            self.embeddings = np.array([embedding])
            self.image_ids = [image_id]
            self.labels = np.array([-1])
        else:
            distances = cosine_distances(embedding.reshape(1, -1), self.embeddings)[0]
            nearest_neighbor = np.argmin(distances)
            if distances[nearest_neighbor] <= self.eps:
                self.labels = np.append(self.labels, self.labels[nearest_neighbor])
            else:
                self.labels = np.append(
                    self.labels, max(self.labels) + 1 if len(self.labels) > 0 else 0
                )

            self.embeddings = np.vstack([self.embeddings, embedding])
            self.image_ids.append(image_id)

        if len(self.embeddings) % 5 == 0:
            self.labels = self.dbscan.fit_predict(self.embeddings)

        self.save_to_db()
        return self.get_all_clusters()

    def remove_image(self, image_id):
        if image_id in self.image_ids:
            indices_to_remove = [
                i for i, id in enumerate(self.image_ids) if id == image_id
            ]
            self.embeddings = np.delete(self.embeddings, indices_to_remove, axis=0)
            self.image_ids = [
                id for i, id in enumerate(self.image_ids) if i not in indices_to_remove
            ]
            self.labels = np.delete(self.labels, indices_to_remove)

            if len(self.embeddings) > 0:
                self.labels = self.dbscan.fit_predict(self.embeddings)

        self.save_to_db()
        return self.get_all_clusters()

    def get_related_images(self, image_id):
        if image_id not in self.image_ids:
            return []

        indices = [i for i, id in enumerate(self.image_ids) if id == image_id]
        embeddings = self.embeddings[indices]

        related_images = set()
        for embedding in embeddings:
            for i, other_embedding in enumerate(self.embeddings):
                if self.image_ids[i] != image_id:
                    similarity = (
                        1
                        - cosine_distances(
                            embedding.reshape(1, -1), other_embedding.reshape(1, -1)
                        )[0][0]
                    )
                    if similarity >= self.eps:
                        related_images.add(self.image_ids[i])

        return list(related_images)

    def save_to_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS face_clusters
                          (id INTEGER PRIMARY KEY, image_ids TEXT, labels TEXT)"""
        )

        image_ids_json = json.dumps(self.image_ids)
        labels_json = json.dumps(
            self.labels.tolist() if self.labels is not None else []
        )

        cursor.execute("DELETE FROM face_clusters")
        cursor.execute(
            "INSERT INTO face_clusters (image_ids, labels) VALUES (?, ?)",
            (image_ids_json, labels_json),
        )

        conn.commit()
        conn.close()

    @classmethod
    def load_from_db(cls, db_path=CLUSTERS_DATABASE_PATH):
        instance = cls(db_path=db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT image_ids, labels FROM face_clusters")
            row = cursor.fetchone()

            if row:
                image_ids, labels = row
                instance.image_ids = json.loads(image_ids)
                instance.labels = np.array(json.loads(labels)) if labels else None

                # Load embeddings from face database
                all_embeddings = get_all_face_embeddings()
                instance.embeddings = []
                for emb in all_embeddings:
                    image_id = get_id_from_path(emb["image_path"])
                    if image_id in instance.image_ids:
                        instance.embeddings.extend(emb["embeddings"])
                instance.embeddings = np.array(instance.embeddings)

        except sqlite3.OperationalError:
            pass

        conn.close()
        return instance
