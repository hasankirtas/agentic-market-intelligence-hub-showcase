"""
User configuration models.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Optional
from datetime import datetime


class UserConfig(BaseModel):
    """
    User configuration model for competitive intelligence monitoring.
    """
    user_id: str = Field(..., description="Unique user identifier")
    urls: List[str] = Field(..., description="List of URLs to monitor")
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "urls": [
                    "https://vercel.com/pricing",
                    "https://netlify.com/pricing"
                ],
                "scan_schedule": "0 * * * *",
                "report_schedule": "0 */6 * * *",
                "emergency_email_enabled": True,
                "email": "user@example.com",
                "thresholds": {
                    "critical_threshold": 0.8,
                    "price_change_threshold": 0.2
                },
                "is_active": True
            }
        }
