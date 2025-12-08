import os
import requests
from tqdm import tqdm
import sys

# Constants
MODEL_URL = "https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx"
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "app", "models", "onnx_models")
MODEL_PATH = os.path.join(MODEL_DIR, "lama_fp32.onnx")

def download_file(url, filename):
    """
    Download a file from a URL to a local filename with a progress bar.
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024 # 1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    
    with open(filename, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
    
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")
        return False
    return True

def main():
    if not os.path.exists(MODEL_DIR):
        print(f"Creating directory: {MODEL_DIR}")
        os.makedirs(MODEL_DIR, exist_ok=True)
        
    if os.path.exists(MODEL_PATH):
        print(f"Model already exists at: {MODEL_PATH}")
        # Optional: check hash or size to verify integrity? 
        # For now, assume if it exists, it's good.
        return

    print(f"Downloading LaMa ONNX model from {MODEL_URL}...")
    try:
        success = download_file(MODEL_URL, MODEL_PATH)
        if success:
            print("Download completed successfully!")
        else:
            print("Download failed.")
            if os.path.exists(MODEL_PATH):
                os.remove(MODEL_PATH)
            sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        if os.path.exists(MODEL_PATH):
             os.remove(MODEL_PATH)
        sys.exit(1)

if __name__ == "__main__":
    main()
