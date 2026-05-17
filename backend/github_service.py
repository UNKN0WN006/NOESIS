"""
GitHub repository ingestion and snapshot generation.
Handles public repository analysis with proper error handling and rate-limit awareness.
"""

import requests
import logging
from typing import Dict, Any, List, Set
from urllib.parse import urlparse
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
    """
    Extract owner and repository name from GitHub URL.
    
    Args:
        repo_url: URL like https://github.com/owner/repo or git@github.com:owner/repo.git
    
    Returns:
        Tuple of (owner, repo)
    
    Raises:
        ValueError: If URL format is invalid
    """
    # Handle HTTPS URLs
    if repo_url.startswith('https://github.com/'):
        path = repo_url.replace('https://github.com/', '').rstrip('/')
        parts = path.split('/')
        if len(parts) >= 2:
            return parts[0], parts[1].replace('.git', '')
    
    # Handle SSH URLs
    if repo_url.startswith('git@github.com:'):
        path = repo_url.replace('git@github.com:', '').rstrip('/')
        parts = path.split('/')
        if len(parts) >= 2:
            return parts[0], parts[1].replace('.git', '')
    
    raise ValueError(f'Invalid GitHub repository URL: {repo_url}')


def fetch_repo_snapshot(repo_url: str, github_token: str = None) -> Dict[str, Any]:
    """
    Fetch repository metadata and file tree from GitHub API.
    
    Analyzes the repository structure to identify:
    - Architecture components (inferred from directory structure)
    - Entry points (public routes, CLI handlers)
    - Critical files (authentication, data access)
    - Language composition
    
    Args:
        repo_url: GitHub repository URL
        github_token: Optional GitHub API token for higher rate limits
    
    Returns:
        Dictionary with repo metadata and analyzed file tree
    
    Raises:
        GitHubAPIError: If GitHub API calls fail
    """
    try:
        owner, repo = parse_repo_url(repo_url)
    except ValueError as e:
        raise GitHubAPIError(str(e))
    
    # Fetch repository metadata
    repo_api = f'https://api.github.com/repos/{owner}/{repo}'
    headers = {'Authorization': f'token {github_token}'} if github_token else {}
    
    try:
        repo_resp = requests.get(repo_api, headers=headers, timeout=10)
        repo_resp.raise_for_status()
        repo_data = repo_resp.json()
    except requests.RequestException as e:
        raise GitHubAPIError(f'Failed to fetch repository: {str(e)}')
    
    # Fetch repository file tree
    tree_api = f'https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1'
    
    try:
        tree_resp = requests.get(tree_api, headers=headers, timeout=10)
        tree_resp.raise_for_status()
        tree_data = tree_resp.json()
    except requests.RequestException as e:
        logger.warning(f'Could not fetch file tree (may be empty repo): {str(e)}')
        tree_data = {'tree': []}
    
    # Analyze file structure
    files: List[Dict[str, Any]] = []
    components: Dict[str, Set[str]] = defaultdict(set)
    languages: Set[str] = set()
    entry_point_candidates: List[str] = []
    critical_files: List[str] = []
    
    for item in tree_data.get('tree', []):
        path = item.get('path', '')
        item_type = item.get('type', 'blob')
        
        if item_type == 'blob':
            files.append({
                'path': path,
                'type': item_type,
                'size': item.get('size', 0),
                'sha': item.get('sha'),
            })
            
            # Classify file language
            for ext, lang in LANGUAGE_INDICATORS.items():
                if path.endswith(ext):
                    languages.add(lang)
                    break
            
            # Heuristic: component classification from path
            path_lower = path.lower()
            for component, keywords in COMPONENT_HEURISTICS.items():
                if any(kw in path_lower for kw in keywords):
                    components[component].add(path)
                    break
            
            # Entry point detection (routes, handlers, main files)
            if any(kw in path_lower for kw in ['route', 'handler', 'endpoint', 'main', 'app.py', 'server']):
                entry_point_candidates.append(path)
            
            # Sensitive file detection
            for category, keywords in SENSITIVE_PATTERNS.items():
                if any(kw in path_lower for kw in keywords):
                    critical_files.append(path)
    
    return {
        'owner': owner,
        'repo': repo,
        'repo_url': repo_url,
        'language': repo_data.get('language', 'Unknown'),
        'description': repo_data.get('description', ''),
        'is_private': repo_data.get('private', False),
        'files': files,
        'file_count': len(files),
        'languages_detected': list(languages),
        'components': {k: list(v) for k, v in components.items()},
        'entry_point_candidates': entry_point_candidates,
        'critical_files': critical_files,
        'created_at': repo_data.get('created_at'),
        'last_updated': repo_data.get('updated_at'),
    }
