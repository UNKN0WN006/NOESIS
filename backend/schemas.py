"""
Data models for NOESIS analysis pipeline.
Pydantic schemas ensure type safety and API contract validation.
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Risk severity classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisStatus(str, Enum):
    """Analysis session lifecycle state."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyzeRequest(BaseModel):
    """Frontend analysis initiation request."""
    repo_url: HttpUrl = Field(..., description="GitHub repository URL")

    @validator('repo_url')
    def validate_github_url(cls, v):
        """Ensure URL is a valid GitHub repository."""
        url_str = str(v)
        if 'github.com' not in url_str:
            raise ValueError('Must be a GitHub repository URL')
        return v


class LogEntry(BaseModel):
    """Analysis execution log record."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(..., description="Log level: info, debug, warn, error")
    message: str


class ArchitectureComponent(BaseModel):
    """Architectural module in the repository."""
    name: str
    files: List[str] = Field(default_factory=list)
    description: str = Field(alias="desc")
    risk_level: RiskLevel = RiskLevel.LOW
    external_interface: bool = False
    depends_on: List[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class EntryPoint(BaseModel):
    """External-facing access route (HTTP, CLI, webhook)."""
    path: str
    handler: str
    auth_method: Optional[str] = Field(None, alias="auth")
    risk_level: RiskLevel = RiskLevel.LOW
    input_types: List[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True


class DataFlow(BaseModel):
    """Input-to-storage trace through the codebase."""
    source: str = Field(..., alias="from")
    sink: str = Field(..., alias="to")
    validation_present: bool = Field(..., alias="validation")
    risk_level: RiskLevel = RiskLevel.LOW
    intermediate_steps: List[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True


class PrivilegeIssue(BaseModel):
    """Authorization boundary violation or privilege escalation risk."""
    component: str
    issue: str
    severity: RiskLevel
    rationale: str
    affected_entry_points: List[str] = Field(default_factory=list)
    remediation_effort: str = Field(default="medium")


class RefactorSuggestion(BaseModel):
    """Actionable remediation with priority and implementation guidance."""
    reason: str = Field(..., alias="why")
    recommendation: str = Field(..., alias="fix")
    impacted_files: List[str] = Field(..., alias="files")
    code_example: Optional[str] = Field(None, alias="code_snippet")
    severity: RiskLevel
    effort: str = Field(..., description="low, medium, or high effort")
    
    class Config:
        populate_by_name = True


class FileRisk(BaseModel):
    """Per-file risk profile and issues discovered."""
    path: str
    risk_score: int = Field(..., ge=0, le=100)
    issues: List[str] = Field(default_factory=list)
    severity: RiskLevel
    language: Optional[str] = None


class ScoreBreakdown(BaseModel):
    """Multi-factor risk scoring dashboard."""
    authentication: int = Field(..., ge=0, le=100)
    authorization: int = Field(..., ge=0, le=100)
    input_validation: int = Field(..., ge=0, le=100)
    data_exposure: int = Field(..., ge=0, le=100)
    dependency_risk: int = Field(..., ge=0, le=100)


class AnalysisResult(BaseModel):
    """Complete security analysis report."""
    session_id: str
    repo_url: str
    score: int = Field(..., ge=0, le=100, description="Overall exploitability score")
    score_breakdown: ScoreBreakdown
    architecture: List[ArchitectureComponent] = Field(default_factory=list)
    entry_points: List[EntryPoint] = Field(default_factory=list)
    data_flows: List[DataFlow] = Field(default_factory=list)
    privilege_issues: List[PrivilegeIssue] = Field(default_factory=list)
    suggestions: List[RefactorSuggestion] = Field(default_factory=list)
    file_risks: List[FileRisk] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }


class AnalysisProgress(BaseModel):
    """Progress update for streaming frontend."""
    session_id: str
    status: AnalysisStatus
    progress: int = Field(..., ge=0, le=100)
    stage: str
    log_lines: List[LogEntry] = Field(default_factory=list)


class AnalysisSession(BaseModel):
    """Session metadata and state tracking."""
    session_id: str
    repo_url: str
    status: AnalysisStatus
    progress: int = Field(default=0, ge=0, le=100)
    started_at: datetime
    completed_at: Optional[datetime] = None
    logs: List[LogEntry] = Field(default_factory=list)
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None
