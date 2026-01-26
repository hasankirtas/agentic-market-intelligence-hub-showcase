"""
Scan endpoints.
Expose scan history for frontend dashboards.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from app.dependencies import get_scan_repository
from app.database.repositories.scan_repository import ScanRepository
from app.api.schemas import ScanResponse
from core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.get("/{user_id}", response_model=list[ScanResponse])
async def list_scans(
    user_id: str,
    limit: int = Query(50, ge=1, le=500, description="Max scans to return"),
    repository: ScanRepository = Depends(get_scan_repository)
):
    """
    Get recent scans for a user (newest first).
    """
    try:
        scans = await repository.get_scans_by_user(user_id=user_id, limit=limit)
        return [ScanResponse.from_scan_result(scan) for scan in scans]
    except Exception as e:
        logger.error(f"Failed to list scans for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scans: {str(e)}"
        )

