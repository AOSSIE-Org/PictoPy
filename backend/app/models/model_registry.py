from __future__ import annotations

from typing import TypedDict, Literal
import os
import sys
from platformdirs import user_data_dir

FeatureType = Literal[
    "object_detection",
    "face_detection",
    "face_embedding",
    "semantic_vision",
    "semantic_text",
]
TierType = Literal["nano", "small", "medium", "required", "manual"]


class ModelSpec(TypedDict):
    filename: str
    url: str
    sha256: str
    size_mb: float
    feature: FeatureType
    tier: TierType


MODEL_REGISTRY: dict[str, ModelSpec] = {
    "yolo_nano": ModelSpec(
        filename="YOLOv11_Nano.onnx",
        url="https://github.com/AOSSIE-Org/PictoPy/releases/download/models-v1.0/YOLOv11_Nano.onnx",
        sha256="64e0a360a854cd1cebf697e38967adb73f24a2c41a86379f8a0bfae1b0c6af0b",
        size_mb=10.2,
        feature="object_detection",
        tier="nano",
    ),
    "yolo_nano_face": ModelSpec(
        filename="YOLOv11_Nano_Face.onnx",
        url="https://github.com/AOSSIE-Org/PictoPy/releases/download/models-v1.0/YOLOv11_Nano_Face.onnx",
        sha256="1d09cb0f31d46700a3e80838623aeafa125f2cd0d1c9a12f0b0853bf64b0a83d",
        size_mb=10.1,
        feature="face_detection",
        tier="nano",
    ),
    "yolo_small": ModelSpec(
        filename="YOLOv11_Small.onnx",
        url="https://github.com/AOSSIE-Org/PictoPy/releases/download/models-v1.0/YOLOv11_Small.onnx",
        sha256="8bfa953dbe93bef33b09be00da01cb4727f25416cb5d2fdb2a9f1083283b8aaa",
        size_mb=36.2,
        feature="object_detection",
        tier="small",
    ),
    "yolo_small_face": ModelSpec(
        filename="YOLOv11_Small_Face.onnx",
        url="https://github.com/AOSSIE-Org/PictoPy/releases/download/models-v1.0/YOLOv11_Small_Face.onnx",
        sha256="213333bbecd049c8e1d8bc63b4799df08d2ec52c8f8a6737b37b75ba839d7c03",
        size_mb=36.1,
        feature="face_detection",
        tier="small",
    ),
    "yolo_medium": ModelSpec(
        filename="YOLOv11_Medium.onnx",
        url="https://github.com/AOSSIE-Org/PictoPy/releases/download/models-v1.0/YOLOv11_Medium.onnx",
        sha256="f53a0bf6a141788f329ab92b438045f0ebac73ff10285b9ef0d06551cdbd01ea",
        size_mb=76.9,
        feature="object_detection",
        tier="medium",
    ),
    "yolo_medium_face": ModelSpec(
        filename="YOLOv11_Medium_Face.onnx",
        url="https://github.com/AOSSIE-Org/PictoPy/releases/download/models-v1.0/YOLOv11_Medium_Face.onnx",
        sha256="fd3ab085d776ee1ce59fd47def82c2abf49bbfde3a10a1b5b660b76cb41a6912",
        size_mb=76.6,
        feature="face_detection",
        tier="medium",
    ),
    "facenet": ModelSpec(
        filename="FaceNet_128D.onnx",
        url="https://github.com/AOSSIE-Org/PictoPy/releases/download/models-v1.0/FaceNet_128D.onnx",
        sha256="c37946ea8cce94141777dcbcccb8a61786c9a7c4f0c9f40471bd27029fa664ed",
        size_mb=87.0,
        feature="face_embedding",
        tier="required",
    ),
    "siglip2_base_vision": ModelSpec(
        filename="SigLIP2_Base_Vision.onnx",
        url="https://github.com/AOSSIE-Org/PictoPy/releases/download/models-v1.0/SigLIP2_Base_Vision.onnx",
        sha256="c5efd0fcbe0e700bd457f2ce4dde5c85b0ea8bb2b2b48948439d1b25c749845d",
        size_mb=355,
        feature="semantic_vision",
        tier="small",
    ),
    "siglip2_base_text": ModelSpec(
        filename="SigLIP2_Base_Text.onnx",
        url="https://github.com/AOSSIE-Org/PictoPy/releases/download/models-v1.0/SigLIP2_Base_Text.onnx",
        sha256="d9d3d199aea7584f215955074afae2aa0f79a618d8eb8b561c5fe6599fc9df35",
        size_mb=1078,
        feature="semantic_text",
        tier="small",
    ),
    "siglip2_large_vision": ModelSpec(
        filename="SigLIP2_Large_Vision.onnx",
        url="PLACEHOLDER_URL",  # TODO
        sha256="PLACEHOLDER_SHA256",  # TODO
        size_mb=0,  # TODO
        feature="semantic_vision",
        tier="medium",
    ),
    "siglip2_large_text": ModelSpec(
        filename="SigLIP2_Large_Text.onnx",
        url="PLACEHOLDER_URL",  # TODO
        sha256="PLACEHOLDER_SHA256",  # TODO
        size_mb=0,  # TODO
        feature="semantic_text",
        tier="medium",
    ),
    "siglip2_so400m_vision": ModelSpec(
        filename="SigLIP2_SO400M_Vision.onnx",
        url="PLACEHOLDER_URL",  # TODO
        sha256="PLACEHOLDER_SHA256",  # TODO
        size_mb=0,  # TODO
        feature="semantic_vision",
        tier="manual",
    ),
    "siglip2_so400m_text": ModelSpec(
        filename="SigLIP2_SO400M_Text.onnx",
        url="PLACEHOLDER_URL",  # TODO
        sha256="PLACEHOLDER_SHA256",  # TODO
        size_mb=0,  # TODO
        feature="semantic_text",
        tier="manual",
    ),
}

TIER_MODELS: dict[str, list[str]] = {
    "nano": ["yolo_nano", "yolo_nano_face"],
    "small": ["yolo_small", "yolo_small_face"],
    "medium": ["yolo_medium", "yolo_medium_face"],
    "required": ["facenet"],  # Required model; not user-selectable
    "manual": [],
}

USER_DATA_MODELS = os.path.join(user_data_dir("PictoPy"), "models")
LOCAL_ONNX_EXPORTS = os.path.join(os.path.dirname(__file__), "ONNX_Exports")


def ensure_model_exports_directory() -> None:
    """Create the active model exports directory if it does not exist."""
    if getattr(sys, "frozen", False):
        os.makedirs(USER_DATA_MODELS, exist_ok=True)
    else:
        os.makedirs(LOCAL_ONNX_EXPORTS, exist_ok=True)


def get_model_path(key: str) -> str:
    filename = MODEL_REGISTRY[key]["filename"]
    ensure_model_exports_directory()

    # In production (compiled by PyInstaller), use the platform-appropriate user data directory.
    if getattr(sys, "frozen", False):
        return os.path.normpath(os.path.join(USER_DATA_MODELS, filename))

    # In development, strictly use the local repo folder
    return os.path.normpath(os.path.join(LOCAL_ONNX_EXPORTS, filename))


def get_model_key_from_path(model_path: str) -> str | None:
    target_filename = os.path.basename(os.path.normpath(model_path)).lower()
    for key, spec in MODEL_REGISTRY.items():
        if spec["filename"].lower() == target_filename:
            return key
    return None
