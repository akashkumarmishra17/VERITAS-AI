"""
Unit tests for image preprocessing, security sanitization, and format validation.
"""

import io
import pytest
from PIL import Image
from src.preprocessing import (
    validate_image_bytes,
    load_image_rgb,
    sanitize_filename,
    ImageValidationError,
)


def create_dummy_image_bytes(format="JPEG", size=(200, 200), color=(100, 150, 200)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_sanitize_filename():
    assert sanitize_filename("my_photo.jpg") == "my_photo.jpg"
    assert sanitize_filename("../../../etc/passwd.png") == "passwd.png"
    assert sanitize_filename("image<script>alert.jpg") == "image_script_alert.jpg"
    assert sanitize_filename("") == "unnamed_image.png"


def test_valid_image_bytes():
    raw_bytes = create_dummy_image_bytes(format="JPEG", size=(250, 180))
    meta = validate_image_bytes(raw_bytes, filename="test.jpg")
    assert meta["valid"] is True
    assert meta["width"] == 250
    assert meta["height"] == 180
    assert meta["format"] == "JPEG"
    assert meta["file_size_bytes"] == len(raw_bytes)


def test_empty_bytes_raises():
    with pytest.raises(ImageValidationError, match="empty"):
        validate_image_bytes(b"", filename="empty.jpg")


def test_corrupt_bytes_raises():
    with pytest.raises(ImageValidationError, match="Invalid or corrupted"):
        validate_image_bytes(b"This is not a real image stream", filename="corrupt.jpg")


def test_too_small_dimensions_raises():
    small_bytes = create_dummy_image_bytes(size=(32, 32))
    with pytest.raises(ImageValidationError, match="too small"):
        validate_image_bytes(small_bytes, filename="small.jpg")


def test_unsupported_extension_raises():
    raw_bytes = create_dummy_image_bytes()
    with pytest.raises(ImageValidationError, match="not supported"):
        validate_image_bytes(raw_bytes, filename="malicious.exe")


def test_load_image_rgb_handles_rgba():
    rgba_img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
    buf = io.BytesIO()
    rgba_img.save(buf, format="PNG")
    
    loaded = load_image_rgb(buf.getvalue())
    assert loaded.mode == "RGB"
    assert loaded.size == (100, 100)
