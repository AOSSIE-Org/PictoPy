from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from app.facenet.facenet import FaceNet
from app.facecluster.facecluster import FaceCluster
from app.utils.path_id_mapping import get_id_from_path
from app.database.faces import store_face_embedding

logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(
        self,
        face_net: Optional[FaceNet] = None,
        face_cluster: Optional[FaceCluster] = None,
        max_workers: int = 4
    ):
        self.face_net = face_net or FaceNet()
        self.face_cluster = face_cluster or FaceCluster()
        self.max_workers = max_workers
        self.processing_lock = Lock()
        
    def process_images(self, image_paths: List[Path]) -> Dict[int, List[str]]:
        """
        Process multiple images in parallel and update clusters.
        
        Args:
            image_paths: List of paths to images to process
            
        Returns:
            Updated clustering results
        """
        logger.info(f"Starting batch processing of {len(image_paths)} images")
        
        embeddings_batch = []
        valid_paths = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all image processing tasks
            future_to_path = {
                executor.submit(self._process_single_image, path): path 
                for path in image_paths
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    embeddings = future.result()
                    if embeddings is not None and len(embeddings) > 0:
                        embeddings_batch.extend(embeddings)
                        valid_paths.extend([path] * len(embeddings))
                except Exception as e:
                    logger.error(f"Error processing image {path}: {str(e)}")
                    continue
        
        # Process all collected embeddings
        with self.processing_lock:
            return self._update_clusters(embeddings_batch, valid_paths)
    
    def _process_single_image(self, image_path: Path) -> Optional[List[np.ndarray]]:
        """
        Process a single image to extract face embeddings.
        
        Args:
            image_path: Path to the image
            
        Returns:
            List of face embeddings if faces found, None otherwise
        """
        try:
            # Detect faces and generate embeddings
            faces = self.face_net.detect_faces(str(image_path))
            if not faces:
                return None
                
            embeddings = []
            for face in faces:
                embedding = self.face_net.generate_embedding(face)
                if embedding is not None:
                    embeddings.append(embedding)
                    # Store embedding in database
                    store_face_embedding(str(image_path), embedding)
                    
            return embeddings
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return None
            
    def _update_clusters(
        self,
        embeddings_batch: List[np.ndarray],
        image_paths: List[Path]
    ) -> Dict[int, List[str]]:
        """
        Update clusters with new embeddings.
        
        Args:
            embeddings_batch: List of face embeddings
            image_paths: Corresponding image paths
            
        Returns:
            Updated clustering results
        """
        if not embeddings_batch:
            return self.face_cluster.get_clusters()
            
        # Convert paths to IDs
        image_ids = [get_id_from_path(str(path)) for path in image_paths]
        
        # Add all embeddings to the cluster manager
        for embedding, image_id in zip(embeddings_batch, image_ids):
            self.face_cluster.add_face(embedding, image_id)
            
        # Force reclustering after batch
        return self.face_cluster.force_recluster()