"""Unit tests for Slack notifications library.

Tests the SlackNotifier class with mocked HTTP requests to ensure
notifications are formatted correctly without making real API calls.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import Timeout, RequestException

from libs.notifications.config import SlackConfig
from libs.notifications.models import IncidentPayload, ActionPayload, HealthAlertPayload
from libs.notifications.slack_client import SlackNotifier


@pytest.fixture
def slack_config():
    """Create a test Slack configuration."""
    return SlackConfig(
        slack_webhook_url="https://hooks.slack.com/services/TEST/WEBHOOK/URL",
        slack_enabled=True,
        slack_username="Test Bot",
        slack_icon_emoji=":robot:",
    )


@pytest.fixture
def slack_notifier(slack_config):
    """Create a test SlackNotifier instance."""
    return SlackNotifier(config=slack_config)


@pytest.fixture
def incident_payload():
    """Create a sample incident payload."""
    return IncidentPayload(
        incident_id="inc-123",
        service_name="payment-api",
        severity="critical",
        title="High CPU Usage Detected",
        description="CPU usage has exceeded 90% threshold",
        metric_name="cpu_usage",
        anomaly_score=0.95,
        expected_value=50.0,
        actual_value=92.5,
        timestamp=datetime(2025, 11, 27, 12, 0, 0),
        metadata={"cluster": "prod", "namespace": "default"},
        dashboard_url="https://dashboard.example.com/incidents/inc-123"
    )


@pytest.fixture
def action_payload():
    """Create a sample action payload."""
    return ActionPayload(
        action_id="act-456",
        service_name="user-auth",
        action_type="restart",
        status="completed",
        target_type="gke",
        reason="Automated recovery from high error rate",
        triggered_by="auto",
        result="Successfully restarted 3 pods",
        timestamp=datetime(2025, 11, 27, 12, 5, 0),
        metadata={"cluster": "prod-cluster", "namespace": "default", "pods_restarted": 3},
        dashboard_url="https://dashboard.example.com/actions/act-456"
    )


@pytest.fixture
def health_payload():
    """Create a sample health alert payload."""
    return HealthAlertPayload(
        service_name="inventory-svc",
        status="degraded",
        message="Response time increased by 50%",
        timestamp=datetime(2025, 11, 27, 12, 10, 0),
        metadata={"avg_response_time_ms": 1500}
    )


class TestSlackNotifier:
    """Test suite for SlackNotifier class."""
    
    def test_init_with_config(self, slack_config):
        """Test initialization with provided config."""
        notifier = SlackNotifier(config=slack_config)
        assert notifier.enabled is True
        assert notifier.webhook_url == str(slack_config.slack_webhook_url)
    
    def test_init_without_config(self):
        """Test initialization without config (loads from env)."""
        with patch.object(SlackConfig, '__init__', return_value=None):
            with patch.object(SlackConfig, 'slack_webhook_url', None):
                with patch.object(SlackConfig, 'is_configured', return_value=False):
                    notifier = SlackNotifier()
                    # Should handle missing config gracefully
                    assert notifier is not None
    
    def test_disabled_notifications(self):
        """Test that disabled notifications don't send messages."""
        config = SlackConfig(slack_enabled=False)
        notifier = SlackNotifier(config=config)
        
        incident = IncidentPayload(
            incident_id="inc-1",
            service_name="test",
            severity="info",
            title="Test",
            description="Test incident"
        )
        
        result = notifier.send_incident_alert(incident)
        assert result is False
    
    @patch('libs.notifications.slack_client.requests.post')
    def test_send_incident_alert_success(self, mock_post, slack_notifier, incident_payload):
        """Test sending incident alert successfully."""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "ok"
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = slack_notifier.send_incident_alert(incident_payload)
        
        assert result is True
        assert mock_post.called
        
        # Verify payload structure
        call_args = mock_post.call_args
        payload = call_args.kwargs['json']
        
        assert 'username' in payload
        assert 'icon_emoji' in payload
        assert 'attachments' in payload
        assert len(payload['attachments']) > 0
        
        attachment = payload['attachments'][0]
        assert 'blocks' in attachment
        assert 'color' in attachment
        assert attachment['color'] == "#FF0000"  # Critical = red
        
        # Verify blocks contain expected data
        blocks = attachment['blocks']
        assert any(incident_payload.title in str(block) for block in blocks)
        assert any(incident_payload.service_name in str(block) for block in blocks)
    
    @patch('libs.notifications.slack_client.requests.post')
    def test_send_action_alert_success(self, mock_post, slack_notifier, action_payload):
        """Test sending action alert successfully."""
        mock_response = Mock()
        mock_response.text = "ok"
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = slack_notifier.send_action_alert(action_payload)
        
        assert result is True
        assert mock_post.called
        
        # Verify payload
        payload = mock_post.call_args.kwargs['json']
        attachment = payload['attachments'][0]
        
        assert attachment['color'] == "#00FF00"  # Completed = green
        
        blocks = attachment['blocks']
        assert any(action_payload.service_name in str(block) for block in blocks)
        assert any(action_payload.action_type in str(block) for block in blocks)
        assert any(action_payload.reason in str(block) for block in blocks)
    
    @patch('libs.notifications.slack_client.requests.post')
    def test_send_health_alert_success(self, mock_post, slack_notifier, health_payload):
        """Test sending health alert successfully."""
        mock_response = Mock()
        mock_response.text = "ok"
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = slack_notifier.send_health_alert(health_payload)
        
        assert result is True
        assert mock_post.called
        
        # Verify payload
        payload = mock_post.call_args.kwargs['json']
        attachment = payload['attachments'][0]
        
        assert attachment['color'] == "#FFA500"  # Degraded = orange
        assert health_payload.service_name in attachment['text']
        assert health_payload.message in attachment['text']
    
    @patch('libs.notifications.slack_client.requests.post')
    def test_send_custom_message_success(self, mock_post, slack_notifier):
        """Test sending custom message successfully."""
        mock_response = Mock()
        mock_response.text = "ok"
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = slack_notifier.send_custom_message(
            text="Test message",
            blocks=[{"type": "section", "text": {"type": "plain_text", "text": "Custom block"}}]
        )
        
        assert result is True
        assert mock_post.called
        
        payload = mock_post.call_args.kwargs['json']
        assert payload['text'] == "Test message"
        assert 'blocks' in payload
    
    @patch('libs.notifications.slack_client.requests.post')
    def test_send_message_timeout(self, mock_post, slack_notifier, incident_payload):
        """Test handling of timeout errors."""
        mock_post.side_effect = Timeout("Request timeout")
        
        result = slack_notifier.send_incident_alert(incident_payload)
        
        assert result is False
    
    @patch('libs.notifications.slack_client.requests.post')
    def test_send_message_request_exception(self, mock_post, slack_notifier, incident_payload):
        """Test handling of request exceptions."""
        mock_post.side_effect = RequestException("Connection error")
        
        result = slack_notifier.send_incident_alert(incident_payload)
        
        assert result is False
    
    @patch('libs.notifications.slack_client.requests.post')
    def test_send_message_http_error(self, mock_post, slack_notifier, incident_payload):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = RequestException("404 Not Found")
        mock_post.return_value = mock_response
        
        result = slack_notifier.send_incident_alert(incident_payload)
        
        assert result is False
    
    @patch('libs.notifications.slack_client.requests.post')
    def test_send_message_unexpected_response(self, mock_post, slack_notifier, incident_payload):
        """Test handling of unexpected responses."""
        mock_response = Mock()
        mock_response.text = "invalid_response"
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = slack_notifier.send_incident_alert(incident_payload)
        
        assert result is False
    
    def test_incident_severity_colors(self, slack_notifier):
        """Test that different severity levels use correct colors."""
        with patch('libs.notifications.slack_client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.text = "ok"
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            # Test critical (red)
            critical = IncidentPayload(
                incident_id="1", service_name="test", severity="critical",
                title="Critical", description="Test"
            )
            slack_notifier.send_incident_alert(critical)
            assert mock_post.call_args.kwargs['json']['attachments'][0]['color'] == "#FF0000"
            
            # Test warning (orange)
            warning = IncidentPayload(
                incident_id="2", service_name="test", severity="warning",
                title="Warning", description="Test"
            )
            slack_notifier.send_incident_alert(warning)
            assert mock_post.call_args.kwargs['json']['attachments'][0]['color'] == "#FFA500"
            
            # Test info (blue)
            info = IncidentPayload(
                incident_id="3", service_name="test", severity="info",
                title="Info", description="Test"
            )
            slack_notifier.send_incident_alert(info)
            assert mock_post.call_args.kwargs['json']['attachments'][0]['color'] == "#0099FF"
    
    def test_action_status_colors(self, slack_notifier):
        """Test that different action statuses use correct colors."""
        with patch('libs.notifications.slack_client.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.text = "ok"
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            # Test completed (green)
            completed = ActionPayload(
                action_id="1", service_name="test", action_type="restart",
                status="completed", target_type="gke", reason="Test"
            )
            slack_notifier.send_action_alert(completed)
            assert mock_post.call_args.kwargs['json']['attachments'][0]['color'] == "#00FF00"
            
            # Test failed (red)
            failed = ActionPayload(
                action_id="2", service_name="test", action_type="restart",
                status="failed", target_type="gke", reason="Test"
            )
            slack_notifier.send_action_alert(failed)
            assert mock_post.call_args.kwargs['json']['attachments'][0]['color'] == "#FF0000"
            
            # Test started (blue)
            started = ActionPayload(
                action_id="3", service_name="test", action_type="restart",
                status="started", target_type="gke", reason="Test"
            )
            slack_notifier.send_action_alert(started)
            assert mock_post.call_args.kwargs['json']['attachments'][0]['color'] == "#0099FF"
