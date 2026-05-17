"""
NOESIS Backend API Server
Orchestrates repository analysis pipeline and exposes REST endpoints.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

try:
    from .schemas import (
        AnalyzeRequest, AnalysisResult, AnalysisSession, AnalysisStatus,
        AnalysisProgress, LogEntry
    )
    from .github_service import fetch_repo_snapshot, GitHubAPIError
    from .bob_service import run_analysis_pipeline
    from .risk_engine import calculate_exploitability_score
except ImportError:
    from schemas import (
        AnalyzeRequest, AnalysisResult, AnalysisSession, AnalysisStatus,
        AnalysisProgress, LogEntry
    )
    from github_service import fetch_repo_snapshot, GitHubAPIError
    from bob_service import run_analysis_pipeline
    from risk_engine import calculate_exploitability_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title='NOESIS Backend',
    description='Enterprise security intelligence for code repositories',
    version='0.1.0'
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# In-memory session storage for active analysis state and progress.
sessions: Dict[str, AnalysisSession] = {}


@app.post('/api/analyze', response_model=Dict)
async def initiate_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks
) -> Dict:
    """
    Initiate a repository security analysis.
    
    Returns immediately with a session ID and queued status.
    Frontend polls /api/analysis/{session_id}/progress for real-time updates.
    
    Args:
        request: AnalyzeRequest with repo_url
        background_tasks: FastAPI background task manager
    
    Returns:
        Session metadata with ID for polling
    """
    session_id = str(uuid.uuid4())
    repo_url = str(request.repo_url)
    
    # Create session record
    session = AnalysisSession(
        session_id=session_id,
        repo_url=repo_url,
        status=AnalysisStatus.QUEUED,
        started_at=datetime.utcnow(),
    )
    sessions[session_id] = session
    
    logger.info(f'Analysis initiated for {repo_url} (session: {session_id})')
    
    # Schedule background analysis
    background_tasks.add_task(
        _execute_analysis,
        session_id=session_id,
        repo_url=repo_url
    )
    
    return {
        'session_id': session_id,
        'repo_url': repo_url,
        'status': AnalysisStatus.QUEUED,
        'created_at': session.started_at.isoformat() + 'Z',
    }


@app.get('/api/analyze/{session_id}/progress', response_model=AnalysisProgress)
async def get_analysis_progress(session_id: str) -> AnalysisProgress:
    """
    Poll for analysis progress and live logs.
    
    Frontend calls this endpoint repeatedly (every 500-1000ms) during analysis
    to display progress bar, stage name, and live execution logs.
    
    Args:
        session_id: Session identifier from /api/analyze
    
    Returns:
        Current progress, status, stage name, and log entries
    
    Raises:
        HTTPException: 404 if session not found
    """
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')
    
    return AnalysisProgress(
        session_id=session_id,
        status=session.status,
        progress=session.progress,
        stage=_get_stage_name(session.progress),
        log_lines=session.logs,
    )


@app.get('/api/analyze/{session_id}/result', response_model=AnalysisResult)
async def get_analysis_result(session_id: str) -> AnalysisResult:
    """
    Retrieve completed analysis report.
    
    Available only when status is COMPLETED. Returns full security analysis
    with all components, risks, and recommendations.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Complete AnalysisResult
    
    Raises:
        HTTPException: 404 if session not found, 202 if still processing
    """
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')
    
    if session.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=202,
            detail=f'Analysis {session.status}. Check /progress endpoint.'
        )
    
    if not session.result:
        raise HTTPException(status_code=500, detail='Result not available')
    
    return session.result


@app.get('/api/health')
async def health_check() -> Dict:
    """Health check endpoint for load balancers."""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'active_sessions': len([s for s in sessions.values() if s.status == AnalysisStatus.RUNNING]),
    }


# ============================================================================
# Background Task Implementation
# ============================================================================


async def _execute_analysis(session_id: str, repo_url: str):
    """
    Execute full analysis pipeline in background.
    
    Stages:
    1. Fetch repository (0-20%)
    2. GitHub snapshot analysis (20-40%)
    3. Run Bob pipeline (40-80%)
    4. Generate export (80-100%)
    """
    session = sessions[session_id]
    
    try:
        session.status = AnalysisStatus.RUNNING
        session.progress = 0
        
        # Stage 1: Fetch repository
        _add_log(session, 'info', 'Fetching repository metadata from GitHub...')
        session.progress = 10
        
        try:
            repo_snapshot = fetch_repo_snapshot(repo_url)
            _add_log(session, 'info', f'Repository fetched: {repo_snapshot["file_count"]} files')
        except GitHubAPIError as e:
            _add_log(session, 'error', f'GitHub API error: {str(e)}')
            raise
        
        session.progress = 25
        
        # Stage 2: Analyze repository structure
        _add_log(session, 'info', 'Analyzing repository structure...')
        
        components = repo_snapshot.get('components', {})
        _add_log(session, 'debug', f'Detected {len(components)} component types')
        
        entry_points = repo_snapshot.get('entry_point_candidates', [])
        _add_log(session, 'info', f'Found {len(entry_points)} entry point candidates')
        
        critical_files = repo_snapshot.get('critical_files', [])
        if critical_files:
            _add_log(session, 'warn', f'Found {len(critical_files)} sensitive files')
        
        session.progress = 40

        # Stage 3: Run architectural analysis pipeline
        _add_log(session, 'info', 'Running analysis pipeline...')

        try:
            analysis_result = run_analysis_pipeline(repo_snapshot, session_id, repo_url)
            _add_log(session, 'info', f'Analysis complete. Score: {analysis_result.get("score")}')
        except Exception as e:
            _add_log(session, 'error', f'Analysis pipeline error: {str(e)}')
            raise
        
        session.progress = 90
        
        # Stage 4: Finalize report
        _add_log(session, 'info', 'Finalizing report...')
        
        # Convert to AnalysisResult model
        session.result = AnalysisResult(**analysis_result)
        session.progress = 100
        session.status = AnalysisStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        
        _add_log(session, 'info', 'Analysis report ready')
        logger.info(f'Analysis completed for session {session_id}')
    
    except Exception as e:
        session.status = AnalysisStatus.FAILED
        session.error = str(e)
        _add_log(session, 'error', f'Analysis failed: {str(e)}')
        logger.error(f'Analysis failed for session {session_id}: {str(e)}', exc_info=True)


def _add_log(session: AnalysisSession, level: str, message: str):
    """Add a log entry to the session."""
    log_entry = LogEntry(
        timestamp=datetime.utcnow(),
        level=level,
        message=message,
    )
    session.logs.append(log_entry)
    logger.log(
        getattr(logging, level.upper()),
        f'[{session.session_id}] {message}'
    )


def _get_stage_name(progress: int) -> str:
    """Map progress percentage to analysis stage name."""
    if progress < 25:
        return 'Cloning repository'
    elif progress < 40:
        return 'Analyzing structure'
    elif progress < 60:
        return 'Mapping components'
    elif progress < 75:
        return 'Tracing data flows'
    elif progress < 90:
        return 'Detecting risks'
    elif progress < 100:
        return 'Generating report'
    else:
        return 'Complete'


# ============================================================================
# Server Startup
# ============================================================================


if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,  # Disable reload when running directly
        log_level='info',
    )
