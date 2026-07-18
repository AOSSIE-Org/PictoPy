from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from app.database.images import db_get_all_images
from app.schemas.images import ErrorResponse
from app.utils.images import image_util_parse_metadata
from pydantic import BaseModel
from app.database.images import (
    db_toggle_image_favourite_status,
    db_get_image_by_id,
    db_search_images_by_tag,
)
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)
router = APIRouter()


# Response Models
class MetadataModel(BaseModel):
    name: str
    date_created: Optional[str]
    width: int
    height: int
    file_location: str
    file_size: int
    item_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None


class ImageData(BaseModel):
    id: str
    path: str
    folder_id: str
    thumbnailPath: str
    metadata: MetadataModel
    isTagged: bool
    isFavourite: bool
    tags: Optional[List[str]] = None


class GetAllImagesResponse(BaseModel):
    success: bool
    message: str
    data: List[ImageData]


class SemanticSearchImage(ImageData):
    score: float


class SemanticSearchData(BaseModel):
    images: List[SemanticSearchImage]
    total: int


class SemanticSearchResponse(BaseModel):
    success: bool
    message: str
    data: SemanticSearchData


@router.get(
    "/",
    response_model=GetAllImagesResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_all_images(
    tagged: Optional[bool] = Query(None, description="Filter images by tagged status")
):
    """Get all images from the database."""
    try:
        # Get all images with tags from database (single query with optional filter)
        images = db_get_all_images(tagged=tagged)

        # Convert to response format
        image_data = [
            ImageData(
                id=image["id"],
                path=image["path"],
                folder_id=image["folder_id"],
                thumbnailPath=image["thumbnailPath"],
                metadata=image_util_parse_metadata(image["metadata"]),
                isTagged=image["isTagged"],
                isFavourite=image.get("isFavourite", False),
                tags=image["tags"],
            )
            for image in images
        ]

        return GetAllImagesResponse(
            success=True,
            message=f"Successfully retrieved {len(image_data)} images",
            data=image_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve images: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/search",
    response_model=GetAllImagesResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 404, 500]},
)
def search_images_by_tag(tag: str = Query(..., description="Tag name to search for")):
    """Search images by tag name."""
    try:
        images = db_search_images_by_tag(tag)

        image_data = [
            ImageData(
                id=image["id"],
                path=image["path"],
                folder_id=image["folder_id"],
                thumbnailPath=image["thumbnailPath"],
                metadata=image_util_parse_metadata(image["metadata"]),
                isTagged=image["isTagged"],
                isFavourite=image.get("isFavourite", False),
                tags=image["tags"],
            )
            for image in images
        ]

        return GetAllImagesResponse(
            success=True,
            message=f"Successfully retrieved {len(image_data)} images for tag '{tag}'",
            data=image_data,
        )

    except Exception as e:
        logger.error(f"Error searching images: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message="Unable to search images due to an internal error",
            ).model_dump(),
        )


@router.get(
    "/semantic-search",
    response_model=SemanticSearchResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 404, 500]},
)
def semantic_search_images(
    query: str = Query(..., min_length=1, description="Query text to search for")
):
    """Semantic search images by query text using SigLIP2."""
    try:
        from app.config.settings import (
            SIGLIP2_ACTIVE_CHECKPOINT,
            SIGLIP2_SCORING_METADATA,
            SIGLIP2_MATCH_THRESHOLD,
            SIGLIP2_QUERY_TEMPLATE,
        )
        from app.models.model_registry import (
            get_siglip2_registry_keys,
            get_siglip2_tokenizer_key,
            get_model_path,
        )
        import os
        import numpy as np

        vision_key, text_key = get_siglip2_registry_keys(SIGLIP2_ACTIVE_CHECKPOINT)
        tokenizer_key = get_siglip2_tokenizer_key(SIGLIP2_ACTIVE_CHECKPOINT)

        text_model_path = get_model_path(text_key)
        tokenizer_model_path = get_model_path(tokenizer_key)

        if not os.path.exists(text_model_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Not Found",
                    message="semantic search unavailable: SigLIP2 text model not installed",
                ).model_dump(),
            )

        if not os.path.exists(tokenizer_model_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Not Found",
                    message="semantic search unavailable: SigLIP2 tokenizer not installed",
                ).model_dump(),
            )

        metadata = SIGLIP2_SCORING_METADATA[SIGLIP2_ACTIVE_CHECKPOINT]
        model_version = metadata["model_version"]
        logit_scale = metadata["logit_scale"]
        logit_bias = metadata["logit_bias"]

        from app.database.image_embeddings import db_get_all_embeddings

        image_ids, matrix = db_get_all_embeddings(model_version)

        if not image_ids:
            return SemanticSearchResponse(
                success=True,
                message="No images have been embedded yet.",
                data=SemanticSearchData(images=[], total=0),
            )

        from app.utils.SigLIP import siglip_util_tokenize_query

        normalized = query.strip().lower()
        if not normalized:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Bad Request",
                    message="Query cannot be empty",
                ).model_dump(),
            )

        # tokenizer is case-sensitive; lowercase matches the calibration-validated regime.
        # calibration parity with validated scoring
        templated = SIGLIP2_QUERY_TEMPLATE.format(query=normalized)
        input_ids, attention_mask = siglip_util_tokenize_query(templated)

        from app.utils.SigLIP import siglip_util_get_text_model

        # Cached across requests -- the ~1GB text tower is expensive to
        # reload on every call. See siglip_util_get_text_model/
        # siglip_util_invalidate_text_model for the uninstall interaction.
        text_model = siglip_util_get_text_model(text_model_path, text_key)
        text_vec = text_model.get_embedding(input_ids, attention_mask)
        # Flatten to 1D vector. (Report shows what shape the method actually returns below)
        text_vec = np.array(text_vec, dtype=np.float32).flatten()

        # scores = 1/(1+np.exp(-(matrix @ text_vec * np.exp(logit_scale) + logit_bias)))
        dot_products = matrix @ text_vec
        scaled_logits = dot_products * np.exp(logit_scale) + logit_bias
        scores = 1 / (1 + np.exp(-scaled_logits))

        match_threshold = SIGLIP2_MATCH_THRESHOLD

        # Keep (id, score) pairs where score >= SIGLIP2_MATCH_THRESHOLD
        matched_pairs = []
        for i, img_id in enumerate(image_ids):
            score = float(scores[i])
            if score >= match_threshold:
                matched_pairs.append((img_id, score))

        # Sort desc by score
        matched_pairs.sort(key=lambda x: x[1], reverse=True)

        if not matched_pairs:
            return SemanticSearchResponse(
                success=True,
                message=f"No matches found with score >= {match_threshold}.",
                data=SemanticSearchData(images=[], total=0),
            )

        matched_ids = [pair[0] for pair in matched_pairs]
        score_lookup = {pair[0]: pair[1] for pair in matched_pairs}

        from app.database.images import db_get_images_by_ids

        db_images = db_get_images_by_ids(matched_ids)

        semantic_images = []
        for img in db_images:
            img_id = img["id"]
            # Round score to 4 decimals
            score = round(score_lookup[img_id], 4)
            semantic_images.append(
                SemanticSearchImage(
                    id=img_id,
                    path=img["path"],
                    folder_id=img["folder_id"],
                    thumbnailPath=img["thumbnailPath"],
                    metadata=image_util_parse_metadata(img["metadata"]),
                    isTagged=img["isTagged"],
                    isFavourite=img.get("isFavourite", False),
                    tags=img["tags"],
                    score=score,
                )
            )

        return SemanticSearchResponse(
            success=True,
            message=f"Found {len(semantic_images)} image(s) matching the query.",
            data=SemanticSearchData(images=semantic_images, total=len(semantic_images)),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Semantic search failed: {str(e)}",
            ).model_dump(),
        )


# adding add to favourite and remove from favourite routes


class ToggleFavouriteRequest(BaseModel):
    image_id: str


@router.post("/toggle-favourite")
def toggle_favourite(req: ToggleFavouriteRequest):
    """
    Toggle the favorite status of an image.
    """
    image_id = req.image_id
    try:
        success = db_toggle_image_favourite_status(image_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found or failed to toggle",
            )
        # Fetch updated status to return
        image = db_get_image_by_id(image_id)
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found after toggle",
            )
        return {
            "success": True,
            "image_id": image_id,
            "isFavourite": image.get("isFavourite", False),
        }
    except HTTPException:
        raise  # Re-raise HTTPExceptions to preserve status codes
    except Exception as e:
        logger.error(f"error in /toggle-favourite route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


class ImageInfoResponse(BaseModel):
    id: str
    path: str
    folder_id: str
    thumbnailPath: str
    metadata: MetadataModel
    isTagged: bool
    isFavourite: bool
    tags: Optional[List[str]] = None
