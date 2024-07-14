from fastapi import APIRouter

from app.facenet.facenet import get_face_embedding
from app.facenet.preprocess import cosine_similarity


router = APIRouter()

@router.post("/match")
def face_matching(payload: dict):
    image_paths = payload['paths']
    #  image_paths = get_all_image_paths_from_db()
    embeddings = []
    for path in image_paths:
        embedding = get_face_embedding(path)
        embeddings.append(embedding)

    for i, e1 in enumerate(embeddings):
        for j, e2 in enumerate(embeddings):
            similarrity = cosine_similarity(e1, e2)
            if i >= j or similarrity < 0.5: continue
            img1 = image_paths[i].split("/")[-1]
            img2 = image_paths[j].split("/")[-1]
            print(img1, img2)



