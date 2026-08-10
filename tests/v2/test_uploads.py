"""Tests for Display Check v2 image upload validation."""

from io import BytesIO

import pytest
from PIL import Image, features

from app.v2.uploads import (
    MAX_UPLOAD_BYTES,
    UploadValidationError,
    sanitize_image_upload,
)


def _image_bytes(format_name: str) -> bytes:
    """Create a tiny valid image payload."""
    output = BytesIO()
    Image.new("RGB", (12, 10), color=(120, 80, 40)).save(output, format=format_name)
    return output.getvalue()


def test_valid_png_is_accepted() -> None:
    """PNG uploads are validated and re-encoded."""
    result = sanitize_image_upload(
        image_bytes=_image_bytes("PNG"),
        filename="reference.png",
        mime_type="image/png",
    )

    assert result.mime_type == "image/png"
    assert result.width == 12
    assert result.height == 10


def test_valid_jpeg_is_accepted() -> None:
    """JPEG uploads are validated and re-encoded."""
    result = sanitize_image_upload(
        image_bytes=_image_bytes("JPEG"),
        filename="reference.jpg",
        mime_type="image/jpeg",
    )

    assert result.mime_type == "image/png"


@pytest.mark.skipif(not features.check("webp"), reason="Pillow WebP support unavailable")
def test_valid_webp_is_accepted() -> None:
    """WEBP uploads are validated when Pillow supports WEBP."""
    result = sanitize_image_upload(
        image_bytes=_image_bytes("WEBP"),
        filename="reference.webp",
        mime_type="image/webp",
    )

    assert result.mime_type == "image/png"


def test_oversized_input_is_rejected() -> None:
    """Uploads larger than 10 MB are rejected before Pillow processing."""
    with pytest.raises(UploadValidationError, match="10 MB"):
        sanitize_image_upload(
            image_bytes=b"0" * (MAX_UPLOAD_BYTES + 1),
            filename="reference.png",
            mime_type="image/png",
        )


def test_invalid_image_is_rejected() -> None:
    """Corrupt images produce a user-safe validation error."""
    with pytest.raises(UploadValidationError, match="Unable to read"):
        sanitize_image_upload(
            image_bytes=b"not an image",
            filename="reference.png",
            mime_type="image/png",
        )


def test_unsupported_extension_is_rejected() -> None:
    """Unsupported file extensions are rejected."""
    with pytest.raises(UploadValidationError, match="Unsupported image type"):
        sanitize_image_upload(
            image_bytes=_image_bytes("PNG"),
            filename="reference.gif",
            mime_type="image/gif",
        )
