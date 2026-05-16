# Structured Bob prompts for ThreatLens AI

PROMPTS = {
    "architecture_mapping": (
        "Analyze the repository snapshot and list the major architectural components. "
        "For each component, provide: name, responsibilities, files involved, and external interfaces. "
        "Output JSON with key 'architecture' as a list of components."
    ),

    "entry_points": (
        "List all external-facing entry points (HTTP routes, CLI commands, cron, webhooks). "
        "For each entry point, include file path, handler function, input types, and expected auth. "
        "Output JSON with key 'entry_points'."
    ),

    "data_flow": (
        "Trace user-controlled input from entry points to persistent storage and critical sinks. "
        "For each trace include the path of files/functions, validation steps, and any missing checks. "
        "Output JSON with key 'data_flows'."
    ),

    "privilege_boundary": (
        "Identify modules that implement authentication/authorization and flag inconsistent enforcement. "
        "Report potential privilege escalation paths and cross-module trust assumptions. "
        "Output JSON with key 'privilege_issues'."
    ),

    "risk_summary": (
        "Summarize findings into severity categories (critical/medium/low) and provide refactor suggestions. "
        "Each suggestion should include reason, impacted files, and a sample remediation snippet where possible. "
        "Output JSON with key 'suggestions'."
    ),
}
