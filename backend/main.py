from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

from .schemas import AnalyzeRequest, AnalysisResult
from .github_service import fetch_repo_snapshot
from .bob_service import run_bob_pipeline
from .risk_engine import compute_exploitability_score

app = FastAPI(title='ThreatLens AI - Backend')


@app.post('/analyze', response_model=AnalysisResult)
def analyze(req: AnalyzeRequest):
    try:
        repo = fetch_repo_snapshot(req.repo_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    analysis = run_bob_pipeline(repo)
    score = compute_exploitability_score(analysis)

    return {
        'score': score,
        'architecture': analysis.get('architecture', {}),
        'entry_points': analysis.get('entry_points', []),
        'data_flows': analysis.get('data_flows', []),
        'privilege_issues': analysis.get('privilege_issues', []),
        'suggestions': analysis.get('suggestions', []),
    }


if __name__ == '__main__':
    uvicorn.run('backend.main:app', host='0.0.0.0', port=8000, reload=True)
