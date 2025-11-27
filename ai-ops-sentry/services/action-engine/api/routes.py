"""FastAPI routes for action engine.

This module provides REST API endpoints for executing remediation actions
on GKE deployments and Cloud Run services. Uses dependency injection for
clients and logger to enable easy testing and future GCP integration.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.core.config import GCPConfig

# Dynamic imports for hyphenated directory
import importlib.util

# Import domain models
models_path = Path(__file__).parent.parent / "domain" / "models.py"
models_spec = importlib.util.spec_from_file_location("models", models_path)
models_module = importlib.util.module_from_spec(models_spec)
models_spec.loader.exec_module(models_module)
RestartDeploymentRequest = models_module.RestartDeploymentRequest
ScaleDeploymentRequest = models_module.ScaleDeploymentRequest
RolloutRestartRequest = models_module.RolloutRestartRequest
ActionResponse = models_module.ActionResponse
TargetType = models_module.TargetType

# Import domain actions
actions_path = Path(__file__).parent.parent / "domain" / "actions.py"
actions_spec = importlib.util.spec_from_file_location("actions", actions_path)
actions_module = importlib.util.module_from_spec(actions_spec)
actions_spec.loader.exec_module(actions_module)
restart_gke_deployment = actions_module.restart_gke_deployment
scale_gke_deployment = actions_module.scale_gke_deployment
rollout_restart_gke_deployment = actions_module.rollout_restart_gke_deployment
restart_cloud_run_service = actions_module.restart_cloud_run_service
scale_cloud_run_service = actions_module.scale_cloud_run_service
create_action_response = actions_module.create_action_response

# Import infra clients
k8s_client_path = Path(__file__).parent.parent / "infra" / "k8s_client.py"
k8s_client_spec = importlib.util.spec_from_file_location("k8s_client", k8s_client_path)
k8s_client_module = importlib.util.module_from_spec(k8s_client_spec)
k8s_client_spec.loader.exec_module(k8s_client_module)
KubernetesClient = k8s_client_module.KubernetesClient

cloud_run_client_path = Path(__file__).parent.parent / "infra" / "cloud_run_client.py"
cloud_run_client_spec = importlib.util.spec_from_file_location("cloud_run_client", cloud_run_client_path)
cloud_run_client_module = importlib.util.module_from_spec(cloud_run_client_spec)
cloud_run_client_spec.loader.exec_module(cloud_run_client_module)
CloudRunClient = cloud_run_client_module.CloudRunClient

actions_logger_path = Path(__file__).parent.parent / "infra" / "actions_logger.py"
actions_logger_spec = importlib.util.spec_from_file_location("actions_logger", actions_logger_path)
actions_logger_module = importlib.util.module_from_spec(actions_logger_spec)
actions_logger_spec.loader.exec_module(actions_logger_module)
ActionsLogger = actions_logger_module.ActionsLogger

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["actions"])

# Global instances (initialized in main.py)
_k8s_client: Optional[KubernetesClient] = None
_cloud_run_client: Optional[CloudRunClient] = None
_actions_logger: Optional[ActionsLogger] = None


def initialize_clients(config: GCPConfig) -> None:
    """Initialize global client instances.
    
    This should be called once during application startup.
    
    Args:
        config: GCP configuration.
    """
    global _k8s_client, _cloud_run_client, _actions_logger
    
    _k8s_client = KubernetesClient(project_id=config.gcp_project_id)
    _cloud_run_client = CloudRunClient(project_id=config.gcp_project_id)
    _actions_logger = ActionsLogger(config=config, backend="console")
    
    logger.info("Initialized action engine clients")


# Dependency injection functions

def get_k8s_client() -> KubernetesClient:
    """Dependency injection for Kubernetes client.
    
    Returns:
        KubernetesClient instance.
        
    Raises:
        HTTPException: If client not initialized.
    """
    if _k8s_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kubernetes client not initialized",
        )
    return _k8s_client


def get_cloud_run_client() -> CloudRunClient:
    """Dependency injection for Cloud Run client.
    
    Returns:
        CloudRunClient instance.
        
    Raises:
        HTTPException: If client not initialized.
    """
    if _cloud_run_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloud Run client not initialized",
        )
    return _cloud_run_client


def get_actions_logger() -> ActionsLogger:
    """Dependency injection for actions logger.
    
    Returns:
        ActionsLogger instance.
        
    Raises:
        HTTPException: If logger not initialized.
    """
    if _actions_logger is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Actions logger not initialized",
        )
    return _actions_logger


# API Endpoints

@router.post(
    "/restart_deployment",
    response_model=ActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Restart a deployment",
    description="Restart a GKE deployment or Cloud Run service by triggering pod/instance recreation.",
)
async def restart_deployment(
    request: RestartDeploymentRequest,
    k8s_client: KubernetesClient = Depends(get_k8s_client),
    cloud_run_client: CloudRunClient = Depends(get_cloud_run_client),
    actions_logger: ActionsLogger = Depends(get_actions_logger),
) -> ActionResponse:
    """Restart a deployment.
    
    This endpoint triggers a restart of either a GKE deployment or Cloud Run service.
    For GKE, it deletes all pods to force recreation. For Cloud Run, it triggers
    a new deployment.
    
    Args:
        request: Restart deployment request.
        k8s_client: Kubernetes client (injected).
        cloud_run_client: Cloud Run client (injected).
        actions_logger: Actions logger (injected).
        
    Returns:
        ActionResponse with execution details.
        
    Raises:
        HTTPException: If restart fails.
    """
    logger.info(
        f"Restart deployment request: {request.service_name} "
        f"({request.target_type.value})"
    )
    
    try:
        if request.target_type == TargetType.GKE:
            # Execute GKE deployment restart
            record = restart_gke_deployment(
                service_name=request.service_name,
                cluster_name=request.cluster_name,
                namespace=request.namespace,
                k8s_client=k8s_client,
                reason=request.reason,
            )
        else:  # TargetType.CLOUD_RUN
            # Execute Cloud Run service restart
            record = restart_cloud_run_service(
                service_name=request.service_name,
                region=request.region,
                cloud_run_client=cloud_run_client,
                reason=request.reason,
            )
        
        # Log the action
        actions_logger.log_action(record)
        
        # Convert to response
        response = create_action_response(record)
        
        logger.info(
            f"Restart deployment completed: {request.service_name} "
            f"(status: {record.status.value})"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to restart deployment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart deployment: {str(e)}",
        )


@router.post(
    "/scale_deployment",
    response_model=ActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Scale a deployment",
    description="Scale a GKE deployment or Cloud Run service by adjusting replica counts.",
)
async def scale_deployment(
    request: ScaleDeploymentRequest,
    k8s_client: KubernetesClient = Depends(get_k8s_client),
    cloud_run_client: CloudRunClient = Depends(get_cloud_run_client),
    actions_logger: ActionsLogger = Depends(get_actions_logger),
) -> ActionResponse:
    """Scale a deployment.
    
    This endpoint adjusts the replica count for a GKE deployment or the
    autoscaling configuration for a Cloud Run service.
    
    Args:
        request: Scale deployment request.
        k8s_client: Kubernetes client (injected).
        cloud_run_client: Cloud Run client (injected).
        actions_logger: Actions logger (injected).
        
    Returns:
        ActionResponse with execution details.
        
    Raises:
        HTTPException: If scaling fails.
    """
    logger.info(
        f"Scale deployment request: {request.service_name} "
        f"({request.target_type.value})"
    )
    
    try:
        if request.target_type == TargetType.GKE:
            # Execute GKE deployment scaling
            record = scale_gke_deployment(
                service_name=request.service_name,
                cluster_name=request.cluster_name,
                namespace=request.namespace,
                k8s_client=k8s_client,
                replicas=request.replicas,
                reason=request.reason,
            )
        else:  # TargetType.CLOUD_RUN
            # Execute Cloud Run service scaling
            record = scale_cloud_run_service(
                service_name=request.service_name,
                region=request.region,
                cloud_run_client=cloud_run_client,
                min_replicas=request.min_replicas,
                max_replicas=request.max_replicas,
                reason=request.reason,
            )
        
        # Log the action
        actions_logger.log_action(record)
        
        # Convert to response
        response = create_action_response(record)
        
        logger.info(
            f"Scale deployment completed: {request.service_name} "
            f"(status: {record.status.value})"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to scale deployment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scale deployment: {str(e)}",
        )


@router.post(
    "/rollout_restart",
    response_model=ActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Rollout restart a GKE deployment",
    description="Perform a rolling restart of a GKE deployment without downtime (GKE only).",
)
async def rollout_restart(
    request: RolloutRestartRequest,
    k8s_client: KubernetesClient = Depends(get_k8s_client),
    actions_logger: ActionsLogger = Depends(get_actions_logger),
) -> ActionResponse:
    """Rollout restart a GKE deployment.
    
    This endpoint performs a gradual restart of a GKE deployment by triggering
    a rolling update. This ensures zero downtime during the restart.
    
    Note: This operation is only available for GKE deployments, not Cloud Run.
    
    Args:
        request: Rollout restart request.
        k8s_client: Kubernetes client (injected).
        actions_logger: Actions logger (injected).
        
    Returns:
        ActionResponse with execution details.
        
    Raises:
        HTTPException: If rollout restart fails.
    """
    logger.info(
        f"Rollout restart request: {request.service_name} "
        f"(cluster: {request.cluster_name})"
    )
    
    try:
        # Execute GKE rollout restart
        record = rollout_restart_gke_deployment(
            service_name=request.service_name,
            cluster_name=request.cluster_name,
            namespace=request.namespace,
            k8s_client=k8s_client,
            reason=request.reason,
        )
        
        # Log the action
        actions_logger.log_action(record)
        
        # Convert to response
        response = create_action_response(record)
        
        logger.info(
            f"Rollout restart completed: {request.service_name} "
            f"(status: {record.status.value})"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to rollout restart deployment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollout restart deployment: {str(e)}",
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the health status of the action engine service.",
)
async def health_check() -> dict:
    """Health check endpoint.
    
    Returns:
        Dictionary with health status.
    """
    return {
        "status": "healthy",
        "service": "action-engine",
        "version": "1.0.0",
    }
