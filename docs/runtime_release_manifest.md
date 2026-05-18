# AI-RISA Local Operator Runtime Release Manifest

## Official Operator Interface

**The AI-RISA Operator Dashboard is now the approved and official interface for all local operator actions.**

- All local agent operations (plan, execute, queue management, artifact review) must be performed via the dashboard.
- The legacy CLI and direct script invocation paths are deprecated for operator use.
- All acceptance, regression, and manual validation must be performed through the dashboard interface.

## Release Notes
- Dashboard interface validated and production-ready.
- Queue acknowledgment bug fixed and merged.
- All acceptance tests pass (see tests/operator_acceptance.py).
- Controlled release discipline enforced.

## Operator Instructions
- Launch the dashboard and use its controls for all local agent operations.
- Refer to the runbook for step-by-step dashboard usage.
- For maintenance or hotfixes, follow standard branch/tag discipline.

---

**This manifest supersedes all prior operator interface instructions.**
