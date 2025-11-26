"""Configuration management for AI Ops Sentry.

This module provides typed configuration objects that read from environment variables
with optional .env file support. All configuration is environment-based with no
hard-coded secrets or project IDs.
"""

import os
from typing import Optional
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GCPConfig(BaseSettings):
    """Google Cloud Platform configuration.
    
    All values are read from environment variables or .env file.
    No defaults are provided for sensitive values like project_id.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # GCP Project Settings
    gcp_project_id: str = Field(
        ...,
        description="GCP Project ID",
        validation_alias="GCP_PROJECT_ID",
    )
    
    gcp_region: str = Field(
        default="us-central1",
        description="GCP region for resources",
        validation_alias="GCP_REGION",
    )
    
    # BigQuery Settings
    bigquery_dataset: str = Field(
        default="aiops_data",
        description="BigQuery dataset name",
        validation_alias="BIGQUERY_DATASET",
    )
    
    bigquery_location: str = Field(
        default="US",
        description="BigQuery dataset location",
        validation_alias="BIGQUERY_LOCATION",
    )
    
    # BigQuery Table Names
    bigquery_table_metrics_raw: str = Field(
        default="metrics_raw",
        description="Raw metrics table",
        validation_alias="BIGQUERY_TABLE_METRICS_RAW",
    )
    
    bigquery_table_metrics_agg_1m: str = Field(
        default="metrics_agg_1m",
        description="1-minute aggregated metrics table",
        validation_alias="BIGQUERY_TABLE_METRICS_AGG_1M",
    )
    
    bigquery_table_logs_clean: str = Field(
        default="logs_clean",
        description="Cleaned logs table",
        validation_alias="BIGQUERY_TABLE_LOGS_CLEAN",
    )
    
    bigquery_table_anomalies: str = Field(
        default="anomalies",
        description="Detected anomalies table",
        validation_alias="BIGQUERY_TABLE_ANOMALIES",
    )
    
    bigquery_table_actions: str = Field(
        default="actions",
        description="Executed actions table",
        validation_alias="BIGQUERY_TABLE_ACTIONS",
    )
    
    # Pub/Sub Settings
    pubsub_topic_metric_batches: str = Field(
        default="metric_batches",
        description="Pub/Sub topic for metric batches",
        validation_alias="PUBSUB_TOPIC_METRIC_BATCHES",
    )
    
    pubsub_topic_log_entries: str = Field(
        default="log_entries",
        description="Pub/Sub topic for log entries",
        validation_alias="PUBSUB_TOPIC_LOG_ENTRIES",
    )
    
    pubsub_topic_anomaly_events: str = Field(
        default="anomaly_events",
        description="Pub/Sub topic for anomaly events",
        validation_alias="PUBSUB_TOPIC_ANOMALY_EVENTS",
    )
    
    # Cloud Storage Settings
    gcs_bucket_models: Optional[str] = Field(
        default=None,
        description="GCS bucket for ML models",
        validation_alias="GCS_BUCKET_MODELS",
    )
    
    gcs_bucket_data: Optional[str] = Field(
        default=None,
        description="GCS bucket for data storage",
        validation_alias="GCS_BUCKET_DATA",
    )

    @field_validator("gcp_project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        """Validate that project ID is not empty."""
        if not v or v.strip() == "":
            raise ValueError("GCP_PROJECT_ID must be set and non-empty")
        return v.strip()

    def get_full_table_id(self, table_name: str) -> str:
        """Get fully qualified BigQuery table ID.
        
        Args:
            table_name: Short table name (e.g., 'metrics_raw')
            
        Returns:
            Fully qualified table ID in format: project.dataset.table
        """
        return f"{self.gcp_project_id}.{self.bigquery_dataset}.{table_name}"

    def get_full_topic_path(self, topic_name: str) -> str:
        """Get fully qualified Pub/Sub topic path.
        
        Args:
            topic_name: Short topic name (e.g., 'metric_batches')
            
        Returns:
            Fully qualified topic path in format: projects/{project}/topics/{topic}
        """
        return f"projects/{self.gcp_project_id}/topics/{topic_name}"


class ServiceConfig(BaseSettings):
    """Generic service configuration.
    
    Common settings shared across all services.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = Field(
        default="aiops-service",
        description="Service name for logging and metrics",
        validation_alias="SERVICE_NAME",
    )
    
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
        validation_alias="ENVIRONMENT",
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        validation_alias="LOG_LEVEL",
    )
    
    port: int = Field(
        default=8080,
        description="Service port",
        validation_alias="PORT",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper


def load_gcp_config() -> GCPConfig:
    """Load GCP configuration from environment.
    
    Returns:
        GCPConfig instance with validated configuration
        
    Raises:
        ValidationError: If required configuration is missing or invalid
    """
    return GCPConfig()


def load_service_config() -> ServiceConfig:
    """Load service configuration from environment.
    
    Returns:
        ServiceConfig instance with validated configuration
    """
    return ServiceConfig()
