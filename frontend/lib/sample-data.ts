// Sample analysis payload used when live backend results are unavailable.
export const sampleAnalysisResult = {
  session_id: 'sample-001',
  repo_url: 'https://github.com/example/vulnerable-app',
  score: 72,
  score_breakdown: {
    authentication: 68,
    authorization: 81,
    input_validation: 55,
    data_exposure: 74,
    dependency_risk: 62,
  },
  architecture: [
    { name: 'web', files: ['app.py', 'routes.py'], desc: 'HTTP layer', risk_level: 'high' },
    { name: 'auth', files: ['auth.py', 'session.py'], desc: 'Authentication module', risk_level: 'medium' },
    { name: 'db', files: ['db.py', 'models.py'], desc: 'Data access layer', risk_level: 'critical' },
    { name: 'admin', files: ['admin.py'], desc: 'Admin panel', risk_level: 'critical' },
  ],
  entry_points: [
    { path: 'routes.py', handler: 'login_handler', auth: 'cookie', risk_level: 'high' },
    { path: 'routes.py', handler: 'admin_view', auth: 'none', risk_level: 'critical' },
    { path: 'api/users.py', handler: 'list_users', auth: 'jwt', risk_level: 'medium' },
  ],
  data_flows: [
    { from: 'routes.py', to: 'db.py', validation: false, risk_level: 'critical' },
    { from: 'api/users.py', to: 'db.py', validation: true, risk_level: 'low' },
    { from: 'admin.py', to: 'db.py', validation: false, risk_level: 'critical' },
  ],
  privilege_issues: [
    {
      component: 'admin.py',
      issue: 'Inconsistent authorization checks — admin endpoints accessible without role verification',
      severity: 'critical',
      rationale: 'An unauthenticated caller can invoke admin endpoints directly. Privilege escalation is trivially achievable.',
    },
    {
      component: 'session.py',
      issue: 'Session tokens are not rotated after privilege elevation',
      severity: 'high',
      rationale: 'Stolen pre-elevation token retains elevated access indefinitely.',
    },
  ],
  suggestions: [
    {
      why: 'Unvalidated input flows directly into SQL query constructor in db.py',
      fix: 'Add parameterized queries via SQLAlchemy ORM; reject requests that fail schema validation at the controller boundary',
      files: ['routes.py', 'db.py'],
      code_snippet:
        "# Before\nquery = f'SELECT * FROM users WHERE id={user_id}'\n# After\nquery = db.session.execute(select(User).where(User.id == user_id))",
      severity: 'critical',
      effort: 'low',
    },
    {
      why: 'Admin view has no authentication decorator — any unauthenticated request will succeed',
      fix: "Apply @require_role('admin') decorator to all /admin/* route handlers",
      files: ['admin.py'],
      code_snippet: "@app.route('/admin/users')\n@require_role('admin')\n def admin_users(): ...",
      severity: 'critical',
      effort: 'low',
    },
    {
      why: 'Session fixation: token is not regenerated after login',
      fix: 'Call session.regenerate() after successful authentication to invalidate the pre-auth token',
      files: ['session.py'],
      severity: 'high',
      effort: 'low',
    },
  ],
  file_risks: [
    { path: 'admin.py', risk_score: 95, issues: ['No authentication on admin routes', 'Direct DB writes without validation'], severity: 'critical' },
    { path: 'db.py', risk_score: 88, issues: ['Raw SQL string formatting', 'No query parameter sanitization'], severity: 'critical' },
    { path: 'routes.py', risk_score: 72, issues: ['Cookie-based auth without SameSite flag', 'Missing CSRF protection'], severity: 'high' },
    { path: 'session.py', risk_score: 65, issues: ['No session rotation on elevation', 'Weak token entropy'], severity: 'high' },
    { path: 'app.py', risk_score: 40, issues: ['Debug mode may be enabled in production'], severity: 'medium' },
  ],
  created_at: '2025-05-16T10:30:00Z',
}

export const sampleLogs = [
  { ts: new Date().toISOString(), level: 'info', message: 'Initializing clone routine...' },
  { ts: new Date().toISOString(), level: 'debug', message: 'Target: vulnerable-app' },
  { ts: new Date().toISOString(), level: 'info', message: 'Running static AST generation...' },
  { ts: new Date().toISOString(), level: 'warn', message: 'Detected high-entropy strings in history' },
]
