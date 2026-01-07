from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
import os
import uuid
import io
from PIL import Image
from app.database.metadata import db_get_metadata, db_update_metadata
from app.schemas.common import ErrorResponse

router = APIRouter()

UPLOAD_DIR = "uploads/avatars"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_avatar(file: UploadFile = File(...)):
    """Upload and set user avatar"""
    try:
        # Validate file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Invalid file type",
                    message="Only PNG, JPG, and JPEG files are allowed"
                ).model_dump()
            )

        # Read and validate file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="File too large",
                    message="File size must be less than 5MB"
                ).model_dump()
            )

        # Generate unique filename
        filename = f"{uuid.uuid4()}{file_ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Process and save image
        try:
            image = Image.open(io.BytesIO(content))
            # Resize to 200x200 for consistency
            image = image.resize((200, 200), Image.Resampling.LANCZOS)
            image.save(filepath, optimize=True, quality=85)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Invalid image",
                    message="Unable to process image file"
                ).model_dump()
            )

        # Update user preferences with new avatar path
        metadata = db_get_metadata() or {}
        user_prefs = metadata.get("user_preferences", {})
        
        # Remove old avatar file if exists
        old_avatar = user_prefs.get("avatar")
        if old_avatar and old_avatar.startswith("/avatars/uploads/"):
            old_path = old_avatar.replace("/avatars/uploads/", f"{UPLOAD_DIR}/")
            if os.path.exists(old_path):
                os.remove(old_path)

        user_prefs["avatar"] = f"/avatars/uploads/{filename}"
        metadata["user_preferences"] = user_prefs
        
        if not db_update_metadata(metadata):
            # Clean up uploaded file on database error
            if os.path.exists(filepath):
                os.remove(filepath)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    success=False,
                    error="Database error",
                    message="Failed to save avatar preference"
                ).model_dump()
            )

        return {
            "success": True,
            "message": "Avatar uploaded successfully",
            "avatar_url": f"/avatars/uploads/{filename}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Failed to upload avatar: {str(e)}"
            ).model_dump()
        )

@router.get("/uploads/{filename}")
async def get_avatar(filename: str):
    """Serve uploaded avatar files"""
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Avatar not found")
    return FileResponse(filepath)