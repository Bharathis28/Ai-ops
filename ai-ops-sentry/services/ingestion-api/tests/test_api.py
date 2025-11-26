"""Unit tests for the Ingestion API."""

from fastapi.testclient import TestClient
from unittest.mock import patch

from services.ingestion-api.main import app

client = TestClient(app)


def test_health_check():
    """Tests the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_receive_metrics_success():
    """Tests successful reception of a valid metrics batch."""
    metrics_payload = [
        {
            "timestamp": "2025-11-26T12:00:00Z",
            "service_name": "test-service",
            "metric_name": "cpu_usage",
            "value": 75.5,
            "tags": {"host": "server-01"},
        }
    ]
    response = client.post("/api/v1/metrics", json=metrics_payload)
    assert response.status_code == 202
    assert response.json() == {"status": "accepted", "message": "1 metrics received."}


def test_receive_empty_metrics_batch():
    """Tests that an empty metrics batch returns a 400 error."""
    response = client.post("/api/v1/metrics", json=[])
    assert response.status_code == 400
    assert response.json() == {"detail": "Empty metrics batch received."}


def test_receive_invalid_metric():
    """Tests that a metric with a missing required field returns a 422 error."""
    invalid_payload = [
        {
            "timestamp": "2025-11-26T12:00:00Z",
            # "service_name" is missing
            "metric_name": "cpu_usage",
            "value": 75.5,
        }
    ]
    response = client.post("/api/v1/metrics", json=invalid_payload)
    assert response.status_code == 422  # Unprocessable Entity
    assert "service_name" in response.text
    assert "Field required" in response.text


def test_receive_invalid_metric_name():
    """Tests that a metric with an invalid name returns a 422 error."""
    invalid_payload = [
        {
            "timestamp": "2025-11-26T12:00:00Z",
            "service_name": "test-service",
            "metric_name": "invalid_metric_name",  # Not in the Literal
            "value": 75.5,
        }
    ]
    response = client.post("/api/v1/metrics", json=invalid_payload)
    assert response.status_code == 422
    assert "metric_name" in response.text
    assert "unexpected value" in response.text
