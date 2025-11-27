# Slack Notifications Library

Reusable notification library for sending structured alerts to Slack from any AI Ops Sentry service.

## Features

- ✅ **Structured Payloads**: Type-safe Pydantic models for incidents, actions, and health alerts
- ✅ **Rich Formatting**: Automatic Slack blocks formatting with colors, emojis, and buttons
- ✅ **Configurable**: Environment-based configuration with .env support
- ✅ **Reusable**: Designed to be used by any service (anomaly-engine, action-engine, etc.)
- ✅ **Tested**: Comprehensive unit tests with mocked HTTP layer
- ✅ **Resilient**: Graceful error handling and timeout protection

## Installation

This library is part of the AI Ops Sentry monorepo. No separate installation needed.

## Configuration

### Environment Variables

Set these in your service's `.env` file:

```bash
# Enable Slack notifications
SLACK_ENABLED=true

# Slack Incoming Webhook URL (required)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional: Override channel (otherwise uses webhook default)
SLACK_CHANNEL=#ai-ops-alerts

# Optional: Customize bot appearance
SLACK_USERNAME=AI Ops Sentry
SLACK_ICON_EMOJI=:robot_face:
```

### Get Slack Webhook URL

1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Enable "Incoming Webhooks"
4. Add webhook to your workspace
5. Copy the webhook URL

## Usage

### Basic Example

```python
from libs.notifications.slack_client import SlackNotifier
from libs.notifications.models import IncidentPayload

# Initialize notifier (loads config from environment)
notifier = SlackNotifier()

# Send incident alert
incident = IncidentPayload(
    incident_id="inc-123",
    service_name="payment-api",
    severity="critical",
    title="High CPU Usage Detected",
    description="CPU usage has exceeded 90% threshold",
    metric_name="cpu_usage",
    anomaly_score=0.95,
    expected_value=50.0,
    actual_value=92.5,
)

notifier.send_incident_alert(incident)
```

### Action Notification

```python
from libs.notifications.models import ActionPayload

action = ActionPayload(
    action_id="act-456",
    service_name="user-auth",
    action_type="restart",
    status="completed",
    target_type="gke",
    reason="Automated recovery from high error rate",
    result="Successfully restarted 3 pods",
    metadata={"cluster": "prod-cluster", "namespace": "default"},
)

notifier.send_action_alert(action)
```

### Health Alert

```python
from libs.notifications.models import HealthAlertPayload

health = HealthAlertPayload(
    service_name="inventory-svc",
    status="degraded",
    message="Response time increased by 50%",
)

notifier.send_health_alert(health)
```

### Custom Message

```python
notifier.send_custom_message(
    text="Custom alert message",
    blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Custom Alert*\nSomething happened!"
            }
        }
    ]
)
```

## Integration Examples

### Anomaly Engine Integration

```python
# In anomaly-engine/domain/anomaly_detector.py

from libs.notifications.slack_client import SlackNotifier
from libs.notifications.models import IncidentPayload

class AnomalyDetector:
    def __init__(self):
        self.slack_notifier = SlackNotifier()
    
    async def detect_anomalies(self, metrics):
        for anomaly in detected_anomalies:
            # Send Slack alert
            incident = IncidentPayload(
                incident_id=anomaly.id,
                service_name=anomaly.service,
                severity=self._get_severity(anomaly.score),
                title=f"Anomaly detected in {anomaly.metric_name}",
                description=f"Anomaly score: {anomaly.score:.2f}",
                metric_name=anomaly.metric_name,
                anomaly_score=anomaly.score,
                expected_value=anomaly.expected,
                actual_value=anomaly.actual,
            )
            self.slack_notifier.send_incident_alert(incident)
```

### Action Engine Integration

```python
# In action-engine/api/routes.py

from libs.notifications.slack_client import SlackNotifier
from libs.notifications.models import ActionPayload

slack_notifier = SlackNotifier()

@router.post("/api/v1/restart_deployment")
async def restart_deployment(request: RestartDeploymentRequest):
    # Execute restart
    result = await k8s_client.restart_deployment(...)
    
    # Send notification
    action = ActionPayload(
        action_id=action_id,
        service_name=request.service_name,
        action_type="restart",
        status="completed" if result.success else "failed",
        target_type=request.target_type,
        reason=request.reason,
        result=result.message,
    )
    slack_notifier.send_action_alert(action)
    
    return ActionResponse(...)
```

## Data Models

### IncidentPayload

Used for anomaly/incident alerts:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `incident_id` | str | Yes | Unique incident identifier |
| `service_name` | str | Yes | Affected service name |
| `severity` | Literal["critical", "warning", "info"] | Yes | Severity level |
| `title` | str | Yes | Brief incident title |
| `description` | str | Yes | Detailed description |
| `metric_name` | str | No | Metric that triggered incident |
| `anomaly_score` | float | No | Anomaly detection score (0-1) |
| `expected_value` | float | No | Expected metric value |
| `actual_value` | float | No | Actual observed value |
| `timestamp` | datetime | No | Incident time (defaults to now) |
| `metadata` | dict | No | Additional context |
| `dashboard_url` | str | No | Link to dashboard |

### ActionPayload

Used for remediation action notifications:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action_id` | str | Yes | Unique action identifier |
| `service_name` | str | Yes | Service being acted upon |
| `action_type` | Literal["restart", "scale", "rollout"] | Yes | Type of action |
| `status` | Literal["started", "completed", "failed"] | Yes | Current status |
| `target_type` | Literal["gke", "cloud_run", "unknown"] | Yes | Target platform |
| `reason` | str | Yes | Reason for action |
| `triggered_by` | Literal["manual", "auto"] | No | How triggered (default: "auto") |
| `result` | str | No | Execution result/error |
| `timestamp` | datetime | No | Execution time (defaults to now) |
| `metadata` | dict | No | Additional context |
| `dashboard_url` | str | No | Link to dashboard |

### HealthAlertPayload

Used for service health status alerts:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `service_name` | str | Yes | Service name |
| `status` | Literal["healthy", "degraded", "down"] | Yes | Health status |
| `message` | str | Yes | Status message |
| `timestamp` | datetime | No | Check time (defaults to now) |
| `metadata` | dict | No | Additional metrics |

## Message Formatting

The library automatically formats messages with:

- **Severity Colors**: Critical (red), Warning (orange), Info (blue)
- **Status Colors**: Completed (green), Failed (red), Started (blue)
- **Emojis**: 🚨 Critical, ⚠️ Warning, ✅ Completed, ❌ Failed, etc.
- **Slack Blocks**: Rich formatting with sections, fields, and buttons
- **Dashboard Links**: Clickable buttons to view in dashboard
- **Metadata**: Key-value pairs displayed in structured format

## Testing

Run unit tests:

```bash
pytest libs/notifications/test_slack_client.py -v
```

All tests use mocked HTTP requests - no real Slack messages are sent during testing.

## Error Handling

The library handles errors gracefully:

- **Disabled Notifications**: Returns `False` without errors
- **Timeouts**: 10-second timeout with logged error
- **HTTP Errors**: Caught and logged, returns `False`
- **Invalid Config**: Logged warning, notifications disabled

All methods return `bool`:
- `True` if message sent successfully
- `False` if sending failed or notifications disabled

## Best Practices

1. **Check Configuration**: Verify `SLACK_ENABLED=true` and webhook URL set
2. **Use Structured Models**: Always use `IncidentPayload`, `ActionPayload`, etc.
3. **Add Dashboard Links**: Include `dashboard_url` for better UX
4. **Include Metadata**: Add context in `metadata` field
5. **Log Errors**: Library logs failures, but check return values
6. **Rate Limiting**: Be mindful of Slack API rate limits for high-volume alerts

## Troubleshooting

### Messages Not Sending

1. Check `SLACK_ENABLED=true` in `.env`
2. Verify `SLACK_WEBHOOK_URL` is set correctly
3. Test webhook URL with curl:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test message"}' \
     YOUR_WEBHOOK_URL
   ```
4. Check service logs for error messages

### Wrong Channel

Set `SLACK_CHANNEL` in `.env` or configure in webhook settings

### Missing Emojis

Ensure `SLACK_ICON_EMOJI` is valid (e.g., `:robot_face:`)

## Future Enhancements

- [ ] Email notification support
- [ ] PagerDuty integration
- [ ] Microsoft Teams support
- [ ] Notification batching/throttling
- [ ] Retry logic with exponential backoff
- [ ] Notification templates
- [ ] Multi-channel routing based on severity

## License

Part of AI Ops Sentry project.
