"""
Lightweight GitHub repository snapshot generator.

This module retrieves repository metadata and a recursive file tree
using the GitHub REST API, then applies conservative heuristics to
classify files and identify likely entry points and sensitive files.
The logic is intentionally explicit and dependency-light.
"""

import requests
import logging
from typing import Dict, Any, List, Set
from collections import defaultdict

logger = logging.getLogger(__name__)

# GitHub API patterns for common file types indicating architecture
LANGUAGE_INDICATORS = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.java': 'Java',
    '.go': 'Go',
    '.rs': 'Rust',
    '.cpp': 'C++',
    '.cs': 'C#',
}

# Architectural pattern heuristics: file path → component role
COMPONENT_HEURISTICS = {
    'auth': ['auth', 'security', 'permission', 'acl', 'oauth', 'jwt', 'session'],
    'api': ['api', 'route', 'handler', 'endpoint', 'controller'],
    'database': ['db', 'model', 'query', 'migration', 'schema', 'repository'],
    'ui': ['ui', 'component', 'template', 'view', 'page', 'client', 'frontend'],
    'admin': ['admin', 'panel', 'dashboard', 'management'],
    'external': ['plugin', 'webhook', 'integration', 'external', 'vendor'],
}

# Sensitive patterns often indicating critical files
SENSITIVE_PATTERNS = {
    'config': ['config', 'settings', 'env', '.env', 'secret', 'credential'],
    'crypto': ['encrypt', 'hash', 'token', 'key', 'signature', 'ssl', 'tls'],
    'validation': ['validate', 'sanitize', 'escape', 'filter', 'check'],
    'access': ['permission', 'role', 'grant', 'deny', 'access', 'auth'],
}


class GitHubAPIError(Exception):
    """GitHub API interaction failed."""
    pass


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    """Return (owner, repo) for common GitHub URL formats.

    Supports HTTPS and SSH GitHub URLs.
    """
    # HTTPS form: https://github.com/owner/repo or with .git
    if repo_url.startswith('https://github.com/'):
        path = repo_url.replace('https://github.com/', '').rstrip('/')
        parts = path.split('/')
        if len(parts) >= 2:
            return parts[0], parts[1].replace('.git', '')

    # SSH form: git@github.com:owner/repo.git
    if repo_url.startswith('git@github.com:'):
        path = repo_url.replace('git@github.com:', '').rstrip('/')
        parts = path.split('/')
        if len(parts) >= 2:
            return parts[0], parts[1].replace('.git', '')

    raise ValueError(f'Unsupported GitHub URL: {repo_url}')


def fetch_repo_snapshot(repo_url: str, github_token: str = None) -> Dict[str, Any]:
    """Retrieve repository metadata and produce an analyzed file snapshot.

    The returned snapshot contains a conservative classification of files,
    likely entry points, and files that match sensitive patterns.

    Args:
        repo_url: repository URL
        github_token: optional token for authenticated requests

    Returns:
        Dict with metadata, file list, and classifications

    Raises:
        GitHubAPIError: on unrecoverable API failures or invalid URL
    """
    try:
        owner, repo = parse_repo_url(repo_url)
    except ValueError as e:
        raise GitHubAPIError(str(e))

    repo_api = f'https://api.github.com/repos/{owner}/{repo}'
    headers = {'Authorization': f'token {github_token}'} if github_token else {}

    try:
        repo_resp = requests.get(repo_api, headers=headers, timeout=10)
        repo_resp.raise_for_status()
        repo_data = repo_resp.json()
    except requests.RequestException as e:
        raise GitHubAPIError(f'Failed to fetch repository metadata: {e}')

    tree_api = f'https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1'
    try:
        tree_resp = requests.get(tree_api, headers=headers, timeout=10)
        tree_resp.raise_for_status()
        tree_data = tree_resp.json()
    except requests.RequestException as e:
        logger.warning('Could not fetch complete file tree; proceeding with available data')
        tree_data = {'tree': []}

    files: List[Dict[str, Any]] = []
    components: Dict[str, Set[str]] = defaultdict(set)
    languages: Set[str] = set()
    entry_point_candidates: List[str] = []
    critical_files: List[str] = []

    for item in tree_data.get('tree', []):
        path = item.get('path', '')
        item_type = item.get('type', 'blob')

        if item_type != 'blob':
            continue

        files.append({
            'path': path,
            'type': item_type,
            'size': item.get('size', 0),
            'sha': item.get('sha'),
        })

        # Language inference
        for ext, lang in LANGUAGE_INDICATORS.items():
            if path.endswith(ext):
                languages.add(lang)
                break

        path_lower = path.lower()
        for component, keywords in COMPONENT_HEURISTICS.items():
            if any(kw in path_lower for kw in keywords):
                components[component].add(path)
                break

        if any(kw in path_lower for kw in ['route', 'handler', 'endpoint', 'main', 'app.py', 'server']):
            entry_point_candidates.append(path)

        for keywords in SENSITIVE_PATTERNS.values():
            if any(kw in path_lower for kw in keywords):
                critical_files.append(path)
                break

    return {
        'owner': owner,
        'repo': repo,
        'repo_url': repo_url,
        'language': repo_data.get('language', 'Unknown'),
        'description': repo_data.get('description', ''),
        'is_private': repo_data.get('private', False),
        'files': files,
        'file_count': len(files),
        'languages_detected': sorted(list(languages)),
        'components': {k: sorted(list(v)) for k, v in components.items()},
        'entry_point_candidates': entry_point_candidates,
        'critical_files': critical_files,
        'created_at': repo_data.get('created_at'),
        'last_updated': repo_data.get('updated_at'),
    }
