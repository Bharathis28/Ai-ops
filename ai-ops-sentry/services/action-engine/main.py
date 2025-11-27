"""Action Engine FastAPI service.

This is the main entry point for the Action Engine service. It provides
REST API endpoints for executing remediation actions on GKE deployments
and Cloud Run services.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.core.config import GCPConfig

# Dynamic import for routes
import importlib.util
routes_path = Path(__file__).parent / "api" / "routes.py"
routes_spec = importlib.util.spec_from_file_location("routes", routes_path)
routes_module = importlib.util.module_from_spec(routes_spec)
routes_spec.loader.exec_module(routes_module)
router = routes_module.router
initialize_clients = routes_module.initialize_clients

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Ops Sentry - Action Engine",
    description="Automated remediation engine for GKE and Cloud Run services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure allowed origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize clients on application startup."""
    logger.info("Starting Action Engine service...")
    
    try:
        # Load configuration
        config = GCPConfig()
        
        # Initialize clients
        initialize_clients(config)
        
        logger.info("Action Engine service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Action Engine service: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down Action Engine service...")


# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "action-engine",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,  # Different port for each service
        reload=True,
        log_level="info",
    )

