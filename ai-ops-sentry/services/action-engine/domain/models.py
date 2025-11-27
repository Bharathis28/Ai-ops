"""Domain models for action engine.

This module defines request and response models for remediation actions.
These models form the stable API contract (v1) and should only accept additive changes.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class TargetType(str, Enum):
    """Type of deployment target."""
    GKE = "GKE"
    CLOUD_RUN = "CloudRun"


class ActionType(str, Enum):
    """Type of remediation action."""
    RESTART_DEPLOYMENT = "restart_deployment"
    SCALE_DEPLOYMENT = "scale_deployment"
    ROLLOUT_RESTART = "rollout_restart"


class ActionStatus(str, Enum):
    """Status of an action execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"


# Request Models (v1 API contract - stable)

class RestartDeploymentRequest(BaseModel):
    """Request model for restarting a deployment.
    
    Attributes:
        service_name: Name of the service/deployment to restart.
        target_type: Type of deployment (GKE or CloudRun).
        cluster_name: GKE cluster name (required for GKE).
        region: GCP region (required for CloudRun).
        namespace: Kubernetes namespace (optional, defaults to 'default' for GKE).
        reason: Reason for the restart (optional).
    """
    service_name: str = Field(
        ...,
        description="Name of the service/deployment to restart",
        min_length=1,
        max_length=100,
    )
    target_type: TargetType = Field(
        ...,
        description="Type of deployment target (GKE or CloudRun)",
    )
    cluster_name: Optional[str] = Field(
        None,
        description="GKE cluster name (required for GKE targets)",
        max_length=100,
    )
    region: Optional[str] = Field(
        None,
        description="GCP region (required for CloudRun targets)",
        max_length=50,
    )
    namespace: str = Field(
        default="default",
        description="Kubernetes namespace (for GKE)",
        max_length=63,
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for the restart",
        max_length=500,
    )

    @field_validator("cluster_name")
    @classmethod
    def validate_gke_cluster(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that cluster_name is provided for GKE targets."""
        if info.data.get("target_type") == TargetType.GKE and not v:
            raise ValueError("cluster_name is required for GKE targets")
        return v

    @field_validator("region")
    @classmethod
    def validate_cloud_run_region(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that region is provided for CloudRun targets."""
        if info.data.get("target_type") == TargetType.CLOUD_RUN and not v:
            raise ValueError("region is required for CloudRun targets")
        return v


class ScaleDeploymentRequest(BaseModel):
    """Request model for scaling a deployment.
    
    Attributes:
        service_name: Name of the service/deployment to scale.
        target_type: Type of deployment (GKE or CloudRun).
        cluster_name: GKE cluster name (required for GKE).
        region: GCP region (required for CloudRun).
        namespace: Kubernetes namespace (optional, defaults to 'default' for GKE).
        min_replicas: Minimum number of replicas.
        max_replicas: Maximum number of replicas.
        replicas: Exact number of replicas (for GKE only, overrides min/max).
        reason: Reason for scaling (optional).
    """
    service_name: str = Field(
        ...,
        description="Name of the service/deployment to scale",
        min_length=1,
        max_length=100,
    )
    target_type: TargetType = Field(
        ...,
        description="Type of deployment target (GKE or CloudRun)",
    )
    cluster_name: Optional[str] = Field(
        None,
        description="GKE cluster name (required for GKE targets)",
        max_length=100,
    )
    region: Optional[str] = Field(
        None,
        description="GCP region (required for CloudRun targets)",
        max_length=50,
    )
    namespace: str = Field(
        default="default",
        description="Kubernetes namespace (for GKE)",
        max_length=63,
    )
    min_replicas: Optional[int] = Field(
        None,
        description="Minimum number of replicas",
        ge=0,
        le=1000,
    )
    max_replicas: Optional[int] = Field(
        None,
        description="Maximum number of replicas",
        ge=1,
        le=1000,
    )
    replicas: Optional[int] = Field(
        None,
        description="Exact number of replicas (GKE only)",
        ge=0,
        le=1000,
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for scaling",
        max_length=500,
    )

    @field_validator("cluster_name")
    @classmethod
    def validate_gke_cluster(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that cluster_name is provided for GKE targets."""
        if info.data.get("target_type") == TargetType.GKE and not v:
            raise ValueError("cluster_name is required for GKE targets")
        return v

    @field_validator("region")
    @classmethod
    def validate_cloud_run_region(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that region is provided for CloudRun targets."""
        if info.data.get("target_type") == TargetType.CLOUD_RUN and not v:
            raise ValueError("region is required for CloudRun targets")
        return v

    @field_validator("max_replicas")
    @classmethod
    def validate_max_replicas(cls, v: Optional[int], info) -> Optional[int]:
        """Validate that max_replicas >= min_replicas."""
        min_replicas = info.data.get("min_replicas")
        if v is not None and min_replicas is not None and v < min_replicas:
            raise ValueError("max_replicas must be >= min_replicas")
        return v


class RolloutRestartRequest(BaseModel):
    """Request model for rolling restart of a deployment.
    
    This performs a gradual restart without downtime (GKE only).
    
    Attributes:
        service_name: Name of the deployment to restart.
        cluster_name: GKE cluster name.
        namespace: Kubernetes namespace (optional, defaults to 'default').
        reason: Reason for the rollout restart (optional).
    """
    service_name: str = Field(
        ...,
        description="Name of the deployment to restart",
        min_length=1,
        max_length=100,
    )
    cluster_name: str = Field(
        ...,
        description="GKE cluster name",
        min_length=1,
        max_length=100,
    )
    namespace: str = Field(
        default="default",
        description="Kubernetes namespace",
        max_length=63,
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for the rollout restart",
        max_length=500,
    )


# Response Models

class ActionResponse(BaseModel):
    """Response model for action execution.
    
    Attributes:
        action_id: Unique identifier for the action.
        action_type: Type of action executed.
        status: Current status of the action.
        message: Human-readable message about the action.
        service_name: Name of the affected service.
        target_type: Type of deployment target.
        timestamp: When the action was executed.
        metadata: Additional metadata about the action.
    """
    action_id: str = Field(
        ...,
        description="Unique identifier for the action",
    )
    action_type: ActionType = Field(
        ...,
        description="Type of action executed",
    )
    status: ActionStatus = Field(
        ...,
        description="Current status of the action",
    )
    message: str = Field(
        ...,
        description="Human-readable message about the action",
    )
    service_name: str = Field(
        ...,
        description="Name of the affected service",
    )
    target_type: TargetType = Field(
        ...,
        description="Type of deployment target",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the action was executed",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the action",
    )


# Internal Models

class ActionRecord(BaseModel):
    """Internal model for logging actions.
    
    This model is used for persisting action history to BigQuery.
    
    Attributes:
        action_id: Unique identifier for the action.
        action_type: Type of action.
        status: Status of the action.
        service_name: Name of the affected service.
        target_type: Type of deployment target.
        cluster_name: GKE cluster name (optional).
        region: GCP region (optional).
        namespace: Kubernetes namespace (optional).
        replicas: Number of replicas (for scale actions).
        min_replicas: Minimum replicas (for scale actions).
        max_replicas: Maximum replicas (for scale actions).
        reason: Reason for the action.
        message: Result message.
        timestamp: When the action was executed.
        metadata: Additional metadata.
    """
    action_id: str
    action_type: ActionType
    status: ActionStatus
    service_name: str
    target_type: TargetType
    cluster_name: Optional[str] = None
    region: Optional[str] = None
    namespace: Optional[str] = None
    replicas: Optional[int] = None
    min_replicas: Optional[int] = None
    max_replicas: Optional[int] = None
    reason: Optional[str] = None
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for BigQuery insertion."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "status": self.status.value,
            "service_name": self.service_name,
            "target_type": self.target_type.value,
            "cluster_name": self.cluster_name,
            "region": self.region,
            "namespace": self.namespace,
            "replicas": self.replicas,
            "min_replicas": self.min_replicas,
            "max_replicas": self.max_replicas,
            "reason": self.reason,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
