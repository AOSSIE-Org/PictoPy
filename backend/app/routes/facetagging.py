from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.database.faces import get_all_face_embeddings
from app.database.images import get_path_from_id
from app.facecluster.init_face_cluster import get_face_cluster
from app.facenet.preprocess import cosine_similarity
from app.utils.path_id_mapping import get_id_from_path

router = APIRouter()

@router.get("/match")
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
                            img1 = img1_data["image_path"].split("/")[-1]
                            img2 = img2_data["image_path"].split("/")[-1]
                            similar_pairs.append(
                                {
                                    "image1": img1,
                                    "image2": img2,
                                    "similarity": float(similarity),
                                }
                            )
                            break
                    else:
                        continue
                    break

        return JSONResponse(
            status_code=200,
            content={
                "data": {"similar_pairs": similar_pairs},
                "message": "Successfully matched face embeddings",
                "success": True
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )

@router.get("/clusters")
def face_clusters():
    try:
        cluster = get_face_cluster()
        raw_clusters = cluster.get_clusters()

        # Convert image IDs to paths
        formatted_clusters = {}
        for cluster_id, image_ids in raw_clusters.items():
            formatted_clusters[int(cluster_id)] = [
                get_path_from_id(image_id) for image_id in image_ids
            ]

        return JSONResponse(
            status_code=200,
            content={
                "data": {"clusters": formatted_clusters},
                "message": "Successfully retrieved face clusters",
                "success": True
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )

@router.get("/related-images")
def get_related_images(path: str = Query(..., description="full path to the image")):
    try:
        cluster = get_face_cluster()
        image_id = get_id_from_path(path)
        related_image_ids = cluster.get_related_images(image_id)
        related_image_paths = [get_path_from_id(id) for id in related_image_ids]
        
        return JSONResponse(
            status_code=200,
            content={
                "data": {"related_images": related_image_paths},
                "message": f"Successfully retrieved related images for {path}",
                "success": True
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "content": {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e)
                }
            }
        )