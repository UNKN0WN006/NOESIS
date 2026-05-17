"""
Core analysis engine: converts repository metadata into security insights.
Implements deterministic heuristic analysis over repository structure.
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

from .schemas import (
    ArchitectureComponent, EntryPoint, DataFlow, PrivilegeIssue,
    RefactorSuggestion, FileRisk, RiskLevel, ScoreBreakdown
)

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """
    Analyzes repository structure to identify security risks.
    
    Strategy:
    1. Map components from directory structure and file naming patterns
    2. Identify entry points (public routes, handlers)
    3. Infer data flows from component relationships
    4. Detect privilege boundary violations and auth gaps
    5. Score each risk factor and generate remediation suggestions
    6. Rank files by risk profile
    """
    
    def __init__(self, repo_snapshot: Dict[str, Any]):
        self.repo = repo_snapshot
        self.components: List[ArchitectureComponent] = []
        self.entry_points: List[EntryPoint] = []
        self.data_flows: List[DataFlow] = []
        self.privilege_issues: List[PrivilegeIssue] = []
        self.suggestions: List[RefactorSuggestion] = []
        self.file_risks: List[FileRisk] = []
        self.score_breakdown = ScoreBreakdown(
            authentication=50,
            authorization=50,
            input_validation=50,
            data_exposure=50,
            dependency_risk=50,
        )
    
    def run_analysis(self) -> Dict[str, Any]:
        """Execute complete analysis pipeline."""
        logger.info("Starting analysis pipeline")
        
        self._map_architecture()
        self._identify_entry_points()
        self._trace_data_flows()
        self._detect_privilege_issues()
        self._generate_suggestions()
        self._score_files()
        self._compute_risk_scores()
        
        logger.info("Analysis complete")
        return self.to_dict()
    
    def _map_architecture(self):
        """Infer architecture from repository structure."""
        components_dict = self.repo.get('components', {})
        
        # Known component archetypes with risk defaults
        archetypes = {
            'auth': ('Authentication & Authorization', RiskLevel.CRITICAL),
            'database': ('Data Access & Persistence', RiskLevel.CRITICAL),
            'api': ('API Routes & Handlers', RiskLevel.HIGH),
            'admin': ('Admin Panel & Management', RiskLevel.CRITICAL),
            'ui': ('UI/Frontend Client', RiskLevel.MEDIUM),
            'external': ('External Integrations', RiskLevel.HIGH),
        }
        
        for component_type, files in components_dict.items():
            if not files:
                continue
            
            archetype_name, default_risk = archetypes.get(
                component_type,
                (component_type.title(), RiskLevel.MEDIUM)
            )
            
            # If no auth component detected and this is API/DB, escalate risk
            has_auth = any('auth' in c.name.lower() for c in self.components)
            if component_type in ['api', 'database'] and not has_auth:
                default_risk = RiskLevel.CRITICAL
            
            comp = ArchitectureComponent(
                name=component_type,
                files=files[:10],  # Limit to first 10 for clarity
                desc=archetype_name,
                risk_level=default_risk,
                external_interface=(component_type in ['api', 'admin', 'external']),
            )
            self.components.append(comp)
    
    def _identify_entry_points(self):
        """Extract external-facing access routes."""
        candidates = self.repo.get('entry_point_candidates', [])
        
        # Heuristic entry point patterns
        patterns = {
            'routes': ('route', 'router', 'endpoint'),
            'http': ('http', 'get', 'post', 'put', 'delete', 'api'),
            'cli': ('cli', 'command', 'main', '__main__'),
            'webhook': ('webhook', 'callback', 'hook'),
        }
        
        auth_patterns = {
            'jwt': ('jwt', 'token', 'bearer'),
            'cookie': ('cookie', 'session'),
            'basic': ('basic', 'auth'),
            'oauth': ('oauth', 'oidc'),
        }
        
        for candidate in candidates:
            candidate_lower = candidate.lower()
            
            # Determine entry point type
            entry_type = 'http'
            for ep_type, keywords in patterns.items():
                if any(kw in candidate_lower for kw in keywords):
                    entry_type = ep_type
                    break
            
            # Detect auth method (default: none = HIGH risk)
            auth_method = None
            for auth_type, keywords in auth_patterns.items():
                if any(kw in candidate_lower for kw in keywords):
                    auth_method = auth_type
                    break
            
            risk = RiskLevel.CRITICAL if auth_method is None else RiskLevel.MEDIUM
            
            ep = EntryPoint(
                path=candidate,
                handler=candidate.split('/')[-1].replace('.py', '').replace('.js', ''),
                auth_method=auth_method,
                risk_level=risk,
                input_types=['string', 'json'] if 'api' in entry_type else [],
            )
            self.entry_points.append(ep)
        
        # If no entry points found but has API component, mark as risk
        if not self.entry_points and any('api' in c.name.lower() for c in self.components):
            logger.warning("API component detected but no entry points identified")
            self.score_breakdown.authentication = 75
            self.score_breakdown.authorization = 80
    
    def _trace_data_flows(self):
        """Map input-to-storage data flows."""
        # Simple heuristic: API → Database is a critical flow
        api_files = [f for c in self.components if c.name == 'api' for f in c.files]
        db_files = [f for c in self.components if c.name == 'database' for f in c.files]
        critical_files = self.repo.get('critical_files', [])
        
        if api_files and db_files:
            for api_file in api_files[:3]:
                for db_file in db_files[:3]:
                    # Heuristic: validation presence in file path
                    has_validation = any(
                        kw in api_file.lower()
                        for kw in ['validate', 'check', 'sanitize', 'schema']
                    )
                    
                    risk = RiskLevel.LOW if has_validation else RiskLevel.CRITICAL
                    
                    flow = DataFlow(
                        source=api_file,
                        sink=db_file,
                        validation_present=has_validation,
                        risk_level=risk,
                        intermediate_steps=[],
                    )
                    self.data_flows.append(flow)
        
        # Check for critical file flows
        for crit_file in critical_files[:3]:
            if any('db' in crit_file.lower() or 'query' in crit_file.lower()):
                flow = DataFlow(
                    source='external_input',
                    sink=crit_file,
                    validation_present=False,
                    risk_level=RiskLevel.CRITICAL,
                )
                self.data_flows.append(flow)
    
    def _detect_privilege_issues(self):
        """Identify authorization boundary violations."""
        # Common privilege escalation patterns
        issues = []
        
        # Issue 1: Missing authentication on entry points
        unauthenticated = [ep for ep in self.entry_points if ep.auth_method is None]
        if unauthenticated:
            issue = PrivilegeIssue(
                component='entry_points',
                issue=f'{len(unauthenticated)} entry points lack authentication',
                severity=RiskLevel.CRITICAL,
                rationale='Unauthenticated access to public endpoints enables privilege escalation and unauthorized data access.',
                affected_entry_points=[ep.path for ep in unauthenticated],
                remediation_effort='low',
            )
            issues.append(issue)
        
        # Issue 2: Admin component without consistent checks
        admin_comps = [c for c in self.components if 'admin' in c.name.lower()]
        if admin_comps and any(ep.auth_method != 'jwt' for ep in self.entry_points):
            issue = PrivilegeIssue(
                component='admin',
                issue='Admin interface uses non-standard authentication',
                severity=RiskLevel.HIGH,
                rationale='Inconsistent authentication across admin endpoints may allow attackers to bypass access controls.',
                remediation_effort='medium',
            )
            issues.append(issue)
        
        # Issue 3: Data access without validation
        unvalidated_flows = [f for f in self.data_flows if not f.validation_present]
        if len(unvalidated_flows) > len(self.data_flows) / 2:
            issue = PrivilegeIssue(
                component='data_access',
                issue='Majority of data flows lack input validation',
                severity=RiskLevel.CRITICAL,
                rationale='Unvalidated inputs can be exploited for SQL injection, command injection, or other code execution attacks.',
                remediation_effort='high',
            )
            issues.append(issue)
        
        self.privilege_issues = issues
    
    def _generate_suggestions(self):
        """Create prioritized remediation recommendations."""
        suggestions = []
        
        # Suggestion 1: Add authentication
        if any(ep.auth_method is None for ep in self.entry_points):
            sugg = RefactorSuggestion(
                reason='Unauthenticated entry points expose the application to unauthorized access',
                recommendation='Apply authentication middleware to all public routes; use JWT tokens or OAuth2',
                impacted_files=[ep.path for ep in self.entry_points if ep.auth_method is None],
                code_example='@app.get("/api/data")\n@require_auth\ndef get_data(token: str = Header()): ...',
                severity=RiskLevel.CRITICAL,
                effort='low',
            )
            suggestions.append(sugg)
        
        # Suggestion 2: Add input validation
        if any(not f.validation_present for f in self.data_flows):
            sugg = RefactorSuggestion(
                reason='Unvalidated input flows create SQL injection and command injection vectors',
                recommendation='Implement parameterized queries and schema validation at controller boundaries',
                impacted_files=list(set(f.source for f in self.data_flows if not f.validation_present)),
                code_example='# Use ORM:\ndb.session.execute(select(User).where(User.id == int(user_id)))\n# NOT string interpolation',
                severity=RiskLevel.CRITICAL,
                effort='medium',
            )
            suggestions.append(sugg)
        
        # Suggestion 3: Fix privilege issues
        if self.privilege_issues:
            critical_issues = [p for p in self.privilege_issues if p.severity == RiskLevel.CRITICAL]
            if critical_issues:
                sugg = RefactorSuggestion(
                    reason=f'{len(critical_issues)} critical privilege issues detected',
                    recommendation='Implement role-based access control (RBAC) with consistent enforcement across all sensitive operations',
                    impacted_files=[],
                    code_example='@app.post("/admin/users")\n@require_role("admin")\ndef create_user(): ...',
                    severity=RiskLevel.CRITICAL,
                    effort='high',
                )
                suggestions.append(sugg)
        
        self.suggestions = suggestions
    
    def _score_files(self):
        """Rank individual files by risk profile."""
        file_scores: Dict[str, Tuple[int, List[str]]] = {}
        
        # Collect all files
        all_files = set()
        for f_list in self.repo.get('components', {}).values():
            all_files.update(f_list)
        for f in self.repo.get('critical_files', []):
            all_files.add(f)
        for ep in self.entry_points:
            all_files.add(ep.path)
        
        for file_path in all_files:
            score = 20  # baseline
            issues = []
            
            file_lower = file_path.lower()
            
            # Risk factors
            if any(kw in file_lower for kw in ['admin', 'auth', 'permission']):
                score += 25
                issues.append('Sensitive administrative or auth-related file')
            
            if any(kw in file_lower for kw in ['db', 'query', 'sql', 'migration']):
                score += 30
                issues.append('Data access layer — high impact if compromised')
                
                # Extra penalty if no validation in flows
                if any(not f.validation_present for f in self.data_flows):
                    score += 20
                    issues.append('Unvalidated data flows detected')
            
            if any(kw in file_lower for kw in ['secret', 'credential', 'token', 'key', 'password']):
                score += 40
                issues.append('Credential storage — critical exposure risk')
            
            if file_path in self.repo.get('entry_point_candidates', []):
                score += 20
                if not any(ep.path == file_path and ep.auth_method for ep in self.entry_points):
                    score += 15
                    issues.append('Unauthenticated entry point')
            
            score = min(score, 100)
            
            # Determine severity
            if score >= 80:
                severity = RiskLevel.CRITICAL
            elif score >= 60:
                severity = RiskLevel.HIGH
            elif score >= 40:
                severity = RiskLevel.MEDIUM
            else:
                severity = RiskLevel.LOW
            
            file_scores[file_path] = (score, issues, severity)
        
        # Create FileRisk objects for top 10 riskiest files
        self.file_risks = [
            FileRisk(
                path=path,
                risk_score=score,
                issues=issues,
                severity=severity,
                language=self._detect_language(path),
            )
            for path, (score, issues, severity) in sorted(
                file_scores.items(),
                key=lambda x: x[1][0],
                reverse=True
            )[:10]
        ]
    
    def _detect_language(self, file_path: str) -> str:
        """Infer programming language from file extension."""
        ext_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.rb': 'Ruby',
            '.php': 'PHP',
        }
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        return 'Unknown'
    
    def _compute_risk_scores(self):
        """Calculate multi-factor risk breakdown."""
        # Authentication risk: based on entry points without auth
        unauthenticated_count = sum(1 for ep in self.entry_points if ep.auth_method is None)
        total_endpoints = len(self.entry_points) if self.entry_points else 1
        auth_risk = int((unauthenticated_count / total_endpoints) * 100) if total_endpoints else 0
        self.score_breakdown.authentication = min(auth_risk + 20, 100)
        
        # Authorization risk: based on privilege issues
        authz_issues = [p for p in self.privilege_issues if 'privilege' in p.issue.lower() or 'auth' in p.issue.lower()]
        authz_risk = min(len(authz_issues) * 25 + 10, 100)
        self.score_breakdown.authorization = authz_risk
        
        # Input validation risk: based on unvalidated data flows
        total_flows = len(self.data_flows) if self.data_flows else 1
        unvalidated = sum(1 for f in self.data_flows if not f.validation_present)
        validation_risk = int((unvalidated / total_flows) * 100) if total_flows else 0
        self.score_breakdown.input_validation = min(validation_risk + 15, 100)
        
        # Data exposure risk: based on critical files
        critical_file_count = len(self.repo.get('critical_files', []))
        exposure_risk = min(critical_file_count * 15 + 10, 100)
        self.score_breakdown.data_exposure = exposure_risk
        
        # Dependency risk baseline until SBOM/CVE integration is added.
        self.score_breakdown.dependency_risk = 35
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize analysis to dictionary."""
        return {
            'components': [c.dict() for c in self.components],
            'entry_points': [ep.dict() for ep in self.entry_points],
            'data_flows': [df.dict() for df in self.data_flows],
            'privilege_issues': [pi.dict() for pi in self.privilege_issues],
            'suggestions': [s.dict() for s in self.suggestions],
            'file_risks': [fr.dict() for fr in self.file_risks],
            'score_breakdown': self.score_breakdown.dict(),
        }
