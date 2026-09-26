# Template: `backend/app/routes/<resource>.py`

Copy and adapt. Modelled on `backend/app/routes/videos.py`.

```python
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from app.database.<resource> import (
    db_get_all_<resource>,
)
from app.schemas.<resource> import ErrorResponse
from app.logging.setup_logging import get_logger

# Initialize logger
logger = get_logger(__name__)
router = APIRouter()


# Response Models
class <Resource>Data(BaseModel):
    id: str
    name: str
    created_at: Optional[str] = None


class GetAll<Resource>Response(BaseModel):
    success: bool
    message: str
    data: List[<Resource>Data]


@router.get(
    "/",
    response_model=GetAll<Resource>Response,
    responses={500: {"model": ErrorResponse}},
)
def get_all_<resource>():
    """Get all <resource> from the database."""
    try:
        rows = db_get_all_<resource>()

        # Build per row: one bad record shouldn't 500 the whole listing and
        # hide every other item.
        data = []
        for row in rows:
            try:
                data.append(
                    <Resource>Data(
                        id=row["id"],
                        name=row["name"],
                        created_at=row.get("created_at"),
                    )
                )
            except Exception as e:
                logger.warning(f"Skipping malformed <resource> row {row.get('id')}: {e}")

        return GetAll<Resource>Response(
            success=True,
            message="<Resource> retrieved successfully",
            data=data,
        )
    except Exception as e:
        logger.error(f"Failed to get <resource>: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve <resource>",
        )
```

## Notes

- The logger line and `router = APIRouter()` go together, right after imports.
- Response models live in this file. Only genuinely shared models move to `schemas/`.
- `responses={500: {"model": ErrorResponse}}` goes on every route so the OpenAPI schema
  documents the error contract.
- Do not leak the exception text into the HTTP response — log it, return a generic message.
- Register the router in `backend/main.py` and mirror the paths in
  `frontend/src/api/apiEndpoints.ts`.
