"""
Risk scoring utilities.

Provides functions to produce a transparent, explainable exploitability
score and a per-factor breakdown. The implementation favors readability
and auditability over opaque model behavior.
"""

from typing import Dict, Any
from .schemas import ScoreBreakdown


def calculate_exploitability_score(analysis: Dict[str, Any]) -> int:
    """Aggregate per-factor scores into a single 0-100 exploitability value.

    The algorithm is intentionally simple and explainable: each factor is
    weighted and the composite is adjusted for critical privilege findings.

    Args:
        analysis: dictionary produced by the analysis engine

    Returns:
        int: exploitability score in range 0..100 (higher = more risky)
    """
    breakdown = analysis.get('score_breakdown', {})

    # Read per-factor scores with sensible defaults
    auth = breakdown.get('authentication', 50)
    authz = breakdown.get('authorization', 50)
    validation = breakdown.get('input_validation', 50)
    exposure = breakdown.get('data_exposure', 50)
    dependency = breakdown.get('dependency_risk', 50)

    weights = {
        'authentication': 0.25,
        'authorization': 0.30,
        'input_validation': 0.20,
        'data_exposure': 0.15,
        'dependency_risk': 0.10,
    }

    composite = (
        auth * weights['authentication'] +
        authz * weights['authorization'] +
        validation * weights['input_validation'] +
        exposure * weights['data_exposure'] +
        dependency * weights['dependency_risk']
    )

    # Amplify score for critical privilege issues (explainable multiplier)
    privilege_issues = analysis.get('privilege_issues', [])
    critical_count = sum(1 for p in privilege_issues if p.get('severity') == 'critical')
    multiplier = min(1 + (critical_count * 0.05), 1.5)
    composite *= multiplier

    return min(int(composite), 100)


def calculate_score_breakdown(repo_snapshot: Dict[str, Any], analysis_result: Dict[str, Any]) -> ScoreBreakdown:
    """Derive five factor scores that explain the overall exploitability."""
    entry_points = analysis_result.get('entry_points', [])
    data_flows = analysis_result.get('data_flows', [])
    privilege_issues = analysis_result.get('privilege_issues', [])

    # Authentication risk: proportion of entry points lacking authentication.
    unauthenticated = sum(1 for ep in entry_points if not ep.get('auth_method'))
    total_eps = len(entry_points) if entry_points else 1
    auth_risk = int((unauthenticated / total_eps) * 100) if total_eps else 0

    if unauthenticated > 0:
        auth_risk = max(auth_risk, 60)

    authentication = min(auth_risk + 20, 100)

    # Authorization risk: critical/high privilege boundary findings.
    auth_issues_critical = sum(
        1 for p in privilege_issues
        if p.get('severity') in ['critical', 'high']
        and ('privilege' in p.get('issue', '').lower() or 'auth' in p.get('issue', '').lower())
    )

    authorization = min(20 + (auth_issues_critical * 20), 100)

    # Input validation risk: unvalidated paths from source to sink.
    unvalidated_flows = sum(1 for f in data_flows if not f.get('validation_present'))
    total_flows = len(data_flows) if data_flows else 1
    validation_risk = int((unvalidated_flows / total_flows) * 100) if total_flows else 0

    input_validation = min(validation_risk + 20, 100)

    # Data exposure risk: repository sensitivity heuristics.
    critical_file_count = len(repo_snapshot.get('critical_files', []))
    data_exposure = min(critical_file_count * 12 + 15, 100)

    # Dependency risk baseline from repository metadata only.
    dependency_risk = 35

    return ScoreBreakdown(
        authentication=authentication,
        authorization=authorization,
        input_validation=input_validation,
        data_exposure=data_exposure,
        dependency_risk=dependency_risk,
    )
