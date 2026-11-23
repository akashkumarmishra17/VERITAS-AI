"""
VERITAS AI - Noise Inconsistency and Residual Analysis.

Every camera sensor introduces Photo-Response Non-Uniformity (PRNU) and photon shot noise.
When an external object is spliced or inpainting is applied, the local noise variance
is disrupted. This module calculates noise residual maps using high-pass filtering
and statistical variance across spatial image blocks.
"""

from dataclasses import dataclass
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image
from scipy.ndimage import median_filter, laplace


@dataclass
class NoiseResult:
    noise_residual_map: Image.Image
    noise_variance_heatmap: Image.Image
    global_noise_mean: float
    global_noise_std: float
    noise_inconsistency_score: float  # Normalized 0.0 - 1.0 (higher = more suspicious)
    noise_kurtosis: float
    block_variance_ratio: float  # Max block variance / Min non-zero block variance
    forensic_interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "global_noise_mean": round(self.global_noise_mean, 3),
            "global_noise_std": round(self.global_noise_std, 3),
            "noise_inconsistency_score": round(self.noise_inconsistency_score, 3),
            "noise_kurtosis": round(self.noise_kurtosis, 3),
            "block_variance_ratio": round(self.block_variance_ratio, 2),
            "forensic_interpretation": self.forensic_interpretation,
        }


def analyze_noise_inconsistency(
    image: Image.Image,
    block_size: int = 24
) -> NoiseResult:
    """
    Analyzes spatial noise uniformity across the image.

    Args:
        image: PIL Image in RGB mode.
        block_size: Window size in pixels for local variance estimation.

    Returns:
        NoiseResult containing residual visualizations and statistical metrics.
    """
    # Convert to grayscale luminance array in float32
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    h, w = gray.shape

    # Extract high-frequency noise residual using median subtraction
    # Noise = Original - Denoised(Original)
    smoothed = median_filter(gray, size=3)
    residual = gray - smoothed

    # Alternatively combine with Laplacian second-derivative response
    lap_response = np.abs(laplace(gray))
    combined_noise = 0.5 * np.abs(residual) + 0.5 * (lap_response / 4.0)

    global_mean = float(np.mean(combined_noise))
    global_std = float(np.std(combined_noise))

    # Calculate local variance across non-overlapping blocks
    pad_h = (block_size - (h % block_size)) % block_size
    pad_w = (block_size - (w % block_size)) % block_size
    padded = np.pad(combined_noise, ((0, pad_h), (0, pad_w)), mode="reflect")

    ph, pw = padded.shape
    bh, bw = ph // block_size, pw // block_size

    # Reshape to (bh, block_size, bw, block_size) and compute variance per block
    blocks = padded.reshape(bh, block_size, bw, block_size)
    block_vars = np.var(blocks, axis=(1, 3))

    mean_block_var = float(np.mean(block_vars)) if np.mean(block_vars) > 1e-6 else 1e-6
    std_block_var = float(np.std(block_vars))
    max_block_var = float(np.max(block_vars))
    min_block_var = float(np.min(block_vars[block_vars > 1e-4])) if np.any(block_vars > 1e-4) else 1e-4

    block_ratio = min(max_block_var / min_block_var, 100.0)

    # Inconsistency coefficient of variation: std(vars) / mean(vars)
    cv = std_block_var / mean_block_var
    # Normalize to [0, 1] range using sigmoid-like scaling
    inconsistency_score = float(1.0 / (1.0 + np.exp(-1.2 * (cv - 1.8))))

    # Kurtosis of noise residual (authentic camera noise has near-normal kurtosis ~ 3.0)
    centered = combined_noise - global_mean
    m4 = np.mean(centered ** 4)
    m2 = np.mean(centered ** 2)
    kurtosis = float(m4 / (m2 ** 2)) if m2 > 1e-6 else 3.0

    # Create visualization maps
    # Residual map (scaled to 0-255)
    residual_vis = np.clip(np.abs(residual) * 8.0, 0, 255).astype(np.uint8)
    residual_img = Image.fromarray(residual_vis, mode="L")

    # Variance heatmap: upsample block_vars to full image size
    # Normalize block_vars between 0 and 255
    bv_norm = np.clip((block_vars / (np.percentile(block_vars, 98) + 1e-6)) * 255.0, 0, 255).astype(np.uint8)
    bv_img_small = Image.fromarray(bv_norm, mode="L")
    bv_heatmap = bv_img_small.resize((w, h), Image.Resampling.BILINEAR)

    # Convert heatmap to pseudo-RGB color (Cyan-to-Red / Turbo gradient representation)
    hm_arr = np.asarray(bv_heatmap, dtype=np.float32) / 255.0
    r_chan = np.clip(255.0 * (1.5 * hm_arr - 0.2), 0, 255).astype(np.uint8)
    g_chan = np.clip(255.0 * (1.0 - np.abs(hm_arr - 0.5) * 2.0), 0, 255).astype(np.uint8)
    b_chan = np.clip(255.0 * (1.2 * (1.0 - hm_arr) - 0.2), 0, 255).astype(np.uint8)
    heatmap_rgb = Image.fromarray(np.stack([r_chan, g_chan, b_chan], axis=2), mode="RGB")

    # Forensic interpretation
    if inconsistency_score > 0.65 or block_ratio > 25.0:
        interpretation = (
            "Substantial spatial noise variance disparity observed across image segments. "
            "Isolated regions show either unnaturally suppressed noise (suggestive of retouching/smoothing) "
            "or discordant high-frequency noise typical of spliced composite imagery."
        )
    elif inconsistency_score > 0.40:
        interpretation = (
            "Mild noise variance heterogeneity detected. Variations are largely consistent with "
            "lighting gradients and variable depth-of-field focus zones."
        )
    else:
        interpretation = (
            "High noise spatial uniformity across the entire sensor frame. "
            "Characteristic of an authentic photograph captured under uniform sensor exposure."
        )

    return NoiseResult(
        noise_residual_map=residual_img,
        noise_variance_heatmap=heatmap_rgb,
        global_noise_mean=global_mean,
        global_noise_std=global_std,
        noise_inconsistency_score=inconsistency_score,
        noise_kurtosis=kurtosis,
        block_variance_ratio=block_ratio,
        forensic_interpretation=interpretation,
    )
