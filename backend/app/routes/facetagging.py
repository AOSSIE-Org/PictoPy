from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.database.faces import get_all_face_embeddings
from app.database.images import get_path_from_id
from app.facecluster.init_face_cluster import get_face_cluster
from app.facenet.preprocess import cosine_similarity
from app.utils.path_id_mapping import get_id_from_path
from app.utils.wrappers import exception_handler_wrapper
from app.schemas.facetagging import (
    SimilarPair,ErrorResponse,
    FaceMatchingResponse,
    FaceClustersResponse,
    GetRelatedImagesResponse
)

router = APIRouter()

@router.get("/match",response_model=FaceMatchingResponse)
@exception_handler_wrapper
def face_matching():
    try:
        all_embeddings = get_all_face_embeddings()

        similar_pairs = []

        for i, img1_data in enumerate(all_embeddings):
            for j, img2_data in enumerate(all_embeddings):
                if i >= j:
                    continue

                for embedding1 in img1_data["embeddings"]:
                    for embedding2 in img2_data["embeddings"]:
                        similarity = cosine_similarity(embedding1, embedding2)
                        if similarity >= 0.5:
                            similar_pairs.append(
                                SimilarPair(
                                    image1=img1_data["image_path"].split("/")[-1],
                                    image2=img2_data["image_path"].split("/")[-1],
                                    similarity=float(similarity)
                                )
                            )
                            break
                    else:
                        continue
                    break

        return FaceMatchingResponse(
            success=True,
            message="Successfully matched face embeddings",
            similar_pairs=similar_pairs
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content":ErrorResponse(
                    success=False,
                    error="Internal server error",
                    message=str(e)
                ),
            }
        )

@router.get("/clusters",response_model=FaceClustersResponse)
@exception_handler_wrapper
def face_clusters():
    try:
        cluster = get_face_cluster()
        raw_clusters = cluster.get_clusters()

        # Convert image IDs to paths
        formatted_clusters = {
            int(cluster_id): [get_path_from_id(image_id) for image_id in image_ids]
            for cluster_id, image_ids in raw_clusters.items()
        }
        
        return FaceClustersResponse(
            success=True,
            message="Successfully retrieved face clusters",
            clusters=formatted_clusters
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content" : ErrorResponse(
                    success=False,
                    error="Internal server error",
                    message=str(e)
                ),
            }
        )

@router.get("/related-images",response_model=GetRelatedImagesResponse)
@exception_handler_wrapper
def get_related_images(path: str = Query(..., description="full path to the image")):
    try:
        cluster = get_face_cluster()
        image_id = get_id_from_path(path)
        related_image_ids = cluster.get_related_images(image_id)
        related_image_paths = [get_path_from_id(id) for id in related_image_ids]
        

        return GetRelatedImagesResponse(
            success=True,
            message=f"Successfully retrieved related images for {path}",
            data={"related_images": related_image_paths}  # Wrapped inside "data"
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content":ErrorResponse(
                    success=False,
                    error="Internal server error",
                    message=str(e)
                ),
            }

        )