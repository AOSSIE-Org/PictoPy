from __future__ import annotations

import shutil
import subprocess
import platform

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


def detect_apple_silicon() -> str | None:
    if platform.system() != "Darwin":
        return None
    if platform.machine() != "arm64":
        return None

    sysctl = shutil.which("sysctl")
    if sysctl:
        try:
            result = subprocess.run(
                [sysctl, "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            chip_name = result.stdout.strip()
            if chip_name:
                return chip_name
        except (OSError, subprocess.SubprocessError):
            pass

    proc = platform.processor()
    if proc:
        return proc

    return "Apple Silicon"


def detect_apple_silicon_tier() -> str | None:
    chip = detect_apple_silicon()
    if chip is None:
        return None

    chip_lower = chip.lower()

    # Base M1 and M2 chips (without Pro/Max/Ultra modifiers) are "small"
    if any(base in chip_lower for base in ["m1", "m2"]):
        if not any(mod in chip_lower for mod in ["pro", "max", "ultra"]):
            return "small"

    # Default to medium for all other Apple Silicon (Pro/Max/Ultra, M3+, and future chips)
    return "medium"


def detect_hardware_tier() -> str:
    """
    Detect system hardware to recommend the best YOLO/FaceNet model tier.
    Returns: 'nano', 'small', or 'medium'
    """
    apple_tier = detect_apple_silicon_tier()
    if apple_tier is not None:
        return apple_tier

    # Check RAM in GB
    ram_gb = psutil.virtual_memory().total / (1024**3)

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
        "apple_silicon": detect_apple_silicon(),
        "available_providers": ort.get_available_providers(),
        "recommended_tier": detect_hardware_tier(),
    }
