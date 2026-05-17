"""
Bob orchestration and session export for repository analysis.

This module executes analysis runs, records session messages, and writes
timestamped JSON exports to bob-exports for auditability.
"""

import json
import os
import logging
import shlex
import subprocess
from datetime import datetime
from typing import Dict, Any

import requests

from .analysis_engine import AnalysisEngine
from .risk_engine import calculate_score_breakdown, calculate_exploitability_score
from .prompt_templates import PROMPTS

logger = logging.getLogger(__name__)

# Export directory for Bob session artifacts.
EXPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'bob-exports')
os.makedirs(EXPORT_DIR, exist_ok=True)


class BobSession:
    """Tracks a single analysis session's conversation and export logic.

    The object is intentionally lightweight: it records messages and
    produces a single JSON export that bundles metadata, conversation
    history, and the structured analysis output.
    """
    
    def __init__(self, session_id: str, repo_url: str):
        self.session_id = session_id
        self.repo_url = repo_url
        self.started_at = datetime.utcnow()
        self.messages = []
        self.analysis_result = None
    
    def add_message(self, role: str, content: str):
        """Append a conversation message.

        Args:
            role: 'user' or 'bob' indicating message origin
            content: textual message content
        """
        self.messages.append({
            'timestamp': datetime.utcnow().isoformat(),
            'role': role,
            'content': content,
        })
    
    def export_to_file(self, analysis_result: Dict[str, Any]) -> str:
        """
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


def run_analysis_pipeline(repo_snapshot: Dict[str, Any], session_id: str, repo_url: str) -> Dict[str, Any]:
    """Run the analysis pipeline and return a structured result.

    The pipeline maps repository structure, computes a factor breakdown,
    derives the aggregate exploitability score, and returns normalized
    fields expected by the API response schema.

    Args:
        repo_snapshot: repository metadata and file tree
        session_id: unique session identifier
        repo_url: canonical repository URL

    Returns:
        A dictionary containing structured analysis and scoring fields.
    """
    
    bob_session = BobSession(session_id, repo_url)
    
    try:
        # Stage 1: architecture mapping and structured findings.
        logger.info('[analysis] Starting architecture analysis')
        bob_session.add_message('user', 'Analyze repository and return structured components')

        analysis = _run_analysis_source(repo_snapshot)
        bob_session.add_message('bob', f'Identified {len(analysis.get("components", []))} components')

        # Stage 2: score calculation.
        logger.info('[analysis] Calculating score breakdown')
        score_breakdown = calculate_score_breakdown(repo_snapshot, analysis)
        analysis['score_breakdown'] = score_breakdown.dict()

        logger.info('[analysis] Calculating exploitability score')
        overall_score = calculate_exploitability_score(analysis)

        # Finalize structured output.
        final_result = {
            'session_id': session_id,
            'repo_url': repo_url,
            'score': overall_score,
            'score_breakdown': analysis['score_breakdown'],
            'architecture': analysis.get('components', []),
            'entry_points': analysis.get('entry_points', []),
            'data_flows': analysis.get('data_flows', []),
            'privilege_issues': analysis.get('privilege_issues', []),
            'suggestions': analysis.get('suggestions', []),
            'file_risks': analysis.get('file_risks', []),
            'created_at': datetime.utcnow().isoformat() + 'Z',
        }

        # Persist export for auditing.
        bob_session.export_to_file(final_result)
        logger.info('[analysis] Pipeline complete')
        return final_result

    except Exception:
        logger.exception('Analysis pipeline failed')
        raise


def parse_bob_response(response_text: str) -> Dict[str, Any]:
    """Extract and parse the JSON object embedded in a Bob text response."""
    try:
        # Extract JSON payload if explanatory text is present.
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start == -1 or end <= start:
            raise ValueError('No JSON found in response')
        
        json_str = response_text[start:end]
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse Bob response: {str(e)}')
        raise ValueError(f'Invalid JSON in Bob response: {str(e)}')


def _run_analysis_source(repo_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Run analysis from configured source and normalize it to internal schema."""
    mode = os.getenv('BOB_MODE', 'local').strip().lower()

    if mode == 'cli':
        logger.info('[analysis] Using Bob CLI source')
        prompt = _build_bob_prompt(repo_snapshot)
        bob_raw = _run_bob_via_cli(prompt)
        return _normalize_analysis_payload(bob_raw)

    if mode == 'http':
        logger.info('[analysis] Using Bob HTTP source')
        prompt = _build_bob_prompt(repo_snapshot)
        bob_raw = _run_bob_via_http(prompt)
        return _normalize_analysis_payload(bob_raw)

    logger.info('[analysis] Using local deterministic source')
    engine = AnalysisEngine(repo_snapshot)
    return engine.run_analysis()


def _build_bob_prompt(repo_snapshot: Dict[str, Any]) -> str:
    """Build a single prompt that asks Bob for the required structured fields."""
    instructions = [
        PROMPTS['architecture_mapping'],
        PROMPTS['entry_points'],
        PROMPTS['data_flow'],
        PROMPTS['privilege_boundary'],
        PROMPTS['risk_summary'],
        (
            'Return strict JSON only with keys: architecture, entry_points, '
            'data_flows, privilege_issues, suggestions, file_risks.'
        ),
    ]
    snapshot = json.dumps(repo_snapshot, indent=2)
    return '\n\n'.join(instructions) + '\n\nRepository snapshot:\n' + snapshot


def _run_bob_via_cli(prompt: str) -> Dict[str, Any]:
    """Invoke Bob through a local CLI command and parse JSON output."""
    command_text = os.getenv('BOB_CLI_COMMAND', 'bob')
    command = shlex.split(command_text)

    if not command:
        raise ValueError('BOB_CLI_COMMAND is empty')

    result = subprocess.run(
        command,
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        stderr = (result.stderr or '').strip()
        raise RuntimeError(f'Bob CLI failed with exit code {result.returncode}: {stderr}')

    return parse_bob_response(result.stdout)


def _run_bob_via_http(prompt: str) -> Dict[str, Any]:
    """Invoke Bob through an HTTP endpoint and parse JSON output."""
    endpoint = os.getenv('BOB_API_ENDPOINT', '').strip()
    api_key = os.getenv('BOB_API_KEY', '').strip()

    if not endpoint:
        raise ValueError('BOB_API_ENDPOINT is not set for BOB_MODE=http')

    headers: Dict[str, str] = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'

    response = requests.post(
        endpoint,
        headers=headers,
        json={'prompt': prompt},
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    if isinstance(data, dict):
        for key in ('response', 'output', 'text', 'content'):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return parse_bob_response(value)

    return parse_bob_response(response.text)


def _normalize_analysis_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Bob output keys to the internal analysis schema."""
    entry_points = []
    for item in payload.get('entry_points', []) or []:
        if not isinstance(item, dict):
            continue
        normalized = dict(item)
        if 'auth_method' not in normalized and 'auth' in normalized:
            normalized['auth_method'] = normalized.get('auth')
        entry_points.append(normalized)

    data_flows = []
    for item in payload.get('data_flows', []) or []:
        if not isinstance(item, dict):
            continue
        normalized = dict(item)
        if 'validation_present' not in normalized and 'validation' in normalized:
            normalized['validation_present'] = normalized.get('validation')
        data_flows.append(normalized)

    return {
        'components': payload.get('components') or payload.get('architecture', []),
        'entry_points': entry_points,
        'data_flows': data_flows,
        'privilege_issues': payload.get('privilege_issues', []),
        'suggestions': payload.get('suggestions', []),
        'file_risks': payload.get('file_risks', []),
    }
