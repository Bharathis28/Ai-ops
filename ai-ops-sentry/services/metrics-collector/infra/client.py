"""HTTP client for sending data to the Ingestion API."""

import json
import logging
from typing import List

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from services.metrics-collector.domain.metrics import MetricPoint

logger = logging.getLogger(__name__)


class IngestionAPIClient:
    """A client for sending metrics to the Ingestion API."""

    def __init__(self, base_url: str):
        """Initializes the client with the API base URL.

        Args:
            base_url: The base URL of the Ingestion API.
        """
        if not base_url:
            raise ValueError("base_url cannot be empty.")
        self.base_url = base_url.rstrip("/")
        self.metrics_endpoint = f"{self.base_url}/api/v1/metrics"

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def send_metrics(self, metrics: List[MetricPoint]) -> None:
        """Sends a batch of metrics to the Ingestion API with retry logic.

        Args:
            metrics: A list of MetricPoint objects to send.

        Raises:
            requests.exceptions.RequestException: If the request fails after all retries.
        """
        if not metrics:
            logger.warning("Attempted to send an empty list of metrics.")
            return

        # Pydantic models must be converted to JSON-serializable dicts
        payload = [metric.model_dump(mode="json") for metric in metrics]

        try:
            logger.info(
                f"Sending {len(metrics)} metrics to {self.metrics_endpoint}..."
            )
            response = requests.post(
                self.metrics_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,  # seconds
            )
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            logger.info(
                f"Successfully sent {len(metrics)} metrics. Status: {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send metrics after multiple retries: {e}")
            raise
