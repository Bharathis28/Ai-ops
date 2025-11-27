"""Slack notification client for AI Ops Sentry.

Provides a reusable SlackNotifier class for sending structured alerts
to Slack via Incoming Webhooks. Supports incident alerts, action notifications,
and custom messages with formatted blocks.
"""

import logging
from typing import Dict, Any, List, Optional
import requests
from requests.exceptions import RequestException, Timeout

from .config import SlackConfig
from .models import IncidentPayload, ActionPayload, HealthAlertPayload

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Client for sending notifications to Slack via Incoming Webhooks.
    
    This class provides high-level methods for sending structured notifications
    about incidents, actions, and health status. It automatically formats
    messages with Slack blocks for better visual presentation.
    
    Example:
        >>> config = SlackConfig(
        ...     slack_webhook_url="https://hooks.slack.com/services/...",
        ...     slack_enabled=True
        ... )
        >>> notifier = SlackNotifier(config)
        >>> incident = IncidentPayload(
        ...     incident_id="inc-123",
        ...     service_name="payment-api",
        ...     severity="critical",
        ...     title="High CPU Usage",
        ...     description="CPU usage exceeds 90%"
        ... )
        >>> notifier.send_incident_alert(incident)
    """
    
    def __init__(self, config: Optional[SlackConfig] = None):
        """Initialize Slack notifier.
        
        Args:
            config: Slack configuration. If None, loads from environment.
        """
        self.config = config or SlackConfig()
        self.webhook_url = str(self.config.slack_webhook_url) if self.config.slack_webhook_url else None
        self.enabled = self.config.is_configured()
        
        if not self.enabled:
            logger.warning(
                "Slack notifications disabled. Set SLACK_ENABLED=true and "
                "SLACK_WEBHOOK_URL in environment to enable."
            )
    
    def send_incident_alert(self, incident: IncidentPayload) -> bool:
        """Send an incident/anomaly alert to Slack.
        
        Formats the incident data into a rich Slack message with blocks
        showing severity, affected service, metric details, and anomaly scores.
        
        Args:
            incident: Incident payload with alert details
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Slack notifications disabled, skipping incident alert")
            return False
        
        # Determine color based on severity
        color_map = {
            "critical": "#FF0000",  # Red
            "warning": "#FFA500",   # Orange
            "info": "#0099FF",      # Blue
        }
        color = color_map.get(incident.severity, "#808080")
        
        # Determine emoji based on severity
        emoji_map = {
            "critical": "🚨",
            "warning": "⚠️",
            "info": "ℹ️",
        }
        emoji = emoji_map.get(incident.severity, "📊")
        
        # Build message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {incident.severity.upper()}: {incident.title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Service:*\n{incident.service_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Incident ID:*\n`{incident.incident_id}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{incident.severity.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{incident.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{incident.description}"
                }
            }
        ]
        
        # Add metric details if available
        if incident.metric_name:
            metric_fields = [
                {
                    "type": "mrkdwn",
                    "text": f"*Metric:*\n{incident.metric_name}"
                }
            ]
            
            if incident.anomaly_score is not None:
                metric_fields.append({
                    "type": "mrkdwn",
                    "text": f"*Anomaly Score:*\n{incident.anomaly_score:.2f}"
                })
            
            if incident.expected_value is not None:
                metric_fields.append({
                    "type": "mrkdwn",
                    "text": f"*Expected:*\n{incident.expected_value:.2f}"
                })
            
            if incident.actual_value is not None:
                metric_fields.append({
                    "type": "mrkdwn",
                    "text": f"*Actual:*\n{incident.actual_value:.2f}"
                })
            
            blocks.append({
                "type": "section",
                "fields": metric_fields
            })
        
        # Add dashboard link if available
        if incident.dashboard_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View in Dashboard",
                            "emoji": True
                        },
                        "url": incident.dashboard_url,
                        "style": "primary"
                    }
                ]
            })
        
        # Send message
        payload = {
            "username": self.config.slack_username,
            "icon_emoji": self.config.slack_icon_emoji,
            "attachments": [
                {
                    "color": color,
                    "blocks": blocks
                }
            ]
        }
        
        if self.config.slack_channel:
            payload["channel"] = self.config.slack_channel
        
        return self._send_message(payload)
    
    def send_action_alert(self, action: ActionPayload) -> bool:
        """Send a remediation action notification to Slack.
        
        Formats the action data into a Slack message showing what action
        was taken, on which service, and the result.
        
        Args:
            action: Action payload with execution details
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Slack notifications disabled, skipping action alert")
            return False
        
        # Determine emoji and color based on status
        if action.status == "completed":
            emoji = "✅"
            color = "#00FF00"  # Green
        elif action.status == "failed":
            emoji = "❌"
            color = "#FF0000"  # Red
        else:  # started
            emoji = "🔄"
            color = "#0099FF"  # Blue
        
        # Action type emoji
        action_emoji_map = {
            "restart": "🔄",
            "scale": "📈",
            "rollout": "🚀",
        }
        action_emoji = action_emoji_map.get(action.action_type, "⚙️")
        
        # Build message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Action {action.status.upper()}: {action_emoji} {action.action_type.capitalize()}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Service:*\n{action.service_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Action ID:*\n`{action.action_id}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{action.action_type.capitalize()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{action.status.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Target:*\n{action.target_type.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Triggered By:*\n{action.triggered_by.capitalize()}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Reason:*\n{action.reason}"
                }
            }
        ]
        
        # Add result if available
        if action.result:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Result:*\n```{action.result}```"
                }
            })
        
        # Add metadata if available
        if action.metadata:
            metadata_text = "\n".join([f"• *{k}:* {v}" for k, v in action.metadata.items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Details:*\n{metadata_text}"
                }
            })
        
        # Add dashboard link if available
        if action.dashboard_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View in Dashboard",
                            "emoji": True
                        },
                        "url": action.dashboard_url
                    }
                ]
            })
        
        # Send message
        payload = {
            "username": self.config.slack_username,
            "icon_emoji": self.config.slack_icon_emoji,
            "attachments": [
                {
                    "color": color,
                    "blocks": blocks
                }
            ]
        }
        
        if self.config.slack_channel:
            payload["channel"] = self.config.slack_channel
        
        return self._send_message(payload)
    
    def send_health_alert(self, health: HealthAlertPayload) -> bool:
        """Send a service health status alert to Slack.
        
        Args:
            health: Health status payload
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Slack notifications disabled, skipping health alert")
            return False
        
        # Determine emoji and color based on status
        status_config = {
            "healthy": {"emoji": "✅", "color": "#00FF00"},
            "degraded": {"emoji": "⚠️", "color": "#FFA500"},
            "down": {"emoji": "🔴", "color": "#FF0000"},
        }
        config = status_config.get(health.status, {"emoji": "❓", "color": "#808080"})
        
        # Build simple message
        text = (
            f"{config['emoji']} *{health.service_name}* is {health.status.upper()}\n"
            f"{health.message}"
        )
        
        payload = {
            "username": self.config.slack_username,
            "icon_emoji": self.config.slack_icon_emoji,
            "attachments": [
                {
                    "color": config["color"],
                    "text": text,
                    "footer": f"AI Ops Sentry • {health.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        }
        
        if self.config.slack_channel:
            payload["channel"] = self.config.slack_channel
        
        return self._send_message(payload)
    
    def send_custom_message(self, text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Send a custom message to Slack.
        
        Args:
            text: Message text (fallback if blocks not supported)
            blocks: Optional Slack blocks for rich formatting
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Slack notifications disabled, skipping custom message")
            return False
        
        payload = {
            "username": self.config.slack_username,
            "icon_emoji": self.config.slack_icon_emoji,
            "text": text,
        }
        
        if blocks:
            payload["blocks"] = blocks
        
        if self.config.slack_channel:
            payload["channel"] = self.config.slack_channel
        
        return self._send_message(payload)
    
    def _send_message(self, payload: Dict[str, Any]) -> bool:
        """Send message to Slack webhook.
        
        Args:
            payload: Slack message payload
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.error("Slack webhook URL not configured")
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            
            if response.text == "ok":
                logger.info("Slack message sent successfully")
                return True
            else:
                logger.warning(f"Unexpected Slack response: {response.text}")
                return False
                
        except Timeout:
            logger.error("Timeout sending message to Slack")
            return False
        except RequestException as e:
            logger.error(f"Failed to send message to Slack: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message to Slack: {e}", exc_info=True)
            return False
