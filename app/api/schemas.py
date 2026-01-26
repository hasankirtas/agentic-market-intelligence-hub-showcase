"""
API request and response schemas.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Optional, Any
from datetime import datetime
from models.config import UserConfig
from models.scan_result import ScanResult
from models.report import Report


# ==================== Config Schemas ====================

class ConfigCreateRequest(BaseModel):
    """Request schema for creating user configuration."""
    user_id: str = Field(..., description="Unique user identifier")
    urls: List[str] = Field(..., description="List of pricing page URLs to monitor")
    scan_schedule: str = Field(
        default="0 * * * *",
        description="Scan schedule in cron format (default: every hour)"
    )
    report_schedule: str = Field(
        default="0 */6 * * *",
        description="Report schedule in cron format (default: every 6 hours)"
    )
    emergency_email_enabled: bool = Field(
        default=True,
        description="Enable immediate email alerts for critical changes"
    )
    email: EmailStr = Field(..., description="Notification email address")
    thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "critical_threshold": 0.8,
            "price_change_threshold": 0.2
        },
        description="Alert thresholds"
    )
    is_active: bool = Field(default=True, description="Whether monitoring is active")


class ConfigUpdateRequest(BaseModel):
    """Request schema for updating user configuration."""
    urls: Optional[List[str]] = Field(None, description="List of pricing page URLs to monitor")
    scan_schedule: Optional[str] = Field(None, description="Scan schedule in cron format")
    report_schedule: Optional[str] = Field(None, description="Report schedule in cron format")
    emergency_email_enabled: Optional[bool] = Field(None, description="Enable immediate email alerts for critical changes")
    email: Optional[EmailStr] = Field(None, description="Notification email address")
    thresholds: Optional[Dict[str, float]] = Field(None, description="Alert thresholds")
    is_active: Optional[bool] = Field(None, description="Whether monitoring is active")


class ConfigResponse(BaseModel):
    """Response schema for user configuration."""
    user_id: str
    urls: List[str]
    scan_schedule: str
    report_schedule: str
    emergency_email_enabled: bool
    email: str
    thresholds: Dict[str, float]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_user_config(cls, config: UserConfig) -> "ConfigResponse":
        """Create ConfigResponse from UserConfig model."""
        return cls(
            user_id=config.user_id,
            urls=config.urls,
            scan_schedule=config.scan_schedule,
            report_schedule=config.report_schedule,
            emergency_email_enabled=config.emergency_email_enabled,
            email=config.email,
            thresholds=config.thresholds,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at
        )


# ==================== Trigger Schemas ====================

class TriggerScanRequest(BaseModel):
    """Request schema for triggering manual scan."""
    user_id: str = Field(..., description="User ID to scan for")
    url: Optional[str] = Field(
        None,
        description="Specific URL to scan (optional, scans all URLs if not provided)"
    )


class TriggerScanResponse(BaseModel):
    """Response schema for trigger scan."""
    scan_id: str = Field(..., description="Scan ID")
    user_id: str = Field(..., description="User ID")
    url: Optional[str] = Field(None, description="Scanned URL")
    status: str = Field(..., description="Scan status: 'initiated', 'error'")
    message: str = Field(..., description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==================== Scan Schemas ====================

class ScanResponse(BaseModel):
    """Response schema for scan result."""
    scan_id: str
    user_id: str
    url: str
    timestamp: datetime
    data: Dict[str, Any]
    status: str
    error_message: Optional[str]
    metadata: Dict[str, Any]
    changes: List[Dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def from_scan_result(cls, scan: ScanResult) -> "ScanResponse":
        """Create ScanResponse from ScanResult model."""
        return cls(
            scan_id=scan.scan_id,
            user_id=scan.user_id,
            url=scan.url,
            timestamp=scan.timestamp,
            data=scan.data,
            status=scan.status,
            error_message=scan.error_message,
            metadata=scan.metadata,
            changes=scan.changes
        )


# ==================== Report Schemas ====================

class ReportResponse(BaseModel):
    """Response schema for report."""
    report_id: str
    user_id: str
    report_type: str
    generated_at: datetime
    changes_detected: int
    critical_changes: int
    changes: List[Dict]
    insights: List[str]
    report_content: str
    email_sent: bool
    email_sent_at: Optional[datetime]

    @classmethod
    def from_report(cls, report: Report) -> "ReportResponse":
        """Create ReportResponse from Report model."""
        return cls(
            report_id=report.report_id,
            user_id=report.user_id,
            report_type=report.report_type,
            generated_at=report.generated_at,
            changes_detected=report.changes_detected,
            critical_changes=report.critical_changes,
            changes=report.changes,
            insights=report.insights,
            report_content=report.report_content,
            email_sent=report.email_sent,
            email_sent_at=report.email_sent_at
        )


class ReportListResponse(BaseModel):
    """Response schema for report list."""
    reports: List[ReportResponse]
    total: int
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=10, description="Page size")
    has_more: bool = Field(..., description="Whether there are more reports")


class ReportDeleteRequest(BaseModel):
    """
    Request body for deleting reports.
    If report_ids is provided, deletes those reports (validated by user_id in path).
    If delete_all is True, deletes all reports for the user.
    """
    report_ids: Optional[List[str]] = Field(None, description="List of report IDs to delete")
    delete_all: bool = Field(False, description="Delete all reports for the user")


# ==================== Error Schemas ====================

class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error detail")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

