from pydantic import BaseModel
from typing import Any, Dict, List


class AnalyzeRequest(BaseModel):
    repo_url: str


class AnalysisResult(BaseModel):
    score: int
    architecture: Dict[str, Any]
    entry_points: List[Dict[str, Any]]
    data_flows: List[Dict[str, Any]]
    privilege_issues: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
