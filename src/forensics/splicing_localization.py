"""
VERITAS AI - Digital Splicing Localization & Anomaly Mapping.

Detects and localizes foreign spliced objects and localized digital edits
by analyzing spatial convergence of ELA compression errors, noise variance
discontinuities, and boundary gradients.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import numpy as np
from PIL import Image
import cv2

from .ela import perform_ela
from .noise_analysis import analyze_noise_inconsistency


@dataclass
class SplicingLocalizationResult:
    binary_mask: Image.Image
    heatmap_overlay: Image.Image
    suspicious_regions: List[Dict[str, Any]]
    num_suspicious_zones: int
    tampering_detected: bool
    splicing_score: float  # 0.0 to 1.0
    forensic_interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_suspicious_zones": self.num_suspicious_zones,
            "tampering_detected": self.tampering_detected,
            "splicing_score": round(self.splicing_score, 3),
            "suspicious_regions": self.suspicious_regions,
            "forensic_interpretation": self.forensic_interpretation,
        }


def generate_tamper_localization_mask(
    image: Image.Image,
    ela_quality: int = 90,
    sensitivity: float = 0.5,
    min_region_area: int = 400,
) -> SplicingLocalizationResult:
    """
    Computes suspicious tampered region masks and bounding boxes.

    Args:
        image: PIL RGB image.
        ela_quality: JPEG quality for ELA stage.
        sensitivity: Detection sensitivity threshold (0.1 to 1.0).
        min_region_area: Minimum pixel area to be classified as a tampered zone.

    Returns:
        SplicingLocalizationResult with mask, heatmap overlay, and bounding boxes.
    """
    img_rgb = np.asarray(image.convert("RGB"))
    h, w, _ = img_rgb.shape

    # 1. Compute ELA response
    ela_res = perform_ela(image, quality=ela_quality, scale_factor=20.0)
    ela_diff = np.asarray(ela_res.difference_image, dtype=np.float32)
    ela_lum = np.mean(ela_diff, axis=2)

    # 2. Compute Noise Inconsistency response
    noise_res = analyze_noise_inconsistency(image, block_size=20)
    noise_hm = np.asarray(noise_res.noise_variance_heatmap.convert("L"), dtype=np.float32)

    # Normalize both maps to 0.0 - 1.0
    norm_ela = ela_lum / (np.percentile(ela_lum, 98) + 1e-5)
    norm_ela = np.clip(norm_ela, 0.0, 1.0)

    norm_noise = noise_hm / (np.percentile(noise_hm, 98) + 1e-5)
    norm_noise = np.clip(norm_noise, 0.0, 1.0)

    # Multi-forensic combined anomaly map
    # Weigh ELA and Noise variance
    combined = 0.65 * norm_ela + 0.35 * norm_noise

    # Smooth to aggregate contiguous regions
    blurred = cv2.GaussianBlur(combined, (15, 15), 0)

    # Adaptive threshold based on sensitivity
    # sensitivity 0.5 -> threshold at 70th percentile
    p_thresh = 92.0 - (sensitivity * 25.0)
    threshold_val = float(np.percentile(blurred, p_thresh))
    threshold_val = max(threshold_val, 0.45)

    binary = ((blurred >= threshold_val) * 255).astype(np.uint8)

    # Morphological cleanup: close small holes, remove tiny isolated specks
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)

    # Find contours
    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    suspicious_regions: List[Dict[str, Any]] = []
    annotated_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    overlay_mask = np.zeros((h, w), dtype=np.uint8)

    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area >= min_region_area:
            x, y, bw, bh = cv2.boundingRect(cnt)
            # Region mean anomaly
            region_crop = blurred[y:y+bh, x:x+bw]
            mean_anomaly = float(np.mean(region_crop)) if region_crop.size > 0 else 0.0

            # Draw region contour and bounding box
            cv2.drawContours(overlay_mask, [cnt], -1, 255, -1)
            cv2.rectangle(annotated_bgr, (x, y), (x + bw, y + bh), (0, 140, 255), 2)
            cv2.putText(
                annotated_bgr,
                f"Zone #{len(suspicious_regions)+1} ({int(area)}px)",
                (x, max(y - 8, 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 140, 255),
                2,
                cv2.LINE_AA,
            )

            suspicious_regions.append({
                "zone_id": len(suspicious_regions) + 1,
                "x": int(x),
                "y": int(y),
                "width": int(bw),
                "height": int(bh),
                "area_pixels": int(area),
                "relative_area_pct": round((area / float(w * h)) * 100.0, 2),
                "anomaly_intensity": round(mean_anomaly, 3),
            })

    # Create semi-transparent overlay
    # Red translucent tint over tampered regions
    overlay_color = np.zeros_like(annotated_bgr)
    overlay_color[overlay_mask > 0] = [0, 50, 220]  # Red in BGR

    alpha = 0.38
    blended = cv2.addWeighted(annotated_bgr, 1.0, overlay_color, alpha, 0.0)

    # Convert back to RGB PIL
    heatmap_pil = Image.fromarray(cv2.cvtColor(blended, cv2.COLOR_BGR2RGB))
    mask_pil = Image.fromarray(opened, mode="L")

    num_zones = len(suspicious_regions)
    total_tampered_area = sum(r["area_pixels"] for r in suspicious_regions)
    pct_tampered = (total_tampered_area / float(w * h)) * 100.0 if (w * h) > 0 else 0.0

    # Score calculation
    if num_zones > 0 and pct_tampered > 1.2:
        tampering_detected = True
        splicing_score = min(0.55 + 0.1 * min(num_zones, 4) + (pct_tampered * 0.01), 0.96)
        interpretation = (
            f"Detected {num_zones} localized suspicious anomaly zone(s) covering approximately "
            f"{pct_tampered:.1f}% of total image canvas. Distinct compression rates and high-frequency "
            "boundary residues are consistent with spliced content or localized digital inpainting."
        )
    elif num_zones > 0:
        tampering_detected = False
        splicing_score = 0.38
        interpretation = (
            f"Minor localized variations detected ({num_zones} small cluster, ~{pct_tampered:.2f}% area). "
            "These may correspond to localized contrast enhancement, sharp specular highlights, or text watermarks."
        )
    else:
        tampering_detected = False
        splicing_score = 0.08
        interpretation = (
            "No coherent spliced or pasted region detected. Error distribution and noise residuals are "
            "spatially consistent across all segments."
        )

    return SplicingLocalizationResult(
        binary_mask=mask_pil,
        heatmap_overlay=heatmap_pil,
        suspicious_regions=suspicious_regions,
        num_suspicious_zones=num_zones,
        tampering_detected=tampering_detected,
        splicing_score=float(splicing_score),
        forensic_interpretation=interpretation,
    )
