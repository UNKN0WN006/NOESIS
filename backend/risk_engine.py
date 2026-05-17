"""
Risk scoring and calculation engine.
Converts architectural analysis into exploitability scores with multi-factor breakdown.
"""

from typing import Dict, Any
from .schemas import ScoreBreakdown


def compute_exploitability_score(analysis: Dict[str, Any]) -> int:
    """
    Compute overall exploitability score (0-100) from analysis results.
    
    The score is a weighted composite of five security factors:
    - Authentication: Are entry points properly authenticated?
    - Authorization: Are privilege boundaries consistently enforced?
    - Input Validation: Are user inputs sanitized before use?
    - Data Exposure: Are sensitive data flows protected?
    - Dependency Risk: Are dependencies known and up-to-date?
    
    Args:
        analysis: Output from analysis_engine.AnalysisEngine
    
    Returns:
        Integer score 0-100 where higher = more exploitable
    """
    breakdown = analysis.get('score_breakdown', {})
    
    # Extract individual factor scores
    auth_score = breakdown.get('authentication', 50)
    authz_score = breakdown.get('authorization', 50)
    validation_score = breakdown.get('input_validation', 50)
    exposure_score = breakdown.get('data_exposure', 50)
    deps_score = breakdown.get('dependency_risk', 50)
    
    # Weighted aggregation: prioritize authentication and authorization
    # since they are the primary mechanisms preventing exploitation
    weights = {
        'authentication': 0.25,      # Critical: without auth, everything is accessible
        'authorization': 0.30,       # Most critical: privilege escalation = full compromise
        'input_validation': 0.20,    # High: enables code execution
        'data_exposure': 0.15,       # Medium: impacts confidentiality
        'dependency_risk': 0.10,     # Medium: known vulnerabilities
    }
    
    overall_score = (
        auth_score * weights['authentication'] +
        authz_score * weights['authorization'] +
        validation_score * weights['input_validation'] +
        exposure_score * weights['data_exposure'] +
        deps_score * weights['dependency_risk']
    )
    
    # Apply risk multipliers for high-impact findings
    privilege_issues = analysis.get('privilege_issues', [])
    critical_privilege_issues = [p for p in privilege_issues if p.get('severity') == 'critical']
    
    # Each critical privilege issue adds 5 points
    privilege_multiplier = min(1 + (len(critical_privilege_issues) * 0.05), 1.5)
    overall_score *= privilege_multiplier
    
    # Cap at 100
    return min(int(overall_score), 100)


def calculate_score_breakdown(repo_snapshot: Dict[str, Any], analysis_result: Dict[str, Any]) -> ScoreBreakdown:
    """
    Detailed breakdown of exploitability across five dimensions.
    
    Provides transparency into how the overall score is constructed,
    enabling users to understand which areas pose the greatest risk.
    
    Args:
        repo_snapshot: Repository metadata from github_service
        analysis_result: Architectural analysis from analysis_engine
    
    Returns:
        ScoreBreakdown object with five factor scores
    """
    entry_points = analysis_result.get('entry_points', [])
    data_flows = analysis_result.get('data_flows', [])
    privilege_issues = analysis_result.get('privilege_issues', [])
    suggestions = analysis_result.get('suggestions', [])
    
    # 1. Authentication Risk (0-100)
    # Based on proportion of entry points lacking authentication
    unauthenticated = sum(1 for ep in entry_points if not ep.get('auth_method'))
    total_eps = len(entry_points) if entry_points else 1
    auth_risk = int((unauthenticated / total_eps) * 100) if total_eps else 0
    
    # Baseline if any endpoints detected without auth
    if unauthenticated > 0:
        auth_risk = max(auth_risk, 60)
    
    authentication = min(auth_risk + 20, 100)
    
    # 2. Authorization Risk (0-100)
    # Based on privilege issues and their severity
    auth_issues_critical = sum(
        1 for p in privilege_issues
        if p.get('severity') in ['critical', 'high']
        and ('privilege' in p.get('issue', '').lower() or 'auth' in p.get('issue', '').lower())
    )
    
    authorization = min(20 + (auth_issues_critical * 20), 100)
    
    # 3. Input Validation Risk (0-100)
    # Based on data flows without validation
    unvalidated_flows = sum(1 for f in data_flows if not f.get('validation_present'))
    total_flows = len(data_flows) if data_flows else 1
    validation_risk = int((unvalidated_flows / total_flows) * 100) if total_flows else 0
    
    input_validation = min(validation_risk + 20, 100)
    
    # 4. Data Exposure Risk (0-100)
    # Based on critical files and sensitive patterns
    critical_file_count = len(repo_snapshot.get('critical_files', []))
    exposure_risk = min(critical_file_count * 12 + 15, 100)
    
    data_exposure = exposure_risk
    
    # 5. Dependency Risk (0-100)
    # Placeholder: would require SBOM/package.json analysis
    # For now: 35 baseline (medium risk) - in production would check known CVEs
    dependency_risk = 35
    
    return ScoreBreakdown(
        authentication=authentication,
        authorization=authorization,
        input_validation=input_validation,
        data_exposure=data_exposure,
        dependency_risk=dependency_risk,
    )
