# AI-RISA Operator Runtime Runbook

## Official Operator Interface

**The Operator Dashboard is the only approved interface for local agent operations.**

### Launching the Dashboard
1. Start the dashboard using the provided launch script or shortcut.
2. Access the dashboard in your browser at the designated local address (e.g., http://localhost:5000).

### Running Local Agent Tasks
- Use the dashboard controls to:
  - Plan and execute agent tasks
  - Manage the event queue
  - Review and download artifacts
  - Monitor agent status and logs

### Acceptance and Regression Testing
- All validation must be performed through the dashboard interface.
- Use the dashboard's test/run controls for acceptance tests.

### Maintenance and Hotfixes
- For code changes, follow standard maintenance/hotfix branch discipline.
- After any update, validate all paths via the dashboard before operator use.

---

**Direct script or CLI use is no longer supported for operator actions.**
