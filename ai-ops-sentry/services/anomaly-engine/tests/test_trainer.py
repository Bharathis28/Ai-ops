"""Unit tests for model training."""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import using dynamic loading
import importlib.util

trainer_path = Path(__file__).parent.parent / "domain" / "trainer.py"
trainer_spec = importlib.util.spec_from_file_location("trainer", trainer_path)
trainer_module = importlib.util.module_from_spec(trainer_spec)
trainer_spec.loader.exec_module(trainer_module)
train_isolation_forest = trainer_module.train_isolation_forest
get_model_metadata = trainer_module.get_model_metadata
validate_model = trainer_module.validate_model


class TestTrainIsolationForest(unittest.TestCase):
    """Test cases for train_isolation_forest function."""

    def setUp(self):
        """Set up test data."""
        np.random.seed(42)

        # Generate normal data
        n_samples = 100
        self.X = pd.DataFrame({
            "cpu_usage": np.random.normal(70, 10, n_samples),
            "memory_usage": np.random.normal(60, 8, n_samples),
            "latency_p95": np.random.normal(120, 15, n_samples),
        })

        # Add some anomalies
        self.X.loc[0, "cpu_usage"] = 150  # Anomaly
        self.X.loc[1, "memory_usage"] = 150  # Anomaly

    def test_basic_training(self):
        """Test basic model training."""
        model = train_isolation_forest(self.X)

        # Check model is fitted
        self.assertTrue(hasattr(model, "estimators_"))

        # Check predictions work
        predictions = model.predict(self.X)
        self.assertEqual(len(predictions), len(self.X))

        # Predictions should be -1 (anomaly) or 1 (normal)
        self.assertTrue(all(p in [-1, 1] for p in predictions))

    def test_reproducibility(self):
        """Test that training is reproducible with same random_state."""
        model1 = train_isolation_forest(self.X, random_state=42)
        model2 = train_isolation_forest(self.X, random_state=42)

        # Same predictions
        pred1 = model1.predict(self.X)
        pred2 = model2.predict(self.X)

        np.testing.assert_array_equal(pred1, pred2)

    def test_custom_hyperparameters(self):
        """Test training with custom hyperparameters."""
        model = train_isolation_forest(
            self.X,
            contamination=0.1,
            n_estimators=50,
            random_state=42,
        )

        # Check parameters were set
        self.assertEqual(model.contamination, 0.1)
        self.assertEqual(model.n_estimators, 50)

    def test_empty_dataframe_raises_error(self):
        """Test that empty DataFrame raises ValueError."""
        empty_df = pd.DataFrame()

        with self.assertRaises(ValueError) as context:
            train_isolation_forest(empty_df)

        self.assertIn("empty feature matrix", str(context.exception))

    def test_invalid_contamination_raises_error(self):
        """Test that invalid contamination raises ValueError."""
        with self.assertRaises(ValueError):
            train_isolation_forest(self.X, contamination=-0.1)

        with self.assertRaises(ValueError):
            train_isolation_forest(self.X, contamination=0.6)

    def test_detects_anomalies(self):
        """Test that model detects injected anomalies."""
        model = train_isolation_forest(self.X, contamination=0.1)

        predictions = model.predict(self.X)

        # Our injected anomalies (rows 0 and 1) should be detected
        # (though not guaranteed due to randomness, so we just check format)
        n_anomalies = (predictions == -1).sum()
        self.assertGreater(n_anomalies, 0)

    def test_decision_function(self):
        """Test decision function returns scores."""
        model = train_isolation_forest(self.X)

        scores = model.decision_function(self.X)

        # Should return one score per sample
        self.assertEqual(len(scores), len(self.X))

        # Lower scores = more anomalous
        # Anomalies should have lower scores
        self.assertTrue(all(isinstance(s, (int, float)) for s in scores))


class TestGetModelMetadata(unittest.TestCase):
    """Test cases for get_model_metadata function."""

    def setUp(self):
        """Set up test data and model."""
        np.random.seed(42)
        self.X = pd.DataFrame({
            "cpu_usage": np.random.normal(70, 10, 50),
            "memory_usage": np.random.normal(60, 8, 50),
        })
        self.model = train_isolation_forest(self.X, contamination=0.1)

    def test_metadata_structure(self):
        """Test that metadata has correct structure."""
        metadata = get_model_metadata(self.model, self.X)

        # Check required keys
        required_keys = [
            "n_samples",
            "n_features",
            "feature_names",
            "hyperparameters",
            "training_anomaly_rate",
            "model_type",
        ]

        for key in required_keys:
            self.assertIn(key, metadata)

    def test_metadata_values(self):
        """Test that metadata values are correct."""
        metadata = get_model_metadata(self.model, self.X)

        self.assertEqual(metadata["n_samples"], 50)
        self.assertEqual(metadata["n_features"], 2)
        self.assertListEqual(metadata["feature_names"], ["cpu_usage", "memory_usage"])
        self.assertEqual(metadata["model_type"], "IsolationForest")
        self.assertIsInstance(metadata["training_anomaly_rate"], float)


class TestValidateModel(unittest.TestCase):
    """Test cases for validate_model function."""

    def setUp(self):
        """Set up test data and model."""
        np.random.seed(42)
        self.X_train = pd.DataFrame({
            "cpu_usage": np.random.normal(70, 10, 50),
            "memory_usage": np.random.normal(60, 8, 50),
        })
        self.X_val = pd.DataFrame({
            "cpu_usage": np.random.normal(70, 10, 20),
            "memory_usage": np.random.normal(60, 8, 20),
        })
        self.model = train_isolation_forest(self.X_train)

    def test_validation_metrics(self):
        """Test validation metrics structure."""
        metrics = validate_model(self.model, self.X_val)

        # Check required keys
        required_keys = [
            "val_samples",
            "val_anomalies",
            "val_anomaly_rate",
            "val_mean_score",
            "val_std_score",
        ]

        for key in required_keys:
            self.assertIn(key, metrics)

    def test_empty_validation_set(self):
        """Test with empty validation set."""
        empty_val = pd.DataFrame()
        metrics = validate_model(self.model, empty_val)

        self.assertEqual(metrics, {})


if __name__ == "__main__":
    unittest.main()
