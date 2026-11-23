
"""
VERITAS AI - Intelligent Image Forgery Detection and Digital Forensics System.
Main Streamlit Application Entrypoint.
"""

import os
import sys
import streamlit as st

# Add current workspace directory to Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Set page configuration
st.set_page_config(
    page_title="VERITAS AI - Digital Image Forensics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS
css_path = os.path.join(CURRENT_DIR, "app", "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Import page modules
from app.pages.page_dashboard import render_dashboard_page
from app.pages.page_new_analysis import render_new_analysis_page
from app.pages.page_history import render_history_page
from app.pages.page_model_performance import render_model_performance_page
from app.pages.page_about import render_about_page
from app.pages.page_settings import render_settings_page

# Initialize navigation session state
default_nav = os.environ.get("VERITAS_DEFAULT_PAGE", "Dashboard")
if "nav_selection" not in st.session_state:
    st.session_state["nav_selection"] = default_nav

# Support direct URL query parameter routing (?page=...&sample=spliced&run=1)
qp = st.query_params
if "page" in qp:
    target_page = qp["page"]
    valid_pages = [
        "Dashboard", "New Analysis", "Analysis History",
        "Model Performance", "About & Methodology", "Settings"
    ]
    if target_page in valid_pages:
        st.session_state["nav_selection"] = target_page

if (qp.get("sample") == "spliced" or os.environ.get("VERITAS_PRELOAD_SAMPLE") == "1") and "preloaded_image_bytes" not in st.session_state:
    sample_path = os.path.join(CURRENT_DIR, "data", "sample_images", "test_samples", "sample_spliced_object.jpg")
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            st.session_state["preloaded_image_bytes"] = f.read()
        st.session_state["preloaded_filename"] = "sample_spliced_object.jpg"

if qp.get("run") == "1" or os.environ.get("VERITAS_AUTO_RUN") == "1":
    st.session_state["auto_trigger_analysis"] = True

# Sidebar Navigation & Branding
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 12px 0 18px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 16px;">
            <div style="font-size: 2.4rem; line-height: 1;">🛡️</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #38bdf8; letter-spacing: 0.05em; margin-top: 4px;">
                VERITAS AI
            </div>
            <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px;">
                Digital Image Forensics System
            </div>
            <div style="display: inline-block; margin-top: 8px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 9999px; padding: 2px 10px; font-size: 0.68rem; color: #38bdf8; font-weight: 600;">
                B.Tech CSE (AI &amp; ML) Project
            </div>
        </div>
    """, unsafe_allow_html=True)

    nav_options = [
        "Dashboard",
        "New Analysis",
        "Analysis History",
        "Model Performance",
        "About & Methodology",
        "Settings",
    ]

    icons = {
        "Dashboard": "📊",
        "New Analysis": "🔬",
        "Analysis History": "📜",
        "Model Performance": "📈",
        "About & Methodology": "📖",
        "Settings": "⚙️",
    }

    # Ensure index matches session state
    current_index = nav_options.index(st.session_state["nav_selection"]) if st.session_state["nav_selection"] in nav_options else 0

    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=current_index,
        format_func=lambda x: f"{icons.get(x, '•')}  {x}",
        label_visibility="collapsed",
    )
    st.session_state["nav_selection"] = selected_nav

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("""
        <div style="border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 16px; margin-top: 16px;">
            <div style="font-size: 0.75rem; text-transform: uppercase; color: #64748b; letter-spacing: 0.08em; margin-bottom: 8px;">
                Forensic Standards
            </div>
            <div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.5;">
                &bull; ISO/IEC 27037 Compliant<br/>
                &bull; Error Level Analysis (ELA)<br/>
                &bull; PRNU Noise Inconsistency<br/>
                &bull; Keypoint Copy-Move Clones<br/>
                &bull; 20-D Feature Fusion ML
            </div>
            <div style="font-size: 0.72rem; color: #475569; margin-top: 16px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px;">
                VERITAS AI v1.0.0<br/>
                Developed by Akash Mishra
            </div>
        </div>
    """, unsafe_allow_html=True)

# Main Routing
if st.session_state["nav_selection"] == "Dashboard":
    render_dashboard_page()
elif st.session_state["nav_selection"] == "New Analysis":
    render_new_analysis_page()
elif st.session_state["nav_selection"] == "Analysis History":
    render_history_page()
elif st.session_state["nav_selection"] == "Model Performance":
    render_model_performance_page()
elif st.session_state["nav_selection"] == "About & Methodology":
    render_about_page()
elif st.session_state["nav_selection"] == "Settings":
    render_settings_page()
