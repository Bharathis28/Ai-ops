"""Anomaly scoring logic for online detection.

This module provides functions to score metrics in real-time using
trained IsolationForest models.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass

from sklearn.base import BaseEstimator
from libs.models.metrics import MetricPoint

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Result of anomaly detection for a single metric point.
    
    Attributes:
        timestamp: When the metric was recorded
        service_name: Service the metric belongs to
        metric_name: Name of the metric
        value: Metric value
        is_anomaly: Whether the point is anomalous
        anomaly_score: Anomaly score from model (lower = more anomalous)
        severity: Severity level (critical, high, medium, low, normal)
        metadata: Additional metadata about the detection
    """
    timestamp: datetime
    service_name: str
    metric_name: str
    value: float
    is_anomaly: bool
    anomaly_score: float
    severity: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "service_name": self.service_name,
            "metric_name": self.metric_name,
            "value": self.value,
            "is_anomaly": self.is_anomaly,
            "anomaly_score": self.anomaly_score,
            "severity": self.severity,
            "metadata": self.metadata,
        }


def score_metrics_batch(
    metrics: List[MetricPoint],
    model: BaseEstimator,
    score_threshold: float = 0.0,
) -> List[AnomalyResult]:
    """Score a batch of metrics for anomalies using a trained model.

    This function takes a list of metrics and a trained model, extracts features,
    scores them, and returns anomaly detection results.

    Args:
        metrics: List of MetricPoint objects to score.
        model: Trained scikit-learn model (e.g., IsolationForest).
        score_threshold: Anomaly score threshold. Points with scores below this
            are flagged as anomalies. Default is 0.0.

    Returns:
        List of AnomalyResult objects with detection results.

    Raises:
        ValueError: If metrics list is empty or model is None.

    Example:
        >>> from libs.models.metrics import MetricPoint
        >>> from sklearn.ensemble import IsolationForest
        >>> import pandas as pd
        >>> 
        >>> # Train a simple model
        >>> X = pd.DataFrame({'cpu': [70, 75, 80], 'memory': [60, 65, 70]})
        >>> model = IsolationForest().fit(X)
        >>> 
        >>> # Score new metrics
        >>> metrics = [
        ...     MetricPoint(
        ...         timestamp=datetime.now(),
        ...         service_name="api",
        ...         metric_name="cpu_usage",
        ...         value=95.0,
        ...         tags={}
        ...     )
        ... ]
        >>> results = score_metrics_batch(metrics, model)
    """
    if not metrics:
        raise ValueError("metrics list cannot be empty")

    if model is None:
        raise ValueError("model cannot be None")

    logger.info(f"Scoring batch of {len(metrics)} metrics")

    # Import pandas here to avoid circular imports
    import pandas as pd

    # Group metrics by service (each service should have its own model)
    # For now, assume all metrics in a batch are for the same service
    service_name = metrics[0].service_name
    logger.debug(f"Processing metrics for service: {service_name}")

    # Extract features from metrics
    # We need to reshape the data to match the training format
    features_dict = {
        "cpu_usage": [],
        "memory_usage": [],
        "latency_p95": [],
        "request_rate": [],
        "error_rate": [],
    }

    # Map metrics to feature columns
    metric_to_feature = {
        "cpu_usage": "cpu_usage",
        "memory_usage": "memory_usage",
        "latency_p95": "latency_p95",
        "request_rate": "request_rate",
        "error_rate": "error_rate",
    }

    # Build feature matrix
    # For each timestamp, we need all 5 metrics
    # For simplicity, we'll score each metric point individually
    # In production, you'd want to aggregate metrics by timestamp first

    results = []

    for metric in metrics:
        try:
            # Create feature vector for this metric
            # For a single metric, we need to create a complete feature vector
            # This is a simplified approach - in production, you'd aggregate
            # all metrics for a given timestamp
            
            feature_vector = _create_feature_vector(metric, metrics)
            
            # Convert to DataFrame for model prediction
            X = pd.DataFrame([feature_vector])
            
            # Get prediction and score
            prediction = model.predict(X)[0]  # -1 = anomaly, 1 = normal
            score = model.decision_function(X)[0]
            
            is_anomaly = bool((prediction == -1) or (score < score_threshold))
            severity = _calculate_severity(score)
            
            result = AnomalyResult(
                timestamp=metric.timestamp,
                service_name=metric.service_name,
                metric_name=metric.metric_name,
                value=metric.value,
                is_anomaly=is_anomaly,
                anomaly_score=float(score),
                severity=severity,
                metadata={
                    "tags": metric.tags,
                    "model_prediction": int(prediction),
                    "score_threshold": score_threshold,
                },
            )
            
            results.append(result)
            
            if is_anomaly:
                logger.warning(
                    f"Anomaly detected: {metric.service_name}/{metric.metric_name} = {metric.value} "
                    f"(score: {score:.4f}, severity: {severity})"
                )
            else:
                logger.debug(
                    f"Normal: {metric.service_name}/{metric.metric_name} = {metric.value} "
                    f"(score: {score:.4f})"
                )
                
        except Exception as e:
            logger.error(f"Error scoring metric {metric.metric_name}: {e}", exc_info=True)
            # Continue processing other metrics
            continue

    logger.info(
        f"Scored {len(results)} metrics: "
        f"{sum(1 for r in results if r.is_anomaly)} anomalies detected"
    )

    return results


def _create_feature_vector(
    metric: MetricPoint,
    all_metrics: List[MetricPoint],
) -> Dict[str, float]:
    """Create a complete feature vector for a single metric.

    In a real system, you'd aggregate all metrics for the same timestamp.
    For simplicity, we use the current metric's value and recent averages.

    Args:
        metric: The metric to create features for.
        all_metrics: All metrics in the batch for context.

    Returns:
        Dictionary with all required features.
    """
    # Feature columns expected by the model
    feature_vector = {
        "cpu_usage": 70.0,      # Default values
        "memory_usage": 60.0,
        "latency_p95": 120.0,
        "request_rate": 1000.0,
        "error_rate": 0.5,
    }

    # Update with actual metric value
    if metric.metric_name in feature_vector:
        feature_vector[metric.metric_name] = metric.value

    # Try to fill in other features from the same batch/timestamp
    for m in all_metrics:
        if (m.timestamp == metric.timestamp and 
            m.service_name == metric.service_name and
            m.metric_name in feature_vector):
            feature_vector[m.metric_name] = m.value

    return feature_vector


def _calculate_severity(score: float) -> str:
    """Calculate severity level based on anomaly score.

    Lower scores indicate more severe anomalies.

    Args:
        score: Anomaly score from model.

    Returns:
        Severity level: "critical", "high", "medium", "low", or "normal".
    """
    if score < -0.2:
        return "critical"
    elif score <= -0.1:  # Changed < to <= for boundary case
        return "high"
    elif score < 0.0:
        return "medium"
    elif score < 0.1:
        return "low"
    else:
        return "normal"


def filter_anomalies(results: List[AnomalyResult]) -> List[AnomalyResult]:
    """Filter results to return only anomalies.

    Args:
        results: List of AnomalyResult objects.

    Returns:
        List containing only anomalous results.
    """
    anomalies = [r for r in results if r.is_anomaly]
    logger.info(f"Filtered {len(anomalies)} anomalies from {len(results)} results")
    return anomalies


def group_by_service(results: List[AnomalyResult]) -> Dict[str, List[AnomalyResult]]:
    """Group anomaly results by service name.

    Args:
        results: List of AnomalyResult objects.

    Returns:
        Dictionary mapping service names to their anomaly results.
    """
    grouped: Dict[str, List[AnomalyResult]] = {}
    
    for result in results:
        if result.service_name not in grouped:
            grouped[result.service_name] = []
        grouped[result.service_name].append(result)
    
    logger.debug(f"Grouped results into {len(grouped)} services")
    return grouped
