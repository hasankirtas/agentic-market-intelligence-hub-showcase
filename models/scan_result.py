"""
Scan result data models.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class ScanResult(BaseModel):
    """
    Scan result model for storing web scraping data.
    """
    scan_id: str = Field(..., description="Unique scan identifier (UUID)")
    user_id: str = Field(..., description="User who initiated the scan")
    url: str = Field(..., description="URL that was scanned")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(
        ...,
        description="Scraped data including pricing, tiers, limits, features"
    )
    status: str = Field(
        default="success",
        description="Scan status: 'success', 'error', 'partial'"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if scan failed"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the scan"
    )
    changes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of detected changes from Analyst Agent"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "scan_123",
                "user_id": "user_456",
                "url": "https://vercel.com/pricing",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": {
                    "pricing": {
                        "hobby": {"price": 0, "currency": "USD"},
                        "pro": {"price": 20, "currency": "USD"}
                    },
                    "tiers": [
                        {
                            "name": "hobby",
                            "price": 0,
                            "limits": {"bandwidth": "100GB"}
                        }
                    ],
                    "features": ["deployment", "ssl", "cdn"]
                },
                "status": "success",
                "metadata": {"crawl_duration": 2.5}
            }
        }
