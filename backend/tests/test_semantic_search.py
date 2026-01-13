import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Mock sentence_transformers before importing app modules that depend on it
sys.modules['sentence_transformers'] = MagicMock()

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.semantic_search import search_images, generate_text_embedding

class TestSemanticSearch(unittest.TestCase):
    
    @patch('app.utils.semantic_search.get_model')
    def test_generate_text_embedding(self, mock_get_model):
        # Mock the model behavior
        mock_model_instance = MagicMock()
        mock_model_instance.encode.return_value = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        mock_get_model.return_value = mock_model_instance
        
        embedding = generate_text_embedding("test query")
        self.assertTrue(isinstance(embedding, np.ndarray))
        self.assertEqual(len(embedding), 3)
        mock_model_instance.encode.assert_called_with("test query")

    @patch('app.utils.semantic_search.generate_text_embedding')
    def test_search_images(self, mock_gen_embedding):
        # Setup mock embedding for query
        query_vec = np.array([1.0, 0.0], dtype=np.float32)
        mock_gen_embedding.return_value = query_vec
        
        # Setup mock embeddings for images
        # Image A: [1.0, 0.0] -> Perfect match (score 1.0)
        # Image B: [0.0, 1.0] -> Orthogonal (score 0.0)
        # Image C: [-1.0, 0.0] -> Opposite (score -1.0)
        embeddings_dict = {
            "img_a": np.array([1.0, 0.0], dtype=np.float32),
            "img_b": np.array([0.0, 1.0], dtype=np.float32),
            "img_c": np.array([-1.0, 0.0], dtype=np.float32)
        }
        
        results = search_images("query", embeddings_dict, limit=3)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['image_id'], "img_a")
        self.assertAlmostEqual(results[0]['score'], 1.0, places=5)
        
        self.assertEqual(results[1]['image_id'], "img_b")
        self.assertAlmostEqual(results[1]['score'], 0.0, places=5)

if __name__ == '__main__':
    unittest.main()
