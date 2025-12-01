"""API routes for Ingestion API service."""

import logging
from typing import List, Optional
from datetime import datetime, timezone
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
        # Phase 8: Enable BigQuery integration
        if _gcp_config is None:
            _gcp_config = load_gcp_config()
        
        # Import dynamically to handle hyphenated directory
        import importlib.util
        from pathlib import Path
        bq_writer_path = Path(__file__).parent.parent / "infra" / "bq_writer.py"
        bq_writer_spec = importlib.util.spec_from_file_location("bq_writer", bq_writer_path)
        bq_writer_module = importlib.util.module_from_spec(bq_writer_spec)
        bq_writer_spec.loader.exec_module(bq_writer_module)
        BigQueryMetricsWriter = bq_writer_module.BigQueryMetricsWriter
        
        _metrics_writer = BigQueryMetricsWriter(config=_gcp_config)
    return _metrics_writer


def get_logs_writer():
    """Lazy initialization of BigQuery logs writer."""
    global _logs_writer, _gcp_config
    if _logs_writer is None:
        # Phase 8: Enable BigQuery integration
        if _gcp_config is None:
            _gcp_config = load_gcp_config()
        
        # Import dynamically to handle hyphenated directory
        import importlib.util
        from pathlib import Path
        bq_writer_path = Path(__file__).parent.parent / "infra" / "bq_writer.py"
        bq_writer_spec = importlib.util.spec_from_file_location("bq_writer", bq_writer_path)
        bq_writer_module = importlib.util.module_from_spec(bq_writer_spec)
        bq_writer_spec.loader.exec_module(bq_writer_module)
        BigQueryLogsWriter = bq_writer_module.BigQueryLogsWriter
        
        _logs_writer = BigQueryLogsWriter(config=_gcp_config)
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

        # Phase 8: Enable BigQuery integration
        metrics_writer = get_metrics_writer()
        if metrics_writer:
            try:
                metrics_writer.write_metrics(metrics)
                logger.info(f"Successfully wrote {len(metrics)} metrics to BigQuery")
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

        # Phase 8: Enable BigQuery integration
        logs_writer = get_logs_writer()
        if logs_writer:
            try:
                logs_writer.write_logs(logs)
                logger.info(f"Successfully wrote {len(logs)} logs to BigQuery")
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
