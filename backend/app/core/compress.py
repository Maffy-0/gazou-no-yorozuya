# JPEG変換

from PIL import Image
import io

def compress_jpeg(image_bytes: bytes, quality: int = 50) -> io.BytesIO:
    """
    バイナリデータを受け取り、指定された品質でJPEG圧縮してBytesIOで返す
    """
    img = Image.open(io.BytesIO(image_bytes))
    
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
        
    img_io = io.BytesIO()
    img.save(img_io, format="JPEG", quality=quality)
    img_io.seek(0)
    
    return img_io