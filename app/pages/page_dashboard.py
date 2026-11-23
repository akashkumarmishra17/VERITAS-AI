"""
VERITAS AI - Dashboard Page.
Forensic investigations overview, metrics summary, quick-launch actions, and sample showcase.
"""

import os
import streamlit as st
import pandas as pd
from PIL import Image

from ..components.ui_elements import render_metric_card
from src.database.db_manager import ForensicDatabaseManager
from src.ml.classifier import VeritasClassifier

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
TEST_SAMPLES_DIR = os.path.join(DATA_DIR, "sample_images", "test_samples")


def render_dashboard_page():
    st.markdown("""
        <div style="margin-bottom: 24px;">
            <h1 style="font-size: 2.2rem; margin-bottom: 4px;">Forensic Intelligence Dashboard</h1>
            <p style="color: #94a3b8; font-size: 1rem; margin: 0;">
                VERITAS AI &mdash; Autonomous multi-modal digital image forgery detection, 
                tamper localization, and forensic decision support.
            </p>
        </div>
    """, unsafe_allow_html=True)

    db = ForensicDatabaseManager()
    stats = db.get_statistics()
    classifier = VeritasClassifier()

    # System Status & Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Total Examinations", str(stats["total_analyses"]), "Historical SQLite records")
    with c2:
        render_metric_card("Authentic Images", str(stats["authentic_count"]), "Verified authentic capture")
    with c3:
        render_metric_card("Tampered / Forged", str(stats["manipulated_count"]), "Spliced or cloned confirmed")
    with c4:
        model_status_str = "ACTIVE (Trained)" if classifier.is_trained else "NOT TRAINED"
        render_metric_card("Inference Engine", model_status_str, classifier.model_version)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Quick Launch Action Cards
    st.markdown("### Quick Actions")
    qa_col1, qa_col2, qa_col3 = st.columns(3)
    with qa_col1:
        st.markdown("""
            <div class="veritas-card">
                <h4 style="margin-top:0; color: #38bdf8;">🔬 New Examination</h4>
                <p style="font-size: 0.85rem; color: #94a3b8;">
                    Upload an image (JPG, PNG, WEBP) to execute ELA, noise inconsistency, 
                    copy-move clustering, and ML classification.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Start New Analysis", use_container_width=True, key="btn_dash_new"):
            st.session_state["nav_selection"] = "New Analysis"
            st.rerun()

    with qa_col2:
        st.markdown("""
            <div class="veritas-card">
                <h4 style="margin-top:0; color: #38bdf8;">📊 Model Performance</h4>
                <p style="font-size: 0.85rem; color: #94a3b8;">
                    Inspect genuine evaluation metrics, confusion matrix, ROC curve, and 
                    cross-validation statistics from the test dataset.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("View Evaluation Metrics", use_container_width=True, key="btn_dash_perf"):
            st.session_state["nav_selection"] = "Model Performance"
            st.rerun()

    with qa_col3:
        st.markdown("""
            <div class="veritas-card">
                <h4 style="margin-top:0; color: #38bdf8;">📜 Analysis History</h4>
                <p style="font-size: 0.85rem; color: #94a3b8;">
                    Review past forensic reports, search records by filename, filter by verdict, 
                    and download court-style PDF audits.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Browse History Log", use_container_width=True, key="btn_dash_hist"):
            st.session_state["nav_selection"] = "Analysis History"
            st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # Interactive Preloaded Forensic Test Samples
    st.markdown("### Preloaded Forensic Test Samples")
    st.caption("Select any verified benchmark image below to quickly test the forensic pipeline without needing to upload your own files.")

    sample_col1, sample_col2, sample_col3 = st.columns(3)

    sample_1_path = os.path.join(TEST_SAMPLES_DIR, "sample_authentic_nature.jpg")
    sample_2_path = os.path.join(TEST_SAMPLES_DIR, "sample_spliced_object.jpg")
    sample_3_path = os.path.join(TEST_SAMPLES_DIR, "sample_copy_move_cloned.jpg")

    with sample_1_path and sample_col1:
        if os.path.exists(sample_1_path):
            st.image(sample_1_path, caption="Authentic Natural Landscape (Single Q=95)", use_container_width=True)
            if st.button("Analyze Authentic Sample", use_container_width=True, key="btn_sample_1"):
                with open(sample_1_path, "rb") as f:
                    st.session_state["preloaded_image_bytes"] = f.read()
                    st.session_state["preloaded_filename"] = "sample_authentic_nature.jpg"
                    st.session_state["nav_selection"] = "New Analysis"
                    st.rerun()

    with sample_2_path and sample_col2:
        if os.path.exists(sample_2_path):
            st.image(sample_2_path, caption="Spliced Donor Object (Dual-Q Compression)", use_container_width=True)
            if st.button("Analyze Spliced Sample", use_container_width=True, key="btn_sample_2"):
                with open(sample_2_path, "rb") as f:
                    st.session_state["preloaded_image_bytes"] = f.read()
                    st.session_state["preloaded_filename"] = "sample_spliced_object.jpg"
                    st.session_state["nav_selection"] = "New Analysis"
                    st.rerun()

    with sample_3_path and sample_col3:
        if os.path.exists(sample_3_path):
            st.image(sample_3_path, caption="Copy-Move Cloned Pattern (Keypoint Duplication)", use_container_width=True)
            if st.button("Analyze Cloned Sample", use_container_width=True, key="btn_sample_3"):
                with open(sample_3_path, "rb") as f:
                    st.session_state["preloaded_image_bytes"] = f.read()
                    st.session_state["preloaded_filename"] = "sample_copy_move_cloned.jpg"
                    st.session_state["nav_selection"] = "New Analysis"
                    st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # Recent Investigations Log Table
    st.markdown("### Recent Forensic Examinations")
    recent_records = db.get_records(limit=6)
    if recent_records:
        summary_rows = []
        for r in recent_records:
            summary_rows.append({
                "ID": r["analysis_uuid"][:10],
                "Timestamp": r["timestamp"],
                "Filename": r["filename"],
                "Dimensions": r["dimensions"],
                "Verdict": r["prediction"],
                "Confidence": f"{r['confidence_score'] * 100:.1f}%" if r['confidence_score'] else "N/A",
                "Copy-Move": "DETECTED" if r["copy_move_detected"] else "None",
                "Spliced Zones": r["num_suspicious_zones"],
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No prior forensic examinations recorded in the local database. Start a new examination above!")
