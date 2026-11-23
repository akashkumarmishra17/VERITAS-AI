"""
VERITAS AI - Feature Extraction Package.
Extracts comprehensive statistical, forensic, frequency, and spatial features
for Machine Learning classification.
"""

from .extractor import extract_forensic_features, FEATURE_NAMES

__all__ = ["extract_forensic_features", "FEATURE_NAMES"]
