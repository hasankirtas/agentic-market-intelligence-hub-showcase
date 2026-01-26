"""
Report workflow.

Executes periodic report generation and email delivery:
1. Aggregate recent scan results
2. Deduplicate changes
3. Generate report with LLM (Reporter Agent)
4. Send scheduled email
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import time

from core.logger import setup_logger
from app.database.repositories.config_repository import ConfigRepository
from app.database.repositories.scan_repository import ScanRepository
from app.database.repositories.report_repository import ReportRepository
from app.services.email_service import EmailService
from utils.change_deduplication import deduplicate_changes

logger = setup_logger(__name__)


async def execute_report_workflow(
    user_id: str,
    reporter_agent: Any,
    email_service: EmailService,
    config_repository: ConfigRepository,
    scan_repository: ScanRepository,
    report_repository: ReportRepository
) -> Dict[str, Any]:
    """
    Execute report workflow for periodic summary.
    
    This workflow is executed less frequently (e.g., every 6 hours) to:
    - Aggregate all changes since last report
    - Generate comprehensive summary report
    - Send scheduled email to user
    
    Args:
        user_id: User identifier
        reporter_agent: Reporter agent instance
        email_service: Email service instance
        config_repository: Config repository instance
        scan_repository: Scan repository instance
        report_repository: Report repository instance
    
    Returns:
        Report workflow execution result
    """
    start_time = time.time()
    
    logger.info(f"Starting report workflow for user: {user_id}")
    
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
            logger.info(f"User {user_id} is inactive, skipping report")
            return {
                "success": True,
                "user_id": user_id,
                "skipped": True,
                "reason": "User inactive",
                "execution_time": time.time() - start_time
            }
        
        # Step 2: Determine time range for report
        last_report = await report_repository.get_latest_report(user_id, report_type="scheduled")
        
        if last_report:
            since_time = last_report.generated_at
            logger.info(f"Fetching scans since last report: {since_time}")
        else:
            # No previous report, use default lookback (6 hours)
            since_time = datetime.utcnow() - timedelta(hours=6)
            logger.info(f"No previous report found, using default lookback: {since_time}")
        
        # Step 3: Get all scans since last report
        recent_scans = await scan_repository.get_scans_since(user_id, since=since_time)
        scan_count = len(recent_scans)
        
        logger.info(f"Found {scan_count} scans since {since_time}")
        
        # Step 4: Aggregate all changes from recent scans
        all_changes = []
        for scan in recent_scans:
            if scan.changes:
                all_changes.extend(scan.changes)
        
        logger.info(f"Aggregated {len(all_changes)} total changes")
        
        # Step 5: Deduplicate changes
        unique_changes = deduplicate_changes(all_changes)
        change_count = len(unique_changes)
        
        logger.info(f"After deduplication: {change_count} unique changes")
        
        # Step 6: Generate report with Reporter Agent
        time_range = f"{since_time.strftime('%Y-%m-%d %H:%M')} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        # Generate a report scan_id (not a scan_id, but ReporterAgent requires it)
        # For scheduled reports, we use a synthetic scan_id since this aggregates multiple scans
        report_scan_id = f"report_scan_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("Executing Reporter Agent for report generation")
        report_result = await reporter_agent.execute({
            "query": "Generate periodic competitive intelligence summary report",
            "changes": unique_changes,
            "user_id": user_id,
            "scan_id": report_scan_id,  # Added: ReporterAgent requires scan_id
            "report_type": "scheduled",
            "time_range": time_range,
            "scan_count": scan_count
        })
        
        if not report_result.get("success"):
            logger.error(f"Reporter Agent failed: {report_result.get('error')}")
            return {
                "success": False,
                "user_id": user_id,
                "error": "Report generation failed",
                "details": report_result.get("error"),
                "execution_time": time.time() - start_time
            }
        
        report = report_result.get("report")
        if not report:
            logger.error("Reporter Agent did not return a report")
            return {
                "success": False,
                "user_id": user_id,
                "error": "No report generated",
                "execution_time": time.time() - start_time
            }
        
        # Step 7: Send scheduled email
        logger.info(f"Sending scheduled report email to {config.email}")
        email_sent = await email_service.send_report_email(
            report=report,
            recipient_email=config.email,
            recipient_name=user_id
        )
        
        execution_time = time.time() - start_time
        
        result = {
            "success": True,
            "user_id": user_id,
            "report_id": report.report_id if hasattr(report, 'report_id') else None,
            "time_range": time_range,
            "scan_count": scan_count,
            "change_count": change_count,
            "email_sent": email_sent,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Report workflow completed successfully in {execution_time:.2f}s")
        
        return result
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Report workflow failed for user {user_id}: {e}", exc_info=True)
        
        return {
            "success": False,
            "user_id": user_id,
            "error": str(e),
            "execution_time": execution_time
        }

