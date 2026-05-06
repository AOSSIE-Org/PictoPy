import shutil
import subprocess

import onnxruntime as ort
import psutil


def detect_physical_gpu() -> list[str]:
    """
    Detect locally installed GPU hardware without relying on ONNX Runtime providers.

    Returns:
        list[str]: Human-readable GPU names detected on the machine.
    """
    gpu_names: list[str] = []

    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return gpu_names

    try:
        result = subprocess.run(
            [nvidia_smi, "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        gpu_names = [
            line.strip() for line in result.stdout.splitlines() if line.strip()
        ]
    except (OSError, subprocess.SubprocessError):
        gpu_names = []

    return gpu_names


def detect_hardware_tier() -> str:
    """
    Detect system hardware to recommend the best YOLO/FaceNet model tier.
    Returns: 'nano', 'small', or 'medium'
    """
    # Check RAM in GB
    ram_gb = psutil.virtual_memory().total / (1024**3)

    # Check for physical GPU hardware directly; this is separate from runtime providers.
    gpu_names = detect_physical_gpu()

    if gpu_names or ram_gb >= 8:
        return "medium"
    elif ram_gb >= 4:
        return "small"
    else:
        return "nano"


def get_hardware_info() -> dict:
    """
    Return detailed hardware information.

    This includes physical hardware detection for recommendations and
    ONNX Runtime provider detection for inference/runtime diagnostics.
    """
    gpu_names = detect_physical_gpu()

    return {
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "gpu_detected": bool(gpu_names),
        "gpu_names": gpu_names,
        "available_providers": ort.get_available_providers(),
        "recommended_tier": detect_hardware_tier(),
    }
