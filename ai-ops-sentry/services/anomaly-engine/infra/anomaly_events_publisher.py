"""Publisher for anomaly events to Pub/Sub.

This module provides functionality to publish anomaly detection events
to a Pub/Sub topic for downstream processing.
"""

import logging
import json
from typing import List
from datetime import datetime

from libs.core.config import GCPConfig

# Import using sys.path to handle hyphenated directory
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import importlib.util
scoring_path = Path(__file__).parent.parent / "domain" / "scoring.py"
scoring_spec = importlib.util.spec_from_file_location("scoring", scoring_path)
scoring_module = importlib.util.module_from_spec(scoring_spec)
scoring_spec.loader.exec_module(scoring_module)
AnomalyResult = scoring_module.AnomalyResult

logger = logging.getLogger(__name__)


class AnomalyEventsPublisher:
    """Publisher for anomaly events to Pub/Sub.

    Currently stubbed - logs events instead of publishing to Pub/Sub.
    Ready for Pub/Sub integration without changing the public interface.
    """

    def __init__(self, config: GCPConfig):
        """Initialize the anomaly events publisher.

        Args:
            config: GCP configuration containing project ID and topic names.
        """
        self.config = config
        self.topic_path = config.get_full_topic_path(config.pubsub_topic_anomaly_events)
        logger.info(f"Initialized AnomalyEventsPublisher for topic: {self.topic_path}")

        # TODO: Initialize Pub/Sub client when ready for actual integration
        # from google.cloud import pubsub_v1
        # self.publisher = pubsub_v1.PublisherClient()

    def publish_anomalies(self, anomalies: List[AnomalyResult]) -> None:
        """Publish anomaly events to Pub/Sub.

        Args:
            anomalies: List of AnomalyResult objects to publish.

        Raises:
            Exception: If publishing fails (in future implementation).
        """
        if not anomalies:
            logger.warning("Attempted to publish empty anomalies list")
            return

        # TODO: Implement actual Pub/Sub publishing
        # Example implementation:
        #
        # for anomaly in anomalies:
        #     message_data = json.dumps(anomaly.to_dict()).encode("utf-8")
        #     
        #     # Add attributes for filtering
        #     attributes = {
        #         "service_name": anomaly.service_name,
        #         "severity": anomaly.severity,
        #         "metric_name": anomaly.metric_name,
        #     }
        #     
        #     future = self.publisher.publish(
        #         self.topic_path,
        #         data=message_data,
        #         **attributes
        #     )
        #     
        #     try:
        #         message_id = future.result(timeout=10)
        #         logger.debug(f"Published anomaly event: {message_id}")
        #     except Exception as e:
        #         logger.error(f"Failed to publish anomaly event: {e}")
        #         raise

        # STUB: Log events instead
        logger.info(
            f"[STUB] Would publish {len(anomalies)} anomaly events to topic {self.topic_path}"
        )

        for anomaly in anomalies:
            logger.info(
                f"[STUB] Event: {anomaly.service_name}/{anomaly.metric_name} "
                f"severity={anomaly.severity}, score={anomaly.anomaly_score:.4f}"
            )

        # Log summary
        severity_counts = {}
        for anomaly in anomalies:
            severity_counts[anomaly.severity] = severity_counts.get(anomaly.severity, 0) + 1

        logger.info(f"[STUB] Severity distribution: {severity_counts}")

    def publish_single_anomaly(self, anomaly: AnomalyResult) -> None:
        """Publish a single anomaly event.

        Args:
            anomaly: AnomalyResult object to publish.
        """
        self.publish_anomalies([anomaly])
