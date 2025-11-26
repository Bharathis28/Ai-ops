"""Entry point for online anomaly scoring service.

This service subscribes to metric batches from Pub/Sub, scores them for anomalies
using trained models, and publishes results.
"""

import logging
import sys
import argparse
from pathlib import Path

# Setup path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.core.config import GCPConfig
from libs.models.model_store import ModelStore

# Dynamic imports for hyphenated directories
import importlib.util

# Import AnomalyWriter
writer_path = Path(__file__).parent / "infra" / "anomaly_writer.py"
writer_spec = importlib.util.spec_from_file_location("anomaly_writer", writer_path)
writer_module = importlib.util.module_from_spec(writer_spec)
writer_spec.loader.exec_module(writer_module)
BigQueryAnomalyWriter = writer_module.BigQueryAnomalyWriter

# Import AnomalyEventsPublisher
publisher_path = Path(__file__).parent / "infra" / "anomaly_events_publisher.py"
publisher_spec = importlib.util.spec_from_file_location("publisher", publisher_path)
publisher_module = importlib.util.module_from_spec(publisher_spec)
publisher_spec.loader.exec_module(publisher_module)
AnomalyEventsPublisher = publisher_module.AnomalyEventsPublisher

# Import MetricsBatchSubscriber
subscriber_path = Path(__file__).parent / "infra" / "pubsub_subscriber.py"
subscriber_spec = importlib.util.spec_from_file_location("subscriber", subscriber_path)
subscriber_module = importlib.util.module_from_spec(subscriber_spec)
subscriber_spec.loader.exec_module(subscriber_module)
MetricsBatchSubscriber = subscriber_module.MetricsBatchSubscriber

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Online anomaly scoring service for AI Ops Sentry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start the online scorer with default settings
  python online_scorer_main.py

  # Start with custom model directory and score threshold
  python online_scorer_main.py --model-dir ./models --threshold -0.1

  # Enable verbose logging
  python online_scorer_main.py --verbose

  # Custom configuration
  python online_scorer_main.py --model-dir gs://my-bucket/models --threshold 0.05
        """,
    )

    parser.add_argument(
        "--model-dir",
        type=str,
        default="./models",
        help="Directory containing trained models (default: ./models)",
    )

    parser.add_argument(
        "--backend",
        type=str,
        default="local",
        choices=["local", "gcs"],
        help="Model storage backend (default: local)",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Anomaly score threshold - scores below this are flagged (default: 0.0)",
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum concurrent message processing workers (default: 4)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def main():
    """Main entry point for online anomaly scorer."""
    args = parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    logger.info("=" * 80)
    logger.info("AI Ops Sentry - Online Anomaly Scorer")
    logger.info("=" * 80)

    # Initialize configuration
    try:
        config = GCPConfig()
        logger.info(f"Loaded configuration for project: {config.gcp_project_id}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}", exc_info=True)
        sys.exit(1)

    # Initialize model store
    try:
        model_store = ModelStore(
            base_path=args.model_dir,
            backend=args.backend,
        )
        logger.info(f"Initialized ModelStore: backend={args.backend}, path={args.model_dir}")
    except Exception as e:
        logger.error(f"Failed to initialize ModelStore: {e}", exc_info=True)
        sys.exit(1)

    # Initialize anomaly writer
    try:
        anomaly_writer = BigQueryAnomalyWriter(config)
        logger.info("Initialized BigQueryAnomalyWriter (stub mode)")
    except Exception as e:
        logger.error(f"Failed to initialize AnomalyWriter: {e}", exc_info=True)
        sys.exit(1)

    # Initialize anomaly events publisher
    try:
        anomaly_publisher = AnomalyEventsPublisher(config)
        logger.info("Initialized AnomalyEventsPublisher (stub mode)")
    except Exception as e:
        logger.error(f"Failed to initialize AnomalyEventsPublisher: {e}", exc_info=True)
        sys.exit(1)

    # Initialize subscriber
    try:
        subscriber = MetricsBatchSubscriber(
            config=config,
            model_store=model_store,
            anomaly_writer=anomaly_writer,
            anomaly_publisher=anomaly_publisher,
            score_threshold=args.threshold,
            max_workers=args.max_workers,
        )
        logger.info("Initialized MetricsBatchSubscriber")
    except Exception as e:
        logger.error(f"Failed to initialize subscriber: {e}", exc_info=True)
        sys.exit(1)

    # Display configuration summary
    logger.info("")
    logger.info("Configuration Summary:")
    logger.info(f"  Project ID: {config.gcp_project_id}")
    logger.info(f"  Subscription: {config.pubsub_subscription_metric_batches}")
    logger.info(f"  Model Store: {args.backend}://{args.model_dir}")
    logger.info(f"  Score Threshold: {args.threshold}")
    logger.info(f"  Max Workers: {args.max_workers}")
    logger.info(f"  Anomaly Table: {config.bigquery_table_anomalies}")
    logger.info(f"  Events Topic: {config.pubsub_topic_anomaly_events}")
    logger.info("")

    # Start the subscriber
    logger.info("Starting online anomaly scorer...")
    logger.info("Press Ctrl+C to stop")
    logger.info("")

    try:
        subscriber.start()  # This blocks indefinitely
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Subscriber failed: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Online anomaly scorer stopped")


if __name__ == "__main__":
    main()
