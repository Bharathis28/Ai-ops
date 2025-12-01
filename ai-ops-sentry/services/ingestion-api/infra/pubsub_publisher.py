"""Pub/Sub publisher for ingestion events."""

import json
import logging
from typing import List, Any
from google.cloud import pubsub_v1
from libs.core.config import GCPConfig
from libs.models.metrics import MetricPoint

logger = logging.getLogger(__name__)


class PubSubMetricsPublisher:
    """Publishes metrics to Pub/Sub topic for downstream processing."""

    def __init__(self, config: GCPConfig):
        """Initialize the Pub/Sub publisher.
        
        Args:
            config: GCP configuration containing project ID and topic names.
        """
        self.config = config
        self.project_id = config.gcp_project_id
        self.topic_name = "metrics-ingestion"
        self.topic_path = f"projects/{self.project_id}/topics/{self.topic_name}"
        
        # Initialize Pub/Sub publisher client
        self.publisher = pubsub_v1.PublisherClient()
        logger.info(f"Initialized PubSubMetricsPublisher for topic: {self.topic_path}")

    def publish_metrics(self, metrics: List[MetricPoint]) -> None:
        """Publish metrics batch to Pub/Sub topic.
        
        Args:
            metrics: List of MetricPoint objects to publish.
            
        Raises:
            Exception: If publishing to Pub/Sub fails.
        """
        if not metrics:
            logger.warning("Attempted to publish empty metrics list to Pub/Sub")
            return

        try:
            # Serialize metrics to JSON with proper datetime handling
            metrics_data = []
            for metric in metrics:
                metric_dict = metric.model_dump()
                # Convert datetime to ISO format string
                if 'timestamp' in metric_dict and hasattr(metric_dict['timestamp'], 'isoformat'):
                    metric_dict['timestamp'] = metric_dict['timestamp'].isoformat()
                metrics_data.append(metric_dict)
            
            message_data = json.dumps({
                "metrics": metrics_data,
                "count": len(metrics)
            })
            
            # Publish to Pub/Sub
            data_bytes = message_data.encode("utf-8")
            future = self.publisher.publish(self.topic_path, data_bytes)
            message_id = future.result()  # Block until published
            
            logger.info(
                f"Published {len(metrics)} metrics to Pub/Sub topic {self.topic_name}, "
                f"message_id: {message_id}"
            )
        except Exception as e:
            logger.error(f"Failed to publish metrics to Pub/Sub: {e}")
            raise

    def close(self) -> None:
        """Close the Pub/Sub publisher client."""
        if hasattr(self, 'publisher'):
            # Publisher client doesn't need explicit closing in newer versions
            logger.info("Pub/Sub metrics publisher closed")


class PubSubLogsPublisher:
    """Publishes logs to Pub/Sub topic for downstream processing."""

    def __init__(self, config: GCPConfig):
        """Initialize the Pub/Sub logs publisher.
        
        Args:
            config: GCP configuration containing project ID and topic names.
        """
        self.config = config
        self.project_id = config.gcp_project_id
        self.topic_name = "log-entries"
        self.topic_path = f"projects/{self.project_id}/topics/{self.topic_name}"
        
        # Initialize Pub/Sub publisher client
        self.publisher = pubsub_v1.PublisherClient()
        logger.info(f"Initialized PubSubLogsPublisher for topic: {self.topic_path}")

    def publish_logs(self, logs: List[Any]) -> None:
        """Publish logs batch to Pub/Sub topic.
        
        Args:
            logs: List of LogEntry objects to publish.
            
        Raises:
            Exception: If publishing to Pub/Sub fails.
        """
        if not logs:
            logger.warning("Attempted to publish empty logs list to Pub/Sub")
            return

        try:
            # Serialize logs to JSON with proper datetime handling
            logs_data = []
            for log in logs:
                log_dict = log.model_dump()
                # Convert datetime to ISO format string
                if 'timestamp' in log_dict and hasattr(log_dict['timestamp'], 'isoformat'):
                    log_dict['timestamp'] = log_dict['timestamp'].isoformat()
                logs_data.append(log_dict)
            
            message_data = json.dumps({
                "logs": logs_data,
                "count": len(logs)
            })
            
            # Publish to Pub/Sub
            data_bytes = message_data.encode("utf-8")
            future = self.publisher.publish(self.topic_path, data_bytes)
            message_id = future.result()  # Block until published
            
            logger.info(
                f"Published {len(logs)} log entries to Pub/Sub topic {self.topic_name}, "
                f"message_id: {message_id}"
            )
        except Exception as e:
            logger.error(f"Failed to publish logs to Pub/Sub: {e}")
            raise

    def close(self) -> None:
        """Close the Pub/Sub publisher client."""
        if hasattr(self, 'publisher'):
            logger.info("Pub/Sub logs publisher closed")
