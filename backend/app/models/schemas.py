from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AuditStatus(str, Enum):
    PENDING = "pending"
    RUNNING_SLITHER = "running_slither"
    RUNNING_AI = "running_ai"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"
    OPTIMIZATION = "Optimization"


SEVERITY_ORDER = {
    Severity.HIGH: 0,
    Severity.MEDIUM: 1,
    Severity.LOW: 2,
    Severity.INFORMATIONAL: 3,
    Severity.OPTIMIZATION: 4,
}

SEVERITY_LABELS = {
    Severity.HIGH: "高危",
    Severity.MEDIUM: "中危",
    Severity.LOW: "低危",
    Severity.INFORMATIONAL: "信息",
    Severity.OPTIMIZATION: "优化建议",
}


class AIExplanation(BaseModel):
    title: str = ""
    problem: str = ""
    impact: str = ""
    recommendation: str = ""
    ai_success: bool = False


class Finding(BaseModel):
    id: str
    detector: str
    severity: Severity
    description: str
    contract: Optional[str] = None
    function: Optional[str] = None
    file: Optional[str] = None
    line: Optional[int] = None
    ai: AIExplanation = Field(default_factory=AIExplanation)
    ai_expanded: bool = True


class AuditSummary(BaseModel):
    total: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    informational: int = 0
    optimization: int = 0
    ai_explained: int = 0


class AuditMeta(BaseModel):
    task_id: str
    status: AuditStatus
    filename: str
    created_at: str
    updated_at: str
    finished_at: Optional[str] = None
    error: Optional[str] = None
    progress: str = ""
    summary: Optional[AuditSummary] = None
    duration_sec: Optional[float] = None


class CreateAuditResponse(BaseModel):
    task_id: str


class AuditStatusResponse(BaseModel):
    task_id: str
    status: AuditStatus
    progress: str
    error: Optional[str] = None
    summary: Optional[AuditSummary] = None
    filename: Optional[str] = None
    finished_at: Optional[str] = None
    duration_sec: Optional[float] = None


class FindingsResponse(BaseModel):
    task_id: str
    findings: list[Finding]


class HealthResponse(BaseModel):
    status: str
    slither_available: bool
    solc_available: bool
    slither_version: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)
