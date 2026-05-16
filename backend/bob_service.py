import json
import os
from datetime import datetime
from typing import Dict, Any
from .prompt_templates import PROMPTS


EXPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'bob-exports')
os.makedirs(EXPORT_DIR, exist_ok=True)


def run_bob_pipeline(repo_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Stubbed Bob orchestration: in real use, call IBM Bob SDK/API and pass PROMPTS.
    Here we simulate responses and write an export JSON file for submission.
    """
    # In production, you would: for p in PROMPTS: call bob.ask(p)
    result = {
        'architecture': [{'name': 'web', 'files': ['app.py', 'routes.py'], 'desc': 'HTTP layer'}],
        'entry_points': [{'path': 'routes.py', 'handler': 'handle_login', 'auth': 'cookie'}],
        'data_flows': [{'from': 'routes.py', 'to': 'db.py', 'validation': False}],
        'privilege_issues': [{'component': 'admin.py', 'issue': 'inconsistent checks'}],
        'suggestions': [{'why': 'missing validation', 'fix': 'add input validation at controller'}],
    }

    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    out_path = os.path.join(EXPORT_DIR, f'bob_export_{repo_snapshot.get("repo","repo")}_{ts}.json')
    with open(out_path, 'w') as f:
        json.dump({'metadata': repo_snapshot, 'analysis': result}, f, indent=2)

    return result
