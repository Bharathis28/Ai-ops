"""Configuration for Action Engine service.

This module provides service-specific configuration that extends the
core GCP configuration.
"""

import os
from dataclasses import dataclass, field

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.core.config import GCPConfig


@dataclass
class ActionEngineConfig(GCPConfig):
    """Action Engine service configuration.
    
    Attributes:
        service_name: Name of the service.
        service_port: Port to run the service on.
        actions_log_backend: Backend for action logging ("console" or "bigquery").
        actions_log_table: BigQuery table for action logs.
        dry_run_mode: If True, don't execute real actions (for testing).
        max_concurrent_actions: Maximum number of concurrent actions.
        action_timeout_seconds: Timeout for individual actions.
    """
    
    service_name: str = "action-engine"
    service_port: int = 8003
    
    # Action logging configuration
    actions_log_backend: str = field(
        default_factory=lambda: os.getenv("ACTIONS_LOG_BACKEND", "console")
    )
    actions_log_table: str = field(
        default_factory=lambda: os.getenv(
            "ACTIONS_LOG_TABLE",
            "ai_ops_sentry.action_logs"
        )
    )
    
    # Execution configuration
    dry_run_mode: bool = field(
        default_factory=lambda: os.getenv("DRY_RUN_MODE", "false").lower() == "true"
    )
    max_concurrent_actions: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_ACTIONS", "5"))
    )
    action_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("ACTION_TIMEOUT_SECONDS", "300"))
    )
    
    # GKE configuration
    default_gke_namespace: str = field(
        default_factory=lambda: os.getenv("DEFAULT_GKE_NAMESPACE", "default")
    )
    
    # Cloud Run configuration
    default_cloud_run_region: str = field(
        default_factory=lambda: os.getenv("DEFAULT_CLOUD_RUN_REGION", "us-central1")
    )


def load_config() -> ActionEngineConfig:
    """Load action engine configuration.
    
    Returns:
        ActionEngineConfig instance.
    """
    return ActionEngineConfig()
