import base64
import io
import re
import warnings
from pathlib import Path
from typing import Literal

from PIL import Image, UnidentifiedImageError

ResolutionPreset = Literal["original", "medium", "small"]
QualityPreset = Literal["high", "medium", "low"]

SUPPORTED_FORMATS = {
    "JPEG": {"mime_type": "image/jpeg", "extension": ".jpg"},
    "PNG": {"mime_type": "image/png", "extension": ".png"},
    "WEBP": {"mime_type": "image/webp", "extension": ".webp"},
}

QUALITY_VALUES: dict[QualityPreset, int] = {
    "high": 80,
    "medium": 60,
    "low": 40,
}

RESOLUTION_MAX_SIDES: dict[ResolutionPreset, int | None] = {
    "original": None,
    "medium": 1280,
    "small": 640,
}

PNG_COMPRESS_LEVELS: dict[QualityPreset, int] = {
    "high": 6,
    "medium": 8,
    "low": 9,
}

MAX_IMAGE_PIXELS = 40_000_000
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


class UnsupportedImageError(ValueError):
    pass


class InvalidImageError(ValueError):
    pass


def compress_image(
    image_bytes: bytes,
    file_name: str,
    resolution: ResolutionPreset,
    quality: QualityPreset,
) -> dict:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(io.BytesIO(image_bytes))
            image.load()
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise InvalidImageError("画像の解像度が大きすぎます。40MP以下の画像を選択してください。") from exc
    except (OSError, UnidentifiedImageError) as exc:
        raise InvalidImageError("画像ファイルとして読み込めません。") from exc

    image_format = (image.format or "").upper()
    if image_format not in SUPPORTED_FORMATS:
        raise UnsupportedImageError("対応形式は JPEG / PNG / WebP のみです。")

    before = _image_info(
        image=image,
        file_name=file_name,
        image_format=image_format,
        byte_size=len(image_bytes),
    )

    output_image = _resize_image(image, resolution)
    output_image = _normalize_mode(output_image, image_format)

    output_io = io.BytesIO()
    _save_image(output_image, output_io, image_format, quality)
    output_bytes = output_io.getvalue()

    after = _image_info(
        image=output_image,
        file_name=None,
        image_format=image_format,
        byte_size=len(output_bytes),
    )

    original_bytes = len(image_bytes)
    compressed_bytes = len(output_bytes)
    reduction_rate = 0
    if original_bytes > 0:
        reduction_rate = round((1 - compressed_bytes / original_bytes) * 100, 1)

    quality_value = QUALITY_VALUES[quality]
    format_info = SUPPORTED_FORMATS[image_format]

    return {
        "imageBase64": base64.b64encode(output_bytes).decode("ascii"),
        "mimeType": format_info["mime_type"],
        "downloadFileName": _build_download_file_name(
            file_name=file_name,
            resolution=resolution,
            quality_value=quality_value,
            extension=format_info["extension"],
        ),
        "compression": {
            "originalBytes": original_bytes,
            "compressedBytes": compressed_bytes,
            "reductionRate": reduction_rate,
        },
        "before": before,
        "after": after,
    }


def _resize_image(image: Image.Image, resolution: ResolutionPreset) -> Image.Image:
    max_side = RESOLUTION_MAX_SIDES[resolution]
    if max_side is None:
        return image.copy()

    width, height = image.size
    current_max_side = max(width, height)
    if current_max_side <= max_side:
        return image.copy()

    ratio = max_side / current_max_side
    new_size = (round(width * ratio), round(height * ratio))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def _normalize_mode(image: Image.Image, image_format: str) -> Image.Image:
    if image_format == "JPEG":
        if image.mode in ("RGB", "L"):
            return image
        return image.convert("RGB")

    if image_format == "PNG":
        return image

    if image_format == "WEBP":
        if image.mode in ("RGB", "RGBA"):
            return image
        return image.convert("RGBA" if "A" in image.getbands() else "RGB")

    return image


def _save_image(
    image: Image.Image,
    output_io: io.BytesIO,
    image_format: str,
    quality: QualityPreset,
) -> None:
    quality_value = QUALITY_VALUES[quality]

    if image_format == "JPEG":
        image.save(output_io, format=image_format, quality=quality_value, optimize=True)
        return

    if image_format == "WEBP":
        image.save(output_io, format=image_format, quality=quality_value, method=6)
        return

    image.save(
        output_io,
        format=image_format,
        optimize=True,
        compress_level=PNG_COMPRESS_LEVELS[quality],
    )


def _image_info(
    image: Image.Image,
    file_name: str | None,
    image_format: str,
    byte_size: int,
) -> dict:
    format_info = SUPPORTED_FORMATS[image_format]
    info = {
        "format": image_format,
        "mimeType": format_info["mime_type"],
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "bytes": byte_size,
    }

    if file_name is not None:
        info["fileName"] = file_name

    return info


def _build_download_file_name(
    file_name: str,
    resolution: ResolutionPreset,
    quality_value: int,
    extension: str,
) -> str:
    original_stem = Path(file_name).stem or "image"
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", original_stem).strip("._-")
    if not safe_stem:
        safe_stem = "image"

    return f"{safe_stem}_{resolution}_q{quality_value}{extension}"
