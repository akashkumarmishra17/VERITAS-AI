"""
VERITAS AI - About & Scientific Methodology Page.
Provides foundational forensic theory, mathematical explanations, pipeline architecture,
and academic references designed for viva / technical examinations.
"""

import streamlit as st


def render_about_page():
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2.1rem; margin-bottom: 4px;">Forensic Science & System Architecture</h1>
            <p style="color: #94a3b8; font-size: 0.95rem; margin: 0;">
                Comprehensive methodology breakdown and mathematical principles for academic evaluation.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. High-Level Architecture Overview
    st.markdown("### 1. System Architecture Pipeline")
    st.markdown("""
        <div class="veritas-card">
            <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.6;">
                <b>VERITAS AI</b> is an end-to-end digital multimedia forensic system that fuses classical 
                Computer Vision physics-based clues with statistical Machine Learning classification. 
                Instead of treating image verification as a pure black-box deep learning task, VERITAS AI 
                models the physical and statistical footprints left by image acquisition, compression, and manipulation.
            </p>
            <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 16px; font-family: monospace; font-size: 0.85rem; color: #38bdf8; overflow-x: auto;">
                Uploaded Image &rarr; Security Sanitization &amp; EXIF Audit<br/>
                &nbsp;&nbsp;&boxur;&rarr; <b>Branch A:</b> Error Level Analysis (JPEG Q=90 Compression Differential)<br/>
                &nbsp;&nbsp;&boxur;&rarr; <b>Branch B:</b> Sensor Noise Inconsistency (High-Pass Laplacian Residual &amp; Block CV)<br/>
                &nbsp;&nbsp;&boxur;&rarr; <b>Branch C:</b> Copy-Move Feature Clustering (SIFT/ORB Keypoints &amp; Translation Vectors)<br/>
                &nbsp;&nbsp;&boxur;&rarr; <b>Branch D:</b> Multi-Domain 20-D Feature Extraction (Statistical Moments, DCT, Color Cross-Correlation)<br/>
                &nbsp;&nbsp;&boxur;&rarr; <b>Branch E:</b> Calibrated ML Classifier (Random Forest / SVM with Inconclusive Margin)<br/>
                &rarr; <b>Output:</b> Tamper Localization Heatmap + Forensic Verdict + Court-Admissible PDF Report
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 2. Forensic Pillars
    st.markdown("### 2. Forensic Methodology Breakdown")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div class="veritas-card">
                <h4 style="color: #38bdf8; margin-top: 0;">🔍 Error Level Analysis (ELA)</h4>
                <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">
                    <b>Concept:</b> Standard JPEG lossy compression operates on 8&times;8 pixel blocks using 
                    Discrete Cosine Transform (DCT) and quantization tables. When an image is saved repeatedly, 
                    each re-save introduces a predictable rate of error degradation.
                </p>
                <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">
                    <b>Mechanism:</b> The system re-saves the candidate image at a fixed quality (e.g., 90%) 
                    and computes the absolute difference:
                    <br/><code>D(x, y) = |I_orig(x, y) - I_recompressed(x, y)|</code>
                </p>
                <p style="font-size: 0.82rem; color: #f59e0b; margin-bottom: 0;">
                    <b>Forensic Caveat:</b> ELA is a forensic indicator, not proof. Sharp contrast edges naturally 
                    yield higher high-frequency error even in untouched photographs.
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="veritas-card">
                <h4 style="color: #38bdf8; margin-top: 0;">🧬 Copy-Move (Cloning) Detection</h4>
                <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">
                    <b>Concept:</b> In copy-move tampering, a region of the image is duplicated elsewhere in the same 
                    frame to conceal evidence or multiply objects.
                </p>
                <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">
                    <b>Mechanism:</b> Feature keypoints are extracted using Scale-Invariant Feature Transform (SIFT) 
                    and ORB. Descriptors are matched against each other using k-Nearest Neighbors (k=2). Trivial adjacent 
                    matches are filtered by a Euclidean distance threshold (&ge; 35px), and translation displacement 
                    vectors are clustered to detect coherent spatial translations.
                </p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="veritas-card">
                <h4 style="color: #38bdf8; margin-top: 0;">📡 Photo-Response Non-Uniformity (PRNU)</h4>
                <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">
                    <b>Concept:</b> Every physical silicon camera sensor imparts microscopic imperfections into 
                    the silicon wafers, acting as a unique camera fingerprint (PRNU) alongside photon shot noise.
                </p>
                <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">
                    <b>Mechanism:</b> High-pass filtering isolates high-frequency noise residuals:
                    <br/><code>N(x, y) = I(x, y) - MedianFilter(I(x, y))</code>
                    <br/>Local variance is evaluated across non-overlapping spatial tiles. Foreign spliced elements 
                    exhibit abrupt discontinuities in noise variance.
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="veritas-card">
                <h4 style="color: #38bdf8; margin-top: 0;">🧠 Multi-Domain Machine Learning</h4>
                <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">
                    <b>Concept:</b> Combines 20 mathematical features across 4 independent domains:
                </p>
                <ul style="font-size: 0.82rem; color: #cbd5e1; margin-bottom: 6px; padding-left: 20px;">
                    <li><b>ELA Statistics:</b> Mean, standard deviation, skewness, kurtosis, p95 error.</li>
                    <li><b>Noise Residue:</b> Global std, block variance ratio, coefficient of variation.</li>
                    <li><b>Edge Gradients:</b> Laplacian variance, Sobel edge magnitude and std.</li>
                    <li><b>Frequency &amp; Chromatic:</b> 2D DCT high-frequency ratio, R-G-B cross correlations.</li>
                </ul>
                <p style="font-size: 0.82rem; color: #34d399; margin-bottom: 0;">
                    <b>Calibrated Decision Zone:</b> Enforces an ambiguity threshold (0.40 - 0.60) labeled as 
                    <b>Inconclusive</b> to eliminate false certainty.
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Academic References
    st.markdown("### 3. Academic & Forensic Standards References")
    st.markdown("""
        1. **Farid, H.** (2009). *Exposing Digital Forgeries from JPEG Ghosts*. IEEE Transactions on Information Forensics and Security, 4(1), 154-160.
        2. **Krawetz, N.** (2007). *A Picture's Worth: Digital Image Analysis and Forensics*. Black Hat Briefings.
        3. **Amerini, I., Ballan, L., Caldelli, R., Del Bimbo, A., & Serra, G.** (2011). *A SIFT-based forensic method for copy-move attack detection and transformation recovery*. IEEE TIFS.
        4. **Dong, J., Wang, W., & Tan, T.** (2013). *CASIA Image Tampering Evaluation Database*. IEEE China Summit and International Conference on Signal and Information Processing.
        5. **ISO/IEC 27037:2012**. *Guidelines for identification, collection, acquisition and preservation of digital evidence*.
    """)
