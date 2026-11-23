"""
Unit tests for 20-dimensional multi-domain forensic feature extractor.
"""

from PIL import Image, ImageDraw
import numpy as np
from src.features.extractor import extract_forensic_features, feature_dict_to_array, FEATURE_NAMES


def test_extract_forensic_features_keys_and_values():
    img = Image.new("RGB", (256, 256), (150, 120, 90))
    draw = ImageDraw.Draw(img)
    draw.ellipse([40, 40, 180, 180], fill=(220, 70, 70))
    
    feats = extract_forensic_features(img)
    
    assert len(feats) == len(FEATURE_NAMES)
    for name in FEATURE_NAMES:
        assert name in feats
        val = feats[name]
        # Assert each feature is a valid finite float (no NaN, no Inf)
        assert isinstance(val, (float, int, np.floating))
        assert not np.isnan(val), f"Feature {name} is NaN"
        assert not np.isinf(val), f"Feature {name} is infinite"


def test_feature_dict_to_array_shape():
    img = Image.new("RGB", (128, 128), (80, 100, 120))
    feats = extract_forensic_features(img)
    arr = feature_dict_to_array(feats)
    
    assert arr.shape == (len(FEATURE_NAMES),)
    assert arr.dtype == np.float32
