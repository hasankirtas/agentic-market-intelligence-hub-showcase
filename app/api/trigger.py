"""
Manual scan trigger endpoint.
Triggers the full workflow: Watcher -> Analyst -> Reporter
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Optional
import uuid
from datetime import datetime
from app.dependencies import (
    get_orchestrator_dependency,
    get_config_repository,
    get_scan_repository,
    get_report_repository,
    get_email_service,
)
from core.orchestration.orchestrator import Orchestrator as CoreOrchestrator
from app.database.repositories.config_repository import ConfigRepository
from app.database.repositories.scan_repository import ScanRepository
from app.database.repositories.report_repository import ReportRepository
from app.services.email_service import EmailService
from app.api.schemas import TriggerScanRequest, TriggerScanResponse, ErrorResponse
from models.scan_result import ScanResult
from core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/trigger", tags=["trigger"])


async def execute_scan_workflow(
    user_id: str,
    url: Optional[str],
    orchestrator: CoreOrchestrator,
    config_repository: ConfigRepository,
    scan_repository: ScanRepository,
    report_repository: ReportRepository,
    email_service: EmailService
):
    """
    Execute the full scan workflow in background.
    
    Workflow: Watcher -> Analyst -> Reporter
    
    Args:
        user_id: User identifier
        url: Optional specific URL to scan
        orchestrator: Orchestrator instance
        config_repository: ConfigRepository instance
        scan_repository: ScanRepository instance
    """
    try:
        logger.info(f"Starting scan workflow for user: {user_id}, URL: {url or 'all'}")
        
        # Get user config to determine URLs to scan
        config = await config_repository.get_config(user_id)
        
        if not config:
            logger.error(f"Config not found for user: {user_id}")
            return
        
        if not config.is_active:
            logger.warning(f"Config is inactive for user: {user_id}")
            return
        
        # Determine URLs to scan
        urls_to_scan = [url] if url else config.urls
        
        if not urls_to_scan:
            logger.warning(f"No URLs configured for user: {user_id}")
            return
        
        # Generate scan ID for this workflow execution
        scan_id = f"scan_{uuid.uuid4().hex}"
        
        try:
            # Prepare initial state for Watcher Agent
            # WatcherAgent expects: urls (array), scan_id, user_id
            # Note: urls and scan_id must be in metadata because workflow_manager
            # only passes query, user_id, and metadata to agents
            initial_state = {
                "user_id": user_id,
                "query": f"Scan pricing pages for user {user_id}",
                "metadata": {
                    "trigger_type": "manual",
                    "timestamp": datetime.utcnow().isoformat(),
                    "urls": urls_to_scan,  # Array of URLs - must be in metadata
                    "scan_id": scan_id  # Must be in metadata to reach agents
                }
            }
            
            # Execute sequential workflow: watcher -> analyst -> reporter
            agent_sequence = ["watcher", "analyst", "reporter"]
            
            logger.info(f"Executing workflow for {len(urls_to_scan)} URL(s): {urls_to_scan}")
            result = await orchestrator.execute_sequential(
                initial_state=initial_state,
                agents=agent_sequence,
                workflow_id=f"manual_scan_{user_id}_{uuid.uuid4().hex[:8]}"
            )
            
            logger.info(f"Workflow completed for user: {user_id}, scan_id: {scan_id}")
            logger.debug(f"Workflow result: {result}")

            # Persist scan results to Firestore (align with scheduled workflow behavior)
            try:
                agent_results = result.get("agent_results", {}) if isinstance(result, dict) else {}
                watcher_out = agent_results.get("watcher", {}) if agent_results else {}
                analyst_out = agent_results.get("analyst", {}) if agent_results else {}
                changes = analyst_out.get("changes", []) if isinstance(analyst_out, dict) else []
                max_severity = 0.0
                if changes:
                    max_severity = max([c.get("severity", 0.0) for c in changes if isinstance(c, dict)])

                for url_result in watcher_out.get("results", []):
                    scan_record = ScanResult(
                        scan_id=scan_id,
                        user_id=user_id,
                        url=url_result.get("url", ""),
                        timestamp=datetime.utcnow(),
                        data=url_result.get("data", {}),
                        status=url_result.get("status", "success"),
                        error_message=url_result.get("error"),
                        metadata={
                            "trigger_type": "manual",
                            "max_severity": max_severity,
                            "is_emergency": False,
                        },
                        changes=changes
                    )
                    await scan_repository.save_scan(scan_record)
                logger.info(f"Saved {len(watcher_out.get('results', []))} scan records for user: {user_id}, scan_id: {scan_id}")
            except Exception as save_err:
                logger.error(f"Failed to persist scans for user {user_id}: {save_err}", exc_info=True)

            # After manual scan, send the generated report via email (if available)
            try:
                last_report = await report_repository.get_latest_report(user_id)
                if last_report:
                    sent = await email_service.send_report_email(
                        report=last_report,
                        user_email=config.email
                    )
                    logger.info(f"Manual scan email sent: {sent} (user: {user_id}, report_id: {getattr(last_report, 'report_id', None)})")
                else:
                    logger.warning(f"No report found to email after manual scan for user: {user_id}")
            except Exception as email_err:
                logger.error(f"Failed to send manual scan email for user {user_id}: {email_err}", exc_info=True)
            
        except Exception as e:
            logger.error(f"Error executing workflow for user {user_id}: {e}", exc_info=True)
        
        logger.info(f"Scan workflow completed for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error in scan workflow execution: {e}")


@router.post("/", response_model=TriggerScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_scan(
    request: TriggerScanRequest,
    background_tasks: BackgroundTasks,
    orchestrator: CoreOrchestrator = Depends(get_orchestrator_dependency),
    config_repository: ConfigRepository = Depends(get_config_repository),
    scan_repository: ScanRepository = Depends(get_scan_repository),
    report_repository: ReportRepository = Depends(get_report_repository),
    email_service: EmailService = Depends(get_email_service),
) -> TriggerScanResponse:
    """
    Trigger a manual scan for a user.
    
    This endpoint initiates the full workflow:
    1. Watcher Agent: Scrapes the pricing page(s)
    2. Analyst Agent: Detects changes and generates ChangeRecords
    3. Reporter Agent: Generates LLM-based report
    
    The scan runs in the background. Use the reports endpoint to check results.
    
    Args:
        request: Trigger scan request
        background_tasks: FastAPI background tasks
        orchestrator: Orchestrator dependency
        config_repository: ConfigRepository dependency
    
    Returns:
        Trigger response with scan ID
    
    Raises:
        HTTPException: If user config not found or inactive
    """
    try:
        # Validate user config exists
        config = await config_repository.get_config(request.user_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration not found for user: {request.user_id}"
            )
        
        if not config.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Configuration is inactive for user: {request.user_id}"
            )
        
        # Validate URL if provided
        if request.url and request.url not in config.urls:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"URL not in user's configuration: {request.url}"
            )
        
        # Generate scan ID
        scan_id = f"scan_{uuid.uuid4().hex}"
        
        # Add background task to execute workflow
        background_tasks.add_task(
            execute_scan_workflow,
            request.user_id,
            request.url,
            orchestrator,
            config_repository,
            scan_repository,
            report_repository,
            email_service
        )
        
        logger.info(f"Triggered scan {scan_id} for user: {request.user_id}, URL: {request.url or 'all'}")
        
        return TriggerScanResponse(
            scan_id=scan_id,
            user_id=request.user_id,
            url=request.url,
            status="initiated",
            message=f"Scan initiated for user {request.user_id}. Processing in background.",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger scan: {str(e)}"
        )
