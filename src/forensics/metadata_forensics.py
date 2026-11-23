"""
VERITAS AI - Metadata (EXIF) Digital Forensics Module.

Extracts and analyzes Exchangeable Image File Format (EXIF) metadata to uncover
digital editing software signatures, timestamp inconsistencies, camera hardware
fingerprints, and metadata stripping anomalies.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


EDITING_SOFTWARE_KEYWORDS = [
    "photoshop", "gimp", "canva", "lightroom", "paint.net",
    "snapseed", "picsart", "corel", "affinity", "pixelmator",
    "fotor", "vsco", "pixlr", "procreate", "befunky",
]


@dataclass
class MetadataForensicResult:
    has_exif: bool
    camera_make: Optional[str]
    camera_model: Optional[str]
    software_tag: Optional[str]
    date_original: Optional[str]
    date_modified: Optional[str]
    editing_software_detected: bool
    detected_software_name: Optional[str]
    timestamp_mismatch: bool
    metadata_stripped: bool
    raw_exif_dict: Dict[str, Any]
    metadata_suspicion_score: float  # 0.0 to 1.0
    forensic_findings: List[str]
    risk_level: str  # "LOW", "MODERATE", "ELEVATED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_exif": self.has_exif,
            "camera_make": self.camera_make,
            "camera_model": self.camera_model,
            "software_tag": self.software_tag,
            "date_original": self.date_original,
            "date_modified": self.date_modified,
            "editing_software_detected": self.editing_software_detected,
            "detected_software_name": self.detected_software_name,
            "timestamp_mismatch": self.timestamp_mismatch,
            "metadata_stripped": self.metadata_stripped,
            "metadata_suspicion_score": round(self.metadata_suspicion_score, 3),
            "forensic_findings": self.forensic_findings,
            "risk_level": self.risk_level,
        }


def analyze_image_metadata(image: Image.Image, filename: str = "") -> MetadataForensicResult:
    """
    Extracts and evaluates EXIF metadata for forensic signatures.

    Args:
        image: PIL Image object.
        filename: Optional filename for reference.

    Returns:
        MetadataForensicResult with parsed metadata and forensic findings.
    """
    findings: List[str] = []
    exif_data: Dict[str, Any] = {}

    try:
        raw_exif = image._getexif()
        if raw_exif is not None:
            for tag_id, value in raw_exif.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                # Convert bytes or un-serializable objects to safe strings
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8", errors="ignore").strip("\x00")
                    except Exception:
                        value = str(value)[:50]
                elif isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], int) and isinstance(value[1], int):
                    # Rational number (e.g. shutter speed, aperture)
                    value = round(value[0] / float(value[1]), 3) if value[1] != 0 else value[0]
                exif_data[tag_name] = str(value)
    except Exception as e:
        findings.append(f"Could not parse EXIF stream: {str(e)}")

    has_exif = bool(exif_data)

    camera_make = exif_data.get("Make")
    camera_model = exif_data.get("Model")
    software_tag = exif_data.get("Software")
    date_original = exif_data.get("DateTimeOriginal") or exif_data.get("DateTimeDigitized")
    date_modified = exif_data.get("DateTime")

    editing_software_detected = False
    detected_software_name = None

    # 1. Analyze Software Tag
    if software_tag:
        sw_lower = software_tag.lower()
        for kw in EDITING_SOFTWARE_KEYWORDS:
            if kw in sw_lower:
                editing_software_detected = True
                detected_software_name = software_tag
                findings.append(
                    f"Digital editing signature found: Image was processed/saved by '{software_tag}'."
                )
                break
        if not editing_software_detected:
            findings.append(f"Software metadata tag present: '{software_tag}'.")

    # 2. Check Timestamp Mismatch
    timestamp_mismatch = False
    if date_original and date_modified and date_original != date_modified:
        timestamp_mismatch = True
        findings.append(
            f"Timestamp divergence detected: Original capture ({date_original}) differs from "
            f"modification timestamp ({date_modified}), indicating post-capture re-saving."
        )

    # 3. Check for Stripped Metadata
    metadata_stripped = False
    if not has_exif:
        metadata_stripped = True
        findings.append(
            "EXIF metadata is completely absent or stripped. Common for online social media uploads "
            "or intentional forensic anti-analysis scrubbing."
        )
    else:
        if camera_make or camera_model:
            findings.append(
                f"Camera hardware signature verified: {camera_make or 'Unknown'} {camera_model or ''}."
            )
        else:
            findings.append(
                "EXIF block is present but lacks standard camera hardware make/model tags."
            )

    # Calculate Suspicion Score
    score = 0.10
    if editing_software_detected:
        score += 0.50
    if timestamp_mismatch:
        score += 0.20
    if metadata_stripped:
        score += 0.15

    score = min(max(score, 0.05), 0.95)

    if score >= 0.55:
        risk_level = "ELEVATED"
    elif score >= 0.30:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    return MetadataForensicResult(
        has_exif=has_exif,
        camera_make=camera_make,
        camera_model=camera_model,
        software_tag=software_tag,
        date_original=date_original,
        date_modified=date_modified,
        editing_software_detected=editing_software_detected,
        detected_software_name=detected_software_name,
        timestamp_mismatch=timestamp_mismatch,
        metadata_stripped=metadata_stripped,
        raw_exif_dict=exif_data,
        metadata_suspicion_score=float(score),
        forensic_findings=findings,
        risk_level=risk_level,
    )
