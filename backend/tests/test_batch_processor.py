import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

from app.facenet.batch_processor import BatchProcessor
from app.facenet.facenet import FaceNet
from app.facecluster.facecluster import FaceCluster

@pytest.fixture
def mock_face_net():
    face_net = Mock(spec=FaceNet)
    # Mock detect_faces to return some dummy faces
    face_net.detect_faces.return_value = [np.zeros((160, 160, 3))]
    # Mock generate_embedding to return a dummy embedding
    face_net.generate_embedding.return_value = np.random.rand(512)
    return face_net

@pytest.fixture
def mock_face_cluster():
    face_cluster = Mock(spec=FaceCluster)
    face_cluster.add_face.return_value = {}
    face_cluster.force_recluster.return_value = {0: ["test_image.jpg"]}
    return face_cluster

def test_batch_processor_init():
    processor = BatchProcessor()
    assert processor.max_workers == 4
    assert processor.face_net is not None
    assert processor.face_cluster is not None

def test_process_images(mock_face_net, mock_face_cluster):
    processor = BatchProcessor(
        face_net=mock_face_net,
        face_cluster=mock_face_cluster
    )
    
    # Create test image paths
    image_paths = [Path(f"test_image_{i}.jpg") for i in range(5)]
    
    # Process images
    results = processor.process_images(image_paths)
    
    # Verify face detection was called for each image
    assert mock_face_net.detect_faces.call_count == len(image_paths)
    
    # Verify embedding generation was called for each face
    assert mock_face_net.generate_embedding.call_count == len(image_paths)
    
    # Verify clustering was updated
    assert mock_face_cluster.force_recluster.called
    assert isinstance(results, dict)

def test_process_images_with_errors(mock_face_net, mock_face_cluster):
    processor = BatchProcessor(
        face_net=mock_face_net,
        face_cluster=mock_face_cluster
    )
    
    # Make detect_faces fail for some images
    def mock_detect_faces(path):
        if "error" in str(path):
            raise Exception("Test error")
        return [np.zeros((160, 160, 3))]
    
    mock_face_net.detect_faces.side_effect = mock_detect_faces
    
    # Create test image paths with some error cases
    image_paths = [
        Path("test_image_1.jpg"),
        Path("error_image.jpg"),
        Path("test_image_2.jpg")
    ]
    
    # Process images
    results = processor.process_images(image_paths)
    
    # Verify processing continues despite errors
    assert isinstance(results, dict)
    assert mock_face_net.detect_faces.call_count == len(image_paths)