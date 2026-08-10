"""Image upload validation and sanitization helpers for Display Check v2."""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
}

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


@dataclass(frozen=True)
class SanitizedImage:
    """Validated session-only image payload."""

    image_bytes: bytes
    mime_type: str
    width: int
    height: int


class UploadValidationError(ValueError):
    """User-safe upload validation error."""


def sanitize_image_upload(
    *,
    image_bytes: bytes,
    filename: str,
    mime_type: str | None,
) -> SanitizedImage:
    """Validate, normalize, and strip metadata from an uploaded image."""
    _validate_size(image_bytes)
    _validate_type(filename, mime_type)

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.verify()
        with Image.open(BytesIO(image_bytes)) as image:
            image = ImageOps.exif_transpose(image)
            _validate_dimensions(image)
            normalized = _normalize_mode(image)
            output = BytesIO()
            normalized.save(output, format="PNG", optimize=True)
    except Image.DecompressionBombError as exc:
        raise UploadValidationError("Image is too large to process safely.") from exc
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        raise UploadValidationError("Unable to read this image.") from exc

    return SanitizedImage(
        image_bytes=output.getvalue(),
        mime_type="image/png",
        width=normalized.width,
        height=normalized.height,
    )


def _validate_size(image_bytes: bytes) -> None:
    """Reject empty or oversized uploads."""
    if not image_bytes:
        raise UploadValidationError("Unable to read this image.")
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise UploadValidationError("Image exceeds the 10 MB limit.")


def _validate_type(filename: str, mime_type: str | None) -> None:
    """Reject unsupported extensions and MIME types."""
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise UploadValidationError("Unsupported image type.")
    if mime_type and mime_type.lower() not in ALLOWED_MIME_TYPES:
        raise UploadValidationError("Unsupported image type.")


def _validate_dimensions(image: Image.Image) -> None:
    """Reject decompression-bomb sized images."""
    width, height = image.size
    if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
        raise UploadValidationError("Image is too large to process safely.")


def _normalize_mode(image: Image.Image) -> Image.Image:
    """Normalize image mode for safe PNG re-encoding."""
    if image.mode in {"RGBA", "LA"}:
        return image.convert("RGBA")
    return image.convert("RGB")
