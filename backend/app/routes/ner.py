from app.database.ner import add_nerdata, extract_ner, compare_ner
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

class QueryPayload(BaseModel):
    query: str

@router.post("/api", tags=["ner"])
async def get_images(payload: QueryPayload):
    print("hello")
    try:
        text = payload.query

        add_nerdata(text)
        it = extract_ner(text)
        pythonic_comeback = compare_ner(it)
        

        return pythonic_comeback

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})




    