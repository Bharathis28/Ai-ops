"""Data models for notification payloads.

Defines Pydantic models for structured notification data that can be
shared across all services. These models ensure type safety and validation
for incident alerts, action notifications, and other events.
"""

from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class IncidentPayload(BaseModel):
    """Payload for anomaly/incident alerts.
    
    Used by anomaly-engine to send structured incident notifications.
    """
    
    incident_id: str = Field(
        ...,
        description="Unique identifier for this incident",
    )
    
    service_name: str = Field(
        ...,
        description="Name of the affected service",
    )
    
    severity: Literal["critical", "warning", "info"] = Field(
        ...,
        description="Incident severity level",
    )
    
    title: str = Field(
        ...,
        description="Brief incident title",
    )
    
    description: str = Field(
        ...,
        description="Detailed incident description",
    )
    
    metric_name: Optional[str] = Field(
        default=None,
        description="Name of the metric that triggered the incident",
    )
    
    anomaly_score: Optional[float] = Field(
        default=None,
        description="Anomaly detection score (0-1)",
    )
    
    expected_value: Optional[float] = Field(
        default=None,
        description="Expected metric value",
    )
    
    actual_value: Optional[float] = Field(
        default=None,
        description="Actual observed metric value",
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the incident occurred",
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context (labels, tags, etc.)",
    )
    
    dashboard_url: Optional[str] = Field(
        default=None,
        description="URL to view incident in dashboard",
    )


class ActionPayload(BaseModel):
    """Payload for remediation action notifications.
    
    Used by action-engine to send structured action execution notifications.
    """
    
    action_id: str = Field(
        ...,
        description="Unique identifier for this action",
    )
    
    service_name: str = Field(
        ...,
        description="Name of the service being acted upon",
    )
    
    action_type: Literal["restart", "scale", "rollout"] = Field(
        ...,
        description="Type of remediation action",
    )
    
    status: Literal["started", "completed", "failed"] = Field(
        ...,
        description="Current action status",
    )
    
    target_type: Literal["gke", "cloud_run", "unknown"] = Field(
        ...,
        description="Target platform type",
    )
    
    reason: str = Field(
        ...,
        description="Reason for taking this action",
    )
    
    triggered_by: Literal["manual", "auto"] = Field(
        default="auto",
        description="How the action was triggered",
    )
    
    result: Optional[str] = Field(
        default=None,
        description="Action execution result or error message",
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the action was executed",
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context (cluster, namespace, replicas, etc.)",
    )
    
    dashboard_url: Optional[str] = Field(
        default=None,
        description="URL to view action in dashboard",
    )


class HealthAlertPayload(BaseModel):
    """Payload for service health alerts.
    
    Generic health status notifications for service monitoring.
    """
    
    service_name: str = Field(
        ...,
        description="Name of the service",
    )
    
    status: Literal["healthy", "degraded", "down"] = Field(
        ...,
        description="Current health status",
    )
    
    message: str = Field(
        ...,
        description="Health status message",
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the health check occurred",
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional health metrics",
    )
