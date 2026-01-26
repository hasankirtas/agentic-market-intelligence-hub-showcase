"""
Emergency report workflow.

Handles critical change detection and emergency notification.
This workflow is triggered when changes exceed critical thresholds.
"""
from typing import Dict, Any, List
from datetime import datetime

from core.logger import setup_logger

logger = setup_logger(__name__)


async def execute_emergency_workflow(
    user_id: str,
    report: Any,
    changes: List[Dict[str, Any]],
    max_severity: float
) -> Dict[str, Any]:
    """
    Execute emergency workflow for critical changes.
    
    This workflow is triggered when change severity exceeds the
    critical threshold. It logs emergency conditions and provides
    metadata for emergency handling.
    
    Note: Email notification is already handled by periodic_workflow,
    so this function focuses on logging and metadata collection.
    
    Args:
        user_id: User identifier
        report: Generated report object
        changes: List of change records
        max_severity: Maximum severity score
    
    Returns:
        Emergency workflow execution result
    """
    logger.warning(
        f"EMERGENCY WORKFLOW TRIGGERED for user {user_id}: "
        f"max_severity={max_severity:.2f}"
    )
    
    try:
        # Filter critical changes
        critical_changes = [
            change for change in changes
            if change.get("severity", 0.0) >= 0.8
        ]
        
        # Log emergency details
        logger.warning(
            f"Critical changes detected: {len(critical_changes)} out of {len(changes)} total changes"
        )
        
        for idx, change in enumerate(critical_changes, 1):
            change_type = change.get("change_type", "unknown")
            severity = change.get("severity", 0.0)
            description = change.get("description", "No description")
            
            logger.warning(
                f"Critical Change #{idx}: type={change_type}, "
                f"severity={severity:.2f}, description={description}"
            )
        
        # Prepare emergency metadata
        emergency_metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "report_id": report.report_id if hasattr(report, 'report_id') else None,
            "total_changes": len(changes),
            "critical_changes": len(critical_changes),
            "max_severity": max_severity,
            "alert_level": "critical" if max_severity >= 0.9 else "high"
        }
        
        logger.info(f"Emergency workflow completed. Metadata: {emergency_metadata}")
        
        return {
            "success": True,
            "emergency_logged": True,
            "metadata": emergency_metadata,
            "critical_change_count": len(critical_changes),
            "max_severity": max_severity
        }
        
    except Exception as e:
        logger.error(f"Emergency workflow failed: {e}", exc_info=True)
        
        return {
            "success": False,
            "emergency_logged": False,
            "error": str(e)
        }
