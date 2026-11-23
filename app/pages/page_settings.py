"""
VERITAS AI - Settings & Engine Configuration Page.
Allows calibration of decision thresholds, model selection, database maintenance,
and diagnostic environment introspection.
"""

import os
import sys
import streamlit as st
import cv2
import sklearn
import PIL

from src.database.db_manager import ForensicDatabaseManager, DEFAULT_DB_PATH


def render_settings_page():
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2.1rem; margin-bottom: 4px;">System Settings & Calibration</h1>
            <p style="color: #94a3b8; font-size: 0.95rem; margin: 0;">
                Configure forensic thresholds, inference models, database storage, and system parameters.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Forensic Engine Calibration
    st.markdown("### 1. Decision Boundary & Calibration")
    st.caption("Adjust the statistical probability margins used to categorize classifier outputs.")

    s_c1, s_c2 = st.columns(2)
    with s_c1:
        auth_threshold = st.slider(
            "Authentic Probability Cutoff (Lower Bound)",
            min_value=0.20,
            max_value=0.48,
            value=0.40,
            step=0.02,
            help="Probabilities below this cutoff are classified as Authentic."
        )
    with s_c2:
        manip_threshold = st.slider(
            "Manipulated Probability Cutoff (Upper Bound)",
            min_value=0.52,
            max_value=0.80,
            value=0.60,
            step=0.02,
            help="Probabilities above this cutoff are classified as Potentially Manipulated."
        )

    st.markdown(f"""
        <div class="veritas-card" style="padding: 14px 18px;">
            <b>Calibrated Zones:</b><br/>
            &bull; <code>[0.00 &ndash; {auth_threshold:.2f}]</code>: <b>Authentic Photograph</b><br/>
            &bull; <code>({auth_threshold:.2f} &ndash; {manip_threshold:.2f})</code>: <b>Inconclusive / Ambiguity Zone</b> (Safeguards against false certainty)<br/>
            &bull; <code>[{manip_threshold:.2f} &ndash; 1.00]</code>: <b>Potentially Manipulated</b>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # 2. Database & Storage Management
    st.markdown("### 2. Forensic History Database")
    db = ForensicDatabaseManager()
    stats = db.get_statistics()

    db_size_kb = 0.0
    if os.path.exists(DEFAULT_DB_PATH):
        db_size_kb = round(os.path.getsize(DEFAULT_DB_PATH) / 1024.0, 1)

    d_c1, d_c2, d_c3 = st.columns(3)
    with d_c1:
        st.write(f"**Database Location:** `{os.path.basename(DEFAULT_DB_PATH)}`")
        st.write(f"**Database Size:** {db_size_kb} KB")
    with d_c2:
        st.write(f"**Total Records:** {stats['total_analyses']}")
        st.write(f"**Authentic Records:** {stats['authentic_count']}")
    with d_c3:
        st.write(f"**Manipulated Records:** {stats['manipulated_count']}")
        st.write(f"**Inconclusive Records:** {stats['inconclusive_count']}")

    if st.button("Clear Session State Cache"):
        for key in list(st.session_state.keys()):
            if key != "nav_selection":
                del st.session_state[key]
        st.success("Session state cleared.")
        st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # 3. Environment & Runtime Diagnostics
    st.markdown("### 3. Runtime Environment Diagnostics")
    st.markdown(f"""
        <div class="veritas-card">
            <table style="width: 100%; font-size: 0.88rem; color: #cbd5e1;">
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">
                    <td style="padding: 6px;"><b>Python Runtime</b></td>
                    <td style="padding: 6px;">{sys.version.split()[0]} ({sys.platform})</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">
                    <td style="padding: 6px;"><b>Streamlit Framework</b></td>
                    <td style="padding: 6px;">{st.__version__}</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">
                    <td style="padding: 6px;"><b>OpenCV Library</b></td>
                    <td style="padding: 6px;">{cv2.__version__}</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">
                    <td style="padding: 6px;"><b>Scikit-Learn ML Engine</b></td>
                    <td style="padding: 6px;">{sklearn.__version__}</td>
                </tr>
                <tr>
                    <td style="padding: 6px;"><b>Pillow Imaging Core</b></td>
                    <td style="padding: 6px;">{PIL.__version__}</td>
                </tr>
            </table>
        </div>
    """, unsafe_allow_html=True)
