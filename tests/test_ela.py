"""
Unit tests for Error Level Analysis (ELA) module.
"""

from PIL import Image, ImageDraw
import numpy as np
from src.forensics.ela import perform_ela, ELAResult


def test_perform_ela_returns_valid_structure():
    img = Image.new("RGB", (256, 256), (120, 150, 180))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 120, 120], fill=(240, 50, 50))
    draw.text((60, 60), "FORGERY TEST", fill=(255, 255, 255))

    res = perform_ela(img, quality=90, scale_factor=15.0)

    assert isinstance(res, ELAResult)
    assert res.quality == 90
    assert res.ela_image.size == (256, 256)
    assert res.anomaly_mask.size == (256, 256)
    assert res.mean_error >= 0.0
    assert res.max_error >= res.mean_error
    assert 0.0 <= res.anomaly_pixel_ratio <= 1.0
    assert isinstance(res.forensic_interpretation, str)
    assert len(res.forensic_interpretation) > 10


def test_ela_quality_parameter():
    img = Image.new("RGB", (128, 128), (80, 80, 80))
    res_q70 = perform_ela(img, quality=70)
    res_q95 = perform_ela(img, quality=95)

    assert res_q70.quality == 70
    assert res_q95.quality == 95
