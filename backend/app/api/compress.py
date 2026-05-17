from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.compress import (
    InvalidImageError,
    QualityPreset,
    ResolutionPreset,
    UnsupportedImageError,
    compress_image as compress_image_core,
)

router = APIRouter(prefix="/api")


@router.post("/compress")
async def compress_image(
    file: UploadFile = File(...),
    resolution: ResolutionPreset = Form("original"),
    quality: QualityPreset = Form("medium"),
):
    request_object_content = await file.read()

    try:
        return compress_image_core(
            image_bytes=request_object_content,
            file_name=file.filename or "image",
            resolution=resolution,
            quality=quality,
        )
    except (InvalidImageError, UnsupportedImageError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"処理エラー: {str(exc)}") from exc
