"""
Report endpoints.
Retrieve generated reports for users.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.dependencies import get_report_repository
from app.database.repositories.report_repository import ReportRepository
from app.api.schemas import ReportResponse, ReportListResponse, ErrorResponse, ReportDeleteRequest
from core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{user_id}", response_model=ReportListResponse)
async def get_user_reports(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    report_type: Optional[str] = Query(None, description="Filter by report type: 'scheduled' or 'emergency'"),
    repository: ReportRepository = Depends(get_report_repository)
) -> ReportListResponse:
    """
    Get reports for a user with pagination.
    
    Args:
        user_id: User identifier
        page: Page number (1-indexed)
        page_size: Number of reports per page (1-100)
        report_type: Optional filter by report type
        repository: ReportRepository dependency
    
    Returns:
        Paginated list of reports
    
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get reports from repository
        if report_type:
            # Use get_reports_by_type if report_type filter is specified
            reports = await repository.get_reports_by_type(
                user_id=user_id,
                report_type=report_type,
                limit=page_size * page  # Get enough for pagination
            )
        else:
            # Use get_reports_by_user if no filter
            reports = await repository.get_reports_by_user(
                user_id=user_id,
                limit=page_size * page  # Get enough for pagination
            )
        
        # Calculate pagination
        total = len(reports)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Slice for current page
        paginated_reports = reports[start_idx:end_idx]
        has_more = end_idx < total
        
        return ReportListResponse(
            reports=[ReportResponse.from_report(report) for report in paginated_reports],
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Failed to get reports for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reports: {str(e)}"
        )


@router.get("/{user_id}/latest", response_model=ReportResponse)
async def get_latest_report(
    user_id: str,
    report_type: Optional[str] = Query(None, description="Filter by report type: 'scheduled' or 'emergency'"),
    repository: ReportRepository = Depends(get_report_repository)
) -> ReportResponse:
    """
    Get the latest report for a user.
    
    Args:
        user_id: User identifier
        report_type: Optional filter by report type
        repository: ReportRepository dependency
    
    Returns:
        Latest report
    
    Raises:
        HTTPException: If no report found or retrieval fails
    """
    try:
        report = await repository.get_latest_report(user_id, report_type=report_type)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No report found for user: {user_id}"
            )
        
        return ReportResponse.from_report(report)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest report for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get latest report: {str(e)}"
        )


@router.get("/{user_id}/{report_id}", response_model=ReportResponse)
async def get_report_by_id(
    user_id: str,
    report_id: str,
    repository: ReportRepository = Depends(get_report_repository)
) -> ReportResponse:
    """
    Get a specific report by ID.
    
    Args:
        user_id: User identifier
        report_id: Report identifier
        repository: ReportRepository dependency
    
    Returns:
        Report details
    
    Raises:
        HTTPException: If report not found or retrieval fails
    """
    try:
        report = await repository.get_report(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {report_id}"
            )
        
        # Verify report belongs to user
        if report.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Report does not belong to this user"
            )
        
        return ReportResponse.from_report(report)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report: {str(e)}"
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict
)
async def delete_reports(
    user_id: str,
    request: ReportDeleteRequest,
    repository: ReportRepository = Depends(get_report_repository)
) -> dict:
    """
    Delete reports for a user.
    - If report_ids provided: delete those (only if they belong to the user).
    - If delete_all is True: delete all reports for the user.
    Returns count of deleted reports.
    """
    try:
        if not request.delete_all and not request.report_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide report_ids or set delete_all=True"
            )

        deleted = await repository.delete_reports_by_user(
            user_id=user_id,
            report_ids=request.report_ids
        ) if not request.delete_all else await repository.delete_reports_by_user(user_id=user_id)

        return {"deleted": deleted}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete reports for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete reports: {str(e)}"
        )
