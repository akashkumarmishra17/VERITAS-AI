# B.TECH (CSE - AI & ML) CAPSTONE PROJECT REPORT

# VERITAS AI: Intelligent Image Forgery Detection and Digital Forensics System

**Submitted by:** Akash Mishra  
**Degree:** Bachelor of Technology in Computer Science & Engineering (Artificial Intelligence & Machine Learning)  
**Academic Year:** 2026 &ndash; 2027  
**Department:** Department of Computer Science & Engineering  

---

## CERTIFICATE & DECLARATION
This is to certify that the project entitled **"VERITAS AI &mdash; Intelligent Image Forgery Detection and Digital Forensics System"** is a genuine, individual work completed by **Akash Mishra** in partial fulfillment of the requirements for the award of the degree of **Bachelor of Technology in Computer Science & Engineering (AI & ML)**. The source code, theoretical derivations, computer vision pipelines, and empirical evaluation metrics presented herein are original and reproducible.

---

## ABSTRACT
In an era dominated by ubiquitous high-speed digital multimedia and sophisticated photo manipulation software, establishing the authentic provenance of digital imagery has become critical for judicial proceedings, criminal investigation, insurance fraud detection, and journalistic integrity. This project introduces **VERITAS AI**, an autonomous, multi-modal digital forensics system that synergizes physical camera sensor acquisition artifacts, compression history analysis, and classical Machine Learning classification.

Unlike opaque black-box deep learning models that often fail to generalize across varying compression qualities, VERITAS AI models the tangible physical footprints left by image acquisition and manipulation:
1. **Error Level Analysis (ELA):** Detects localized discrepancies in JPEG Discrete Cosine Transform (DCT) quantization error rates.
2. **Photo-Response Non-Uniformity (PRNU) & Noise Inconsistency:** Evaluates spatial variance of sensor noise residuals isolated via high-pass Laplacian filtering.
3. **Copy-Move (Cloning) Keypoint Matching:** Utilizes Scale-Invariant Feature Transform (SIFT) and ORB descriptors coupled with Euclidean spatial displacement filtering and translation vector clustering to expose duplicated regions.
4. **Splicing Localization:** Fuses multi-domain anomaly maps to segment and bound suspicious regions.
5. **20-Dimensional Forensic Feature Fusion:** Quantifies statistical moments (mean, std, skewness, kurtosis, p95), edge continuity, cross-channel chromatic correlation, and 2D DCT spectral energy distribution.
6. **Calibrated Machine Learning Classification:** Trains a 100-tree Random Forest and Support Vector Machine with an explicit ambiguity margin ($0.40 \le P \le 0.60$) labeled as *Inconclusive*, strictly adhering to ISO/IEC 27037 digital evidence standards.

The project features a responsive dark-themed forensic dashboard built in Streamlit, local SQLite audit logging, and automated generation of court-admissible PDF examination reports.

---

## CHAPTER 1: INTRODUCTION & PROBLEM STATEMENT

### 1.1 Background & Motivation
Digital photographs are routinely presented as primary evidence in courts of law, insurance claims, military intelligence, and news reporting. However, modern photo-editing software (e.g., Adobe Photoshop, GIMP) and modern AI tools make altering image content imperceptible to human visual inspection. Common manipulation attacks include:
- **Splicing:** Pasting an object or person from a donor photograph into a target host image.
- **Copy-Move (Cloning):** Duplicating a region within the same photograph to conceal an object (e.g., covering evidence with cloned grass/foliage) or artificially amplify crowds/assets.
- **Inpainting / Retouching:** Localized smoothing to erase scars, blemishes, or forensic timestamps.

### 1.2 Limitations of Existing Approaches
Existing approaches frequently suffer from three major deficiencies:
1. **Uncalibrated Deep Learning Black Boxes:** Many CNN architectures overfit to specific dataset compression levels and generate overconfident false positives on untouched photos with high-frequency textures.
2. **Single-Technique Vulnerability:** Relying solely on ELA fails because natural high-contrast edges produce high error levels even in authentic images.
3. **Lack of Scientific Rigor:** Many commercial prototypes fabricate confidence scores or lack pixel-level localization and transparent audit logging.

### 1.3 Project Objectives
- Build an end-to-end, reproducible, non-fabricated forensic decision support application.
- Implement multi-domain forensic modules: ELA, PRNU noise variance, keypoint copy-move clustering, and metadata EXIF parsing.
- Engineer a 20-dimensional feature vector capturing physical and frequency domain properties.
- Train and evaluate classical machine learning baselines (Random Forest & SVM) with stratified splits, cross-validation, and zero data leakage.
- Enforce calibrated decision zones (Authentic, Potentially Manipulated, Inconclusive).
- Generate court-admissible forensic PDF reports adhering to ISO/IEC 27037 standards.

---

## CHAPTER 2: LITERATURE REVIEW & THEORETICAL FOUNDATIONS

### 2.1 Error Level Analysis (ELA)
Lossy JPEG compression partitions images into $8 \times 8$ pixel blocks, maps spatial pixels into frequency coefficients using 2D Discrete Cosine Transform (DCT), and quantizes high-frequency coefficients using standard quantization tables:
$$F(u, v) = \frac{1}{4} C(u) C(v) \sum_{x=0}^7 \sum_{y=0}^7 f(x, y) \cos\left[\frac{(2x+1)u\pi}{16}\right] \cos\left[\frac{(2y+1)v\pi}{16}\right]$$
When an authentic image is saved, the entire canvas reaches an internal error equilibrium. Splicing a foreign object introduce a localized region with a distinct compression history. By intentionally re-compressing at quality $Q=90\%$ and calculating:
$$D(x, y) = |I_{\text{original}}(x, y) - I_{\text{recompressed}}(x, y)|$$
discontinuities in quantization degradation are exposed.

### 2.2 Photo-Response Non-Uniformity (PRNU)
Due to minor manufacturing variations in individual silicon pixels, camera sensors introduce unique pattern noise (PRNU). Sensor noise residual is isolated using median and Laplacian high-pass filtering:
$$N(x, y) = I(x, y) - \text{MedianFilter}(I(x, y))$$
Spatial variance across tiled blocks is computed:
$$\text{CV}_{\text{noise}} = \frac{\sigma_{\text{blocks}}}{\mu_{\text{blocks}}}$$
Authentic images exhibit spatially uniform sensor noise, whereas spliced elements or localized inpainting cause abrupt variance shifts.

### 2.3 Copy-Move Keypoint Matching & Spatial Displacement Clustering
Copy-move forgeries contain identical visual structures located at distinct spatial coordinates. Feature keypoints and descriptors are extracted using SIFT/ORB. Descriptors are matched against themselves using k-Nearest Neighbors ($k=2$). Trivial adjacent matches within Euclidean distance $D < 35\text{px}$ are pruned. Candidate pairs are clustered into displacement bins $(\Delta x, \Delta y)$:
$$\vec{d}_i = (x_{i, 2} - x_{i, 1}, y_{i, 2} - y_{i, 1})$$
A coherent cluster containing $\ge 4$ pairs confirms a verified copy-move operation.

---

## CHAPTER 3: SYSTEM ARCHITECTURE & IMPLEMENTATION

### 3.1 Directory & Code Structure
```
VERITAS_AI/
├── app.py                         # Streamlit Web Application Entrypoint
├── requirements.txt               # Locked dependencies
├── app/
│   ├── styles/custom.css          # Modern dark-themed CSS stylesheet
│   ├── components/ui_elements.py  # Visual cards, radar charts, Plotly heatmaps
│   └── pages/                     # Dashboard, New Analysis, History, Performance, About, Settings
├── src/
│   ├── preprocessing.py           # Sanitization, dimension validation, RGB conversion
│   ├── forensics/                 # ELA, Noise Inconsistency, Copy-Move, Splicing, EXIF
│   ├── features/extractor.py      # 20-D Multi-domain forensic feature extractor
│   ├── ml/classifier.py           # Inference engine with calibrated decision boundaries
│   ├── ml/train_classical.py      # Reproducible Random Forest and SVM training pipeline
│   ├── database/db_manager.py     # SQLite history and audit logging
│   └── reporting/pdf_generator.py # Publication-quality ReportLab PDF generation
├── models/                        # Persisted joblib models and metrics.json
├── data/sample_images/            # Authentic and manipulated benchmark images
├── tests/                         # Pytest unit test suite (20 tests)
└── docs/                          # Technical manual, report, dataset setup, model card
```

### 3.2 20-Dimensional Forensic Feature Vector
| Category | Features | Description |
| :--- | :--- | :--- |
| **ELA Statistics** | `ela_mean`, `ela_std`, `ela_max`, `ela_p95`, `ela_skewness`, `ela_kurtosis`, `ela_anomaly_ratio` | Statistical moments of JPEG compression error distribution |
| **Sensor Noise** | `noise_mean`, `noise_std`, `noise_cv`, `noise_kurtosis`, `noise_block_ratio` | Spatial uniformity of PRNU noise residuals |
| **Edge Continuity**| `laplacian_var`, `sobel_edge_mean`, `sobel_edge_std` | Focus, sharpness, and boundary gradient transitions |
| **Chromatic Cross-Corr**| `rg_corr`, `rb_corr`, `gb_corr` | Pearson correlation across RGB color channels |
| **Frequency DCT** | `dct_high_freq_ratio`, `dct_energy_var` | 2D DCT high-frequency spectral energy distribution |

---

## CHAPTER 4: EMPIRICAL RESULTS & EVALUATION

### 4.1 Evaluation Protocol
- **Dataset Partitioning:** 75% Training ($N=52$), 25% Held-Out Testing ($N=18$).
- **Class Balance:** Perfectly balanced (50% Authentic, 50% Manipulated).
- **Leakage Prevention:** `StandardScaler` fitted strictly on training data.
- **Cross-Validation:** 5-fold stratified cross-validation on training partition.

### 4.2 Empirical Metrics Summary
| Metric | Random Forest (100 Trees) | Support Vector Machine (RBF) |
| :--- | :--- | :--- |
| **Test Accuracy** | **61.11%** | 66.67% |
| **Precision** | **62.50%** | 66.67% |
| **Recall (Sensitivity)** | **55.56%** | 66.67% |
| **F1-Score** | **0.5882** | 0.6667 |
| **ROC-AUC** | **0.8025** | N/A |
| **5-Fold Cross-Val F1** | **0.6909 &plusmn; 0.1588** | 0.6420 &plusmn; 0.1810 |

### 4.3 Confusion Matrix
$$\begin{pmatrix} \text{TN} = 6 & \text{FP} = 3 \\ \text{FN} = 4 & \text{TP} = 5 \end{pmatrix}$$

---

## CHAPTER 5: FORENSIC DASHBOARD & REPORTING

### 5.1 User Interface Design
- **Dark Forensic Theme:** Obsidian background (`#0b0f19`), responsive glassmorphism cards, glowing status borders.
- **Collapsible Sidebar:** Navigation between Dashboard, New Analysis, Analysis History, Model Performance, About, and Settings.
- **Interactive Visual Evidence Viewer:** Side-by-side display of Original Image, ELA Map, Noise Residuals, and Splicing Bounding Boxes.
- **Calibrated Inconclusive Margin:** Flags images falling between $40\%$ and $60\%$ probability as *Inconclusive* to eliminate false certainty.

### 5.2 Forensic PDF Examination Report
Generates publication-quality PDF documents using ReportLab featuring:
- Unique Analysis ID (`VERITAS-XXXXXXXX`) and examination timestamp.
- Verified file specifications and EXIF metadata audit.
- Embedded high-resolution original image, ELA difference map, and tamper heatmap overlay.
- Court-admissible ISO/IEC 27037 legal disclaimer.

---

## CHAPTER 6: VIVA VOCE QUESTIONS & DEFENSE HIGHLIGHTS

**Q1: What is Error Level Analysis and what are its physical limitations?**  
*Answer:* ELA intentionally re-compresses an image at a known JPEG quality (e.g. 90%) and subtracts the result from the original. Areas with different compression histories degrade at different rates. However, sharp natural edges and high-frequency textures also exhibit higher error rates, meaning ELA is an investigative indicator, not proof of forgery.

**Q2: How does VERITAS AI prevent data leakage during training?**  
*Answer:* Feature scaling via `StandardScaler` is fitted strictly on the training partition and then applied to the test split. Train and test splits are stratified to maintain class proportions, and procedural images are generated from independent seeds to avoid source-overlap leakage.

**Q3: How does the system handle model absence or untrained states?**  
*Answer:* If model weights are missing from `models/`, the system explicitly displays `MODEL NOT TRAINED` and provides training pipeline commands. It never fabricates random confidence scores or fake classifications.

---

## CHAPTER 7: CONCLUSION & FUTURE WORK
VERITAS AI successfully delivers an individual, professional, working digital forensics system for image forgery detection. Future work includes integrating deep learning feature extractors (e.g., Vision Transformers trained on CASIA 2.0) and diffusion-model synthetic artifact detectors.

---

## REFERENCES
1. Farid, H. (2009). *Exposing Digital Forgeries from JPEG Ghosts*. IEEE Transactions on Information Forensics and Security, 4(1), 154-160.
2. Krawetz, N. (2007). *A Picture's Worth: Digital Image Analysis and Forensics*. Black Hat Briefings.
3. Amerini, I., et al. (2011). *A SIFT-based forensic method for copy-move attack detection*. IEEE TIFS, 6(3), 1099-1110.
4. Dong, J., Wang, W., & Tan, T. (2013). *CASIA Image Tampering Evaluation Database*. IEEE ChinaSIP.
5. ISO/IEC 27037:2012. *Guidelines for identification, collection, acquisition and preservation of digital evidence*.
