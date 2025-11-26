"""Main entry point for the Online Scorer service."""

import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point for the Online Scorer service."""
    logger.info("Online Scorer service starting")
    # Placeholder for real-time scoring pipeline
    logger.info("Online Scorer service initialized successfully")


if __name__ == "__main__":
    main()
