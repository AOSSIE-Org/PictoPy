import asyncio
import logging

from app.database.metadata import db_get_metadata
from app.models.model_registry import TIER_MODELS
from app.utils.model_downloader import ensure_model

logger = logging.getLogger(__name__)


def _get_preferred_yolo_tier() -> str:
    metadata = db_get_metadata() or {}
    user_preferences = metadata.get("user_preferences") or {}
    tier = user_preferences.get("YOLO_model_size", "small")

    if tier not in TIER_MODELS:
        return "small"

    return tier


async def _ensure_ai_tagging_models_async() -> None:
    tier = _get_preferred_yolo_tier()
    model_keys = list(TIER_MODELS.get(tier, TIER_MODELS["small"]))
    if "facenet" not in model_keys:
        model_keys.append("facenet")

    for model_key in model_keys:
        logger.info("Ensuring AI tagging model is available: %s", model_key)
        await ensure_model(model_key)


def ensure_ai_tagging_models() -> None:
    asyncio.run(_ensure_ai_tagging_models_async())