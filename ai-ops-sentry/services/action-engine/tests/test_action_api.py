"""Unit tests for Action Engine API routes.

These tests use mocked clients to validate API behavior without
requiring real GCP infrastructure.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Dynamic import for main app
import importlib.util

main_path = Path(__file__).parent.parent / "main.py"
main_spec = importlib.util.spec_from_file_location("action_main", main_path)
main_module = importlib.util.module_from_spec(main_spec)
main_spec.loader.exec_module(main_module)
app = main_module.app

# Import models for test data
models_path = Path(__file__).parent.parent / "domain" / "models.py"
models_spec = importlib.util.spec_from_file_location("action_models", models_path)
models_module = importlib.util.module_from_spec(models_spec)
models_spec.loader.exec_module(models_module)
ActionStatus = models_module.ActionStatus
ActionType = models_module.ActionType
TargetType = models_module.TargetType
ActionRecord = models_module.ActionRecord


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_k8s_client():
    """Create mock Kubernetes client."""
    mock = Mock()
    mock.delete_deployment_pods.return_value = True
    mock.scale_deployment.return_value = True
    mock.rollout_restart_deployment.return_value = True
    mock.get_deployment_info.return_value = {
        "name": "test-deployment",
        "namespace": "default",
        "replicas": 3,
    }
    return mock


@pytest.fixture
def mock_cloud_run_client():
    """Create mock Cloud Run client."""
    mock = Mock()
    mock.restart_service.return_value = True
    mock.scale_service.return_value = True
    mock.get_service_info.return_value = {
        "name": "test-service",
        "region": "us-central1",
        "min_replicas": 1,
        "max_replicas": 10,
    }
    return mock


@pytest.fixture
def mock_actions_logger():
    """Create mock actions logger."""
    mock = Mock()
    mock.log_action.return_value = None
    return mock


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "action-engine"


class TestRestartDeploymentEndpoint:
    """Tests for restart deployment endpoint."""
    
    def test_restart_gke_deployment(
        self,
        client,
        mock_k8s_client,
        mock_cloud_run_client,
        mock_actions_logger,
    ):
        """Test restarting a GKE deployment."""
        # Patch the dependency functions to return our mocks
        with patch('action_main.routes_module.get_k8s_client', return_value=mock_k8s_client), \
             patch('action_main.routes_module.get_cloud_run_client', return_value=mock_cloud_run_client), \
             patch('action_main.routes_module.get_actions_logger', return_value=mock_actions_logger):
            
            # Make request
            response = client.post(
                "/api/v1/restart_deployment",
                json={
                    "service_name": "test-deployment",
                    "target_type": "gke",
                    "cluster_name": "test-cluster",
                    "namespace": "default",
                    "reason": "High CPU usage detected",
                },
            )

            # Validate response
            assert response.status_code == 200
            data = response.json()
            assert data["service_name"] == "test-deployment"
            assert data["action_type"] == "restart"
            assert data["target_type"] == "gke"
            assert "action_id" in data
            
            # Verify client was called
            mock_k8s_client.delete_deployment_pods.assert_called_once()
            mock_actions_logger.log_action.assert_called_once()
    
    def test_restart_cloud_run_service(
        self,
        client,
        mock_k8s_client,
        mock_cloud_run_client,
        mock_actions_logger,
    ):
        """Test restarting a Cloud Run service."""
        # Patch the dependency functions
        with patch('action_main.routes_module.get_k8s_client', return_value=mock_k8s_client), \
             patch('action_main.routes_module.get_cloud_run_client', return_value=mock_cloud_run_client), \
             patch('action_main.routes_module.get_actions_logger', return_value=mock_actions_logger):
            
            # Make request
            response = client.post(
                "/api/v1/restart_deployment",
                json={
                    "service_name": "test-service",
                    "target_type": "cloud_run",
                    "region": "us-central1",
                    "reason": "Memory leak detected",
                },
            )

            # Validate response
            assert response.status_code == 200
            data = response.json()
            assert data["service_name"] == "test-service"
            assert data["action_type"] == "restart"
            assert data["target_type"] == "cloud_run"
            
            # Verify client was called
            mock_cloud_run_client.restart_service.assert_called_once()
            mock_actions_logger.log_action.assert_called_once()
    
    def test_restart_missing_cluster_name(self, client):
        """Test validation error when cluster_name missing for GKE."""
        response = client.post(
            "/api/v1/restart_deployment",
            json={
                "service_name": "test-deployment",
                "target_type": "gke",
                "namespace": "default",
                "reason": "Test",
            },
        )
        
        # Should return validation error
        assert response.status_code == 422


class TestScaleDeploymentEndpoint:
    """Tests for scale deployment endpoint."""
    
    def test_scale_gke_deployment(
        self,
        client,
        mock_k8s_client,
        mock_cloud_run_client,
        mock_actions_logger,
    ):
        """Test scaling a GKE deployment."""
        with patch('action_main.routes_module.get_k8s_client', return_value=mock_k8s_client), \
             patch('action_main.routes_module.get_cloud_run_client', return_value=mock_cloud_run_client), \
             patch('action_main.routes_module.get_actions_logger', return_value=mock_actions_logger):
            
            # Make request
            response = client.post(
                "/api/v1/scale_deployment",
                json={
                    "service_name": "test-deployment",
                    "target_type": "gke",
                    "cluster_name": "test-cluster",
                    "namespace": "default",
                    "replicas": 5,
                    "reason": "Increased traffic",
                },
            )

            # Validate response
            assert response.status_code == 200
            data = response.json()
            assert data["service_name"] == "test-deployment"
            assert data["action_type"] == "scale"
            
            # Verify client was called
            mock_k8s_client.scale_deployment.assert_called_once()
            mock_actions_logger.log_action.assert_called_once()
    
    def test_scale_cloud_run_service(
        self,
        client,
        mock_k8s_client,
        mock_cloud_run_client,
        mock_actions_logger,
    ):
        """Test scaling a Cloud Run service."""
        with patch('action_main.routes_module.get_k8s_client', return_value=mock_k8s_client), \
             patch('action_main.routes_module.get_cloud_run_client', return_value=mock_cloud_run_client), \
             patch('action_main.routes_module.get_actions_logger', return_value=mock_actions_logger):
            
            # Make request
            response = client.post(
                "/api/v1/scale_deployment",
                json={
                    "service_name": "test-service",
                    "target_type": "cloud_run",
                    "region": "us-central1",
                    "min_replicas": 2,
                    "max_replicas": 20,
                    "reason": "Increased traffic",
                },
            )

            # Validate response
            assert response.status_code == 200
            data = response.json()
            assert data["service_name"] == "test-service"
            assert data["action_type"] == "scale"
            
            # Verify client was called
            mock_cloud_run_client.scale_service.assert_called_once()
            mock_actions_logger.log_action.assert_called_once()
    
    def test_scale_invalid_replicas(self, client):
        """Test validation error for invalid replica counts."""
        response = client.post(
            "/api/v1/scale_deployment",
            json={
                "service_name": "test-deployment",
                "target_type": "gke",
                "cluster_name": "test-cluster",
                "namespace": "default",
                "replicas": 0,  # Invalid
                "reason": "Test",
            },
        )
        
        # Should return validation error
        assert response.status_code == 422


class TestRolloutRestartEndpoint:
    """Tests for rollout restart endpoint."""
    
    def test_rollout_restart_gke_deployment(
        self,
        client,
        mock_k8s_client,
        mock_actions_logger,
    ):
        """Test rollout restart of a GKE deployment."""
        with patch('action_main.routes_module.get_k8s_client', return_value=mock_k8s_client), \
             patch('action_main.routes_module.get_actions_logger', return_value=mock_actions_logger):
            
            # Make request
            response = client.post(
                "/api/v1/rollout_restart",
                json={
                    "service_name": "test-deployment",
                    "cluster_name": "test-cluster",
                    "namespace": "default",
                    "reason": "Configuration update",
                },
            )

            # Validate response
            assert response.status_code == 200
            data = response.json()
            assert data["service_name"] == "test-deployment"
            assert data["action_type"] == "rollout_restart"
            assert data["target_type"] == "gke"
            
            # Verify client was called
            mock_k8s_client.rollout_restart_deployment.assert_called_once()
            mock_actions_logger.log_action.assert_called_once()
    
    def test_rollout_restart_missing_cluster_name(self, client):
        """Test validation error when cluster_name missing."""
        response = client.post(
            "/api/v1/rollout_restart",
            json={
                "service_name": "test-deployment",
                "namespace": "default",
                "reason": "Test",
            },
        )
        
        # Should return validation error
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

        """Test restarting a GKE deployment."""
        # Make request
        response = client.post(
            "/api/v1/restart_deployment",
            json={
                "service_name": "test-deployment",
                "target_type": "gke",
                "cluster_name": "test-cluster",
                "namespace": "default",
                "reason": "High CPU usage detected",
            },
        )
        
        # Validate response
        assert response.status_code == 200
        data = response.json()
        assert data["service_name"] == "test-deployment"
        assert data["action_type"] == "restart"
        assert data["target_type"] == "gke"
        assert "action_id" in data
        
        # Verify client was called
        mock_k8s_client.delete_deployment_pods.assert_called_once()
    
    def test_restart_cloud_run_service(
        self,
        client,
        mock_cloud_run_client,
    ):
        """Test restarting a Cloud Run service."""
        # Make request
        response = client.post(
            "/api/v1/restart_deployment",
            json={
                "service_name": "test-service",
                "target_type": "cloud_run",
                "region": "us-central1",
                "reason": "Memory leak detected",
            },
        )
        
        # Validate response
        assert response.status_code == 200
        data = response.json()
        assert data["service_name"] == "test-service"
        assert data["action_type"] == "restart"
        assert data["target_type"] == "cloud_run"
        
        # Verify client was called
        mock_cloud_run_client.restart_service.assert_called_once()
    
    def test_restart_missing_cluster_name(self, client):
        """Test validation error when cluster_name missing for GKE."""
        response = client.post(
            "/api/v1/restart_deployment",
            json={
                "service_name": "test-deployment",
                "target_type": "gke",
                "namespace": "default",
                "reason": "Test",
            },
        )
        
        # Should return validation error
        assert response.status_code == 422


class TestScaleDeploymentEndpoint:
    """Tests for scale deployment endpoint."""
    
    def test_scale_gke_deployment(
        self,
        client,
        mock_k8s_client,
    ):
        """Test scaling a GKE deployment."""
        # Make request
        response = client.post(
            "/api/v1/scale_deployment",
            json={
                "service_name": "test-deployment",
                "target_type": "gke",
                "cluster_name": "test-cluster",
                "namespace": "default",
                "replicas": 5,
                "reason": "Increased traffic",
            },
        )
        
        # Validate response
        assert response.status_code == 200
        data = response.json()
        assert data["service_name"] == "test-deployment"
        assert data["action_type"] == "scale"
        
        # Verify client was called
        mock_k8s_client.scale_deployment.assert_called_once()
    
    def test_scale_cloud_run_service(
        self,
        client,
        mock_cloud_run_client,
    ):
        """Test scaling a Cloud Run service."""
        # Make request
        response = client.post(
            "/api/v1/scale_deployment",
            json={
                "service_name": "test-service",
                "target_type": "cloud_run",
                "region": "us-central1",
                "min_replicas": 2,
                "max_replicas": 20,
                "reason": "Increased traffic",
            },
        )
        
        # Validate response
        assert response.status_code == 200
        data = response.json()
        assert data["service_name"] == "test-service"
        assert data["action_type"] == "scale"
        
        # Verify client was called
        mock_cloud_run_client.scale_service.assert_called_once()
    
    def test_scale_invalid_replicas(self, client):
        """Test validation error for invalid replica counts."""
        response = client.post(
            "/api/v1/scale_deployment",
            json={
                "service_name": "test-deployment",
                "target_type": "gke",
                "cluster_name": "test-cluster",
                "namespace": "default",
                "replicas": 0,  # Invalid
                "reason": "Test",
            },
        )
        
        # Should return validation error
        assert response.status_code == 422


class TestRolloutRestartEndpoint:
    """Tests for rollout restart endpoint."""
    
    def test_rollout_restart_gke_deployment(
        self,
        client,
        mock_k8s_client,
    ):
        """Test rollout restart of a GKE deployment."""
        # Make request
        response = client.post(
            "/api/v1/rollout_restart",
            json={
                "service_name": "test-deployment",
                "cluster_name": "test-cluster",
                "namespace": "default",
                "reason": "Configuration update",
            },
        )
        
        # Validate response
        assert response.status_code == 200
        data = response.json()
        assert data["service_name"] == "test-deployment"
        assert data["action_type"] == "rollout_restart"
        assert data["target_type"] == "gke"
        
        # Verify client was called
        mock_k8s_client.rollout_restart_deployment.assert_called_once()
    
    def test_rollout_restart_missing_cluster_name(self, client):
        """Test validation error when cluster_name missing."""
        response = client.post(
            "/api/v1/rollout_restart",
            json={
                "service_name": "test-deployment",
                "namespace": "default",
                "reason": "Test",
            },
        )
        
        # Should return validation error
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
