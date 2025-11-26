# API Specifications

## Ingestion API

### POST /api/v1/metrics
Ingest metrics data.

**Request Body:**
```json
{
  "timestamp": "2025-11-26T00:00:00Z",
  "metric_name": "cpu_usage",
  "value": 75.5,
  "tags": {
    "host": "server-01",
    "region": "us-east-1"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Metric ingested successfully"
}
```

### GET /api/v1/anomalies
Retrieve detected anomalies.

**Query Parameters:**
- `start_time`: ISO 8601 timestamp
- `end_time`: ISO 8601 timestamp
- `severity`: optional filter (low, medium, high, critical)

**Response:**
```json
{
  "anomalies": [
    {
      "id": "anomaly-123",
      "timestamp": "2025-11-26T00:00:00Z",
      "metric": "cpu_usage",
      "severity": "high",
      "score": 0.95
    }
  ]
}
```

## Dashboard API

### GET /api/v1/dashboard/metrics
Retrieve metrics for dashboard visualization.
