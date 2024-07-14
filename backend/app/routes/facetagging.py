from fastapi import APIRouter, HTTPException
from app.database.faces import get_all_face_embeddings
from app.facenet.preprocess import cosine_similarity

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
                
                for embedding1 in img1_data['embeddings']:
                    for embedding2 in img2_data['embeddings']:
                        similarity = cosine_similarity(embedding1, embedding2)
                        if similarity >= 0.5:
                            img1 = img1_data['image_path'].split("/")[-1]
                            img2 = img2_data['image_path'].split("/")[-1]
                            similar_pairs.append({
                                'image1': img1,
                                'image2': img2,
                                'similarity': float(similarity)
                            })
                            break
                    else:
                        continue
                    break
        
        return {"similar_pairs": similar_pairs}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
