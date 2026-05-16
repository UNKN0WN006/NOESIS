import requests
from typing import Dict, Any, List
from urllib.parse import urlparse


def fetch_repo_snapshot(repo_url: str) -> Dict[str, Any]:
    """Minimal repo fetch: for a public GitHub repo, pull the file list (tree).
    This is a simple helper—expand with authentication and rate-limit handling.
    """
    parsed = urlparse(repo_url)
    # expect urls like https://github.com/owner/repo
    parts = parsed.path.strip('/').split('/')
    if len(parts) < 2:
        raise ValueError('Invalid GitHub repo URL')
    owner, repo = parts[0], parts[1]
    api = f'https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1'
    r = requests.get(api)
    r.raise_for_status()
    data = r.json()
    files: List[Dict[str, Any]] = []
    for item in data.get('tree', []):
        files.append({'path': item.get('path'), 'type': item.get('type')})
    return {'owner': owner, 'repo': repo, 'files': files}
