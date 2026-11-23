"""
VERITAS AI - Model Performance & Scientific Evaluation Page.
Displays actual evaluated metrics from models/metrics.json, including confusion matrix,
ROC curves, feature importances, dataset composition, and methodology explanations.
"""

import os
import streamlit as st
import pandas as pd

from ..components.ui_elements import (
    render_metric_card,
    plot_confusion_matrix,
    plot_roc_curve,
    plot_feature_importances,
)
from src.ml.classifier import VeritasClassifier
from src.ml.train_classical import run_training_pipeline


def render_model_performance_page():
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2.1rem; margin-bottom: 4px;">Forensic Model Evaluation & Scientific Benchmark</h1>
            <p style="color: #94a3b8; font-size: 0.95rem; margin: 0;">
                Rigorous empirical evaluation metrics computed exclusively on unseen held-out test splits.
            </p>
        </div>
    """, unsafe_allow_html=True)

    classifier = VeritasClassifier()
    metrics = classifier.get_test_metrics()

    if not metrics or not classifier.is_trained:
        st.markdown("""
            <div class="veritas-card verdict-banner-untrained">
                <div style="font-size: 2.5rem; margin-bottom: 8px;">⚙️</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #f8fafc;">MODEL NOT TRAINED</div>
                <p style="color: #94a3b8; font-size: 0.95rem; max-width: 650px; margin: 10px auto;">
                    No trained machine learning model weights or evaluation metrics were located in the 
                    <code>models/</code> directory. In strict adherence to scientific integrity, VERITAS AI 
                    never fabricates or displays synthetic accuracy figures.
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("#### Train Model Pipeline")
        st.write("You can initiate the automated feature extraction and training pipeline right now:")
        if st.button("🚀 Train Random Forest Forensic Classifier", use_container_width=True):
            with st.spinner("Executing training pipeline (feature extraction, split, scaling, training)..."):
                run_training_pipeline()
                st.success("Training completed! Reloading metrics...")
                st.rerun()
        return

    # Display Actual Test Metrics
    eval_m = metrics["evaluation_metrics"]
    dataset_sum = metrics["dataset_summary"]
    cm = metrics["confusion_matrix"]
    roc_points = metrics.get("roc_curve", [])

    st.markdown(f"##### Evaluated Architecture: **{metrics['model_name']}**")
    st.caption(f"Last Trained: {metrics.get('training_timestamp', 'Unknown')} | Dataset: {dataset_sum['total_images']} images ({dataset_sum['authentic_count']} Authentic, {dataset_sum['manipulated_count']} Manipulated)")

    # Top Metric Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_metric_card("Test Accuracy", f"{eval_m['accuracy'] * 100:.1f}%", f"N = {dataset_sum['test_samples']} test samples")
    with c2:
        render_metric_card("Precision", f"{eval_m['precision'] * 100:.1f}%", "Manipulated class fidelity")
    with c3:
        render_metric_card("Recall (Sensitivity)", f"{eval_m['recall'] * 100:.1f}%", f"Detected {cm['true_positives']} of {cm['true_positives'] + cm['false_negatives']} forgeries")
    with c4:
        render_metric_card("F1-Score", f"{eval_m['f1_score']:.4f}", "Harmonic mean of P & R")
    with c5:
        render_metric_card("ROC-AUC", f"{eval_m['roc_auc']:.4f}", "Area under ROC curve")

    st.markdown("<br/>", unsafe_allow_html=True)

    # Interactive Visualizations: Confusion Matrix and ROC Curve
    col_vis1, col_vis2 = st.columns(2)
    with col_vis1:
        st.markdown("##### Empirical Confusion Matrix (Test Split)")
        st.caption(f"True Negatives: {cm['true_negatives']} | False Positives: {cm['false_positives']} | False Negatives: {cm['false_negatives']} | True Positives: {cm['true_positives']}")
        st.plotly_chart(plot_confusion_matrix(cm), use_container_width=True)

    with col_vis2:
        st.markdown("##### Receiver Operating Characteristic (ROC) Curve")
        st.caption(f"Quantifies discriminative ability across decision thresholds (AUC = {eval_m['roc_auc']:.4f})")
        st.plotly_chart(plot_roc_curve(roc_points, eval_m["roc_auc"]), use_container_width=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Cross-Validation & Architecture Comparison
    col_cv1, col_cv2 = st.columns(2)
    with col_cv1:
        st.markdown("##### 5-Fold Stratified Cross-Validation")
        st.markdown(f"""
            <div class="veritas-card">
                <p style="margin: 0; color: #94a3b8; font-size: 0.9rem;">
                    To test generalization stability across variable data subsets, 5-fold stratified cross-validation was performed on the training split:
                </p>
                <div style="font-size: 1.6rem; font-weight: 700; color: #38bdf8; margin: 12px 0 6px 0;">
                    F1 Mean: {eval_m.get('cross_val_f1_mean', 0.0):.4f} &plusmn; {eval_m.get('cross_val_f1_std', 0.0):.4f}
                </div>
                <p style="margin: 0; color: #64748b; font-size: 0.8rem;">
                    Stratified folds guarantee proportional representation of Authentic and Manipulated classes.
                </p>
            </div>
        """, unsafe_allow_html=True)

    with col_cv2:
        svm_comp = metrics.get("svm_comparison", {})
        st.markdown("##### Architecture Comparison: Random Forest vs SVM")
        st.markdown(f"""
            <div class="veritas-card">
                <table style="width: 100%; font-size: 0.9rem; color: #cbd5e1;">
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                        <th style="padding: 6px; text-align: left;">Classifier Architecture</th>
                        <th style="padding: 6px; text-align: center;">Test Accuracy</th>
                        <th style="padding: 6px; text-align: center;">Test F1</th>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); color: #38bdf8;">
                        <td style="padding: 6px; text-align: left;"><b>Random Forest (100 Trees)</b></td>
                        <td style="padding: 6px; text-align: center;"><b>{eval_m['accuracy'] * 100:.1f}%</b></td>
                        <td style="padding: 6px; text-align: center;"><b>{eval_m['f1_score']:.4f}</b></td>
                    </tr>
                    <tr>
                        <td style="padding: 6px; text-align: left;">Support Vector Machine (RBF)</td>
                        <td style="padding: 6px; text-align: center;">{svm_comp.get('accuracy', 0.0) * 100:.1f}%</td>
                        <td style="padding: 6px; text-align: center;">{svm_comp.get('f1_score', 0.0):.4f}</td>
                    </tr>
                </table>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Feature Importance Rankings
    st.markdown("##### Feature Importance Hierarchy")
    st.caption("Gini importance measures how significantly each forensic domain feature purifies decision nodes:")
    importances = metrics.get("feature_importances", {})
    if importances:
        st.plotly_chart(plot_feature_importances(importances, top_n=12), use_container_width=True)

    # Dataset Composition & Methodology Explanations
    with st.expander("📚 Dataset Composition & Scientific Methodology"):
        st.markdown(f"""
            **Evaluation Protocol & Scientific Rigor:**
            - **Total Evaluated Imagery:** {dataset_sum['total_images']} high-resolution images.
            - **Class Balance:** Perfectly balanced distribution ({dataset_sum['authentic_count']} Authentic vs {dataset_sum['manipulated_count']} Manipulated).
            - **Train / Test Partitioning:** 75% training ({dataset_sum['train_samples']} samples), 25% test ({dataset_sum['test_samples']} samples).
            - **Data Leakage Safeguards:** Feature scaling (`StandardScaler`) was fitted exclusively on the training partition.
            - **Forensic Classes Included:** Single-generation authentic JPEG, dual-compression spliced inserts, keypoint-rich copy-move cloned regions, and spatial noise suppression inpainting.
        """)

    # Option to retrain pipeline
    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button("🔄 Retrain Forensic Models on Dataset", use_container_width=True):
        with st.spinner("Retraining Random Forest and SVM models..."):
            run_training_pipeline()
            st.success("Models retrained and test metrics successfully updated!")
            st.rerun()
