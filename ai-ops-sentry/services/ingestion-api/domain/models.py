"""Domain models for the Ingestion API."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from libs.models.metrics import MetricPoint


class MetricIngestRequest(BaseModel):
    """Request model for ingesting a batch of metrics."""

    metrics: List[MetricPoint] = Field(
        ...,
        min_length=1,
        description="List of metric data points to ingest",
    )

    @field_validator("metrics")
    @classmethod
    def validate_metrics_not_empty(cls, v: List[MetricPoint]) -> List[MetricPoint]:
        """Ensure metrics list is not empty."""
        if not v:
            raise ValueError("Metrics list cannot be empty")
        return v


class MetricIngestResponse(BaseModel):
    """Response model for metric ingestion."""

    status: str = Field(default="accepted", description="Status of the ingestion request")
    message: str = Field(..., description="Human-readable message")
    metrics_received: int = Field(..., description="Number of metrics received")
    timestamp: datetime = Field(default_factory=datetime.now, description="Server timestamp")


class LogEntry(BaseModel):
    """A single log entry."""

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="The timestamp when the log was recorded (UTC)",
    )
    service_name: str = Field(..., description="The name of the service that generated the log")
    level: str = Field(..., description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    message: str = Field(..., description="The log message content")
    metadata: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional metadata/context for the log entry",
    )

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is one of the standard levels."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper


class LogIngestRequest(BaseModel):
    """Request model for ingesting a batch of log entries."""

    logs: List[LogEntry] = Field(
        ...,
        min_length=1,
        description="List of log entries to ingest",
    )

    @field_validator("logs")
    @classmethod
    def validate_logs_not_empty(cls, v: List[LogEntry]) -> List[LogEntry]:
        """Ensure logs list is not empty."""
        if not v:
            raise ValueError("Logs list cannot be empty")
        return v


class LogIngestResponse(BaseModel):
    """Response model for log ingestion."""

    status: str = Field(default="accepted", description="Status of the ingestion request")
    message: str = Field(..., description="Human-readable message")
    logs_received: int = Field(..., description="Number of logs received")
    timestamp: datetime = Field(default_factory=datetime.now, description="Server timestamp")


class HealthCheckResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(default="ok", description="Health status")
    service: str = Field(default="ingestion-api", description="Service name")
    timestamp: datetime = Field(default_factory=datetime.now, description="Current server time")
