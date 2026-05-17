import base64
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.compress import (
    InvalidImageError,
    QualityPreset,
    ResolutionPreset,
    UnsupportedImageError,
    compress_image as compress_image_core,
)
from app.db import save_compressed_image

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
READ_CHUNK_SIZE = 1024 * 1024


@router.post("/compress")
async def compress_image(
    file: UploadFile = File(...),
    resolution: ResolutionPreset = Form("original"),
    quality: QualityPreset = Form("medium"),
):
    request_object_content = await _read_limited_upload(file)
    file_name = file.filename or "image"

    try:
        response_data = compress_image_core(
            image_bytes=request_object_content,
            file_name=file_name,
            resolution=resolution,
            quality=quality,
        )

        saved_data = compress_image_core(
            image_bytes=request_object_content,
            file_name=file_name,
            resolution="small",
            quality="low",
        )
        _save_result_to_db(file_name, saved_data)

        return response_data
    except (InvalidImageError, UnsupportedImageError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Image compression failed")
        raise HTTPException(status_code=500, detail="処理エラーが発生しました。") from exc


async def _read_limited_upload(file: UploadFile) -> bytes:
    chunks = []
    total_size = 0

    while True:
        chunk = await file.read(READ_CHUNK_SIZE)
        if not chunk:
            break

        total_size += len(chunk)
        if total_size > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="ファイルサイズは20MB以下にしてください。",
            )

        chunks.append(chunk)

    return b"".join(chunks)


def _save_result_to_db(original_file_name: str, result: dict) -> None:
    image_blob = base64.b64decode(result["imageBase64"])
    after = result["after"]
    compression = result["compression"]

    save_compressed_image(
        original_file_name=original_file_name,
        stored_file_name=result["downloadFileName"],
        mime_type=result["mimeType"],
        image_format=after["format"],
        width=after["width"],
        height=after["height"],
        mode=after["mode"],
        original_bytes=compression["originalBytes"],
        saved_bytes=compression["compressedBytes"],
        reduction_rate=compression["reductionRate"],
        image_blob=image_blob,
    )
