"""Unit tests for the metrics domain module."""

from services.metrics-collector.domain.metrics import (
    MetricPoint,
    generate_fake_metrics,
    SERVICE_NAMES,
)


def test_generate_fake_metrics_returns_list_of_metric_points():
    """Tests that generate_fake_metrics returns a list of MetricPoint objects."""
    metrics = generate_fake_metrics()
    assert isinstance(metrics, list)
    assert all(isinstance(m, MetricPoint) for m in metrics)
    assert len(metrics) > 0


def test_generate_fake_metrics_for_specific_services():
    """Tests that metrics are generated for the specified services."""
    custom_services = ["service-a", "service-b"]
    metrics = generate_fake_metrics(service_names=custom_services)
    generated_service_names = {m.service_name for m in metrics}
    assert generated_service_names == set(custom_services)


def test_metric_point_structure():
    """Tests the structure and types of a generated MetricPoint."""
    metric = generate_fake_metrics(service_names=["test-service"])[0]
    assert isinstance(metric.service_name, str)
    assert isinstance(metric.metric_name, str)
    assert isinstance(metric.value, float)
    assert isinstance(metric.tags, dict)
