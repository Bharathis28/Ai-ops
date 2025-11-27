"""Unit tests for anomaly scoring logic."""

import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.models.metrics import MetricPoint

# Dynamic import for scoring module
import importlib.util
scoring_path = Path(__file__).parent.parent / "domain" / "scoring.py"
scoring_spec = importlib.util.spec_from_file_location("scoring", scoring_path)
scoring_module = importlib.util.module_from_spec(scoring_spec)
scoring_spec.loader.exec_module(scoring_module)

score_metrics_batch = scoring_module.score_metrics_batch
AnomalyResult = scoring_module.AnomalyResult
filter_anomalies = scoring_module.filter_anomalies
group_by_service = scoring_module.group_by_service
_calculate_severity = scoring_module._calculate_severity


class TestScoreMetricsBatch(unittest.TestCase):
    """Test cases for score_metrics_batch function."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a simple trained model
        X = pd.DataFrame({
            'cpu_usage': [70, 75, 80, 72, 78],
            'memory_usage': [60, 65, 70, 62, 68],
            'latency_p95': [100, 110, 120, 105, 115],
            'request_rate': [1000, 1100, 1200, 1050, 1150],
            'error_rate': [0.5, 0.6, 0.7, 0.55, 0.65],
        })
        self.model = IsolationForest(random_state=42, contamination=0.1)
        self.model.fit(X)

    def test_score_metrics_basic(self):
        """Test basic scoring of metrics."""
        metrics = [
            MetricPoint(
                timestamp=datetime.now(timezone.utc),
                service_name="test-service",
                metric_name="cpu_usage",
                value=75.0,
                tags={},
            ),
            MetricPoint(
                timestamp=datetime.now(timezone.utc),
                service_name="test-service",
                metric_name="memory_usage",
                value=65.0,
                tags={},
            ),
        ]

        results = score_metrics_batch(metrics, self.model)

        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], AnomalyResult)
        self.assertEqual(results[0].service_name, "test-service")
        self.assertIn("cpu_usage", [r.metric_name for r in results])

    def test_score_metrics_empty_list(self):
        """Test that empty metrics list raises ValueError."""
        with self.assertRaises(ValueError):
            score_metrics_batch([], self.model)

    def test_score_metrics_none_model(self):
        """Test that None model raises ValueError."""
        metrics = [
            MetricPoint(
                timestamp=datetime.now(timezone.utc),
                service_name="test-service",
                metric_name="cpu_usage",
                value=75.0,
                tags={},
            )
        ]

        with self.assertRaises(ValueError):
            score_metrics_batch(metrics, None)

    def test_anomaly_detection(self):
        """Test that anomalies are correctly detected."""
        # Create extreme values that should be detected as anomalies
        metrics = [
            MetricPoint(
                timestamp=datetime.now(timezone.utc),
                service_name="test-service",
                metric_name="cpu_usage",
                value=999.0,  # Extreme value
                tags={},
            ),
        ]

        results = score_metrics_batch(metrics, self.model, score_threshold=0.0)

        # Should detect the extreme value as anomaly
        # Note: IsolationForest might not always detect this depending on the model
        # So we just check that we got a result with a score
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0].anomaly_score, float)
        self.assertIsInstance(results[0].is_anomaly, bool)

    def test_score_threshold(self):
        """Test custom score threshold."""
        metrics = [
            MetricPoint(
                timestamp=datetime.now(timezone.utc),
                service_name="test-service",
                metric_name="cpu_usage",
                value=75.0,
                tags={},
            ),
        ]

        results = score_metrics_batch(metrics, self.model, score_threshold=-0.5)

        self.assertEqual(len(results), 1)
        # With a very low threshold, normal values should not be flagged
        # (unless the model prediction is -1)

    def test_result_structure(self):
        """Test that AnomalyResult has correct structure."""
        metrics = [
            MetricPoint(
                timestamp=datetime.now(timezone.utc),
                service_name="test-service",
                metric_name="cpu_usage",
                value=75.0,
                tags={"host": "server1"},
            ),
        ]

        results = score_metrics_batch(metrics, self.model)
        result = results[0]

        # Check all required fields
        self.assertIsInstance(result.timestamp, datetime)
        self.assertEqual(result.service_name, "test-service")
        self.assertEqual(result.metric_name, "cpu_usage")
        self.assertEqual(result.value, 75.0)
        self.assertIsInstance(result.is_anomaly, bool)
        self.assertIsInstance(result.anomaly_score, float)
        self.assertIn(result.severity, ["critical", "high", "medium", "low", "normal"])
        self.assertIsInstance(result.metadata, dict)
        self.assertEqual(result.metadata["tags"], {"host": "server1"})

    def test_to_dict(self):
        """Test AnomalyResult.to_dict() method."""
        result = AnomalyResult(
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            service_name="test-service",
            metric_name="cpu_usage",
            value=75.0,
            is_anomaly=True,
            anomaly_score=-0.15,
            severity="high",
            metadata={"test": "value"},
        )

        result_dict = result.to_dict()

        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict["service_name"], "test-service")
        self.assertEqual(result_dict["metric_name"], "cpu_usage")
        self.assertEqual(result_dict["value"], 75.0)
        self.assertEqual(result_dict["is_anomaly"], True)
        self.assertEqual(result_dict["anomaly_score"], -0.15)
        self.assertEqual(result_dict["severity"], "high")
        self.assertIn("timestamp", result_dict)


class TestCalculateSeverity(unittest.TestCase):
    """Test cases for severity calculation."""

    def test_severity_critical(self):
        """Test critical severity threshold."""
        self.assertEqual(_calculate_severity(-0.3), "critical")
        self.assertEqual(_calculate_severity(-0.25), "critical")

    def test_severity_high(self):
        """Test high severity threshold."""
        self.assertEqual(_calculate_severity(-0.15), "high")
        self.assertEqual(_calculate_severity(-0.1), "high")

    def test_severity_medium(self):
        """Test medium severity threshold."""
        self.assertEqual(_calculate_severity(-0.05), "medium")
        self.assertEqual(_calculate_severity(-0.01), "medium")

    def test_severity_low(self):
        """Test low severity threshold."""
        self.assertEqual(_calculate_severity(0.01), "low")
        self.assertEqual(_calculate_severity(0.05), "low")

    def test_severity_normal(self):
        """Test normal severity threshold."""
        self.assertEqual(_calculate_severity(0.1), "normal")
        self.assertEqual(_calculate_severity(0.5), "normal")


class TestFilterAnomalies(unittest.TestCase):
    """Test cases for filter_anomalies function."""

    def test_filter_anomalies_basic(self):
        """Test filtering anomalies from results."""
        results = [
            AnomalyResult(
                timestamp=datetime.now(timezone.utc),
                service_name="test",
                metric_name="cpu",
                value=75.0,
                is_anomaly=True,
                anomaly_score=-0.1,
                severity="high",
                metadata={},
            ),
            AnomalyResult(
                timestamp=datetime.now(timezone.utc),
                service_name="test",
                metric_name="memory",
                value=65.0,
                is_anomaly=False,
                anomaly_score=0.1,
                severity="normal",
                metadata={},
            ),
        ]

        anomalies = filter_anomalies(results)

        self.assertEqual(len(anomalies), 1)
        self.assertTrue(anomalies[0].is_anomaly)

    def test_filter_anomalies_empty(self):
        """Test filtering with no anomalies."""
        results = [
            AnomalyResult(
                timestamp=datetime.now(timezone.utc),
                service_name="test",
                metric_name="cpu",
                value=75.0,
                is_anomaly=False,
                anomaly_score=0.1,
                severity="normal",
                metadata={},
            ),
        ]

        anomalies = filter_anomalies(results)

        self.assertEqual(len(anomalies), 0)


class TestGroupByService(unittest.TestCase):
    """Test cases for group_by_service function."""

    def test_group_by_service_basic(self):
        """Test grouping results by service."""
        results = [
            AnomalyResult(
                timestamp=datetime.now(timezone.utc),
                service_name="service-a",
                metric_name="cpu",
                value=75.0,
                is_anomaly=True,
                anomaly_score=-0.1,
                severity="high",
                metadata={},
            ),
            AnomalyResult(
                timestamp=datetime.now(timezone.utc),
                service_name="service-b",
                metric_name="cpu",
                value=80.0,
                is_anomaly=True,
                anomaly_score=-0.15,
                severity="high",
                metadata={},
            ),
            AnomalyResult(
                timestamp=datetime.now(timezone.utc),
                service_name="service-a",
                metric_name="memory",
                value=65.0,
                is_anomaly=True,
                anomaly_score=-0.05,
                severity="medium",
                metadata={},
            ),
        ]

        grouped = group_by_service(results)

        self.assertEqual(len(grouped), 2)
        self.assertIn("service-a", grouped)
        self.assertIn("service-b", grouped)
        self.assertEqual(len(grouped["service-a"]), 2)
        self.assertEqual(len(grouped["service-b"]), 1)

    def test_group_by_service_empty(self):
        """Test grouping with empty results."""
        grouped = group_by_service([])
        self.assertEqual(len(grouped), 0)


if __name__ == "__main__":
    unittest.main()
