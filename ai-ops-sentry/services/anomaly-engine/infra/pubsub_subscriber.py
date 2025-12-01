"""Pub/Sub subscriber for metric batches.

This module provides a subscriber that listens to metric batches from Pub/Sub,
loads the appropriate model for each service, and scores the metrics for anomalies.
"""

import logging
import json
from typing import Dict, List, Optional, Callable
from datetime import datetime, timezone
import time

from libs.core.config import GCPConfig
from libs.models.model_store import ModelStore
from libs.models.metrics import MetricPoint
from sklearn.base import BaseEstimator

# Import using sys.path to handle hyphenated directory
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import importlib.util

# Import scoring module
scoring_path = Path(__file__).parent.parent / "domain" / "scoring.py"
scoring_spec = importlib.util.spec_from_file_location("scoring", scoring_path)
scoring_module = importlib.util.module_from_spec(scoring_spec)
scoring_spec.loader.exec_module(scoring_module)
score_metrics_batch = scoring_module.score_metrics_batch
AnomalyResult = scoring_module.AnomalyResult

# Import anomaly writer
writer_path = Path(__file__).parent / "anomaly_writer.py"
writer_spec = importlib.util.spec_from_file_location("anomaly_writer", writer_path)
writer_module = importlib.util.module_from_spec(writer_spec)
writer_spec.loader.exec_module(writer_module)
AnomalyWriter = writer_module.AnomalyWriter

# Import anomaly events publisher
publisher_path = Path(__file__).parent / "anomaly_events_publisher.py"
publisher_spec = importlib.util.spec_from_file_location("publisher", publisher_path)
publisher_module = importlib.util.module_from_spec(publisher_spec)
publisher_spec.loader.exec_module(publisher_module)
AnomalyEventsPublisher = publisher_module.AnomalyEventsPublisher

logger = logging.getLogger(__name__)


class MetricsBatchSubscriber:
    """Subscriber for metric batches from Pub/Sub.

    This class subscribes to a Pub/Sub subscription, processes incoming metric batches,
    loads the appropriate model for each service, scores the metrics, and writes
    anomaly results.

    Design principles:
    - Failure in one batch does not crash the service
    - Models are cached to avoid reloading on every batch
    - Messages are properly acked/nacked based on processing success
    - All Pub/Sub and BigQuery logic is hidden behind interfaces
    """

    def __init__(
        self,
        config: GCPConfig,
        model_store: ModelStore,
        anomaly_writer: AnomalyWriter,
        anomaly_publisher: AnomalyEventsPublisher,
        score_threshold: float = 0.0,
        max_workers: int = 4,
    ):
        """Initialize the metrics batch subscriber.

        Args:
            config: GCP configuration.
            model_store: ModelStore for loading trained models.
            anomaly_writer: AnomalyWriter for persisting results.
            anomaly_publisher: AnomalyEventsPublisher for publishing events.
            score_threshold: Anomaly score threshold.
            max_workers: Maximum number of concurrent message processing workers.
        """
        self.config = config
        self.model_store = model_store
        self.anomaly_writer = anomaly_writer
        self.anomaly_publisher = anomaly_publisher
        self.score_threshold = score_threshold
        self.max_workers = max_workers

        # Model cache to avoid reloading on every batch
        self._model_cache: Dict[str, BaseEstimator] = {}

        # Subscription path
        self.subscription_path = config.get_full_subscription_path(
            config.pubsub_subscription_metric_batches
        )

        logger.info(
            f"Initialized MetricsBatchSubscriber: subscription={self.subscription_path}, "
            f"threshold={score_threshold}"
        )

        # Initialize Pub/Sub subscriber
        if config.enable_gcp_clients:
            from google.cloud import pubsub_v1
            self.subscriber = pubsub_v1.SubscriberClient()
        else:
            self.subscriber = None
            logger.warning("GCP clients disabled, Pub/Sub subscription will not start")

    def _get_model(self, service_name: str) -> Optional[BaseEstimator]:
        """Get model for a service, using cache if available.

        Args:
            service_name: Name of the service.

        Returns:
            Trained model, or None if not found.
        """
        # Check cache first
        if service_name in self._model_cache:
            logger.debug(f"Using cached model for service: {service_name}")
            return self._model_cache[service_name]

        # Load from storage
        try:
            if not self.model_store.model_exists(service_name):
                logger.warning(f"No model found for service: {service_name}")
                return None

            model = self.model_store.load_model(service_name)
            self._model_cache[service_name] = model
            logger.info(f"Loaded and cached model for service: {service_name}")
            return model

        except Exception as e:
            logger.error(f"Failed to load model for service {service_name}: {e}", exc_info=True)
            return None

    def _parse_message(self, message_data: bytes) -> List[MetricPoint]:
        """Parse Pub/Sub message into MetricPoint objects.

        Args:
            message_data: Raw message data from Pub/Sub.

        Returns:
            List of MetricPoint objects.

        Raises:
            ValueError: If message parsing fails.
        """
        try:
            data = json.loads(message_data.decode("utf-8"))

            # Expected format:
            # {
            #     "service_name": "frontend-api",
            #     "metrics": [
            #         {
            #             "timestamp": "2024-01-01T00:00:00Z",
            #             "metric_name": "cpu_usage",
            #             "value": 75.0,
            #             "tags": {}
            #         },
            #         ...
            #     ]
            # }

            service_name = data.get("service_name")
            metrics_data = data.get("metrics", [])

            if not service_name:
                raise ValueError("Message missing 'service_name' field")

            metrics = []
            for metric_data in metrics_data:
                metric = MetricPoint(
                    timestamp=datetime.fromisoformat(metric_data["timestamp"].replace("Z", "+00:00")),
                    service_name=service_name,
                    metric_name=metric_data["metric_name"],
                    value=float(metric_data["value"]),
                    tags=metric_data.get("tags", {}),
                )
                metrics.append(metric)

            logger.debug(f"Parsed {len(metrics)} metrics from message")
            return metrics

        except Exception as e:
            logger.error(f"Failed to parse message: {e}", exc_info=True)
            raise ValueError(f"Invalid message format: {e}")

    def _process_message(self, message) -> bool:
        """Process a single Pub/Sub message.

        Args:
            message: Pub/Sub message object.

        Returns:
            True if processing succeeded, False otherwise.
        """
        try:
            logger.debug(f"Processing message: {message.message_id}")

            # Parse message
            metrics = self._parse_message(message.data)

            if not metrics:
                logger.warning("No metrics in message")
                return True  # Ack empty messages

            service_name = metrics[0].service_name
            logger.info(f"Processing {len(metrics)} metrics for service: {service_name}")

            # Get model for this service
            model = self._get_model(service_name)

            if model is None:
                logger.warning(
                    f"Skipping batch for {service_name}: no model available"
                )
                return True  # Ack messages for services without models

            # Score metrics
            results = score_metrics_batch(
                metrics=metrics,
                model=model,
                score_threshold=self.score_threshold,
            )

            # Filter to only anomalies
            from importlib.util import spec_from_file_location, module_from_spec
            filter_anomalies = scoring_module.filter_anomalies
            anomalies = filter_anomalies(results)

            if anomalies:
                logger.info(f"Detected {len(anomalies)} anomalies")

                # Write to BigQuery
                try:
                    self.anomaly_writer.write_anomalies(anomalies)
                except Exception as e:
                    logger.error(f"Failed to write anomalies: {e}", exc_info=True)
                    return False  # Nack so we can retry

                # Publish to anomaly events topic
                try:
                    self.anomaly_publisher.publish_anomalies(anomalies)
                except Exception as e:
                    logger.error(f"Failed to publish anomaly events: {e}", exc_info=True)
                    # Don't fail the whole batch just because publishing failed
                    # Anomalies are already written to BigQuery

            else:
                logger.info("No anomalies detected in batch")

            return True  # Success - ack message

        except ValueError as e:
            # Invalid message format - log and ack to avoid infinite retries
            logger.error(f"Invalid message format: {e}")
            return True

        except Exception as e:
            # Unexpected error - nack to retry
            logger.error(f"Error processing message: {e}", exc_info=True)
            return False

    def _message_callback(self, message) -> None:
        """Callback for Pub/Sub message processing.

        Args:
            message: Pub/Sub message object.
        """
        success = self._process_message(message)

        if success:
            message.ack()
            logger.debug(f"Acked message: {message.message_id}")
        else:
            message.nack()
            logger.warning(f"Nacked message: {message.message_id}")

    def start(self) -> None:
        """Start the subscriber and listen for messages.

        This method blocks indefinitely, processing messages as they arrive.

        Raises:
            Exception: If subscriber fails to start.
        """
        logger.info(f"Starting subscriber for: {self.subscription_path}")

        if self.subscriber is None:
            logger.warning("[STUB] GCP clients disabled, subscriber not started")
            logger.info("Subscriber would listen for messages and process metric batches")
            # Run stub mode - just log
            logger.info("Running in stub mode - no actual subscription")
            try:
                while True:
                    time.sleep(60)
                    logger.debug("[STUB] Subscriber idle, waiting for messages...")
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
            return

        # Actual Pub/Sub subscription
        from google.cloud import pubsub_v1
        from concurrent.futures import TimeoutError

        flow_control = pubsub_v1.types.FlowControl(
            max_messages=self.max_workers,
        )

        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self._message_callback,
            flow_control=flow_control,
        )

        logger.info(f"Listening for messages on {self.subscription_path}")

        try:
            streaming_pull_future.result()
        except TimeoutError:
            streaming_pull_future.cancel()
            streaming_pull_future.result()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            streaming_pull_future.cancel()
        except Exception as e:
            logger.error(f"Subscriber error: {e}", exc_info=True)
            streaming_pull_future.cancel()
            raise

        # STUB: Simulate receiving messages
        logger.info("[STUB] Subscriber started (stub mode - no actual Pub/Sub connection)")
        logger.info("[STUB] In production, this would listen for metric batches from Pub/Sub")
        logger.info("[STUB] Use Ctrl+C to stop the service")

        try:
            while True:
                time.sleep(1)  # Keep the service running
        except KeyboardInterrupt:
            logger.info("Shutting down subscriber")

    def reload_models(self) -> None:
        """Reload all cached models.

        Useful for hot-reloading when new models are trained.
        """
        logger.info("Reloading all cached models")
        self._model_cache.clear()
        logger.info("Model cache cleared")
