"""
Unit tests for ReportLab forensic PDF report generation.
"""

import os
import tempfile
from PIL import Image
from src.reporting.pdf_generator import generate_forensic_pdf_report


def test_pdf_report_generation():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        temp_pdf_path = tf.name

    try:
        orig = Image.new("RGB", (300, 300), (100, 150, 200))
        ela = Image.new("RGB", (300, 300), (10, 15, 20))
        overlay = Image.new("RGB", (300, 300), (110, 150, 200))

        pdf_path = generate_forensic_pdf_report(
            analysis_id="VERITAS-UNITTEST-01",
            filename="unit_test_photo.jpg",
            metadata={"width": 300, "height": 300, "format": "JPEG", "file_size_kb": 85.0, "megapixels": 0.09, "mode": "RGB"},
            prediction_result={"prediction": "Authentic", "confidence_score": 0.91, "manipulated_probability": 0.09, "model_version": "RandomForest-v1.0"},
            ela_result={"mean_error": 3.4, "std_error": 2.1, "quality": 90, "forensic_interpretation": "Uniform error level distribution."},
            noise_result={"noise_inconsistency_score": 0.22, "block_variance_ratio": 4.5, "forensic_interpretation": "High spatial noise uniformity."},
            copy_move_result={"matched_pairs_count": 0, "copy_move_detected": False, "forensic_interpretation": "No cloned keypoint clusters."},
            splicing_result={"num_suspicious_zones": 0, "splicing_score": 0.12, "forensic_interpretation": "No spliced anomalies."},
            metadata_forensics={"risk_level": "LOW", "detected_software_name": None, "forensic_findings": ["Camera hardware signature verified."]},
            original_img=orig,
            ela_img=ela,
            tamper_overlay_img=overlay,
            output_path=temp_pdf_path,
        )

        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1000  # Non-empty PDF
        # Verify valid PDF magic header (%PDF-)
        with open(pdf_path, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-"

    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
