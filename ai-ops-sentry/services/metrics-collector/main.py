"""Main entry point for the Metrics Collector service."""

import logging
import sys
from pathlib import Path
import time

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.core.config import load_service_config
from services.metrics-collector.domain.metrics import generate_fake_metrics
from services.metrics-collector.infra.client import IngestionAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point for the Metrics Collector service.

    This function loads configuration, generates fake metrics, and sends them
    to the ingestion API in a loop.
    """
    logger.info("Metrics Collector service starting...")

    try:
        service_config = load_service_config()
        logger.info(f"Configuration loaded for environment: {service_config.environment}")
    except Exception as e:
        logger.exception(f"Failed to load configuration: {e}")
        sys.exit(1)

    api_client = IngestionAPIClient(base_url=service_config.ingestion_api_url)

    logger.info("Metrics Collector service initialized successfully. Starting collection loop.")

    # In a real scenario, this would be a single run triggered by a cron job.
    # For demonstration, we run it in a loop.
    while True:
        try:
            metrics_to_send = generate_fake_metrics()
            logger.info(f"Generated {len(metrics_to_send)} fake metrics.")

            api_client.send_metrics(metrics_to_send)

        except Exception as e:
            logger.exception(f"An error occurred during metric collection: {e}")

        logger.info("Waiting for 60 seconds before next collection cycle...")
        time.sleep(60)


if __name__ == "__main__":
    main()
