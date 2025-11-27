"""Domain logic for remediation actions.

This module contains the core business logic for executing remediation actions
on GKE deployments and Cloud Run services. All functions are designed with
abstract signatures that can work with stubbed or real GCP clients.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional
from pathlib import Path
import sys
import importlib.util

# Dynamic import for models
models_path = Path(__file__).parent / "models.py"
models_spec = importlib.util.spec_from_file_location("action_models", models_path)
models_module = importlib.util.module_from_spec(models_spec)
models_spec.loader.exec_module(models_module)
ActionType = models_module.ActionType
ActionStatus = models_module.ActionStatus
ActionRecord = models_module.ActionRecord
TargetType = models_module.TargetType
RestartDeploymentRequest = models_module.RestartDeploymentRequest
ScaleDeploymentRequest = models_module.ScaleDeploymentRequest
RolloutRestartRequest = models_module.RolloutRestartRequest
ActionResponse = models_module.ActionResponse

logger = logging.getLogger(__name__)


def restart_gke_deployment(
    service_name: str,
    cluster_name: str,
    namespace: str,
    k8s_client,  # KubernetesClient interface
    reason: Optional[str] = None,
) -> ActionRecord:
    """Restart a GKE deployment by deleting all pods.
    
    This triggers Kubernetes to recreate the pods with the current deployment spec.
    
    Args:
        service_name: Name of the deployment to restart.
        cluster_name: GKE cluster name.
        namespace: Kubernetes namespace.
        k8s_client: Kubernetes client instance.
        reason: Reason for the restart.
        
    Returns:
        ActionRecord with execution details.
        
    Raises:
        Exception: If restart fails.
    """
    action_id = str(uuid.uuid4())
    logger.info(
        f"Restarting GKE deployment: {service_name} in cluster {cluster_name}, "
        f"namespace {namespace} (action_id: {action_id})"
    )
    
    try:
        # Delete pods to trigger restart
        k8s_client.delete_deployment_pods(
            deployment_name=service_name,
            namespace=namespace,
            cluster_name=cluster_name,
        )
        
        message = f"Successfully restarted deployment {service_name}"
        status = ActionStatus.SUCCESS
        logger.info(f"Action {action_id}: {message}")
        
    except Exception as e:
        message = f"Failed to restart deployment {service_name}: {str(e)}"
        status = ActionStatus.FAILED
        logger.error(f"Action {action_id}: {message}", exc_info=True)
    
    return ActionRecord(
        action_id=action_id,
        action_type=ActionType.RESTART_DEPLOYMENT,
        status=status,
        service_name=service_name,
        target_type=TargetType.GKE,
        cluster_name=cluster_name,
        namespace=namespace,
        reason=reason,
        message=message,
        timestamp=datetime.utcnow(),
    )


def scale_gke_deployment(
    service_name: str,
    cluster_name: str,
    namespace: str,
    k8s_client,  # KubernetesClient interface
    replicas: Optional[int] = None,
    reason: Optional[str] = None,
) -> ActionRecord:
    """Scale a GKE deployment to a specific number of replicas.
    
    Args:
        service_name: Name of the deployment to scale.
        cluster_name: GKE cluster name.
        namespace: Kubernetes namespace.
        k8s_client: Kubernetes client instance.
        replicas: Target number of replicas.
        reason: Reason for scaling.
        
    Returns:
        ActionRecord with execution details.
        
    Raises:
        Exception: If scaling fails.
    """
    action_id = str(uuid.uuid4())
    logger.info(
        f"Scaling GKE deployment: {service_name} to {replicas} replicas in "
        f"cluster {cluster_name}, namespace {namespace} (action_id: {action_id})"
    )
    
    try:
        k8s_client.scale_deployment(
            deployment_name=service_name,
            namespace=namespace,
            cluster_name=cluster_name,
            replicas=replicas,
        )
        
        message = f"Successfully scaled deployment {service_name} to {replicas} replicas"
        status = ActionStatus.SUCCESS
        logger.info(f"Action {action_id}: {message}")
        
    except Exception as e:
        message = f"Failed to scale deployment {service_name}: {str(e)}"
        status = ActionStatus.FAILED
        logger.error(f"Action {action_id}: {message}", exc_info=True)
    
    return ActionRecord(
        action_id=action_id,
        action_type=ActionType.SCALE_DEPLOYMENT,
        status=status,
        service_name=service_name,
        target_type=TargetType.GKE,
        cluster_name=cluster_name,
        namespace=namespace,
        replicas=replicas,
        reason=reason,
        message=message,
        timestamp=datetime.utcnow(),
    )


def rollout_restart_gke_deployment(
    service_name: str,
    cluster_name: str,
    namespace: str,
    k8s_client,  # KubernetesClient interface
    reason: Optional[str] = None,
) -> ActionRecord:
    """Perform a rolling restart of a GKE deployment.
    
    This triggers a gradual restart without downtime by updating the deployment spec
    to force pod recreation.
    
    Args:
        service_name: Name of the deployment to restart.
        cluster_name: GKE cluster name.
        namespace: Kubernetes namespace.
        k8s_client: Kubernetes client instance.
        reason: Reason for the rollout restart.
        
    Returns:
        ActionRecord with execution details.
        
    Raises:
        Exception: If rollout restart fails.
    """
    action_id = str(uuid.uuid4())
    logger.info(
        f"Rolling restart of GKE deployment: {service_name} in cluster {cluster_name}, "
        f"namespace {namespace} (action_id: {action_id})"
    )
    
    try:
        k8s_client.rollout_restart_deployment(
            deployment_name=service_name,
            namespace=namespace,
            cluster_name=cluster_name,
        )
        
        message = f"Successfully initiated rollout restart for deployment {service_name}"
        status = ActionStatus.SUCCESS
        logger.info(f"Action {action_id}: {message}")
        
    except Exception as e:
        message = f"Failed to rollout restart deployment {service_name}: {str(e)}"
        status = ActionStatus.FAILED
        logger.error(f"Action {action_id}: {message}", exc_info=True)
    
    return ActionRecord(
        action_id=action_id,
        action_type=ActionType.ROLLOUT_RESTART,
        status=status,
        service_name=service_name,
        target_type=TargetType.GKE,
        cluster_name=cluster_name,
        namespace=namespace,
        reason=reason,
        message=message,
        timestamp=datetime.utcnow(),
    )


def restart_cloud_run_service(
    service_name: str,
    region: str,
    cloud_run_client,  # CloudRunClient interface
    reason: Optional[str] = None,
) -> ActionRecord:
    """Restart a Cloud Run service.
    
    This triggers a new deployment of the Cloud Run service.
    
    Args:
        service_name: Name of the Cloud Run service.
        region: GCP region where the service is deployed.
        cloud_run_client: Cloud Run client instance.
        reason: Reason for the restart.
        
    Returns:
        ActionRecord with execution details.
        
    Raises:
        Exception: If restart fails.
    """
    action_id = str(uuid.uuid4())
    logger.info(
        f"Restarting Cloud Run service: {service_name} in region {region} "
        f"(action_id: {action_id})"
    )
    
    try:
        cloud_run_client.restart_service(
            service_name=service_name,
            region=region,
        )
        
        message = f"Successfully restarted Cloud Run service {service_name}"
        status = ActionStatus.SUCCESS
        logger.info(f"Action {action_id}: {message}")
        
    except Exception as e:
        message = f"Failed to restart Cloud Run service {service_name}: {str(e)}"
        status = ActionStatus.FAILED
        logger.error(f"Action {action_id}: {message}", exc_info=True)
    
    return ActionRecord(
        action_id=action_id,
        action_type=ActionType.RESTART_DEPLOYMENT,
        status=status,
        service_name=service_name,
        target_type=TargetType.CLOUD_RUN,
        region=region,
        reason=reason,
        message=message,
        timestamp=datetime.utcnow(),
    )


def scale_cloud_run_service(
    service_name: str,
    region: str,
    cloud_run_client,  # CloudRunClient interface
    min_replicas: Optional[int] = None,
    max_replicas: Optional[int] = None,
    reason: Optional[str] = None,
) -> ActionRecord:
    """Scale a Cloud Run service.
    
    Updates the autoscaling configuration for the Cloud Run service.
    
    Args:
        service_name: Name of the Cloud Run service.
        region: GCP region where the service is deployed.
        cloud_run_client: Cloud Run client instance.
        min_replicas: Minimum number of instances.
        max_replicas: Maximum number of instances.
        reason: Reason for scaling.
        
    Returns:
        ActionRecord with execution details.
        
    Raises:
        Exception: If scaling fails.
    """
    action_id = str(uuid.uuid4())
    logger.info(
        f"Scaling Cloud Run service: {service_name} in region {region} "
        f"(min: {min_replicas}, max: {max_replicas}, action_id: {action_id})"
    )
    
    try:
        cloud_run_client.scale_service(
            service_name=service_name,
            region=region,
            min_instances=min_replicas,
            max_instances=max_replicas,
        )
        
        message = (
            f"Successfully scaled Cloud Run service {service_name} "
            f"(min: {min_replicas}, max: {max_replicas})"
        )
        status = ActionStatus.SUCCESS
        logger.info(f"Action {action_id}: {message}")
        
    except Exception as e:
        message = f"Failed to scale Cloud Run service {service_name}: {str(e)}"
        status = ActionStatus.FAILED
        logger.error(f"Action {action_id}: {message}", exc_info=True)
    
    return ActionRecord(
        action_id=action_id,
        action_type=ActionType.SCALE_DEPLOYMENT,
        status=status,
        service_name=service_name,
        target_type=TargetType.CLOUD_RUN,
        region=region,
        min_replicas=min_replicas,
        max_replicas=max_replicas,
        reason=reason,
        message=message,
        timestamp=datetime.utcnow(),
    )


def create_action_response(record: ActionRecord) -> ActionResponse:
    """Convert an ActionRecord to an ActionResponse.
    
    Args:
        record: ActionRecord from domain function.
        
    Returns:
        ActionResponse for API response.
    """
    return ActionResponse(
        action_id=record.action_id,
        action_type=record.action_type,
        status=record.status,
        message=record.message,
        service_name=record.service_name,
        target_type=record.target_type,
        timestamp=record.timestamp,
        metadata={
            "cluster_name": record.cluster_name,
            "region": record.region,
            "namespace": record.namespace,
            "replicas": record.replicas,
            "min_replicas": record.min_replicas,
            "max_replicas": record.max_replicas,
            "reason": record.reason,
        },
    )
