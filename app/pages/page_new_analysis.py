"""
VERITAS AI - New Forensic Examination Page.
Handles image upload, parameter configuration, multi-stage forensic execution,
visual artifacts rendering, ML inference, database logging, and PDF report export.
"""

import os
import uuid
import time
from typing import Optional
import streamlit as st
import pandas as pd
from PIL import Image

from ..components.ui_elements import (
    render_verdict_banner,
    plot_forensic_radar,
    plot_feature_importances,
)
from src.preprocessing import validate_image_bytes, load_image_rgb, ImageValidationError
from src.forensics.ela import perform_ela
from src.forensics.noise_analysis import analyze_noise_inconsistency
from src.forensics.copy_move import detect_copy_move
from src.forensics.splicing_localization import generate_tamper_localization_mask
from src.forensics.metadata_forensics import analyze_image_metadata
from src.ml.classifier import VeritasClassifier
from src.database.db_manager import ForensicDatabaseManager
from src.reporting.pdf_generator import generate_forensic_pdf_report


def render_new_analysis_page():
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2.1rem; margin-bottom: 4px;">New Forensic Examination</h1>
            <p style="color: #94a3b8; font-size: 0.95rem; margin: 0;">
                Perform comprehensive multi-modal digital image forgery analysis and manipulation localization.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar / Expander Forensic Analysis Configuration
    with st.expander("⚙️ Forensic Engine Parameters & Calibration", expanded=False):
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            ela_quality = st.slider("ELA Resave JPEG Quality", min_value=70, max_value=98, value=90, step=1,
                                    help="Quality factor for intentional re-compression. Standard forensic baseline is 90-95.")
        with c_p2:
            ela_scale = st.slider("ELA Error Amplification Scale", min_value=10.0, max_value=35.0, value=18.0, step=1.0,
                                  help="Multiplier to amplify subtle pixel-level compression residues for visual analysis.")
        with c_p3:
            sensitivity = st.slider("Localization Anomaly Sensitivity", min_value=0.1, max_value=0.9, value=0.5, step=0.05,
                                    help="Adaptive threshold sensitivity for clustering suspicious regions.")

    # File Uploader & Preloaded Sample Handler
    st.markdown("#### 1. Upload Target Image")
    uploaded_file = st.file_uploader(
        "Choose an image file to analyze",
        type=["jpg", "jpeg", "png", "webp"],
        help="Permitted formats: JPG, JPEG, PNG, WEBP. Maximum file size: 25 MB.",
    )

    image_bytes = None
    filename = "uploaded_image.jpg"

    # Check for preloaded sample selected from Dashboard
    if uploaded_file is not None:
        image_bytes = uploaded_file.read()
        filename = uploaded_file.name
        # Clear preloaded state if user uploads new file
        if "preloaded_image_bytes" in st.session_state:
            del st.session_state["preloaded_image_bytes"]
    elif "preloaded_image_bytes" in st.session_state:
        image_bytes = st.session_state["preloaded_image_bytes"]
        filename = st.session_state.get("preloaded_filename", "sample_image.jpg")
        st.info(f"Loaded benchmark sample: **{filename}** (Click 'Clear Preloaded Sample' below to upload your own file).")
        if st.button("Clear Preloaded Sample"):
            del st.session_state["preloaded_image_bytes"]
            st.rerun()

    if not image_bytes:
        st.markdown("""
            <div class="veritas-card" style="text-align: center; padding: 40px; border: 2px dashed rgba(255, 255, 255, 0.15);">
                <div style="font-size: 2.5rem; margin-bottom: 10px;">📁</div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #f8fafc;">No image selected for examination</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 6px;">
                    Drag and drop an image above or select a sample image from the Dashboard.
                </div>
            </div>
        """, unsafe_allow_html=True)
        return

    # Image Validation
    try:
        validation_info = validate_image_bytes(image_bytes, filename=filename)
        pil_image = load_image_rgb(image_bytes)
    except ImageValidationError as e:
        st.error(f"Image Validation Failed: {str(e)}")
        return
    except Exception as e:
        st.error(f"Error loading image: {str(e)}")
        return

    # Image Preview & Metadata Ribbon
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    with m_col1:
        st.caption("Filename")
        st.write(f"**{validation_info['filename']}**")
    with m_col2:
        st.caption("Dimensions")
        st.write(f"**{validation_info['width']} &times; {validation_info['height']}**")
    with m_col3:
        st.caption("File Size")
        st.write(f"**{validation_info['file_size_kb']} KB**")
    with m_col4:
        st.caption("Detected Format")
        st.write(f"**{validation_info['format']} ({validation_info['mode']})**")
    with m_col5:
        st.caption("Resolution")
        st.write(f"**{validation_info['megapixels']} MP**")

    # Execution Action Button
    st.markdown("<br/>", unsafe_allow_html=True)
    run_analysis_btn = st.button("🚀 Execute Forensic Inspection Pipeline", use_container_width=True)

    # Persist analysis state in session so interaction with tabs/downloads doesn't wipe output
    cache_key = f"analysis_{filename}_{len(image_bytes)}_{ela_quality}_{sensitivity}"
    auto_trigger = (st.session_state.get("auto_trigger_analysis", False) or os.environ.get("VERITAS_AUTO_RUN") == "1") and cache_key not in st.session_state
    if st.session_state.get("auto_trigger_analysis"):
        st.session_state["auto_trigger_analysis"] = False

    if run_analysis_btn or auto_trigger or (cache_key in st.session_state):
        if run_analysis_btn or auto_trigger:
            progress_bar = st.progress(0, text="Initializing forensic engine...")
            
            # Step 1: Preprocessing & Security
            progress_bar.progress(15, text="Step 1/5: Sanitizing image payload and parsing EXIF headers...")
            time.sleep(0.1)
            metadata_res = analyze_image_metadata(pil_image, filename=filename)

            # Step 2: Error Level Analysis
            progress_bar.progress(35, text="Step 2/5: Computing Error Level Analysis (JPEG compression differential)...")
            ela_res = perform_ela(pil_image, quality=ela_quality, scale_factor=ela_scale)

            # Step 3: Noise Inconsistency Analysis
            progress_bar.progress(55, text="Step 3/5: Estimating Photo-Response Non-Uniformity (PRNU) noise variance...")
            noise_res = analyze_noise_inconsistency(pil_image)

            # Step 4: Copy-Move Feature Matching
            progress_bar.progress(70, text="Step 4/5: Detecting SIFT/ORB keypoints and translation shift clusters...")
            copy_move_res = detect_copy_move(pil_image)

            # Step 5: Splicing Localization & ML Inference
            progress_bar.progress(85, text="Step 5/5: Running splicing anomaly localization and machine learning classifier...")
            splicing_res = generate_tamper_localization_mask(pil_image, ela_quality=ela_quality, sensitivity=sensitivity)
            
            classifier = VeritasClassifier()
            pred_res = classifier.predict(pil_image)

            progress_bar.progress(100, text="Forensic examination complete!")
            time.sleep(0.2)
            progress_bar.empty()

            analysis_uuid = f"VERITAS-{uuid.uuid4().hex[:8].upper()}"

            st.session_state[cache_key] = {
                "uuid": analysis_uuid,
                "metadata_res": metadata_res,
                "ela_res": ela_res,
                "noise_res": noise_res,
                "copy_move_res": copy_move_res,
                "splicing_res": splicing_res,
                "pred_res": pred_res,
                "pil_image": pil_image,
                "validation_info": validation_info,
            }

        # Retrieve cached analysis results
        res = st.session_state[cache_key]
        pred_res = res["pred_res"]
        ela_res = res["ela_res"]
        noise_res = res["noise_res"]
        copy_move_res = res["copy_move_res"]
        splicing_res = res["splicing_res"]
        metadata_res = res["metadata_res"]
        analysis_uuid = res["uuid"]

        st.markdown("<br/>", unsafe_allow_html=True)

        # 1. Main Forensic Verdict Banner
        render_verdict_banner(
            prediction=pred_res.prediction,
            confidence=pred_res.confidence_score,
            manipulated_probability=pred_res.manipulated_probability,
            model_version=pred_res.model_version,
            decision_zone=pred_res.calibrated_decision_zone,
            notes=pred_res.forensic_notes,
        )

        st.markdown("<br/>", unsafe_allow_html=True)

        # 2. Detailed Findings Tabs
        t_visual, t_radar, t_zones, t_exif, t_features = st.tabs([
            "🖼️ Visual Evidence Artifacts",
            "📊 Forensic Radar & Importances",
            "🎯 Splicing Localization Zones",
            "📋 Metadata & Hardware Signatures",
            "🔢 20-D Feature Vector",
        ])

        with t_visual:
            v_c1, v_c2 = st.columns(2)
            with v_c1:
                st.markdown("##### Original Evidence Image")
                st.image(pil_image, use_container_width=True)
                st.caption(f"Original {validation_info['format']} image canvas ({validation_info['width']}x{validation_info['height']}px).")

            with v_c2:
                st.markdown(f"##### Error Level Analysis (JPEG Q={ela_quality})")
                st.image(ela_res.ela_image, use_container_width=True)
                st.caption(f"Amplified compression error map ({ela_scale:.0f}x scale). Uniform color indicates consistent compression.")

            v_c3, v_c4 = st.columns(2)
            with v_c3:
                st.markdown("##### Noise Variance Heatmap (PRNU Sensor Inconsistency)")
                st.image(noise_res.noise_variance_heatmap, use_container_width=True)
                st.caption("Spatial noise variance distribution. Hot spots indicate localized smoothing or foreign sensor noise.")

            with v_c4:
                st.markdown("##### Splicing Anomaly / Bounding Box Overlay")
                st.image(splicing_res.heatmap_overlay, use_container_width=True)
                st.caption(f"Detected {splicing_res.num_suspicious_zones} localized suspicious anomaly zones.")

            if copy_move_res.copy_move_detected or copy_move_res.matched_pairs_count > 0:
                st.markdown("##### Copy-Move Cloned Keypoint Translation Vectors")
                st.image(copy_move_res.visualization_image, use_container_width=True)
                st.caption(f"Keypoint matches: {copy_move_res.matched_pairs_count} pairs ({copy_move_res.clustered_clusters_count} translation cluster(s)).")

        with t_radar:
            r_c1, r_c2 = st.columns([1, 1])
            with r_c1:
                st.markdown("##### Multi-Domain Forensic Risk Radar")
                st.caption("Normalized scores across forensic inspection dimensions:")
                radar_scores = {
                    "ELA Error Variance": min(ela_res.std_error / 12.0, 1.0),
                    "Noise Inconsistency": noise_res.noise_inconsistency_score,
                    "Copy-Move Suspicion": copy_move_res.suspicion_score,
                    "Splicing Anomaly": splicing_res.splicing_score,
                    "Metadata Risk": metadata_res.metadata_suspicion_score,
                }
                st.plotly_chart(plot_forensic_radar(radar_scores), use_container_width=True)

            with r_c2:
                st.markdown("##### Random Forest Forensic Feature Importances")
                st.caption("Top mathematical features driving the classifier decision:")
                if pred_res.feature_importances:
                    st.plotly_chart(plot_feature_importances(pred_res.feature_importances, top_n=8), use_container_width=True)
                else:
                    st.info("Feature importances unavailable (Model is not yet trained).")

        with t_zones:
            st.markdown("##### Suspicious Tampered Region Localization")
            if splicing_res.suspicious_regions:
                zones_df = pd.DataFrame(splicing_res.suspicious_regions)
                st.dataframe(zones_df, use_container_width=True, hide_index=True)
                st.caption(splicing_res.forensic_interpretation)
            else:
                st.success("No localized spliced anomaly zones detected across the image canvas.")

            st.markdown("##### Copy-Move Duplication Analysis")
            st.write(copy_move_res.forensic_interpretation)

        with t_exif:
            st.markdown("##### Metadata & Digital Signature Forensic Audit")
            e_c1, e_c2 = st.columns(2)
            with e_c1:
                st.write(f"**Camera Hardware:** {metadata_res.camera_make or 'Not Recorded'} {metadata_res.camera_model or ''}")
                st.write(f"**Software Signature:** {metadata_res.software_tag or 'None / Stripped'}")
                st.write(f"**Editing Software Flag:** {'⚠️ YES' if metadata_res.editing_software_detected else 'None Detected'}")
            with e_c2:
                st.write(f"**Original Capture Date:** {metadata_res.date_original or 'Unknown'}")
                st.write(f"**Modification Date:** {metadata_res.date_modified or 'Unknown'}")
                st.write(f"**Overall Metadata Risk Rating:** `{metadata_res.risk_level}`")

            st.markdown("###### Forensic Findings Log:")
            for item in metadata_res.forensic_findings:
                st.write(f"- {item}")

            if metadata_res.raw_exif_dict:
                with st.expander("View Full Raw EXIF Dictionary"):
                    st.json(metadata_res.raw_exif_dict)

        with t_features:
            st.markdown("##### Extracted 20-Dimensional Forensic Feature Vector")
            st.caption("Calculated multi-domain mathematical features passed into the machine learning classifier:")
            feat_list = [{"Feature Name": k, "Extracted Value": f"{v:.5f}"} for k, v in pred_res.extracted_features.items()]
            st.dataframe(pd.DataFrame(feat_list), use_container_width=True, hide_index=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # 3. Actions: Save to SQLite Database & Download PDF Report
        act_col1, act_col2 = st.columns(2)

        with act_col1:
            if st.button("💾 Save Examination to History Database", use_container_width=True):
                db = ForensicDatabaseManager()
                rec_id = db.record_analysis(
                    analysis_uuid=analysis_uuid,
                    filename=filename,
                    file_format=validation_info["format"],
                    dimensions=f"{validation_info['width']}x{validation_info['height']}",
                    file_size_kb=validation_info["file_size_kb"],
                    prediction=pred_res.prediction,
                    confidence_score=pred_res.confidence_score,
                    manipulated_probability=pred_res.manipulated_probability,
                    ela_mean_error=ela_res.mean_error,
                    noise_inconsistency_score=noise_res.noise_inconsistency_score,
                    copy_move_detected=copy_move_res.copy_move_detected,
                    num_suspicious_zones=splicing_res.num_suspicious_zones,
                    metadata_risk=metadata_res.risk_level,
                    model_version=pred_res.model_version,
                    notes_summary=pred_res.forensic_notes,
                )
                st.success(f"Examination committed to local database with Record ID #{rec_id} (UUID: {analysis_uuid})")

        with act_col2:
            # Generate PDF Report dynamically
            try:
                pdf_path = generate_forensic_pdf_report(
                    analysis_id=analysis_uuid,
                    filename=filename,
                    metadata=validation_info,
                    prediction_result=pred_res.to_dict(),
                    ela_result=ela_res.to_dict(),
                    noise_result=noise_res.to_dict(),
                    copy_move_result=copy_move_res.to_dict(),
                    splicing_result=splicing_res.to_dict(),
                    metadata_forensics=metadata_res.to_dict(),
                    original_img=pil_image,
                    ela_img=ela_res.ela_image,
                    tamper_overlay_img=splicing_res.heatmap_overlay,
                )
                with open(pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()

                st.download_button(
                    label="📄 Download Forensic PDF Examination Report",
                    data=pdf_bytes,
                    file_name=f"VERITAS_Report_{analysis_uuid}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Error generating PDF report: {str(e)}")
