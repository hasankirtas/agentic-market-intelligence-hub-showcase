"""
FastAPI main application.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.orchestrator import initialize_orchestrator, cleanup_orchestrator, get_orchestrator
from app.api import health, config, trigger, reports, scans
from app.api.exceptions import validation_exception_handler, general_exception_handler
from app.services.scheduler_service import SchedulerService
from app.dependencies import (
    set_scheduler,
    get_email_service,
    get_firestore_client,
    get_config_repository,
    get_scan_repository,
    get_report_repository
)
from core.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI startup and shutdown events.
    
    Startup:
    - Initialize orchestrator and all agents
    - Initialize and start scheduler service
    
    Shutdown:
    - Stop scheduler service
    - Cleanup orchestrator and release resources
    """
    settings = get_settings()
    scheduler = None
    
    # Startup
    logger.info("Starting application...")
    try:
        # Initialize orchestrator
        await initialize_orchestrator()
        logger.info("Orchestrator initialized")
        
        # Initialize scheduler if enabled and user_id is configured
        if settings.scheduler_enabled and settings.default_user_id:
            logger.info("Initializing scheduler service...")
            
            orchestrator = get_orchestrator()
            
            # Get agents from orchestrator
            watcher_agent = orchestrator.agents.get("watcher")
            analyst_agent = orchestrator.agents.get("analyst")
            reporter_agent = orchestrator.agents.get("reporter")
            
            if not all([watcher_agent, analyst_agent, reporter_agent]):
                logger.warning("Not all agents available, skipping scheduler initialization")
            else:
                # Get service instances
                firestore_client = get_firestore_client()
                config_repo = get_config_repository(firestore_client=firestore_client)
                scan_repo = get_scan_repository(firestore_client=firestore_client)
                report_repo = get_report_repository(firestore_client=firestore_client)
                email_service = get_email_service(report_repository=report_repo)
                
                # Get user configuration for scheduling
                user_config = await config_repo.get_config(settings.default_user_id)
                
                if not user_config:
                    logger.warning(f"No configuration found for user: {settings.default_user_id}, skipping scheduler")
                elif not user_config.is_active:
                    logger.info(f"User {settings.default_user_id} is inactive, skipping scheduler")
                else:
                    # Create scheduler instance
                    scheduler = SchedulerService(
                        user_id=settings.default_user_id,
                        watcher_agent=watcher_agent,
                        analyst_agent=analyst_agent,
                        reporter_agent=reporter_agent,
                        email_service=email_service,
                        config_repository=config_repo,
                        scan_repository=scan_repo,
                        report_repository=report_repo,
                        timezone=settings.scheduler_timezone
                    )
                    
                    # Start scheduler with user config
                    await scheduler.start(user_config)
                    
                    # Store globally
                    set_scheduler(scheduler)
                    
                    logger.info(
                        f"Scheduler started for user: {settings.default_user_id} "
                        f"(scan: {user_config.scan_schedule}, report: {user_config.report_schedule})"
                    )
        else:
            logger.info("Scheduler disabled or no default user configured")
        
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        # Stop scheduler if running
        if scheduler and scheduler.is_running:
            logger.info("Stopping scheduler...")
            scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")
        
        # Cleanup orchestrator
        await cleanup_orchestrator()
        logger.info("Application shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health.router)
app.include_router(config.router)
app.include_router(trigger.router)
app.include_router(reports.router)
app.include_router(scans.router)


@app.get("/")
async def root():
    """
    Root endpoint.
    
    Returns:
        API information
    """
    return {
        "service": "agentic-market-intelligence-hub",
        "version": settings.api_version,
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
