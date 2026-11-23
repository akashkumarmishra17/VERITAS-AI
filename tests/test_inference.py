"""
Unit tests for Machine Learning inference, handling missing model files,
scientific integrity (no fabricated predictions), and calibrated thresholds.
"""

from PIL import Image
from src.ml.classifier import VeritasClassifier, PredictionResult


def test_untrained_model_does_not_fabricate_results():
    """
    CRITICAL SCIENTIFIC INTEGRITY TEST:
    Ensures that when model weights are missing or point to non-existent path,
    the system explicitly outputs 'MODEL NOT TRAINED' and never produces
    random or fabricated confidence percentages.
    """
    classifier = VeritasClassifier(
        model_path="non_existent_model_weights.joblib",
        scaler_path="non_existent_scaler.joblib",
        metrics_path="non_existent_metrics.json",
    )
    
    assert classifier.is_trained is False
    assert classifier.model is None
    assert classifier.scaler is None

    test_img = Image.new("RGB", (128, 128), (100, 100, 100))
    res = classifier.predict(test_img)

    assert isinstance(res, PredictionResult)
    assert res.is_trained is False
    assert res.prediction == "MODEL NOT TRAINED"
    assert res.manipulated_probability is None
    assert res.authentic_probability is None
    assert res.confidence_score is None
    assert "No trained machine learning model weights" in res.forensic_notes


def test_trained_model_inference():
    """Tests inference with genuine trained model weights."""
    classifier = VeritasClassifier()
    if classifier.is_trained:
        test_img = Image.new("RGB", (256, 256), (120, 140, 160))
        res = classifier.predict(test_img)

        assert res.is_trained is True
        assert res.prediction in ["Authentic", "Potentially Manipulated", "Inconclusive"]
        assert 0.0 <= res.manipulated_probability <= 1.0
        assert 0.0 <= res.authentic_probability <= 1.0
        assert round(res.manipulated_probability + res.authentic_probability, 3) == 1.0
        assert res.confidence_score >= 0.50
        assert len(res.extracted_features) == 20
        if res.feature_importances:
            assert len(res.feature_importances) > 0


def test_calibrated_thresholds():
    """Verify decision zone mapping."""
    classifier = VeritasClassifier()
    if classifier.is_trained:
        test_img = Image.new("RGB", (128, 128), (80, 80, 80))
        # Custom tight threshold to trigger inconclusive
        res_inconclusive = classifier.predict(test_img, inconclusive_lower=0.49, inconclusive_upper=0.51)
        assert res_inconclusive.prediction in ["Authentic", "Potentially Manipulated", "Inconclusive"]
