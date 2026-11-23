"""
Unit tests for Noise analysis, Copy-Move detection, Splicing localization,
and EXIF Metadata forensics.
"""

from PIL import Image, ImageDraw
import numpy as np
from src.forensics.noise_analysis import analyze_noise_inconsistency, NoiseResult
from src.forensics.copy_move import detect_copy_move, CopyMoveResult
from src.forensics.splicing_localization import generate_tamper_localization_mask
from src.forensics.metadata_forensics import analyze_image_metadata


def test_noise_analysis():
    img = Image.new("RGB", (256, 256), (100, 100, 100))
    res = analyze_noise_inconsistency(img, block_size=24)

    assert isinstance(res, NoiseResult)
    assert 0.0 <= res.noise_inconsistency_score <= 1.0
    assert res.global_noise_mean >= 0.0
    assert res.noise_variance_heatmap.size == (256, 256)
    assert len(res.forensic_interpretation) > 0


def test_copy_move_detection_on_solid_image():
    # Solid image should gracefully report insufficient keypoints or 0 clusters
    img = Image.new("RGB", (200, 200), (128, 128, 128))
    res = detect_copy_move(img)

    assert isinstance(res, CopyMoveResult)
    assert res.copy_move_detected is False
    assert res.clustered_clusters_count == 0
    assert 0.0 <= res.suspicion_score <= 1.0


def test_splicing_localization():
    img = Image.new("RGB", (256, 256), (140, 160, 180))
    res = generate_tamper_localization_mask(img)

    assert res.binary_mask.size == (256, 256)
    assert res.heatmap_overlay.size == (256, 256)
    assert isinstance(res.suspicious_regions, list)
    assert 0.0 <= res.splicing_score <= 1.0


def test_metadata_forensics_stripped():
    # Fresh PIL image has no EXIF
    img = Image.new("RGB", (100, 100), (50, 50, 50))
    res = analyze_image_metadata(img, filename="test.jpg")

    assert res.has_exif is False
    assert res.metadata_stripped is True
    assert 0.0 <= res.metadata_suspicion_score <= 1.0
    assert res.risk_level in ["LOW", "MODERATE", "ELEVATED"]
