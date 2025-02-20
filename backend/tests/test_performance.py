import time
from pathlib import Path
import numpy as np
import logging
import psutil
import os
from app.database.faces import batch_insert_face_embeddings, insert_face_embeddings

# Set up logging with more visible formatting
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='\n%(message)s\n'  # Simplified format for better readability
)

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def test_embedding_insertion_performance():
    """Compare performance of batch vs single insertions"""
    initial_memory = get_memory_usage()
    
    # Test configuration
    test_config = {
        "num_images": 100,
        "embeddings_per_image": 5,
        "embedding_size": 128,
        "batch_size": 1000
    }
    
    # Test data setup
    test_data = [
        (f"test_image_{i}.jpg", [
            np.random.rand(test_config["embedding_size"]).astype(np.float32)
            for _ in range(test_config["embeddings_per_image"])]
        )
        for i in range(test_config["num_images"])
    ]
    
    results = {}
    
    # Test single insertions
    print("\n🔄 Running single insertion tests...")
    start_time = time.perf_counter()
    for image_path, embeddings in test_data:
        insert_face_embeddings(image_path, embeddings)
    results["single_insert_time"] = time.perf_counter() - start_time
    
    # Test batch insertions
    print("🔄 Running batch insertion tests...")
    start_time = time.perf_counter()
    batch_insert_face_embeddings(test_data)
    results["batch_insert_time"] = time.perf_counter() - start_time
    
    # Calculate metrics
    results["improvement"] = (
        (results["single_insert_time"] - results["batch_insert_time"]) 
        / results["single_insert_time"] * 100
    )
    
    final_memory = get_memory_usage()
    memory_diff = final_memory - initial_memory
    
    # Print detailed results
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                    PERFORMANCE TEST RESULTS                     ║
╠════════════════════════════════════════════════════════════════╣
║ Configuration:                                                 ║
║ • Images: {test_config["num_images"]:,}                                              ║
║ • Embeddings per image: {test_config["embeddings_per_image"]}                                    ║
║ • Embedding size: {test_config["embedding_size"]}                                        ║
║ • Batch size: {test_config["batch_size"]:,}                                          ║
╟────────────────────────────────────────────────────────────────╢
║ Timing Results:                                               ║
║ • Single insertion: {results["single_insert_time"]:.2f}s                                   ║
║ • Batch insertion: {results["batch_insert_time"]:.2f}s                                    ║
╟────────────────────────────────────────────────────────────────╢
║ Performance Improvement:                                      ║
║ • Improvement: {results["improvement"]:.1f}%                                          ║
╟────────────────────────────────────────────────────────────────╢
║ Memory Usage:                                                 ║
║ • Initial: {initial_memory:.2f} MB                                           ║
║ • Final: {final_memory:.2f} MB                                             ║
║ • Difference: {memory_diff:.2f} MB                                        ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Add summary section
    print("\n" + "-" * 80)
    print("PERFORMANCE TEST SUMMARY")
    print("-" * 80)
    print(f"""
    🚀 Overall Results:
    ==================
    ✅ Performance Improvement: {results["improvement"]:.1f}%
    ⚡ Speed-up Factor: {results["single_insert_time"] / results["batch_insert_time"]:.1f}x
    
    📊 Timing Details:
    ================
    • Single Mode: {results["single_insert_time"]:.2f}s
    • Batch Mode: {results["batch_insert_time"]:.2f}s
    
    💾 Memory Impact:
    ===============
    • Start: {initial_memory:.1f} MB
    • End: {final_memory:.1f} MB
    • Delta: {memory_diff:.1f} MB ({(memory_diff/initial_memory)*100:.1f}% change)
    """)
    print("-" * 80)
    
    # Assertions
    assert results["improvement"] > 0, "Batch processing should be faster than single insertions"
    assert results["batch_insert_time"] < results["single_insert_time"], (
        "Batch time should be less than single insert time"
    )