"""Domain models and logic for metrics."""

import datetime
import random
from typing import Dict, List, Literal

from pydantic import BaseModel, Field

MetricName = Literal[
    "cpu_usage",
    "memory_usage",
    "latency_p95",
    "request_rate",
    "error_rate",
]

SERVICE_NAMES = ["frontend-api", "backend-worker", "data-pipeline", "auth-service"]


class MetricPoint(BaseModel):
    """A single data point for a metric at a specific time."""

    timestamp: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="The timestamp when the metric was recorded (UTC).",
    )
    service_name: str = Field(..., description="The name of the service being monitored.")
    metric_name: MetricName = Field(..., description="The name of the metric.")
    value: float = Field(..., description="The value of the metric.")
    tags: Dict[str, str] = Field(default_factory=dict, description="Optional key-value tags.")


def generate_fake_metrics(
    service_names: List[str] = SERVICE_NAMES,
) -> List[MetricPoint]:
    """Generates a list of fake metrics for a given set of services.

    Args:
        service_names: A list of service names to generate metrics for.

    Returns:
        A list of MetricPoint objects with randomized values.
    """
    metrics = []
    for service in service_names:
        metrics.extend(
            [
                MetricPoint(
                    service_name=service,
                    metric_name="cpu_usage",
                    value=random.uniform(5.0, 95.0),
                    tags={"host": f"host-{random.randint(1, 5)}", "region": "us-central1"},
                ),
                MetricPoint(
                    service_name=service,
                    metric_name="memory_usage",
                    value=random.uniform(100.0, 2048.0),
                    tags={"host": f"host-{random.randint(1, 5)}", "region": "us-central1"},
                ),
                MetricPoint(
                    service_name=service,
                    metric_name="latency_p95",
                    value=random.uniform(50.0, 500.0),
                    tags={"endpoint": "/api/v1/data"},
                ),
                MetricPoint(
                    service_name=service,
                    metric_name="request_rate",
                    value=random.uniform(10.0, 100.0),
                ),
                MetricPoint(
                    service_name=service,
                    metric_name="error_rate",
                    value=random.uniform(0.0, 0.05),
                ),
            ]
        )
    return metrics
