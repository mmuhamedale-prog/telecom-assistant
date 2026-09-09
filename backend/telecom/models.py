from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SIPEvent(BaseModel):
    timestamp: Optional[datetime] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    reason: Optional[str] = None
    call_id: Optional[str] = None
    from_user: Optional[str] = None
    to_user: Optional[str] = None
    raw: str


class TelecomAnalysis(BaseModel):
    protocol: str = "SIP"
    status: str
    events: List[SIPEvent] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    probable_causes: List[str] = Field(default_factory=list)
    severity: str = "info"
    evidence: List[str] = Field(default_factory=list)
    recommended_checks: List[str] = Field(default_factory=list)


class TelecomRealtimeEvent(BaseModel):
    event_type: str
    source: str = "unknown"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)
