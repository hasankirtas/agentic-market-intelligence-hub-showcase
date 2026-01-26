"""
Scan workflow.

Executes scanning and change detection workflow:
1. Scan URLs (Watcher Agent)
2. Analyze changes (Analyst Agent)
3. Check emergency threshold
4. Send emergency email if critical
"""
from typing import Dict, Any, Optional
from datetime import datetime
import time
import uuid

from core.logger import setup_logger
from app.database.repositories.config_repository import ConfigRepository
from app.database.repositories.scan_repository import ScanRepository
from app.services.email_service import EmailService
from models.config import UserConfig
from models.scan_result import ScanResult

logger = setup_logger(__name__)


async def execute_scan_workflow(
    user_id: str,
    watcher_agent: Any,
    analyst_agent: Any,
    config_repository: ConfigRepository,
    scan_repository: ScanRepository,
    email_service: Optional[EmailService] = None
) -> Dict[str, Any]:
    """
    Execute scan workflow for change detection.
    
    This workflow is executed frequently (e.g., every hour) to:
    - Scan competitor URLs
    - Detect changes against baseline
    - Trigger emergency alerts if threshold exceeded
    
    Args:
        user_id: User identifier
        watcher_agent: Watcher agent instance
        analyst_agent: Analyst agent instance
        config_repository: Config repository instance
        scan_repository: Scan repository instance
        email_service: Email service instance (optional, for emergency alerts)
    
    Returns:
        Scan workflow execution result
    """
    start_time = time.time()
    
    logger.info(f"Starting scan workflow for user: {user_id}")
    
    try:
        # Step 1: Get user configuration
        config = await config_repository.get_config(user_id)
        
        if not config:
            logger.warning(f"Configuration not found for user: {user_id}")
            return {
                "success": False,
                "user_id": user_id,
                "error": "Configuration not found",
                "execution_time": time.time() - start_time
            }
        
        if not config.is_active:
            logger.info(f"User {user_id} is inactive, skipping scan")
            return {
                "success": True,
                "user_id": user_id,
                "skipped": True,
                "reason": "User inactive",
                "execution_time": time.time() - start_time
            }
        
        # Generate scan_id for this workflow execution
        scan_id = f"scan_{user_id}_{uuid.uuid4().hex[:8]}"
        
        # Step 2: Execute Watcher Agent (scan URLs)
        logger.info(f"Executing Watcher Agent for {len(config.urls)} URLs")
        scan_result = await watcher_agent.execute({
            "query": f"Scan pricing pages for user {user_id}",
            "urls": config.urls,
            "user_id": user_id,
            "scan_id": scan_id
        })
        
        if not scan_result.get("success"):
            logger.error(f"Watcher Agent failed: {scan_result.get('error')}")
            return {
                "success": False,
                "user_id": user_id,
                "error": "Scan failed",
                "details": scan_result.get("error"),
                "execution_time": time.time() - start_time
            }
        
        # Step 3: Execute Analyst Agent (detect changes)
        logger.info("Executing Analyst Agent for change detection")
        analysis_result = await analyst_agent.execute({
            "query": "Analyze changes and detect critical updates",
            "results": scan_result.get("results", []),  # Fixed: use "results" not "scan_results"
            "user_id": user_id,
            "scan_id": scan_id
        })
        
        if not analysis_result.get("success"):
            logger.error(f"Analyst Agent failed: {analysis_result.get('error')}")
            return {
                "success": False,
                "user_id": user_id,
                "error": "Analysis failed",
                "details": analysis_result.get("error"),
                "execution_time": time.time() - start_time
            }
        
        changes = analysis_result.get("changes", [])
        change_count = len(changes)
        
        logger.info(f"Detected {change_count} changes")
        
        # Step 4: Check emergency threshold
        max_severity = 0.0
        if changes:
            max_severity = max([change.get("severity", 0.0) for change in changes])
        
        critical_threshold = config.thresholds.get("critical_threshold", 0.8)
        is_emergency = max_severity >= critical_threshold
        
        emergency_email_sent = False
        
        # Step 5: Send emergency email if critical and enabled
        if is_emergency and config.emergency_email_enabled and email_service:
            logger.warning(f"Emergency threshold exceeded (severity: {max_severity})")
            
            try:
                # Get critical changes for emergency email
                critical_changes = [c for c in changes if c.get("severity", 0.0) >= critical_threshold]
                
                emergency_email_sent = await email_service.send_emergency_email(
                    user_id=user_id,
                    recipient_email=config.email,
                    changes=critical_changes,
                    max_severity=max_severity
                )
                
                logger.info(f"Emergency email sent: {emergency_email_sent}")
            except Exception as e:
                logger.error(f"Failed to send emergency email: {e}")

        # Step 5.5: ALWAYS send a manual scan report (User Requirement)
        # This ensures the user gets feedback that the scan actually ran
        if email_service:
             try:
                logger.info("Sending manual scan completion report (mandatory)")
                
                # Prepare a simple report structure
                report_data = {
                    "scan_id": scan_id,
                    "urls_scanned": len(config.urls),
                    "changes_detected": change_count,
                    "max_severity": max_severity,
                    "execution_time": f"{time.time() - start_time:.2f}s",
                    "changes": changes,
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                }

                # Use the new specialized method for manual scan reports
                await email_service.send_scan_summary_email(
                    recipient_email=config.email,
                    scan_id=scan_id,
                    urls_scanned=len(config.urls),
                    change_count=change_count,
                    changes=changes,
                    max_severity=max_severity,
                    execution_time=f"{time.time() - start_time:.2f}s"
                )
             except Exception as e:
                 logger.error(f"Failed to send manual scan report: {e}")
        
        # Calculate execution time for metadata
        current_execution_time = time.time() - start_time
        
        # Step 6: Save scan result to Firestore
        try:
            # Use scan_id from workflow (already generated at start)
            # Fallback to scan_result's scan_id if somehow missing
            final_scan_id = scan_result.get("scan_id") or scan_id
            
            # Create ScanResult objects for each URL scanned
            for url_result in scan_result.get("results", []):  # Fixed: use "results" not "scan_results"
                scan_record = ScanResult(
                    scan_id=final_scan_id,
                    user_id=user_id,
                    url=url_result.get("url", ""),
                    timestamp=datetime.utcnow(),
                    data=url_result.get("data", {}),
                    status=url_result.get("status", "success"),
                    error_message=url_result.get("error"),
                    metadata={
                        "execution_time": current_execution_time,
                        "max_severity": max_severity,
                        "is_emergency": is_emergency
                    },
                    changes=changes  # Include changes detected by Analyst Agent
                )
                
                await scan_repository.save_scan(scan_record)
            
            logger.info(f"Scan results saved to Firestore (scan_id: {final_scan_id})")
        except Exception as e:
            logger.error(f"Failed to save scan results: {e}", exc_info=True)
            # Don't fail the workflow if save fails
        
        # Final execution time for return value
        execution_time = time.time() - start_time
        
        result = {
            "success": True,
            "user_id": user_id,
            "change_count": change_count,
            "max_severity": max_severity,
            "is_emergency": is_emergency,
            "emergency_email_sent": emergency_email_sent,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Scan workflow completed successfully in {execution_time:.2f}s")
        
        return result
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Scan workflow failed for user {user_id}: {e}", exc_info=True)
        
        return {
            "success": False,
            "user_id": user_id,
            "error": str(e),
            "execution_time": execution_time
        }

