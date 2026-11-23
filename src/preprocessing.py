"""
VERITAS AI - Image Preprocessing and Validation Module.

Provides robust validation, safety sanitization, EXIF handling,
and format conversions for uploaded digital images.
"""

import io
import os
import re
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageOps

# Protect against decompression bomb attacks
Image.MAX_IMAGE_PIXELS = 50_000_000

# Permitted extensions and MIME types
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit
MIN_DIMENSION = 64
MAX_DIMENSION = 8192


class ImageValidationError(Exception):
    """Custom exception raised when an image fails security or validation checks."""
    pass


def sanitize_filename(filename: str) -> str:
    """
    Sanitize uploaded filename to prevent directory traversal or script injection.
    """
    if not filename:
        return "unnamed_image.png"
    # Keep only alphanumeric, dash, underscore, and dot
    clean_name = os.path.basename(filename)
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean_name)
    return clean_name[:100]  # limit length


def validate_image_bytes(file_bytes: bytes, filename: str = "") -> Dict[str, Any]:
    """
    Validates uploaded raw bytes for security, file size, integrity, and dimensions.

    Returns:
        dict: Validated metadata including dimensions, format, mode, and file size.
    Raises:
        ImageValidationError: If the file is invalid, corrupt, or exceeds limits.
    """
    if not file_bytes:
        raise ImageValidationError("Uploaded file is empty (0 bytes).")

    file_size = len(file_bytes)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ImageValidationError(
            f"File size ({file_size / (1024 * 1024):.1f} MB) exceeds maximum allowed limit of "
            f"{MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f} MB."
        )

    # Check extension if filename provided
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise ImageValidationError(
                f"File extension '{ext}' is not supported. Supported extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
            )

    try:
        # Initial verification of image integrity without full decompression
        with Image.open(io.BytesIO(file_bytes)) as img_verify:
            img_format = (img_verify.format or "").upper()
            if img_format not in ALLOWED_FORMATS:
                raise ImageValidationError(
                    f"Detected image format '{img_format}' is not supported. Allowed formats: {', '.join(sorted(ALLOWED_FORMATS))}."
                )
            img_verify.verify()

        # Reopen to load image properties (verify closes the file handle)
        with Image.open(io.BytesIO(file_bytes)) as img:
            width, height = img.size
            mode = img.mode

            if width < MIN_DIMENSION or height < MIN_DIMENSION:
                raise ImageValidationError(
                    f"Image dimensions ({width}x{height}) are too small. Minimum required: {MIN_DIMENSION}x{MIN_DIMENSION}."
                )

            if width > MAX_DIMENSION or height > MAX_DIMENSION:
                raise ImageValidationError(
                    f"Image dimensions ({width}x{height}) exceed maximum allowed dimension of {MAX_DIMENSION}px."
                )

            megapixels = (width * height) / 1_000_000.0

            return {
                "valid": True,
                "filename": sanitize_filename(filename),
                "format": img_format,
                "mode": mode,
                "width": width,
                "height": height,
                "aspect_ratio": round(width / float(height), 3),
                "megapixels": round(megapixels, 2),
                "file_size_bytes": file_size,
                "file_size_kb": round(file_size / 1024.0, 1),
                "file_size_mb": round(file_size / (1024.0 * 1024.0), 2),
            }

    except ImageValidationError:
        raise
    except Exception as e:
        raise ImageValidationError(f"Invalid or corrupted image file: {str(e)}")


def load_image_rgb(file_bytes_or_path: Any) -> Image.Image:
    """
    Safely loads an image from bytes, BytesIO, or a file path and converts it to RGB.
    Handles orientation correction based on EXIF tag.
    """
    if isinstance(file_bytes_or_path, bytes):
        stream = io.BytesIO(file_bytes_or_path)
    elif isinstance(file_bytes_or_path, io.BytesIO):
        stream = file_bytes_or_path
    elif isinstance(file_bytes_or_path, str):
        if not os.path.exists(file_bytes_or_path):
            raise FileNotFoundError(f"Image file not found: {file_bytes_or_path}")
        with open(file_bytes_or_path, "rb") as f:
            stream = io.BytesIO(f.read())
    else:
        raise ValueError("Unsupported input type for loading image.")

    try:
        img = Image.open(stream)
        # Apply EXIF rotation if present
        img = ImageOps.exif_transpose(img)
        # Convert any color mode (RGBA, P, L, CMYK) safely to RGB
        if img.mode != "RGB":
            img = img.convert("RGB")
        return img
    except Exception as e:
        raise ImageValidationError(f"Could not decode image stream to RGB: {str(e)}")


def resize_for_display(img: Image.Image, max_dim: int = 1024) -> Image.Image:
    """
    Resizes image proportionally if either dimension exceeds max_dim,
    preserving full aspect ratio.
    """
    w, h = img.size
    if max(w, h) <= max_dim:
        return img.copy()

    scale = max_dim / float(max(w, h))
    new_w = int(w * scale)
    new_h = int(h * scale)
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
