"""
VERITAS AI - Error Level Analysis (ELA) Module.

Error Level Analysis works by intentionally re-saving an image at a known JPEG compression
level (e.g., 90% or 95%) and calculating the difference between the original and recompressed
image. Since distinct sections of an image that have been edited, pasted from another source,
or re-saved multiple times degrade at different rates, ELA highlights these compression
inconsistencies as bright or contrasting regions.

CRITICAL FORENSIC NOTE:
ELA is a forensic clue and indicator, NOT mathematical proof of forgery.
High-frequency sharp edges, high-contrast textures, and dark gradients naturally
exhibit higher error rates even in untouched authentic photographs.
"""

import io
from dataclasses import dataclass
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image, ImageChops, ImageEnhance


@dataclass
class ELAResult:
    ela_image: Image.Image
    difference_image: Image.Image
    anomaly_mask: Image.Image
    mean_error: float
    std_error: float
    max_error: float
    p95_error: float
    anomaly_pixel_ratio: float  # Percentage of pixels with error > threshold
    quality: int
    scale_factor: float
    forensic_interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean_error": round(self.mean_error, 3),
            "std_error": round(self.std_error, 3),
            "max_error": round(self.max_error, 3),
            "p95_error": round(self.p95_error, 3),
            "anomaly_pixel_ratio": round(self.anomaly_pixel_ratio, 4),
            "quality": self.quality,
            "scale_factor": round(self.scale_factor, 1),
            "forensic_interpretation": self.forensic_interpretation,
        }


def perform_ela(
    image: Image.Image,
    quality: int = 90,
    scale_factor: float = 15.0,
    auto_scale: bool = False,
) -> ELAResult:
    """
    Performs Error Level Analysis on a PIL RGB image.

    Args:
        image: Source PIL Image in RGB format.
        quality: JPEG compression quality for re-saving (70-98, default 90).
        scale_factor: Multiplier to amplify subtle error levels (default 15.0).
        auto_scale: If True, dynamically scales error based on maximum observed difference.

    Returns:
        ELAResult dataclass containing visual outputs and statistical metrics.
    """
    if quality < 50 or quality > 99:
        quality = 90

    # Ensure RGB
    if image.mode != "RGB":
        orig_rgb = image.convert("RGB")
    else:
        orig_rgb = image

    # Re-save into in-memory JPEG buffer
    buffer = io.BytesIO()
    orig_rgb.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    recompressed = Image.open(buffer)

    # Compute absolute pixel-wise difference
    diff = ImageChops.difference(orig_rgb, recompressed)
    diff_arr = np.asarray(diff, dtype=np.float32)

    # Error per pixel (average across color channels R, G, B)
    channel_mean_err = np.mean(diff_arr, axis=2)

    mean_err = float(np.mean(channel_mean_err))
    std_err = float(np.std(channel_mean_err))
    max_err = float(np.max(channel_mean_err))
    p95_err = float(np.percentile(channel_mean_err, 95))

    # Determine visual amplification scale
    if auto_scale and max_err > 0:
        effective_scale = min(255.0 / max_err, 40.0)
    else:
        effective_scale = scale_factor

    # Amplify difference for human visualization
    # Clip to [0, 255]
    amplified_arr = np.clip(diff_arr * effective_scale, 0, 255).astype(np.uint8)
    ela_image = Image.fromarray(amplified_arr, mode="RGB")

    # Generate anomaly mask: pixels where error exceeds (mean + 2.5 * std)
    # and error is above a noise baseline
    threshold = max(mean_err + 2.5 * std_err, 12.0)
    anomaly_binary = (channel_mean_err >= threshold).astype(np.uint8) * 255
    anomaly_mask = Image.fromarray(anomaly_binary, mode="L")

    total_pixels = channel_mean_err.size
    anomaly_pixels = int(np.sum(anomaly_binary > 0))
    anomaly_ratio = float(anomaly_pixels) / float(total_pixels) if total_pixels > 0 else 0.0

    # Formulate forensic interpretation based on statistical dispersion
    if std_err > 8.0 and anomaly_ratio > 0.04:
        interpretation = (
            "Elevated error variance detected. Certain localized areas degrade at significantly "
            "different rates compared to the surrounding background, which is consistent with "
            "digital insertion (splicing) or multi-generation JPEG re-saving."
        )
    elif std_err < 3.5 and mean_err < 5.0:
        interpretation = (
            "Uniform and low error level distribution observed across the image canvas. "
            "This pattern is typical of an authentic single-generation photograph or an image "
            "with uniform compression history."
        )
    else:
        interpretation = (
            "Moderate error level distribution. Differences are primarily correlated with natural "
            "high-frequency texture details and object boundaries. No conclusive tampering indicated by ELA alone."
        )

    return ELAResult(
        ela_image=ela_image,
        difference_image=diff,
        anomaly_mask=anomaly_mask,
        mean_error=mean_err,
        std_error=std_err,
        max_error=max_err,
        p95_error=p95_err,
        anomaly_pixel_ratio=anomaly_ratio,
        quality=quality,
        scale_factor=effective_scale,
        forensic_interpretation=interpretation,
    )
