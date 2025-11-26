"""BigQuery reader for loading historical metrics.

This module provides functions to load historical metrics data.
Currently implemented with a stub that returns dummy data, but designed
with a stable interface for easy BigQuery integration later.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def load_historical_metrics(
    service_name: str,
    days: int = 7,
    end_date: Optional[datetime] = None,
) -> pd.DataFrame:
    """Load historical metrics for a specific service.

    Public interface is stable - implementation can switch from stub to
    actual BigQuery without changing callers.

    Args:
        service_name: Name of the service to load metrics for (e.g., "frontend-api").
        days: Number of days of historical data to load. Default is 7.
        end_date: End date for the query. If None, uses current time.

    Returns:
        DataFrame with columns:
        - timestamp: datetime64
        - service_name: str
        - cpu_usage: float (0-100)
        - memory_usage: float (0-100)
        - latency_p95: float (milliseconds)
        - request_rate: float (requests per second)
        - error_rate: float (0-100 percentage)

    Raises:
        ValueError: If days is not positive or service_name is empty.

    Example:
        >>> df = load_historical_metrics("frontend-api", days=7)
        >>> df.shape
        (1008, 7)  # 7 days * 24 hours * 6 samples/hour
        >>> df.columns.tolist()
        ['timestamp', 'service_name', 'cpu_usage', 'memory_usage', ...]
    """
    if not service_name:
        raise ValueError("service_name cannot be empty")

    if days <= 0:
        raise ValueError(f"days must be positive, got {days}")

    logger.info(f"Loading {days} days of metrics for service: {service_name}")

    # TODO: Replace with actual BigQuery query when ready
    # Example implementation:
    #
    # from google.cloud import bigquery
    # from libs.core.config import load_gcp_config
    #
    # config = load_gcp_config()
    # client = bigquery.Client(project=config.gcp_project_id)
    #
    # if end_date is None:
    #     end_date = datetime.now(timezone.utc)
    # start_date = end_date - timedelta(days=days)
    #
    # query = f"""
    # SELECT
    #     timestamp,
    #     service_name,
    #     cpu_usage,
    #     memory_usage,
    #     latency_p95,
    #     request_rate,
    #     error_rate
    # FROM `{config.get_full_table_id(config.bigquery_table_metrics_raw)}`
    # WHERE service_name = @service_name
    #   AND timestamp >= @start_date
    #   AND timestamp < @end_date
    # ORDER BY timestamp ASC
    # """
    #
    # job_config = bigquery.QueryJobConfig(
    #     query_parameters=[
    #         bigquery.ScalarQueryParameter("service_name", "STRING", service_name),
    #         bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
    #         bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
    #     ]
    # )
    #
    # df = client.query(query, job_config=job_config).to_dataframe()
    # logger.info(f"Loaded {len(df)} rows from BigQuery")
    # return df

    # STUB IMPLEMENTATION: Generate dummy data
    logger.warning(
        "[STUB] Using dummy data instead of BigQuery. "
        "Replace implementation when BigQuery is available."
    )

    df = _generate_dummy_metrics(service_name, days, end_date)

    logger.info(f"Generated {len(df)} rows of dummy metrics for {service_name}")

    return df


def _generate_dummy_metrics(
    service_name: str,
    days: int,
    end_date: Optional[datetime] = None,
) -> pd.DataFrame:
    """Generate dummy metrics data for testing.

    This is an internal helper function that will be removed when
    BigQuery integration is implemented.

    Args:
        service_name: Service name.
        days: Number of days of data.
        end_date: End date, defaults to now.

    Returns:
        DataFrame with dummy metrics.
    """
    if end_date is None:
        end_date = datetime.now()

    # Generate timestamps (every 10 minutes)
    start_date = end_date - timedelta(days=days)
    freq = "10min"
    timestamps = pd.date_range(start=start_date, end=end_date, freq=freq)

    n_samples = len(timestamps)

    # Set random seed for reproducibility
    np.random.seed(42)

    # Generate realistic metrics with some anomalies
    # Normal ranges
    cpu_normal = 70
    memory_normal = 60
    latency_normal = 120
    request_rate_normal = 1000
    error_rate_normal = 0.5

    # Generate base metrics with noise
    cpu_usage = cpu_normal + np.random.normal(0, 5, n_samples)
    memory_usage = memory_normal + np.random.normal(0, 8, n_samples)
    latency_p95 = latency_normal + np.random.normal(0, 15, n_samples)
    request_rate = request_rate_normal + np.random.normal(0, 100, n_samples)
    error_rate = error_rate_normal + np.random.normal(0, 0.2, n_samples)

    # Inject some anomalies (5% of data)
    n_anomalies = int(n_samples * 0.05)
    anomaly_indices = np.random.choice(n_samples, n_anomalies, replace=False)

    for idx in anomaly_indices:
        # Random anomaly type
        anomaly_type = np.random.choice(["cpu_spike", "memory_spike", "latency_spike", "error_spike"])

        if anomaly_type == "cpu_spike":
            cpu_usage[idx] = np.random.uniform(90, 100)
        elif anomaly_type == "memory_spike":
            memory_usage[idx] = np.random.uniform(85, 95)
        elif anomaly_type == "latency_spike":
            latency_p95[idx] = np.random.uniform(300, 500)
        elif anomaly_type == "error_spike":
            error_rate[idx] = np.random.uniform(5, 15)

    # Clip to valid ranges
    cpu_usage = np.clip(cpu_usage, 0, 100)
    memory_usage = np.clip(memory_usage, 0, 100)
    latency_p95 = np.clip(latency_p95, 0, None)
    request_rate = np.clip(request_rate, 0, None)
    error_rate = np.clip(error_rate, 0, 100)

    # Create DataFrame
    df = pd.DataFrame({
        "timestamp": timestamps,
        "service_name": service_name,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "latency_p95": latency_p95,
        "request_rate": request_rate,
        "error_rate": error_rate,
    })

    # Add some missing values (2% of data)
    n_missing = int(n_samples * 0.02)
    for col in ["cpu_usage", "memory_usage", "latency_p95", "request_rate", "error_rate"]:
        missing_indices = np.random.choice(n_samples, n_missing, replace=False)
        df.loc[missing_indices, col] = np.nan

    return df


def load_metrics_from_csv(filepath: str) -> pd.DataFrame:
    """Load metrics from a CSV file.

    This is a helper function for local development and testing.

    Args:
        filepath: Path to CSV file.

    Returns:
        DataFrame with metrics.
    """
    logger.info(f"Loading metrics from CSV: {filepath}")

    df = pd.read_csv(filepath)

    # Convert timestamp to datetime
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    logger.info(f"Loaded {len(df)} rows from CSV")

    return df
