"""
IBM Bob pipeline orchestration and conversation management.
Handles Bob invocation, prompt templating, response parsing, and session export.

Ready for live Bob SDK integration when IBM credentials are available.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from .analysis_engine import AnalysisEngine
from .risk_engine import calculate_score_breakdown, compute_exploitability_score

logger = logging.getLogger(__name__)

# Export directory for Bob sessions and analysis artifacts
EXPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'bob-exports')
os.makedirs(EXPORT_DIR, exist_ok=True)


class BobSession:
    """Manages a single Bob conversation session."""
    
    def __init__(self, session_id: str, repo_url: str):
        self.session_id = session_id
        self.repo_url = repo_url
        self.started_at = datetime.utcnow()
        self.messages = []  # Bob conversation history
        self.analysis_result = None
    
    def add_message(self, role: str, content: str):
        """Record a message in the Bob conversation."""
        self.messages.append({
            'timestamp': datetime.utcnow().isoformat(),
            'role': role,  # 'user' or 'bob'
            'content': content,
        })
    
    def export_to_file(self, analysis_result: Dict[str, Any]) -> str:
        """
        Export session to timestamped JSON file for audit trail.
        
        Files are saved to bob-exports/ with structure:
        {
            "metadata": {...},
            "conversation": [{...}],
            "analysis": {...}
        }
        """
        repo_name = self.repo_url.split('/')[-1].replace('.git', '')
        timestamp = self.started_at.strftime('%Y%m%dT%H%M%SZ')
        filename = f'bob_export_{repo_name}_{timestamp}.json'
        filepath = os.path.join(EXPORT_DIR, filename)
        
        export = {
            'metadata': {
                'session_id': self.session_id,
                'repo_url': self.repo_url,
                'started_at': self.started_at.isoformat(),
                'completed_at': datetime.utcnow().isoformat(),
                'message_count': len(self.messages),
            },
            'conversation': self.messages,
            'analysis': analysis_result,
        }
        
        with open(filepath, 'w') as f:
            json.dump(export, f, indent=2)
        
        logger.info(f'Bob session exported to {filepath}')
        return filepath


def run_bob_pipeline(repo_snapshot: Dict[str, Any], session_id: str, repo_url: str) -> Dict[str, Any]:
    """
    Execute complete Bob-based analysis pipeline.
    
    This implementation uses heuristic-based analysis (ready for Bob SDK integration).
    When IBM Bob SDK becomes available, replace the AnalysisEngine calls with:
        bob = IBMBob(api_key=..., api_endpoint=...)
        response = bob.prompt(message, context=repo_snapshot)
    
    Args:
        repo_snapshot: Repository data from github_service
        session_id: Unique analysis session identifier
        repo_url: Repository URL being analyzed
    
    Returns:
        Dictionary with complete analysis results
    """
    
    # Initialize Bob session for export
    bob_session = BobSession(session_id, repo_url)
    
    try:
        # Stage 1: Architecture Mapping
        logger.info('[Bob] Starting architecture analysis')
        bob_session.add_message('user', 'Analyze repository structure and identify architecture components')
        
        # In production: call Bob SDK here
        # For now: use AnalysisEngine heuristics
        engine = AnalysisEngine(repo_snapshot)
        analysis = engine.run_analysis()
        
        bob_session.add_message('bob', f'Identified {len(analysis["components"])} architectural components')
        
        # Stage 2: Calculate Score Breakdown
        logger.info('[Bob] Calculating risk scores')
        score_breakdown = calculate_score_breakdown(repo_snapshot, analysis)
        analysis['score_breakdown'] = score_breakdown.dict()
        
        # Stage 3: Compute Overall Exploitability Score
        logger.info('[Bob] Computing exploitability score')
        overall_score = compute_exploitability_score(analysis)
        
        # Stage 4: Export Session
        logger.info('[Bob] Exporting session')
        final_result = {
            'session_id': session_id,
            'repo_url': repo_url,
            'score': overall_score,
            'score_breakdown': analysis['score_breakdown'],
            'architecture': analysis['components'],
            'entry_points': analysis['entry_points'],
            'data_flows': analysis['data_flows'],
            'privilege_issues': analysis['privilege_issues'],
            'suggestions': analysis['suggestions'],
            'file_risks': analysis['file_risks'],
            'created_at': datetime.utcnow().isoformat() + 'Z',
        }
        
        # Export for audit
        bob_session.export_to_file(final_result)
        
        logger.info(f'[Bob] Analysis complete. Score: {overall_score}')
        return final_result
    
    except Exception as e:
        logger.error(f'[Bob] Pipeline error: {str(e)}')
        raise


def parse_bob_response(response_text: str) -> Dict[str, Any]:
    """
    Parse structured JSON response from Bob.
    
    Bob responses are expected to be valid JSON with keys:
    - architecture
    - entry_points
    - data_flows
    - privilege_issues
    - suggestions
    
    Args:
        response_text: Bob's response text
    
    Returns:
        Parsed dictionary
    
    Raises:
        ValueError: If response is not valid JSON
    """
    try:
        # Find JSON in response (Bob may include explanatory text)
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start == -1 or end <= start:
            raise ValueError('No JSON found in response')
        
        json_str = response_text[start:end]
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse Bob response: {str(e)}')
        raise ValueError(f'Invalid JSON in Bob response: {str(e)}')
