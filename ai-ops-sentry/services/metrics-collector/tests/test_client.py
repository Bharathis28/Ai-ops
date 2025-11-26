"""Unit tests for the IngestionAPIClient."""

import pytest
import requests
from unittest.mock import patch, MagicMock

from services.metrics-collector.infra.client import IngestionAPIClient
from libs.models.metrics import MetricPoint


@pytest.fixture
def client():
    """Fixture for IngestionAPIClient."""
    return IngestionAPIClient(base_url="http://fake-api.com")


def test_client_initialization():
    """Tests that the client initializes correctly."""
    client = IngestionAPIClient(base_url="http://test.com/")
    assert client.base_url == "http://test.com"
    assert client.metrics_endpoint == "http://test.com/api/v1/metrics"


def test_client_initialization_empty_url():
    """Tests that initialization fails with an empty URL."""
    with pytest.raises(ValueError):
        IngestionAPIClient(base_url="")


@patch("requests.post")
def test_send_metrics_success(mock_post, client):
    """Tests successful metric sending."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    metrics = [MetricPoint(service_name="test", metric_name="cpu_usage", value=50.0)]
    client.send_metrics(metrics)

    mock_post.assert_called_once()
    # Check that the payload is correctly serialized
    sent_json = mock_post.call_args.kwargs["json"]
    assert len(sent_json) == 1
    assert sent_json[0]["service_name"] == "test"


@patch("requests.post")
def test_send_metrics_retry_on_failure(mock_post, client):
    """Tests that the client retries on HTTP failure."""
    mock_post.side_effect = requests.exceptions.ConnectionError("Test connection error")

    metrics = [MetricPoint(service_name="test", metric_name="cpu_usage", value=50.0)]

    with pytest.raises(requests.exceptions.ConnectionError):
        client.send_metrics(metrics)

    # Tenacity is configured to try 3 times
    assert mock_post.call_count == 3


def test_send_empty_metrics_list(client):
    """Tests that sending an empty list does not make an HTTP call."""
    with patch("requests.post") as mock_post:
        client.send_metrics([])
        mock_post.assert_not_called()
