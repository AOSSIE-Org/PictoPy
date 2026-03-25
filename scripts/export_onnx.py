pip install torch onnx onnxruntime ultralytics numpy


import time
import torch
import numpy as np
import onnxruntime as ort
from ultralytics import YOLO


def export_model():
    """
    Export YOLOv8n model to ONNX
    """

    model = YOLO("yolov8n.pt")

    model.export(format="onnx", opset=12)

    print("✅ Model exported to ONNX")


def benchmark_pytorch():
    """
    Benchmark PyTorch inference
    """

    model = YOLO("yolov8n.pt")

    dummy_input = np.random.rand(1, 3, 640, 640).astype(np.float32)

    start = time.time()
    model.predict(dummy_input, verbose=False)
    end = time.time()

    return end - start


def benchmark_onnx():
    """
    Benchmark ONNX inference
    """

    session = ort.InferenceSession("yolov8n.onnx")

    dummy_input = np.random.rand(1, 3, 640, 640).astype(np.float32)

    input_name = session.get_inputs()[0].name

    start = time.time()
    session.run(None, {input_name: dummy_input})
    end = time.time()

    return end - start


if __name__ == "__main__":
    export_model()

    pytorch_time = benchmark_pytorch()
    onnx_time = benchmark_onnx()

    print(f"PyTorch Inference Time: {pytorch_time:.4f} sec")
    print(f"ONNX Inference Time: {onnx_time:.4f} sec")

    speedup = pytorch_time / onnx_time if onnx_time > 0 else 0
    print(f"⚡ Speedup: {speedup:.2f}x")
