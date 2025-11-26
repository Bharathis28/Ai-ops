"""Main entry point for the Ingestion API service."""

import logging
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.core.config import load_service_config

# Import using sys.path manipulation to handle hyphenated directory names
import importlib.util
import sys
routes_path = Path(__file__).parent / "api" / "routes.py"
spec = importlib.util.spec_from_file_location("routes", routes_path)
routes_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routes_module)
api_router = routes_module.router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application."""
    app = FastAPI(
        title="AI Ops Sentry - Ingestion API",
        version="0.1.0",
        description="Receives and processes metrics and logs.",
    )
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["Monitoring"])
    def health_check():
        """Health check endpoint."""
        return {"status": "ok"}

    return app


app = create_app()


def main() -> None:
    """Entry point to run the Ingestion API service."""
    try:
        config = load_service_config()
        logger.info(f"Starting Ingestion API on port {config.port}")
        uvicorn.run(
            "services.ingestion-api.main:app",
            host="0.0.0.0",
            port=config.port,
            reload=config.environment == "development",
            log_level=config.log_level.lower(),
        )
    except Exception as e:
        logger.exception(f"Failed to start Ingestion API: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
