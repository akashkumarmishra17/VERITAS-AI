# VERITAS AI &mdash; Model Card: Random Forest Forensics Classifier

## Model Details
- **Model Name:** VERITAS Random Forest Forensics Classifier (100 Trees)
- **Model Version:** `RandomForest-v1.0`
- **Model Architecture:** Ensemble of 100 Decorrelated Decision Trees with Gini impurity split criterion, balanced class weighting, and max depth = 10.
- **Comparison Baseline:** Support Vector Classifier with Radial Basis Function kernel (RBF SVC, C=1.0).
- **Developers:** Akash Mishra, B.Tech CSE (AI & ML)
- **Release Date:** November 2026
- **License:** MIT License

---

## Intended Use
- **Primary Intended Use:** Automated decision support for multimedia forensic examiners, journalism verification desks, law enforcement digital forensic units, and academic research in image authenticity.
- **Primary Task:** Binary classification (Authentic Photograph vs. Potentially Manipulated Image) accompanied by a calibrated inconclusive decision margin (0.40 - 0.60 probability) and pixel-level tamper localization.

---

## Input Features (20-Dimensional Forensic Feature Vector)
The model consumes a 20-dimensional mathematical feature vector extracted across four physical and statistical domains:
1. `ela_mean`: Global average of pixel difference in Error Level Analysis.
2. `ela_std`: Standard deviation of ELA error dispersion.
3. `ela_max`: Peak absolute compression difference.
4. `ela_p95`: 95th percentile of ELA error distribution.
5. `ela_skewness`: Third standardized moment measuring asymmetry of compression errors.
6. `ela_kurtosis`: Fourth standardized moment measuring heavy-tailedness of error distribution.
7. `ela_anomaly_ratio`: Percentage of pixels exceeding adaptive threshold $(\mu + 2.5\sigma)$.
8. `noise_mean`: Global mean of high-pass Laplacian noise residual.
9. `noise_std`: Standard deviation of spatial noise residual.
10. `noise_cv`: Spatial coefficient of variation of local block variances ($\sigma_{blocks} / \mu_{blocks}$).
11. `noise_kurtosis`: Kurtosis of noise residual (authentic camera sensors display near-Gaussian kurtosis $\approx 3.0$).
12. `noise_block_ratio`: Ratio of maximum to minimum local block variance.
13. `laplacian_var`: Variance of Laplacian operator (focus / sharpness / blur metric).
14. `sobel_edge_mean`: Average gradient magnitude from Sobel filters.
15. `sobel_edge_std`: Standard deviation of edge gradient transitions.
16. `rg_corr`: Pearson cross-correlation between Red and Green color channels.
17. `rb_corr`: Pearson cross-correlation between Red and Blue color channels.
18. `gb_corr`: Pearson cross-correlation between Green and Blue color channels.
19. `dct_high_freq_ratio`: Energy ratio of high-frequency Discrete Cosine Transform (DCT) coefficients.
20. `dct_energy_var`: Total variance of 2D DCT spectral energy distribution.

---

## Empirical Evaluation Metrics (Held-Out Test Set)
Metrics evaluated strictly on the unseen test partition ($N=18$ images, 9 Authentic, 9 Manipulated):

| Metric | Score | Explanation |
| :--- | :--- | :--- |
| **Test Accuracy** | **61.1%** | Overall correct classifications on held-out test data. |
| **Precision** | **62.5%** | Fidelity of positive (manipulated) predictions. |
| **Recall (Sensitivity)** | **55.6%** | Proportion of actual forgeries successfully detected. |
| **F1-Score** | **0.5882** | Harmonic mean of Precision and Recall. |
| **ROC-AUC** | **0.8025** | Area Under Receiver Operating Characteristic Curve (strong discriminative ability). |
| **5-Fold Cross-Val F1** | **0.6909 &plusmn; 0.1588** | Generalization stability across 5 stratified training folds. |

### Confusion Matrix Breakdown
- **True Negatives (Authentic $\rightarrow$ Authentic):** 6
- **False Positives (Authentic $\rightarrow$ Manipulated):** 3
- **False Negatives (Manipulated $\rightarrow$ Authentic):** 4
- **True Positives (Manipulated $\rightarrow$ Manipulated):** 5

---

## Decision Calibration & Inconclusive Margin
To prevent false certainty and respect forensic evidentiary standards:
- **$P(\text{Manipulated}) \le 0.40$:** Categorized as **Authentic Photograph**.
- **$0.40 < P(\text{Manipulated}) < 0.60$:** Categorized as **Inconclusive / Ambiguity Zone** (system flags image for human examiner review rather than forcing an uncertain verdict).
- **$P(\text{Manipulated}) \ge 0.60$:** Categorized as **Potentially Manipulated**.

---

## Limitations & Ethical Considerations
1. **Multiple Social Media Re-compressions:** Platforms like WhatsApp, Twitter/X, and Facebook strip EXIF and recompress images aggressively at varying quality factors, which may diminish subtle ELA artifacts.
2. **Generative AI / Deepfakes:** This model is designed for traditional digital manipulations (splicing, cloning, inpainting, retouching) and should be complemented with specialized diffusion/GAN detectors when analyzing text-to-image synthesis.
3. **Forensic Use:** In compliance with ISO/IEC 27037:2012, automated findings must be verified by a certified digital forensic analyst prior to submission in judicial proceedings.
