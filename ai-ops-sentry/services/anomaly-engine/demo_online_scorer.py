"""Demo script for online anomaly scoring service.

This script demonstrates how the online scorer works by simulating
the full pipeline: metric ingestion -> scoring -> anomaly detection.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timezone
import json

# Setup path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.models.model_store import ModelStore
from libs.models.metrics import MetricPoint

# Dynamic imports
import importlib.util

scoring_path = Path(__file__).parent / "domain" / "scoring.py"
scoring_spec = importlib.util.spec_from_file_location("scoring", scoring_path)
scoring_module = importlib.util.module_from_spec(scoring_spec)
scoring_spec.loader.exec_module(scoring_module)
score_metrics_batch = scoring_module.score_metrics_batch
filter_anomalies = scoring_module.filter_anomalies

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def demo_online_scoring():
    """Demonstrate online anomaly scoring with a trained model."""
    
    logger.info("=" * 80)
    logger.info("Online Anomaly Scoring Demo")
    logger.info("=" * 80)
    
    # Step 1: Load trained model
    logger.info("\n1. Loading trained model for 'frontend-api'...")
    model_store = ModelStore(base_path="./models", backend="local")
    
    if not model_store.model_exists("frontend-api"):
        logger.error("No trained model found for frontend-api")
        logger.info("Please run the offline trainer first:")
        logger.info("  python services/anomaly-engine/main.py frontend-api --days 7")
        return
    
    model = model_store.load_model("frontend-api")
    metadata = model_store.load_metadata("frontend-api")
    
    logger.info(f"✓ Model loaded successfully")
    if metadata:
        logger.info(f"  Trained on: {metadata.get('n_samples')} samples")
        logger.info(f"  Features: {metadata.get('n_features')}")
        logger.info(f"  Training anomaly rate: {metadata.get('training_anomaly_rate', 0)*100:.2f}%")
    
    # Step 2: Simulate incoming metric batch
    logger.info("\n2. Simulating incoming metric batch...")
    logger.info("   (In production, this would come from Pub/Sub)")
    
    # Create a batch of metrics - mix of normal and anomalous
    now = datetime.now(timezone.utc)
    
    metrics_batch = [
        # Normal metrics
        MetricPoint(
            timestamp=now,
            service_name="frontend-api",
            metric_name="cpu_usage",
            value=72.0,
            tags={"host": "server-1", "region": "us-east1"},
        ),
        MetricPoint(
            timestamp=now,
            service_name="frontend-api",
            metric_name="memory_usage",
            value=65.0,
            tags={"host": "server-1", "region": "us-east1"},
        ),
        MetricPoint(
            timestamp=now,
            service_name="frontend-api",
            metric_name="latency_p95",
            value=120.0,
            tags={"host": "server-1", "region": "us-east1"},
        ),
        
        # Anomalous: High CPU
        MetricPoint(
            timestamp=now,
            service_name="frontend-api",
            metric_name="cpu_usage",
            value=98.0,
            tags={"host": "server-2", "region": "us-east1"},
        ),
        
        # Anomalous: Very high latency
        MetricPoint(
            timestamp=now,
            service_name="frontend-api",
            metric_name="latency_p95",
            value=850.0,
            tags={"host": "server-3", "region": "us-west1"},
        ),
        
        # Anomalous: High error rate
        MetricPoint(
            timestamp=now,
            service_name="frontend-api",
            metric_name="error_rate",
            value=12.5,
            tags={"host": "server-4", "region": "us-central1"},
        ),
    ]
    
    logger.info(f"✓ Created batch with {len(metrics_batch)} metrics")
    
    # Step 3: Score the batch
    logger.info("\n3. Scoring metrics for anomalies...")
    
    results = score_metrics_batch(
        metrics=metrics_batch,
        model=model,
        score_threshold=0.0,
    )
    
    logger.info(f"✓ Scored {len(results)} metrics")
    
    # Step 4: Filter and display anomalies
    logger.info("\n4. Filtering anomalies...")
    
    anomalies = filter_anomalies(results)
    
    logger.info(f"✓ Found {len(anomalies)} anomalies")
    
    if anomalies:
        logger.info("\n" + "=" * 80)
        logger.info("DETECTED ANOMALIES")
        logger.info("=" * 80)
        
        for i, anomaly in enumerate(anomalies, 1):
            logger.info(f"\nAnomaly #{i}:")
            logger.info(f"  Service: {anomaly.service_name}")
            logger.info(f"  Metric: {anomaly.metric_name}")
            logger.info(f"  Value: {anomaly.value}")
            logger.info(f"  Severity: {anomaly.severity.upper()}")
            logger.info(f"  Anomaly Score: {anomaly.anomaly_score:.4f}")
            logger.info(f"  Tags: {anomaly.metadata.get('tags', {})}")
            
            # Provide context
            if anomaly.metric_name == "cpu_usage" and anomaly.value > 95:
                logger.info(f"  → CPU usage critically high! May need to scale up.")
            elif anomaly.metric_name == "latency_p95" and anomaly.value > 500:
                logger.info(f"  → Latency spike detected! Check for slow queries.")
            elif anomaly.metric_name == "error_rate" and anomaly.value > 10:
                logger.info(f"  → High error rate! Check application logs.")
    else:
        logger.info("\n✓ All metrics are normal - no anomalies detected")
    
    # Step 5: Show what would happen in production
    logger.info("\n" + "=" * 80)
    logger.info("PRODUCTION WORKFLOW")
    logger.info("=" * 80)
    logger.info("\nIn production, these anomalies would:")
    logger.info("  1. Be written to BigQuery 'anomalies' table")
    logger.info("  2. Be published to 'anomaly_events' Pub/Sub topic")
    logger.info("  3. Trigger downstream actions (alerts, auto-scaling, etc.)")
    logger.info("  4. Be displayed in the monitoring dashboard")
    
    # Step 6: Show sample Pub/Sub message format
    if anomalies:
        logger.info("\n" + "=" * 80)
        logger.info("SAMPLE PUB/SUB MESSAGE")
        logger.info("=" * 80)
        
        sample_anomaly = anomalies[0]
        message = {
            "timestamp": sample_anomaly.timestamp.isoformat(),
            "service_name": sample_anomaly.service_name,
            "metric_name": sample_anomaly.metric_name,
            "value": sample_anomaly.value,
            "severity": sample_anomaly.severity,
            "anomaly_score": sample_anomaly.anomaly_score,
            "tags": sample_anomaly.metadata.get("tags", {}),
        }
        
        logger.info("\nMessage to 'anomaly_events' topic:")
        logger.info(json.dumps(message, indent=2))
    
    logger.info("\n" + "=" * 80)
    logger.info("Demo completed successfully!")
    logger.info("=" * 80)


if __name__ == "__main__":
    demo_online_scoring()
