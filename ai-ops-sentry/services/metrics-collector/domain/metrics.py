"""Domain models and logic for metrics."""

import random
from typing import List

from libs.models.metrics import MetricPoint, SERVICE_NAMES, MetricName


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
