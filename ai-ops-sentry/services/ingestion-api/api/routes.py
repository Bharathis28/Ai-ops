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

# Lazy-loaded BigQuery writers and Pub/Sub publishers
_metrics_writer = None
_logs_writer = None
_metrics_publisher = None
_logs_publisher = None
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


def get_metrics_publisher():
    """Lazy initialization of Pub/Sub metrics publisher."""
    global _metrics_publisher, _gcp_config
    if _metrics_publisher is None:
        if _gcp_config is None:
            _gcp_config = load_gcp_config()
        
        if not _gcp_config.enable_gcp_clients:
            return None
            
        # Import dynamically
        from pathlib import Path
        pubsub_path = Path(__file__).parent.parent / "infra" / "pubsub_publisher.py"
        pubsub_spec = importlib.util.spec_from_file_location("pubsub_publisher", pubsub_path)
        pubsub_module = importlib.util.module_from_spec(pubsub_spec)
        pubsub_spec.loader.exec_module(pubsub_module)
        PubSubMetricsPublisher = pubsub_module.PubSubMetricsPublisher
        
        _metrics_publisher = PubSubMetricsPublisher(config=_gcp_config)
    return _metrics_publisher


def get_logs_publisher():
    """Lazy initialization of Pub/Sub logs publisher."""
    global _logs_publisher, _gcp_config
    if _logs_publisher is None:
        if _gcp_config is None:
            _gcp_config = load_gcp_config()
        
        if not _gcp_config.enable_gcp_clients:
            return None
            
        # Import dynamically
        from pathlib import Path
        pubsub_path = Path(__file__).parent.parent / "infra" / "pubsub_publisher.py"
        pubsub_spec = importlib.util.spec_from_file_location("pubsub_publisher", pubsub_path)
        pubsub_module = importlib.util.module_from_spec(pubsub_spec)
        pubsub_spec.loader.exec_module(pubsub_module)
        PubSubLogsPublisher = pubsub_module.PubSubLogsPublisher
        
        _logs_publisher = PubSubLogsPublisher(config=_gcp_config)
    return _logs_publisher


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

        # Publish to Pub/Sub for downstream processing
        try:
            metrics_publisher = get_metrics_publisher()
            if metrics_publisher:
                try:
                    metrics_publisher.publish_metrics(metrics)
                    logger.info(f"Published {len(metrics)} metrics to Pub/Sub")
                except Exception as e:
                    logger.error(f"Failed to publish metrics to Pub/Sub: {e}")
                    # Don't fail the request if Pub/Sub fails
            else:
                logger.warning("Pub/Sub publisher not initialized, skipping publish")
        except Exception as e:
            logger.error(f"Failed to initialize Pub/Sub publisher: {e}")
            # Don't fail the request if Pub/Sub initialization fails

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

        # Publish to Pub/Sub for downstream processing
        try:
            logs_publisher = get_logs_publisher()
            if logs_publisher:
                try:
                    logs_publisher.publish_logs(logs)
                    logger.info(f"Published {len(logs)} logs to Pub/Sub")
                except Exception as e:
                    logger.error(f"Failed to publish logs to Pub/Sub: {e}")
                    # Don't fail the request if Pub/Sub fails
            else:
                logger.warning("Pub/Sub publisher not initialized, skipping publish")
        except Exception as e:
            logger.error(f"Failed to initialize Pub/Sub publisher: {e}")
            # Don't fail the request if Pub/Sub initialization fails

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


@router.get(
    "/metrics/recent",
    tags=["Query"],
    summary="Get Recent Metrics",
    description="Fetch recent metrics from BigQuery for the dashboard.",
)
def get_recent_metrics(
    service_name: Optional[str] = None,
    limit: int = 1000
):
    """Get recent metrics from BigQuery."""
    try:
        global _gcp_config
        if _gcp_config is None:
            _gcp_config = load_gcp_config()
        
        from google.cloud import bigquery
        client = bigquery.Client(project=_gcp_config.gcp_project_id)
        
        query = f"""
            SELECT 
                timestamp,
                service_name,
                metric_name,
                value,
                labels
            FROM `{_gcp_config.get_full_table_id(_gcp_config.bigquery_table_metrics_raw)}`
            {"WHERE service_name = @service_name" if service_name else ""}
            ORDER BY timestamp DESC
            LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
            ] + ([bigquery.ScalarQueryParameter("service_name", "STRING", service_name)] if service_name else [])
        )
        
        results = client.query(query, job_config=job_config).result()
        
        metrics = []
        for row in results:
            metrics.append({
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "service_name": row.service_name,
                "metric_name": row.metric_name,
                "value": float(row.value) if row.value else 0,
                "labels": row.labels or {}
            })
        
        return {"metrics": metrics, "count": len(metrics)}
        
    except Exception as e:
        logger.error(f"Failed to fetch metrics: {e}")
        # Return empty data instead of error to keep dashboard working
        return {"metrics": [], "count": 0, "error": str(e)}


@router.get(
    "/anomalies/recent",
    tags=["Query"],
    summary="Get Recent Anomalies",
    description="Fetch recent anomalies from BigQuery for the dashboard.",
)
def get_recent_anomalies(limit: int = 50):
    """Get recent anomalies from BigQuery."""
    try:
        global _gcp_config
        if _gcp_config is None:
            _gcp_config = load_gcp_config()
        
        from google.cloud import bigquery
        client = bigquery.Client(project=_gcp_config.gcp_project_id)
        
        query = f"""
            SELECT 
                timestamp,
                service_name,
                metric_name,
                anomaly_score,
                expected_value,
                actual_value,
                severity,
                description
            FROM `{_gcp_config.get_full_table_id(_gcp_config.bigquery_table_anomalies)}`
            ORDER BY timestamp DESC
            LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
            ]
        )
        
        results = client.query(query, job_config=job_config).result()
        
        anomalies = []
        for row in results:
            anomalies.append({
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "service_name": row.service_name,
                "metric_name": row.metric_name,
                "anomaly_score": float(row.anomaly_score) if row.anomaly_score else 0,
                "expected_value": float(row.expected_value) if row.expected_value else 0,
                "actual_value": float(row.actual_value) if row.actual_value else 0,
                "severity": row.severity or "medium",
                "is_anomaly": row.anomaly_score > 0.7 if row.anomaly_score else False,
                "metric_values": {
                    row.metric_name: float(row.actual_value) if row.actual_value else 0
                }
            })
        
        return {"anomalies": anomalies, "count": len(anomalies)}
        
    except Exception as e:
        logger.error(f"Failed to fetch anomalies: {e}")
        return {"anomalies": [], "count": 0, "error": str(e)}


@router.get(
    "/services/health",
    tags=["Query"],
    summary="Get Services Health",
    description="Fetch aggregated service health metrics from BigQuery.",
)
def get_services_health():
    """Get service health aggregated from recent metrics."""
    try:
        global _gcp_config
        if _gcp_config is None:
            _gcp_config = load_gcp_config()
        
        from google.cloud import bigquery
        client = bigquery.Client(project=_gcp_config.gcp_project_id)
        
        # Get latest metrics per service
        query = f"""
            WITH latest_metrics AS (
                SELECT 
                    service_name,
                    metric_name,
                    value,
                    timestamp,
                    ROW_NUMBER() OVER (PARTITION BY service_name, metric_name ORDER BY timestamp DESC) as rn
                FROM `{_gcp_config.get_full_table_id(_gcp_config.bigquery_table_metrics_raw)}`
                WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
            )
            SELECT 
                service_name,
                MAX(CASE WHEN metric_name = 'cpu_usage' THEN value END) as cpu_usage,
                MAX(CASE WHEN metric_name = 'memory_usage' THEN value END) as memory_usage,
                MAX(CASE WHEN metric_name = 'latency_p95' THEN value END) as latency_p95,
                MAX(CASE WHEN metric_name = 'error_rate' THEN value END) as error_rate,
                MAX(CASE WHEN metric_name = 'request_rate' THEN value END) as request_rate,
                MAX(timestamp) as last_updated
            FROM latest_metrics
            WHERE rn = 1
            GROUP BY service_name
        """
        
        results = client.query(query).result()
        
        services = []
        for row in results:
            cpu = float(row.cpu_usage) if row.cpu_usage else 0
            error_rate = float(row.error_rate) if row.error_rate else 0
            
            # Determine status based on metrics
            if cpu > 80 or error_rate > 5:
                status = "critical"
            elif cpu > 60 or error_rate > 2:
                status = "degraded"
            else:
                status = "healthy"
            
            services.append({
                "name": row.service_name,
                "status": status,
                "latency_p95": float(row.latency_p95) if row.latency_p95 else 0,
                "error_rate": error_rate,
                "cpu_usage": cpu,
                "memory_usage": float(row.memory_usage) if row.memory_usage else 0,
                "request_rate": float(row.request_rate) if row.request_rate else 0,
                "anomaly_score": 0,  # Would come from anomalies table join
                "last_updated": row.last_updated.isoformat() if row.last_updated else None
            })
        
        return {"services": services, "count": len(services)}
        
    except Exception as e:
        logger.error(f"Failed to fetch services health: {e}")
        return {"services": [], "count": 0, "error": str(e)}
