"""API routes for Ingestion API service."""

import logging
import random
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import importlib.util
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from libs.models.metrics import MetricPoint
from libs.core.config import load_gcp_config, GCPConfig

# Import domain models using dynamic loading to handle hyphenated directory
models_path = Path(__file__).parent.parent / "domain" / "models.py"
models_spec = importlib.util.spec_from_file_location("domain_models", models_path)
models_module = importlib.util.module_from_spec(models_spec)
models_spec.loader.exec_module(models_module)
MetricIngestRequest = models_module.MetricIngestRequest
MetricIngestResponse = models_module.MetricIngestResponse
LogIngestRequest = models_module.LogIngestRequest
LogIngestResponse = models_module.LogIngestResponse
HealthCheckResponse = models_module.HealthCheckResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Lazy-loaded BigQuery writers to avoid blocking at import time
_metrics_writer = None
_logs_writer = None
_gcp_config: Optional[GCPConfig] = None


def get_metrics_writer():
    """Lazy initialization of BigQuery metrics writer."""
    global _metrics_writer, _gcp_config
    if _metrics_writer is None:
        # For now, return None (stub mode)
        # TODO: Uncomment when ready for actual BigQuery integration
        # if _gcp_config is None:
        #     _gcp_config = load_gcp_config()
        # from services.ingestion-api.infra.bq_writer import BigQueryMetricsWriter
        # _metrics_writer = BigQueryMetricsWriter(config=_gcp_config)
        pass
    return _metrics_writer


def get_logs_writer():
    """Lazy initialization of BigQuery logs writer."""
    global _logs_writer, _gcp_config
    if _logs_writer is None:
        # For now, return None (stub mode)
        # TODO: Uncomment when ready for actual BigQuery integration
        # if _gcp_config is None:
        #     _gcp_config = load_gcp_config()
        # from services.ingestion-api.infra.bq_writer import BigQueryLogsWriter
        # _logs_writer = BigQueryLogsWriter(config=_gcp_config)
        pass
    return _logs_writer


@router.post(
    "/metrics",
    response_model=MetricIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Ingestion"],
    summary="Ingest Metrics",
    description="Accepts a batch of metrics for processing and storage.",
)
def receive_metrics(request: MetricIngestRequest) -> MetricIngestResponse:
    """
    Receives a batch of metrics, validates them, and writes to BigQuery.

    Args:
        request: MetricIngestRequest containing a list of metrics.

    Returns:
        MetricIngestResponse with ingestion status.

    Raises:
        HTTPException: If the request is invalid or processing fails.
    """
    try:
        metrics = request.metrics
        logger.info(f"Received a batch of {len(metrics)} metrics.")

        # For now, just log the metrics (stub mode)
        logger.info(f"Metrics written to BigQuery (stub): {len(metrics)} records")
        
        # TODO: Uncomment when ready for actual BigQuery integration
        # metrics_writer = get_metrics_writer()
        # if metrics_writer:
        #     try:
        #         metrics_writer.write_metrics(metrics)
        #     except Exception as e:
        #         logger.error(f"Failed to write metrics to BigQuery: {e}")
        #         raise HTTPException(
        #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #             detail="Failed to persist metrics",
        #         )
        # else:
        #     logger.warning("BigQuery writer not initialized, skipping write")

        # TODO: Publish to Pub/Sub topic `metric_batches` for downstream processing
        # pubsub_publisher.publish(topic="metric_batches", data=metrics)

        return MetricIngestResponse(
            message=f"Successfully ingested {len(metrics)} metrics",
            metrics_received=len(metrics),
        )

    except ValidationError as e:
        logger.error(f"Validation error in metrics ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error in metrics ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/logs",
    response_model=LogIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Ingestion"],
    summary="Ingest Logs",
    description="Accepts a batch of log entries for processing and storage.",
)
def receive_logs(request: LogIngestRequest) -> LogIngestResponse:
    """
    Receives a batch of log entries, validates them, and writes to BigQuery.

    Args:
        request: LogIngestRequest containing a list of log entries.

    Returns:
        LogIngestResponse with ingestion status.

    Raises:
        HTTPException: If the request is invalid or processing fails.
    """
    try:
        logs = request.logs
        logger.info(f"Received a batch of {len(logs)} log entries.")

        # For now, just log the entries (stub mode)
        logger.info(f"Logs written to BigQuery (stub): {len(logs)} records")
        
        # TODO: Uncomment when ready for actual BigQuery integration
        # logs_writer = get_logs_writer()
        # if logs_writer:
        #     try:
        #         logs_writer.write_logs(logs)
        #     except Exception as e:
        #         logger.error(f"Failed to write logs to BigQuery: {e}")
        #         raise HTTPException(
        #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #             detail="Failed to persist logs",
        #         )
        # else:
        #     logger.warning("BigQuery logs writer not initialized, skipping write")

        # TODO: Publish to Pub/Sub topic `log_entries` for downstream processing
        # pubsub_publisher.publish(topic="log_entries", data=logs)

        return LogIngestResponse(
            message=f"Successfully ingested {len(logs)} log entries",
            logs_received=len(logs),
        )

    except ValidationError as e:
        logger.error(f"Validation error in logs ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error in logs ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/metrics",
    response_model=List[MetricPoint],
    tags=["Ingestion"],
    summary="Query Metrics",
    description="Retrieves metrics for a given service and time range.",
)
def query_metrics(
    service_name: Optional[str] = None,
    hours: int = 24,
) -> List[MetricPoint]:
    """
    Query metrics from storage (stub implementation returns mock data).

    Args:
        service_name: Optional service name filter
        hours: Number of hours to look back (default 24)

    Returns:
        List of MetricPoint objects
    """
    # Generate mock data for development
    logger.info(f"Querying metrics for service={service_name}, hours={hours}")
    
    services = [service_name] if service_name else ["payment-api", "user-auth", "order-service", "notification-service"]
    metrics = []
    
    now = datetime.now(timezone.utc)
    for i in range(hours):
        for service in services:
            timestamp = now - timedelta(hours=i)
            metrics.append(MetricPoint(
                timestamp=timestamp,
                service_name=service,
                cpu_usage=random.uniform(20, 90),
                memory_usage=random.uniform(30, 85),
                latency_p95=random.uniform(50, 500),
                request_rate=random.uniform(100, 1000),
                error_rate=random.uniform(0, 5),
            ))
    
    logger.info(f"Returning {len(metrics)} metric points")
    return metrics


@router.get(
    "/healthz",
    response_model=HealthCheckResponse,
    tags=["Monitoring"],
    summary="Health Check",
    description="Returns the health status of the Ingestion API service.",
)
def health_check() -> HealthCheckResponse:
    """
    Health check endpoint to verify service availability.

    Returns:
        HealthCheckResponse with service status.
    """
    return HealthCheckResponse()
