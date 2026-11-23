"""
VERITAS AI - Multi-Domain Forensic Feature Extractor.

Extracts a 20-dimensional forensic feature vector spanning:
1. Error Level Analysis (ELA) error distribution moments (mean, std, skew, kurtosis, max, p95, anomaly ratio)
2. Spatial noise residue variance & block inconsistency metrics
3. Gradient & Laplacian edge continuity statistics
4. Cross-color channel correlation & chromatic distribution
5. Discrete Cosine Transform (DCT) frequency domain energy distribution
"""

from typing import Dict, List, Tuple, Any
import numpy as np
from PIL import Image
import cv2
from scipy.stats import skew, kurtosis
from scipy.fftpack import dct

from ..forensics.ela import perform_ela
from ..forensics.noise_analysis import analyze_noise_inconsistency

FEATURE_NAMES = [
    "ela_mean",
    "ela_std",
    "ela_max",
    "ela_p95",
    "ela_skewness",
    "ela_kurtosis",
    "ela_anomaly_ratio",
    "noise_mean",
    "noise_std",
    "noise_cv",
    "noise_kurtosis",
    "noise_block_ratio",
    "laplacian_var",
    "sobel_edge_mean",
    "sobel_edge_std",
    "rg_corr",
    "rb_corr",
    "gb_corr",
    "dct_high_freq_ratio",
    "dct_energy_var",
]


def extract_forensic_features(image: Image.Image, ela_quality: int = 90) -> Dict[str, float]:
    """
    Extracts the full 20-dimensional forensic feature dictionary from a PIL Image.

    Args:
        image: PIL Image in RGB mode.
        ela_quality: Quality parameter for ELA extraction (default 90).

    Returns:
        Dict mapping feature name to floating point value.
    """
    img_rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    h, w, _ = img_rgb.shape

    # 1. ELA Features
    ela_res = perform_ela(image, quality=ela_quality)
    diff_arr = np.asarray(ela_res.difference_image, dtype=np.float32)
    ela_lum = np.mean(diff_arr, axis=2).flatten()

    ela_mean = float(np.mean(ela_lum))
    ela_std = float(np.std(ela_lum))
    ela_max = float(np.max(ela_lum))
    ela_p95 = float(np.percentile(ela_lum, 95))
    ela_skew = float(skew(ela_lum)) if ela_std > 1e-4 else 0.0
    ela_kurt = float(kurtosis(ela_lum)) if ela_std > 1e-4 else 0.0
    ela_anomaly_ratio = float(ela_res.anomaly_pixel_ratio)

    # 2. Noise Inconsistency Features
    noise_res = analyze_noise_inconsistency(image, block_size=24)
    noise_mean = float(noise_res.global_noise_mean)
    noise_std = float(noise_res.global_noise_std)
    noise_cv = float(noise_std / noise_mean) if noise_mean > 1e-4 else 0.0
    noise_kurt = float(noise_res.noise_kurtosis)
    noise_block_ratio = float(noise_res.block_variance_ratio)

    # 3. Edge and Gradient Features
    gray_uint8 = cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2GRAY)
    laplacian_var = float(cv2.Laplacian(gray_uint8, cv2.CV_64F).var())

    sobel_x = cv2.Sobel(gray_uint8, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray_uint8, cv2.CV_64F, 0, 1, ksize=3)
    sobel_mag = np.hypot(sobel_x, sobel_y)
    sobel_edge_mean = float(np.mean(sobel_mag))
    sobel_edge_std = float(np.std(sobel_mag))

    # 4. Color Channel Correlations
    r = img_rgb[:, :, 0].flatten()
    g = img_rgb[:, :, 1].flatten()
    b = img_rgb[:, :, 2].flatten()

    def safe_corr(a: np.ndarray, b_arr: np.ndarray) -> float:
        s_a = np.std(a)
        s_b = np.std(b_arr)
        if s_a < 1e-4 or s_b < 1e-4:
            return 1.0
        c = np.corrcoef(a, b_arr)[0, 1]
        return float(c) if not np.isnan(c) else 1.0

    rg_corr = safe_corr(r, g)
    rb_corr = safe_corr(r, b)
    gb_corr = safe_corr(g, b)

    # 5. Frequency Domain / DCT Features
    # Resample to 256x256 for consistent frequency domain analysis
    small_gray = cv2.resize(gray_uint8, (256, 256)).astype(np.float32)
    # 2D DCT
    dct_2d = dct(dct(small_gray.T, norm='ortho').T, norm='ortho')
    dct_abs = np.abs(dct_2d)

    # Split into low and high frequency quadrants
    low_freq_energy = np.sum(dct_abs[:64, :64])
    total_energy = np.sum(dct_abs)
    high_freq_energy = total_energy - low_freq_energy

    dct_high_freq_ratio = float(high_freq_energy / total_energy) if total_energy > 1e-4 else 0.0
    dct_energy_var = float(np.var(dct_abs))

    return {
        "ela_mean": ela_mean,
        "ela_std": ela_std,
        "ela_max": ela_max,
        "ela_p95": ela_p95,
        "ela_skewness": ela_skew,
        "ela_kurtosis": ela_kurt,
        "ela_anomaly_ratio": ela_anomaly_ratio,
        "noise_mean": noise_mean,
        "noise_std": noise_std,
        "noise_cv": noise_cv,
        "noise_kurtosis": noise_kurt,
        "noise_block_ratio": noise_block_ratio,
        "laplacian_var": laplacian_var,
        "sobel_edge_mean": sobel_edge_mean,
        "sobel_edge_std": sobel_edge_std,
        "rg_corr": rg_corr,
        "rb_corr": rb_corr,
        "gb_corr": gb_corr,
        "dct_high_freq_ratio": dct_high_freq_ratio,
        "dct_energy_var": dct_energy_var,
    }


def feature_dict_to_array(feature_dict: Dict[str, float]) -> np.ndarray:
    """
    Converts a feature dictionary to an ordered 1D numpy array aligned with FEATURE_NAMES.
    """
    return np.array([feature_dict[name] for name in FEATURE_NAMES], dtype=np.float32)
