from fastapi import APIRouter, Query, HTTPException, status
from typing import Dict, Any, List
from app.database.faces import get_all_face_embeddings
from app.database.images import get_path_from_id
from app.facecluster.init_face_cluster import get_face_cluster
from app.facenet.preprocess import cosine_similarity
from app.utils.path_id_mapping import get_id_from_path
from app.utils.wrappers import exception_handler_wrapper
from app.schemas.facetagging import (
    SimilarPair,
    ErrorResponse,
    FaceMatchingResponse,
    FaceClustersResponse,
    GetRelatedImagesResponse,
)

# Annotate webcam_locks; adjust key/value types as needed.
webcam_locks: Dict[Any, Any] = {}

router = APIRouter()


@router.get(
    "/match",
    response_model=FaceMatchingResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
@exception_handler_wrapper
def face_matching() -> FaceMatchingResponse:
    try:
        all_embeddings = get_all_face_embeddings()
        similar_pairs: List[SimilarPair] = []

        for i, img1_data in enumerate(all_embeddings):
            for j, img2_data in enumerate(all_embeddings):
                if i >= j:
                    continue

                for embedding1 in img1_data["embeddings"]:
                    for embedding2 in img2_data["embeddings"]:
                        similarity = cosine_similarity(embedding1, embedding2)
                        if similarity >= 0.7:
                            # Get file names from the image paths
                            img1_filename = img1_data["image_path"].split("/")[-1]
                            img2_filename = img2_data["image_path"].split("/")[-1]
                            similar_pairs.append(
                                SimilarPair(
                                    image1=img1_filename,
                                    image2=img2_filename,
                                    similarity=float(similarity),
                                )
                            )
                            # Break out after first match for these embeddings
                            break
                    else:
                        continue
                    break

        return FaceMatchingResponse(
            success=True,
            message="Successfully matched face embeddings",
            similar_pairs=similar_pairs,
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message="Unable to get face embedding",
            ),
        )


@router.get(
    "/clusters",
    response_model=FaceClustersResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
@exception_handler_wrapper
def face_clusters() -> FaceClustersResponse:
    try:
        cluster = get_face_cluster()
        raw_clusters = cluster.get_clusters()

        # Convert image IDs to paths while filtering out any None values.
        formatted_clusters: Dict[int, List[str]] = {
            int(cluster_id): [
                p
                for p in (get_path_from_id(int(image_id)) for image_id in image_ids)
                if p is not None
            ]
            for cluster_id, image_ids in raw_clusters.items()
        }

        return FaceClustersResponse(
            success=True,
            message="Successfully retrieved face clusters",
            clusters=formatted_clusters,
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message="Unable to get face clusters",
            ).model_dump(),
        )


@router.get(
    "/related-images",
    response_model=GetRelatedImagesResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
@exception_handler_wrapper
def get_related_images(
    path: str = Query(..., description="full path to the image")
) -> GetRelatedImagesResponse:
    try:
        cluster = get_face_cluster()
        image_id = get_id_from_path(path)
        if image_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Invalid image path",
                    message=f"Image path '{path}' is not valid",
                ).model_dump(),
            )
        related_image_ids = cluster.get_related_images(image_id)
        # Use a list comprehension with a walrus operator to filter out None values.
        related_image_paths: List[str] = [
            p
            for _id in related_image_ids
            if (p := get_path_from_id(int(_id))) is not None
        ]

        return GetRelatedImagesResponse(
            success=True,
            message=f"Successfully retrieved related images for {path}",
            data={"related_images": related_image_paths},  # Wrapped inside "data"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message="Uanble to get related images",
            ).model_dump(),
        )
