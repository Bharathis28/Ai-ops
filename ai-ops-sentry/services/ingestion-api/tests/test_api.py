"""Unit tests for the Ingestion API."""

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import dynamically to handle hyphenated directory
import importlib.util

main_path = Path(__file__).parent.parent / "main.py"
main_spec = importlib.util.spec_from_file_location("main", main_path)
main_module = importlib.util.module_from_spec(main_spec)
main_spec.loader.exec_module(main_module)
app = main_module.app

client = TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check_legacy(self):
        """Tests the legacy health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_check_v1(self):
        """Tests the v1 health check endpoint."""
        response = client.get("/api/v1/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "ingestion-api"
        assert "timestamp" in data


class TestMetricsIngestion:
    """Tests for metrics ingestion endpoints."""

    def test_receive_metrics_success(self):
        """Tests successful reception of a valid metrics batch."""
        metrics_payload = {
            "metrics": [
                {
                    "timestamp": "2025-11-26T12:00:00Z",
                    "service_name": "test-service",
                    "metric_name": "cpu_usage",
                    "value": 75.5,
                    "tags": {"host": "server-01"},
                }
            ]
        }
        response = client.post("/api/v1/metrics", json=metrics_payload)
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert data["metrics_received"] == 1
        assert "Successfully ingested" in data["message"]

    def test_receive_multiple_metrics(self):
        """Tests reception of multiple metrics."""
        metrics_payload = {
            "metrics": [
                {
                    "timestamp": "2025-11-26T12:00:00Z",
                    "service_name": "service-1",
                    "metric_name": "cpu_usage",
                    "value": 50.0,
                    "tags": {},
                },
                {
                    "timestamp": "2025-11-26T12:00:01Z",
                    "service_name": "service-2",
                    "metric_name": "memory_usage",
                    "value": 1024.0,
                    "tags": {},
                },
            ]
        }
        response = client.post("/api/v1/metrics", json=metrics_payload)
        assert response.status_code == 202
        data = response.json()
        assert data["metrics_received"] == 2

    def test_receive_empty_metrics_batch(self):
        """Tests that an empty metrics batch returns a 422 error."""
        response = client.post("/api/v1/metrics", json={"metrics": []})
        assert response.status_code == 422

    def test_receive_invalid_metric_missing_field(self):
        """Tests that a metric with a missing required field returns a 422 error."""
        invalid_payload = {
            "metrics": [
                {
                    "timestamp": "2025-11-26T12:00:00Z",
                    # "service_name" is missing
                    "metric_name": "cpu_usage",
                    "value": 75.5,
                }
            ]
        }
        response = client.post("/api/v1/metrics", json=invalid_payload)
        assert response.status_code == 422
        assert "service_name" in response.text

    def test_receive_invalid_metric_name(self):
        """Tests that a metric with an invalid name returns a 422 error."""
        invalid_payload = {
            "metrics": [
                {
                    "timestamp": "2025-11-26T12:00:00Z",
                    "service_name": "test-service",
                    "metric_name": "invalid_metric_name",
                    "value": 75.5,
                }
            ]
        }
        response = client.post("/api/v1/metrics", json=invalid_payload)
        assert response.status_code == 422

    def test_receive_invalid_metric_value_type(self):
        """Tests that a metric with invalid value type returns a 422 error."""
        invalid_payload = {
            "metrics": [
                {
                    "timestamp": "2025-11-26T12:00:00Z",
                    "service_name": "test-service",
                    "metric_name": "cpu_usage",
                    "value": "not-a-number",  # Should be float
                }
            ]
        }
        response = client.post("/api/v1/metrics", json=invalid_payload)
        assert response.status_code == 422


class TestLogsIngestion:
    """Tests for logs ingestion endpoints."""

    def test_receive_logs_success(self):
        """Tests successful reception of a valid logs batch."""
        logs_payload = {
            "logs": [
                {
                    "timestamp": "2025-11-26T12:00:00Z",
                    "service_name": "test-service",
                    "level": "INFO",
                    "message": "Test log message",
                    "metadata": {"request_id": "123"},
                }
            ]
        }
        response = client.post("/api/v1/logs", json=logs_payload)
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert data["logs_received"] == 1

    def test_receive_logs_various_levels(self):
        """Tests reception of logs with different levels."""
        logs_payload = {
            "logs": [
                {
                    "service_name": "test-service",
                    "level": "DEBUG",
                    "message": "Debug message",
                },
                {
                    "service_name": "test-service",
                    "level": "warning",  # Test case insensitivity
                    "message": "Warning message",
                },
                {
                    "service_name": "test-service",
                    "level": "ERROR",
                    "message": "Error message",
                },
            ]
        }
        response = client.post("/api/v1/logs", json=logs_payload)
        assert response.status_code == 202
        data = response.json()
        assert data["logs_received"] == 3

    def test_receive_empty_logs_batch(self):
        """Tests that an empty logs batch returns a 422 error."""
        response = client.post("/api/v1/logs", json={"logs": []})
        assert response.status_code == 422

    def test_receive_invalid_log_level(self):
        """Tests that a log with invalid level returns a 422 error."""
        invalid_payload = {
            "logs": [
                {
                    "service_name": "test-service",
                    "level": "INVALID_LEVEL",
                    "message": "Test message",
                }
            ]
        }
        response = client.post("/api/v1/logs", json=invalid_payload)
        assert response.status_code == 422

    def test_receive_log_missing_required_field(self):
        """Tests that a log with missing required field returns a 422 error."""
        invalid_payload = {
            "logs": [
                {
                    "service_name": "test-service",
                    # "level" is missing
                    "message": "Test message",
                }
            ]
        }
        response = client.post("/api/v1/logs", json=invalid_payload)
        assert response.status_code == 422
