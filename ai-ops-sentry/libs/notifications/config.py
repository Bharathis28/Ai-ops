"""Configuration for notifications library.

Reads notification settings from environment variables with optional .env support.
All sensitive values (webhook URLs, API keys) must be provided via environment.
"""

from typing import Optional
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class SlackConfig(BaseSettings):
    """Slack notification configuration.
    
    Reads from environment variables or .env file.
    The webhook URL should be obtained from Slack's Incoming Webhooks app.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    slack_webhook_url: Optional[HttpUrl] = Field(
        default=None,
        description="Slack Incoming Webhook URL",
        validation_alias="SLACK_WEBHOOK_URL",
    )
    
    slack_enabled: bool = Field(
        default=False,
        description="Enable/disable Slack notifications",
        validation_alias="SLACK_ENABLED",
    )
    
    slack_channel: Optional[str] = Field(
        default=None,
        description="Override default channel (optional)",
        validation_alias="SLACK_CHANNEL",
    )
    
    slack_username: str = Field(
        default="AI Ops Sentry",
        description="Bot username for messages",
        validation_alias="SLACK_USERNAME",
    )
    
    slack_icon_emoji: str = Field(
        default=":robot_face:",
        description="Bot icon emoji",
        validation_alias="SLACK_ICON_EMOJI",
    )
    
    def is_configured(self) -> bool:
        """Check if Slack is properly configured."""
        return self.slack_enabled and self.slack_webhook_url is not None


class EmailConfig(BaseSettings):
    """Email notification configuration.
    
    Placeholder for future email notification support.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    email_enabled: bool = Field(
        default=False,
        description="Enable/disable email notifications",
        validation_alias="EMAIL_ENABLED",
    )
    
    # Future: SMTP settings, recipients, etc.
