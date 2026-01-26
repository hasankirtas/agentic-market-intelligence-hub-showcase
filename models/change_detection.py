"""
Change detection data models.
"""
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict
from datetime import datetime


class ChangeRecord(BaseModel):
    """
    Change detection record model.
    """
    change_id: str = Field(..., description="Unique change identifier (UUID)")
    scan_id: str = Field(..., description="Scan ID that detected this change")
    url: str = Field(..., description="URL where change was detected")
    change_type: str = Field(
        ...,
        description="Type of change: 'price_change', 'limit_change', 'feature_change', 'tier_change'"
    )
    tier_name: Optional[str] = Field(
        default=None,
        description="Tier name if applicable"
    )
    previous_value: Any = Field(
        ...,
        description="Previous value before change"
    )
    current_value: Any = Field(
        ...,
        description="Current value after change"
    )
    change_percent: Optional[float] = Field(
        default=None,
        description="Percentage change (for numeric values)"
    )
    severity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Change severity score (0.0 to 1.0)"
    )
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    is_critical: bool = Field(
        default=False,
        description="Whether this change exceeds critical threshold"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the change"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "change_id": "change_123",
                "scan_id": "scan_456",
                "url": "https://vercel.com/pricing",
                "change_type": "price_change",
                "tier_name": "pro",
                "previous_value": 20,
                "current_value": 25,
                "change_percent": 25.0,
                "severity": 0.9,
                "detected_at": "2024-01-01T12:00:00Z",
                "is_critical": True
            }
        }

