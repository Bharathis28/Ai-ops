"""API routes for Ingestion API service."""

import logging
from typing import List

from fastapi import APIRouter, HTTPException

from libs.models.metrics import MetricPoint

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/metrics", status_code=202)
def receive_metrics(metrics: List[MetricPoint]):
    """
    Receives a batch of metrics, validates them, and acknowledges receipt.

    In a real implementation, this would publish the metrics to a Pub/Sub topic
    and/or write them to a database like BigQuery.
    """
    if not metrics:
        raise HTTPException(status_code=400, detail="Empty metrics batch received.")

    logger.info(f"Received a batch of {len(metrics)} metrics.")

    # Placeholder for future logic:
    # 1. Publish to Pub/Sub topic `metric_batches`
    # 2. Asynchronously write to BigQuery table `metrics_raw`

    # For now, just log the first metric as a sample
    logger.debug(f"Sample metric received: {metrics[0].model_dump_json()}")

    return {"status": "accepted", "message": f"{len(metrics)} metrics received."}
