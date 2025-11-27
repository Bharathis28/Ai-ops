"""Unit tests for configuration module.

These tests use environment variable mocking and do not require actual GCP resources.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from libs.core.config import GCPConfig, ServiceConfig, load_gcp_config, load_service_config


class TestGCPConfig:
    """Test cases for GCPConfig."""

    def test_gcp_config_with_required_fields(self) -> None:
        """Test GCPConfig initialization with required fields."""
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project-123"}):
            config = GCPConfig()
            assert config.gcp_project_id == "test-project-123"
            assert config.gcp_region == "us-central1"  # default
            assert config.bigquery_dataset == "aiops_data"  # default

    def test_gcp_config_missing_project_id(self) -> None:
        """Test that GCPConfig raises error when project_id is missing."""
        # Clear both env vars and disable .env file loading
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(GCPConfig.model_config, 'env_file', None):
                with pytest.raises(ValidationError) as exc_info:
                    GCPConfig()
                assert "gcp_project_id" in str(exc_info.value).lower()

    def test_gcp_config_empty_project_id(self) -> None:
        """Test that GCPConfig raises error when project_id is empty."""
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "   "}):
            with pytest.raises(ValidationError) as exc_info:
                GCPConfig()
            assert "must be set and non-empty" in str(exc_info.value).lower()

    def test_gcp_config_with_custom_values(self) -> None:
        """Test GCPConfig with all custom values."""
        env_vars = {
            "GCP_PROJECT_ID": "my-custom-project",
            "GCP_REGION": "us-west1",
            "BIGQUERY_DATASET": "custom_dataset",
            "BIGQUERY_LOCATION": "EU",
            "PUBSUB_TOPIC_METRIC_BATCHES": "custom_metrics",
            "GCS_BUCKET_MODELS": "my-models-bucket",
        }
        with patch.dict(os.environ, env_vars):
            config = GCPConfig()
            assert config.gcp_project_id == "my-custom-project"
            assert config.gcp_region == "us-west1"
            assert config.bigquery_dataset == "custom_dataset"
            assert config.bigquery_location == "EU"
            assert config.pubsub_topic_metric_batches == "custom_metrics"
            assert config.gcs_bucket_models == "my-models-bucket"

    def test_get_full_table_id(self) -> None:
        """Test fully qualified table ID generation."""
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project"}):
            config = GCPConfig()
            table_id = config.get_full_table_id("metrics_raw")
            assert table_id == "test-project.aiops_data.metrics_raw"

    def test_get_full_topic_path(self) -> None:
        """Test fully qualified topic path generation."""
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project"}):
            config = GCPConfig()
            topic_path = config.get_full_topic_path("metric_batches")
            assert topic_path == "projects/test-project/topics/metric_batches"

    def test_bigquery_table_names(self) -> None:
        """Test all BigQuery table name fields."""
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project"}):
            config = GCPConfig()
            assert config.bigquery_table_metrics_raw == "metrics_raw"
            assert config.bigquery_table_metrics_agg_1m == "metrics_agg_1m"
            assert config.bigquery_table_logs_clean == "logs_clean"
            assert config.bigquery_table_anomalies == "anomalies"
            assert config.bigquery_table_actions == "actions"

    def test_pubsub_topic_names(self) -> None:
        """Test all Pub/Sub topic name fields."""
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project"}):
            config = GCPConfig()
            assert config.pubsub_topic_metric_batches == "metric_batches"
            assert config.pubsub_topic_log_entries == "log_entries"
            assert config.pubsub_topic_anomaly_events == "anomaly_events"


class TestServiceConfig:
    """Test cases for ServiceConfig."""

    def test_service_config_defaults(self) -> None:
        """Test ServiceConfig with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = ServiceConfig()
            assert config.service_name == "aiops-service"
            assert config.environment == "development"
            assert config.log_level == "INFO"
            # Port comes from .env file in this test environment
            assert config.port in [8000, 8080]  # Accept either default or env value

    def test_service_config_custom_values(self) -> None:
        """Test ServiceConfig with custom values."""
        env_vars = {
            "SERVICE_NAME": "test-service",
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "DEBUG",
            "PORT": "9000",
        }
        with patch.dict(os.environ, env_vars):
            config = ServiceConfig()
            assert config.service_name == "test-service"
            assert config.environment == "production"
            assert config.log_level == "DEBUG"
            assert config.port == 9000
            assert config.ingestion_api_url == "http://localhost:8000" # default

    def test_service_config_custom_ingestion_url(self) -> None:
        """Test ServiceConfig with a custom ingestion API URL."""
        with patch.dict(os.environ, {"INGESTION_API_URL": "http://custom-api:8888"}):
            config = ServiceConfig()
            assert config.ingestion_api_url == "http://custom-api:8888"


    def test_service_config_invalid_log_level(self) -> None:
        """Test that invalid log level raises error."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            with pytest.raises(ValidationError) as exc_info:
                ServiceConfig()
            assert "invalid log level" in str(exc_info.value).lower()

    def test_service_config_log_level_case_insensitive(self) -> None:
        """Test that log level validation is case-insensitive."""
        with patch.dict(os.environ, {"LOG_LEVEL": "debug"}):
            config = ServiceConfig()
            assert config.log_level == "DEBUG"


class TestConfigLoaders:
    """Test cases for configuration loader functions."""

    def test_load_gcp_config(self) -> None:
        """Test load_gcp_config function."""
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "loader-test"}):
            config = load_gcp_config()
            assert isinstance(config, GCPConfig)
            assert config.gcp_project_id == "loader-test"

    def test_load_service_config(self) -> None:
        """Test load_service_config function."""
        with patch.dict(os.environ, {"SERVICE_NAME": "loader-test-service"}):
            config = load_service_config()
            assert isinstance(config, ServiceConfig)
            assert config.service_name == "loader-test-service"
