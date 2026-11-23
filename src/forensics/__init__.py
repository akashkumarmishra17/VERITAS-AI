"""
VERITAS AI - Digital Forensics Analysis Package.
Includes ELA, Noise Inconsistency, Copy-Move (Cloning), Splicing Localization,
and Metadata EXIF Forensics.
"""

from .ela import perform_ela, ELAResult
from .noise_analysis import analyze_noise_inconsistency, NoiseResult
from .copy_move import detect_copy_move, CopyMoveResult
from .splicing_localization import generate_tamper_localization_mask
from .metadata_forensics import analyze_image_metadata, MetadataForensicResult

__all__ = [
    "perform_ela",
    "ELAResult",
    "analyze_noise_inconsistency",
    "NoiseResult",
    "detect_copy_move",
    "CopyMoveResult",
    "generate_tamper_localization_mask",
    "analyze_image_metadata",
    "MetadataForensicResult",
]
