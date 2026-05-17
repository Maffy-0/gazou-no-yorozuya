from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.core.compress import compress_jpeg

router = APIRouter(prefix="/api")

@router.post("/compress")
async def compress_image(
    file: UploadFile = File(...),
    quality: int = Query(50, ge=1, le=100) # フロントから画質設定も受け取れるように拡張
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="画像ファイルではありません。")
        
    try:
        request_object_content = await file.read()
        
        # 🔥 アルゴリズムの処理を丸投げ
        compressed_io = compress_jpeg(request_object_content, quality=quality)
        
        return StreamingResponse(compressed_io, media_type="image/jpeg")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"処理エラー: {str(e)}")