from typing import Dict, Any


def compute_exploitability_score(analysis: Dict[str, Any]) -> int:
    """Compute a simple weighted score from analysis dict and normalize to 0-100."""
    public_endpoints = len(analysis.get('entry_points', []))
    missing_validation = sum(1 for f in analysis.get('data_flows', []) if not f.get('validation'))
    auth_inconsistencies = len(analysis.get('privilege_issues', []))
    dangerous_deps = 0  # placeholder if dependency scanning is added

    raw = (public_endpoints * 2) + (missing_validation * 3) + (auth_inconsistencies * 4) + (dangerous_deps * 2)
    # naive normalization: cap at 100
    score = min(int((raw / 10.0) * 100), 100)
    return score
