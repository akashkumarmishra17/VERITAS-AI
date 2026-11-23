# VERITAS AI &mdash; User Operation Guide & Technical Manual

Welcome to **VERITAS AI – Intelligent Image Forgery Detection and Digital Forensics System**. This guide provides step-by-step instructions for running, operating, and interpreting results from the forensic dashboard.

---

## 1. Quickstart: Installation & Launch
VERITAS AI runs locally on Windows 11 with Anaconda Python 3.10.

```bash
# 1. Activate the Conda environment
conda activate veritas

# 2. Navigate to project root directory
cd "C:\Users\AKASH MISHRA\Desktop\VERITAS_AI"

# 3. Launch the Streamlit application
streamlit run app.py
```

The application will launch automatically in your default web browser at `http://localhost:8501`.

---

## 2. Navigating the Forensic Dashboard

### A. Dashboard Overview
- **Forensic Metrics:** Summarizes total investigations performed, count of authentic images, count of confirmed forgeries, and current state of the inference engine.
- **Quick Launch Buttons:** 1-click shortcuts to initiate a new analysis, view model evaluation metrics, or browse audit history.
- **Preloaded Test Samples Showcase:** Provides 3 preloaded benchmark images (`sample_authentic_nature.jpg`, `sample_spliced_object.jpg`, `sample_copy_move_cloned.jpg`) so evaluators can run live tests with a single click.

---

### B. Performing a New Forensic Examination
1. Click **New Analysis** in the left sidebar.
2. In the upload area, drag and drop an image (`.jpg`, `.jpeg`, `.png`, or `.webp`) or click one of the sample analysis buttons.
3. Review the image metadata ribbon (Filename, Dimensions, Resolution, File Size, Detected Format).
4. *(Optional)* Expand the **Forensic Engine Parameters & Calibration** panel:
   - **ELA Resave JPEG Quality:** Select between 70% and 98% (default 90%).
   - **ELA Error Amplification Scale:** Multiplier between 10x and 35x (default 18x).
   - **Localization Anomaly Sensitivity:** Adaptive threshold sensitivity (default 0.50).
5. Click **"🚀 Execute Forensic Inspection Pipeline"**.
6. The progress indicator will track the 5 inspection stages:
   - Preprocessing & security sanitization
   - Error Level Analysis (ELA)
   - Noise variance inconsistency (PRNU)
   - Copy-Move keypoint matching & spatial displacement clustering
   - Splicing localization & Random Forest inference.

---

### C. Interpreting the Forensic Results
The system presents a multi-modal examination dashboard:

1. **Main Forensic Verdict Banner:**
   - **AUTHENTIC PHOTOGRAPH (Green):** Low error variance, uniform sensor noise, no cloned keypoint clusters, classifier probability $\le 40\%$.
   - **POTENTIALLY MANIPULATED (Red):** Elevated error variance, localized noise suppression, cloned translation clusters, or classifier probability $\ge 60\%$.
   - **INCONCLUSIVE (Amber):** Ambiguity margin ($40\% - 60\%$). Mixed physical indicators warranting manual examiner review.
   - **MODEL NOT TRAINED (Grey):** Displayed if model weights are missing; zero fake numbers.

2. **Visual Evidence Artifacts Tab:**
   - **Original Evidence Image** vs. **Error Level Analysis (ELA)**.
   - **Noise Variance Heatmap:** Identifies regions with altered sensor noise residuals.
   - **Splicing Anomaly / Bounding Box Overlay:** Highlights suspect spliced regions with bounding boxes.
   - **Copy-Move Cloned Keypoints:** Displays connecting translation vectors between source and clone regions.

3. **Forensic Radar & Feature Importances Tab:**
   - Radar chart illustrating the 5-dimensional risk profile.
   - Bar chart displaying the top mathematical features driving the Random Forest decision.

4. **Splicing Localization Zones Tab:**
   - Coordinates ($x, y$), width, height, pixel area, and relative canvas percentage for each suspect zone.

5. **Metadata & Hardware Signatures Tab:**
   - Camera make, model, original vs. modification timestamp discrepancies, and digital software editing signatures (e.g. Adobe Photoshop, GIMP).

6. **20-D Feature Vector Tab:**
   - Complete table of extracted mathematical features.

---

### D. Exporting Reports & Logging History
- **Save to Database:** Click **"💾 Save Examination to History Database"** to persist the audit trail in local SQLite (`data/veritas_history.db`).
- **Download PDF Report:** Click **"📄 Download Forensic PDF Examination Report"** to generate a publication-quality PDF containing executive summaries, embedded visual evidence, and ISO/IEC 27037 disclaimers.

---

### E. Analysis History Log
- Access past examinations, search by filename or UUID, filter by verdict, view comprehensive audit details, or export the log to CSV.

---

### F. Model Performance & Retraining
- Inspect empirical test metrics (Accuracy, Precision, Recall, F1, ROC-AUC), interactive confusion matrix, ROC curve, and 5-fold cross-validation.
- Click **"🔄 Retrain Forensic Models on Dataset"** to re-extract features and update weights.
