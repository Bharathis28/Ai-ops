"""BigQuery client for dashboard data retrieval.

This module provides mock implementations of data retrieval functions.
In production, these will be replaced with actual BigQuery queries.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import random


def get_overview_stats() -> Dict[str, Any]:
    """Get overview statistics for the dashboard.
    
    Returns:
        Dictionary containing overview KPIs:
        - total_anomalies_24h: Total anomalies in last 24 hours
        - critical_anomalies: Count of critical severity anomalies
        - services_monitored: Number of services being monitored
        - auto_remediations: Number of auto-remediation actions executed
        - anomalies_trend: Percentage change from previous period
        - remediations_trend: Percentage change in remediations
    """
    return {
        "total_anomalies_24h": 47,
        "critical_anomalies": 3,
        "services_monitored": 12,
        "auto_remediations": 8,
        "anomalies_trend": -12.5,  # Percentage change
        "remediations_trend": 25.0,
        "services_healthy": 9,
        "services_degraded": 2,
        "services_down": 1,
    }


def get_anomalies_timeseries(
    hours: int = 24,
    interval_minutes: int = 60,
) -> List[Dict[str, Any]]:
    """Get time-series data of anomaly counts.
    
    Args:
        hours: Number of hours to look back
        interval_minutes: Interval between data points in minutes
        
    Returns:
        List of dictionaries with timestamp and anomaly counts by severity
    """
    now = datetime.now()
    data = []
    
    points = (hours * 60) // interval_minutes
    for i in range(points):
        timestamp = now - timedelta(minutes=interval_minutes * (points - i))
        data.append({
            "timestamp": timestamp,
            "critical": random.randint(0, 3),
            "high": random.randint(1, 8),
            "medium": random.randint(3, 15),
            "low": random.randint(5, 20),
            "total": random.randint(10, 40),
        })
    
    return data


def get_latest_incidents(limit: int = 5) -> List[Dict[str, Any]]:
    """Get latest incidents for overview page.
    
    Args:
        limit: Maximum number of incidents to return
        
    Returns:
        List of incident dictionaries
    """
    severities = ["critical", "high", "medium", "low"]
    services = ["api-gateway", "payment-service", "user-service", "notification-service"]
    
    incidents = []
    for i in range(limit):
        severity = random.choice(severities if i > 0 else ["critical", "high"])
        incidents.append({
            "id": f"INC-{1000 + i}",
            "service": random.choice(services),
            "severity": severity,
            "detected_at": datetime.now() - timedelta(minutes=random.randint(5, 120)),
            "summary": f"High latency detected in {random.choice(services)}",
            "status": random.choice(["open", "investigating", "resolved"]),
        })
    
    return incidents


def get_anomalies(
    time_range: str = "24h",
    severity: Optional[str] = None,
    service: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Get filtered list of anomalies.
    
    Args:
        time_range: Time range filter (24h, 7d, 30d)
        severity: Severity filter (critical, high, medium, low)
        service: Service name filter
        limit: Maximum results to return
        
    Returns:
        List of anomaly records
    """
    services = [
        "api-gateway", "payment-service", "user-service",
        "notification-service", "auth-service", "analytics-service"
    ]
    severities = ["critical", "high", "medium", "low"]
    
    anomalies = []
    for i in range(limit):
        sev = severity if severity else random.choice(severities)
        svc = service if service else random.choice(services)
        
        anomalies.append({
            "id": f"ANO-{2000 + i}",
            "service": svc,
            "detected_at": datetime.now() - timedelta(hours=random.randint(0, 24)),
            "severity": sev,
            "anomaly_score": round(random.uniform(0.7, 0.99), 2),
            "metric": random.choice(["cpu_usage", "memory_usage", "latency_p95", "error_rate"]),
            "actual_value": round(random.uniform(50, 95), 1),
            "expected_value": round(random.uniform(20, 50), 1),
            "ai_summary": f"Detected unusual {random.choice(['CPU', 'memory', 'latency'])} pattern in {svc}",
            "root_cause": random.choice([
                "Database connection pool exhausted",
                "Memory leak in request handler",
                "Downstream service degradation",
                "Traffic spike from new campaign",
            ]),
            "status": random.choice(["open", "investigating", "resolved", "false_positive"]),
        })
    
    return anomalies


def get_services_health() -> List[Dict[str, Any]]:
    """Get health status of all monitored services.
    
    Returns:
        List of service health records
    """
    services = [
        {"name": "api-gateway", "status": "healthy"},
        {"name": "payment-service", "status": "healthy"},
        {"name": "user-service", "status": "degraded"},
        {"name": "notification-service", "status": "healthy"},
        {"name": "auth-service", "status": "healthy"},
        {"name": "analytics-service", "status": "down"},
        {"name": "search-service", "status": "healthy"},
        {"name": "recommendation-service", "status": "healthy"},
        {"name": "inventory-service", "status": "degraded"},
        {"name": "order-service", "status": "healthy"},
        {"name": "shipping-service", "status": "healthy"},
        {"name": "metrics-collector", "status": "healthy"},
    ]
    
    for svc in services:
        svc.update({
            "latency_p95": round(random.uniform(50, 500), 1),
            "error_rate": round(random.uniform(0, 5), 2),
            "anomaly_score": round(random.uniform(0, 0.95), 2),
            "requests_per_min": random.randint(100, 10000),
            "cpu_usage": round(random.uniform(20, 85), 1),
            "memory_usage": round(random.uniform(30, 75), 1),
        })
        
        # Adjust metrics based on status
        if svc["status"] == "down":
            svc["error_rate"] = round(random.uniform(90, 100), 2)
            svc["anomaly_score"] = round(random.uniform(0.9, 0.99), 2)
        elif svc["status"] == "degraded":
            svc["latency_p95"] = round(random.uniform(400, 800), 1)
            svc["anomaly_score"] = round(random.uniform(0.7, 0.85), 2)
    
    return services


def get_actions_history(
    limit: int = 50,
    action_type: Optional[str] = None,
    service: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get history of auto-remediation actions.
    
    Args:
        limit: Maximum results to return
        action_type: Filter by action type (restart, scale, rollout_restart)
        service: Filter by service name
        
    Returns:
        List of action records
    """
    services = [
        "api-gateway", "payment-service", "user-service",
        "notification-service", "auth-service"
    ]
    action_types = ["restart", "scale", "rollout_restart"]
    
    actions = []
    for i in range(limit):
        act_type = action_type if action_type else random.choice(action_types)
        svc = service if service else random.choice(services)
        
        result = random.choice(["success", "success", "success", "failed"])  # 75% success rate
        
        actions.append({
            "id": f"ACT-{3000 + i}",
            "timestamp": datetime.now() - timedelta(hours=random.randint(0, 48)),
            "service": svc,
            "action_type": act_type,
            "target_type": random.choice(["gke", "cloud_run"]),
            "triggered_by": random.choice(["auto", "auto", "auto", "manual"]),  # 75% auto
            "result": result,
            "duration_seconds": random.randint(5, 120),
            "reason": random.choice([
                "High CPU usage detected (95%)",
                "Memory leak suspected",
                "Latency threshold exceeded",
                "Error rate spike",
                "Manual intervention",
            ]),
            "details": {
                "replicas_before": random.randint(2, 5) if act_type == "scale" else None,
                "replicas_after": random.randint(6, 10) if act_type == "scale" else None,
            },
        })
    
    return actions


def get_service_metrics_timeseries(
    service_name: str,
    metric: str,
    hours: int = 24,
) -> List[Dict[str, Any]]:
    """Get time-series metrics for a specific service.
    
    Args:
        service_name: Name of the service
        metric: Metric name (cpu_usage, memory_usage, latency_p95, error_rate)
        hours: Hours of history to retrieve
        
    Returns:
        List of metric data points
    """
    now = datetime.now()
    data = []
    
    base_value = {
        "cpu_usage": 45,
        "memory_usage": 60,
        "latency_p95": 150,
        "error_rate": 1.5,
    }.get(metric, 50)
    
    for i in range(hours * 4):  # 15-minute intervals
        timestamp = now - timedelta(minutes=15 * (hours * 4 - i))
        value = base_value + random.uniform(-20, 20)
        
        data.append({
            "timestamp": timestamp,
            "value": max(0, value),
            "anomaly": random.random() > 0.9,  # 10% anomaly rate
        })
    
    return data
