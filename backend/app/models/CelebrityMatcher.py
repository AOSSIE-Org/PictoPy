import pickle
import numpy as np
import os
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

class CelebrityMatcher:
    def __init__(self, encodings_path=None):
        """
        Initializes the CelebrityMatcher by loading encodings and optimizing them into a matrix.
        
        Args:
            encodings_path (str): Path to the pickle file containing celebrity encodings.
                                  If None, defaults to 'celebrity_encodings.pkl' in this directory.
        """
        if encodings_path is None:
            encodings_path = os.path.join(os.path.dirname(__file__), 'celebrity_encodings.pkl')

        self.names = []
        self.embeddings_matrix = None
        self._load_and_optimize(encodings_path)

    def _load_and_optimize(self, path):
        """
        Loads the pickle file and converts the dictionary of lists into a NumPy matrix.
        """
        # Resolve absolute path if relative path is provided
        if not os.path.isabs(path):
            if os.path.exists(path):
                pass
            else:
                 # Check relative to this file location as fallback
                 dir_of_file = os.path.dirname(__file__)
                 potential_path = os.path.join(dir_of_file, os.path.basename(path))
                 if os.path.exists(potential_path):
                     path = potential_path

        if not os.path.exists(path):
            logger.error(f"Celebrity encodings file not found: {path}")
            return

        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            # Data is expected to be { "Name": [embedding1, embedding2], ... }
            if not isinstance(data, dict):
                logger.error("Loaded data is not a dictionary.")
                return

            all_names = []
            all_embeddings = []

            for name, embeddings_list in data.items():
                for embedding in embeddings_list:
                    all_names.append(name)
                    all_embeddings.append(embedding)
            
            if all_embeddings:
                self.names = np.array(all_names)
                self.embeddings_matrix = np.array(all_embeddings)
                logger.info(f"Loaded {len(self.names)} celebrity encodings for {len(data)} identities.")
            else:
                logger.warning("No embeddings found in the loaded data.")

        except Exception as e:
            logger.error(f"Failed to load celebrity encodings: {e}")

    def identify_face(self, unknown_embedding, threshold=0.7):
        """
        Identifies the celebrity from the given embedding using Euclidean distance.
        
        Args:
            unknown_embedding (np.ndarray): The 128D embedding of the face to identify.
            threshold (float): The distance threshold for a match.
            
        Returns:
            str: The name of the celebrity if found, otherwise None.
        """
        if self.embeddings_matrix is None or unknown_embedding is None:
            return None

        # Ensure unknown_embedding is the correct shape for broadcasting
        # Calculate Euclidean distance: sqrt(sum((x - y)^2))
        # axis=1 to calculate distance for each row in the matrix
        distances = np.linalg.norm(self.embeddings_matrix - unknown_embedding, axis=1)
        
        min_distance_idx = np.argmin(distances)
        min_distance = distances[min_distance_idx]

        logger.debug(f"Closest match: {self.names[min_distance_idx]} with distance: {min_distance}")

        if min_distance < threshold:
            return self.names[min_distance_idx]
        else:
            return None
