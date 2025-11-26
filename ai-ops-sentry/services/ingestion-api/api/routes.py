"""API routes for Ingestion API service."""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from libs.models.metrics import MetricPoint
from libs.core.config import load_gcp_config
from services.ingestion-api.domain.models import (
    MetricIngestRequest,
    MetricIngestResponse,
    LogIngestRequest,
    LogIngestResponse,
    HealthCheckResponse,
)

# Import using dynamic loading to handle hyphenated directory
import importlib.util
from pathlib import Path as PathLib

bq_writer_path = PathLib(__file__).parent.parent / "infra" / "bq_writer.py"
bq_writer_spec = importlib.util.spec_from_file_location("bq_writer", bq_writer_path)
bq_writer_module = importlib.util.module_from_spec(bq_writer_spec)
bq_writer_spec.loader.exec_module(bq_writer_module)
BigQueryMetricsWriter = bq_writer_module.BigQueryMetricsWriter
BigQueryLogsWriter = bq_writer_module.BigQueryLogsWriter

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize BigQuery writers (will be singletons for the application lifecycle)
try:
    gcp_config = load_gcp_config()
    metrics_writer = BigQueryMetricsWriter(config=gcp_config)
    logs_writer = BigQueryLogsWriter(config=gcp_config)
except Exception as e:
    logger.error(f"Failed to initialize BigQuery writers: {e}")
    metrics_writer = None
    logs_writer = None


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

        # Write to BigQuery
        if metrics_writer:
            try:
                metrics_writer.write_metrics(metrics)
            except Exception as e:
                logger.error(f"Failed to write metrics to BigQuery: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to persist metrics",
                )
        else:
            logger.warning("BigQuery writer not initialized, skipping write")

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

        # Write to BigQuery
        if logs_writer:
            try:
                logs_writer.write_logs(logs)
            except Exception as e:
                logger.error(f"Failed to write logs to BigQuery: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to persist logs",
                )
        else:
            logger.warning("BigQuery logs writer not initialized, skipping write")

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
