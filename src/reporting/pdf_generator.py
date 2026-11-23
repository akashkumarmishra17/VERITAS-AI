"""
VERITAS AI - Professional Forensic PDF Report Generator.

Generates comprehensive, court-admissible-style digital forensic examination
reports containing investigation metadata, multi-forensic visual evidence,
feature distributions, and scientific limitations disclaimers.
"""

import io
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether,
    HRFlowable,
)


def _pil_to_temp_file(img: Image.Image, max_dim: int = 500) -> str:
    """Helper to save PIL image as a temporary JPEG file for ReportLab."""
    w, h = img.size
    scale = min(max_dim / float(max(w, h)), 1.0)
    resized = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    if resized.mode != "RGB":
        resized = resized.convert("RGB")
    resized.save(path, format="JPEG", quality=90)
    return path


def generate_forensic_pdf_report(
    analysis_id: str,
    filename: str,
    metadata: Dict[str, Any],
    prediction_result: Dict[str, Any],
    ela_result: Dict[str, Any],
    noise_result: Dict[str, Any],
    copy_move_result: Dict[str, Any],
    splicing_result: Dict[str, Any],
    metadata_forensics: Dict[str, Any],
    original_img: Image.Image,
    ela_img: Image.Image,
    tamper_overlay_img: Optional[Image.Image] = None,
    output_path: Optional[str] = None,
) -> str:
    """
    Builds a professional forensic examination report in PDF format.

    Returns:
        str: Absolute path to the generated PDF file.
    """
    if not output_path:
        reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "reports"))
        os.makedirs(reports_dir, exist_ok=True)
        safe_id = "".join(c for c in analysis_id if c.isalnum() or c in ("-", "_"))
        output_path = os.path.join(reports_dir, f"VERITAS_Report_{safe_id}.pdf")

    temp_files = []
    try:
        orig_temp = _pil_to_temp_file(original_img, max_dim=450)
        ela_temp = _pil_to_temp_file(ela_img, max_dim=450)
        temp_files.extend([orig_temp, ela_temp])

        overlay_temp = None
        if tamper_overlay_img is not None:
            overlay_temp = _pil_to_temp_file(tamper_overlay_img, max_dim=450)
            temp_files.append(overlay_temp)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        # Custom Typography
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
        )
        section_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "BodySmall",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155"),
        )
        body_bold = ParagraphStyle(
            "BodyBold",
            parent=body_style,
            fontName="Helvetica-Bold",
        )
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b"),
        )

        story = []

        # 1. Header Banner Table
        header_data = [
            [
                Paragraph("<b>VERITAS AI</b> &mdash; Digital Image Forensic Report", title_style),
                Paragraph(f"<b>Report ID:</b> {analysis_id}<br/><b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style),
            ]
        ]
        header_table = Table(header_data, colWidths=[360, 180])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=10))

        # 2. Executive Summary & Verdict Badge
        verdict = prediction_result.get("prediction", "Inconclusive")
        prob_manip = prediction_result.get("manipulated_probability")
        conf_str = f"{prob_manip * 100:.1f}% Manipulated Risk" if prob_manip is not None else "N/A (Untrained)"
        model_ver = prediction_result.get("model_version", "Unknown")

        if verdict == "Authentic":
            badge_bg = colors.HexColor("#dcfce7")
            badge_border = colors.HexColor("#16a34a")
            badge_text_color = colors.HexColor("#15803d")
        elif verdict == "Potentially Manipulated":
            badge_bg = colors.HexColor("#fee2e2")
            badge_border = colors.HexColor("#dc2626")
            badge_text_color = colors.HexColor("#b91c1c")
        elif verdict == "MODEL NOT TRAINED":
            badge_bg = colors.HexColor("#f1f5f9")
            badge_border = colors.HexColor("#64748b")
            badge_text_color = colors.HexColor("#475569")
        else:
            badge_bg = colors.HexColor("#fef3c7")
            badge_border = colors.HexColor("#d97706")
            badge_text_color = colors.HexColor("#b45309")

        verdict_cell = Paragraph(
            f"<font size='14' color='{badge_text_color.hexval()}'><b>VERDICT: {verdict.upper()}</b></font><br/>"
            f"<font size='9' color='#334155'>Confidence: <b>{conf_str}</b> | Architecture: <b>{model_ver}</b></font>",
            body_style
        )
        verdict_table = Table([[verdict_cell]], colWidths=[540])
        verdict_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), badge_bg),
            ("BOX", (0, 0), (-1, -1), 1.5, badge_border),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(verdict_table)
        story.append(Spacer(1, 10))

        # 3. File Metadata Table
        story.append(Paragraph("1. Evidence File Specifications", section_style))
        meta_table_data = [
            [
                Paragraph("<b>Filename:</b>", body_style), Paragraph(str(filename), body_style),
                Paragraph("<b>Dimensions:</b>", body_style), Paragraph(f"{metadata.get('width', 0)} &times; {metadata.get('height', 0)} px", body_style),
            ],
            [
                Paragraph("<b>File Format:</b>", body_style), Paragraph(str(metadata.get("format", "Unknown")), body_style),
                Paragraph("<b>Megapixels:</b>", body_style), Paragraph(f"{metadata.get('megapixels', 0)} MP", body_style),
            ],
            [
                Paragraph("<b>File Size:</b>", body_style), Paragraph(f"{metadata.get('file_size_kb', 0)} KB", body_style),
                Paragraph("<b>Color Mode:</b>", body_style), Paragraph(str(metadata.get("mode", "RGB")), body_style),
            ],
        ]
        meta_table = Table(meta_table_data, colWidths=[90, 180, 90, 180])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # 4. Multi-Forensic Findings Table
        story.append(Paragraph("2. Forensic Inspection Summary", section_style))
        forensic_table_data = [
            [Paragraph("<b>Forensic Module</b>", body_bold), Paragraph("<b>Key Indicator Metric</b>", body_bold), Paragraph("<b>Observation & Significance</b>", body_bold)],
            [
                Paragraph("Error Level Analysis (ELA)", body_style),
                Paragraph(f"Mean Error: {ela_result.get('mean_error', 0)}<br/>Std Error: {ela_result.get('std_error', 0)}", body_style),
                Paragraph(str(ela_result.get("forensic_interpretation", "N/A")), body_style),
            ],
            [
                Paragraph("Noise Inconsistency", body_style),
                Paragraph(f"Score: {noise_result.get('noise_inconsistency_score', 0)}<br/>Ratio: {noise_result.get('block_variance_ratio', 0)}", body_style),
                Paragraph(str(noise_result.get("forensic_interpretation", "N/A")), body_style),
            ],
            [
                Paragraph("Copy-Move Detection", body_style),
                Paragraph(f"Pairs: {copy_move_result.get('matched_pairs_count', 0)}<br/>Detected: {'YES' if copy_move_result.get('copy_move_detected') else 'NO'}", body_style),
                Paragraph(str(copy_move_result.get("forensic_interpretation", "N/A")), body_style),
            ],
            [
                Paragraph("Splicing Localization", body_style),
                Paragraph(f"Zones: {splicing_result.get('num_suspicious_zones', 0)}<br/>Score: {splicing_result.get('splicing_score', 0)}", body_style),
                Paragraph(str(splicing_result.get("forensic_interpretation", "N/A")), body_style),
            ],
            [
                Paragraph("Metadata & EXIF", body_style),
                Paragraph(f"Risk: {metadata_forensics.get('risk_level', 'LOW')}<br/>Software: {metadata_forensics.get('detected_software_name') or 'None'}", body_style),
                Paragraph("; ".join(metadata_forensics.get("forensic_findings", ["No EXIF anomalies."])), body_style),
            ],
        ]
        forensic_table = Table(forensic_table_data, colWidths=[130, 110, 300])
        forensic_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ffffff")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(forensic_table)
        story.append(Spacer(1, 10))

        # 5. Visual Evidence Panel
        story.append(Paragraph("3. Visual Evidence Artifacts", section_style))
        img_w = 260
        img_h = 160
        img_row1 = [
            [
                Paragraph("<b>Original Evidence Image</b>", body_style),
                Paragraph(f"<b>Error Level Analysis (JPEG Q={ela_result.get('quality', 90)})</b>", body_style),
            ],
            [
                RLImage(orig_temp, width=img_w, height=img_h),
                RLImage(ela_temp, width=img_w, height=img_h),
            ]
        ]
        img_table = Table(img_row1, colWidths=[270, 270])
        img_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(KeepTogether([img_table]))

        if overlay_temp is not None:
            story.append(Spacer(1, 6))
            overlay_row = [
                [Paragraph("<b>Localization Anomaly Map / Suspicious Zones Overlay</b>", body_style)],
                [RLImage(overlay_temp, width=320, height=180)]
            ]
            overlay_table = Table(overlay_row, colWidths=[540])
            overlay_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(KeepTogether([overlay_table]))

        story.append(Spacer(1, 10))

        # 6. Legal & Scientific Limitations Disclaimer
        story.append(Paragraph("4. Scientific Integrity & Limitations Disclaimer", section_style))
        disclaimer_text = (
            "NOTICE: VERITAS AI is an automated digital forensic decision-support tool based on statistical "
            "machine learning and computer vision algorithms. Error Level Analysis (ELA) and noise residue patterns "
            "serve as investigative indicators rather than incontrovertible mathematical proofs of tampering. "
            "Re-compression, social media scrubbing, and high-frequency edge textures naturally introduce compression "
            "artifacts. All conclusions presented in this automated report should be validated by a certified "
            "digital forensic examiner under standard forensic evidence handling procedures (ISO/IEC 27037:2012)."
        )
        story.append(Paragraph(disclaimer_text, disclaimer_style))

        # Build document
        doc.build(story)
        return output_path

    finally:
        # Clean up temporary files
        for p in temp_files:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
