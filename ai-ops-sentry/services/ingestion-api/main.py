"""Main entry point for the Ingestion API service."""

import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point for the Ingestion API service."""
    logger.info("Ingestion API service starting")
    # Placeholder for FastAPI application initialization
    logger.info("Ingestion API service initialized successfully")


if __name__ == "__main__":
    main()
