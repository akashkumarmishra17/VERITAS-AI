# VERITAS AI &mdash; Dataset Setup & Acquisition Guide

## 1. Overview
VERITAS AI is designed to work with standard academic digital forensics benchmarks for image tampering detection and localization:
- **CASIA Image Tampering Evaluation Database (CASIA v1.0 & v2.0)**
- **CoMoFoD Copy-Move Forgery Database**
- **NIST Nimble 2016 / 2017 Challenge Datasets**
- **VERITAS Procedurally Synthesized Forensic Benchmark (Included)**

In strict adherence to academic integrity and intellectual property licensing, large external third-party datasets (such as CASIA's multi-gigabyte archives) are not bundled directly into the repository. Instead, this project provides:
1. An automated, reproducible benchmark generator (`src/create_sample_dataset.py`) providing genuine authentic, spliced, and copy-move test samples.
2. Complete instructions below to download, verify, and place external academic datasets.

---

## 2. Included Synthetic Benchmark Dataset
The project includes a procedural image generation script that simulates physical camera noise, single-generation and multi-generation JPEG quantization, and geometric copy-move operations.

To re-generate or expand the included benchmark dataset:
```bash
python src/create_sample_dataset.py
```
This generates:
- `data/sample_images/authentic/`: Single-generation authentic JPEG photographs with uniform sensor noise profiles.
- `data/sample_images/manipulated/`: Dual-compression spliced images and cloned keypoint copy-move images.
- `data/sample_images/test_samples/`: User-accessible demonstration images for instant UI testing:
  - `sample_authentic_nature.jpg`
  - `sample_spliced_object.jpg`
  - `sample_copy_move_cloned.jpg`

---

## 3. Integrating CASIA 2.0 Dataset

### About CASIA 2.0
The CASIA Image Tampering Database (developed by the Institute of Automation, Chinese Academy of Sciences) is the most widely cited benchmark in image forensics.
- **Authentic Class (`Au`)**: 7,491 natural photographs (uncompressed TIFF and single-save JPEG).
- **Tampered Class (`Tp`)**: 5,123 manipulated images spanning splicing and copy-move operations with boundary feathering.

### Step-by-Step CASIA Setup Instructions
1. **Download:**
   Download CASIA 2.0 from the official IEEE / academic repository or authorized mirror (e.g. Kaggle `sophatvathana/casia-dataset`):
   ```bash
   # Using Kaggle CLI (if configured):
   kaggle datasets download -d sophatvathana/casia-dataset
   ```
2. **Extraction:**
   Extract the archive:
   ```
   data/
   ├── casia2/
   │   ├── Au/    <-- (Authentic images: Au_ani_..., Au_nat_...)
   │   └── Tp/    <-- (Tampered images: Tp_D_..., Tp_S_...)
   ```
3. **Train VERITAS AI on CASIA:**
   Run the training pipeline specifying the CASIA directories:
   ```bash
   python -c "
   from src.ml.train_classical import load_dataset_features, train_and_evaluate
   df = load_dataset_features('data/casia2/Au', 'data/casia2/Tp', cache_csv='data/casia2_features.csv')
   train_and_evaluate(df)
   "
   ```

---

## 4. Integrating CoMoFoD Dataset

### About CoMoFoD
The CoMoFoD (Copy-Move Forgery Database) consists of 260 forged image sets in 512x512 resolution, testing copy-move robustness against transformations such as rotation, scaling, JPEG compression, and noise addition.

### Setup Instructions:
1. Download CoMoFoD from the official university website.
2. Place the uncompressed images into `data/comofod/`.
3. To evaluate keypoint clustering accuracy on CoMoFoD:
   ```bash
   python -c "
   import glob
   from PIL import Image
   from src.forensics.copy_move import detect_copy_move
   for img_path in glob.glob('data/comofod/*_F.png')[:10]:
       im = Image.open(img_path)
       res = detect_copy_move(im)
       print(img_path, 'Detected:', res.copy_move_detected, 'Clusters:', res.clustered_clusters_count)
   "
   ```

---

## 5. Directory Structure Standards
Ensure your directories adhere to this standardized layout:
```
data/
├── extracted_features.csv        <-- Cached 20-D feature vectors
├── veritas_history.db            <-- Local SQLite forensic history database
└── sample_images/
    ├── authentic/               <-- Authentic training images (Class 0)
    ├── manipulated/             <-- Manipulated training images (Class 1)
    └── test_samples/            <-- Demonstration images for UI upload
```
