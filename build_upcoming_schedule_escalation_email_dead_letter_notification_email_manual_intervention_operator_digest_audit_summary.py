"""
v73.2-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-operator-digest-audit-summary
Deterministic operator digest and audit summary. Pure reporting slice.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# === 1. Constants/Paths ===
RECONCILED_LEDGER_PATH = "ops/events/upcoming_schedule_manual_intervention_resolution_ledger_reconciled.json"
RECONCILIATION_AUDIT_PATH = "ops/events/upcoming_schedule_manual_intervention_resolution_reconciliation_audit.json"
RETRY_OUTCOME_PATH = "ops/events/upcoming_schedule_manual_intervention_retry_requeue_outcome_ledger.json"
RETRY_EXECUTOR_PATH = "ops/events/upcoming_schedule_manual_intervention_retry_requeue_executor.json"
REMINDER_PROJECTION_PATH = "ops/events/upcoming_schedule_manual_intervention_reminder_projection.json"
DIGEST_JSON_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_digest.json"
DIGEST_MD_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_digest.md"

# === 2. Load Artifacts ===
def load_json(path: str) -> Any:
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# === 3. Digest Computation ===
def compute_digest(ledger, reminder, executor, outcome, reconciliation):
    now = datetime.utcnow().isoformat() + "Z"
    # Totals by state
    totals = {}
    for c in ledger:
        state = c.get("resolution_state", "unknown")
        totals[state] = totals.get(state, 0) + 1
    # Open unresolved queue
    open_cases = [c for c in ledger if c.get("resolution_state") not in ("resolved_no_retry", "resolved", "closed")]
    # Breached/stale queue (from reminder projection if available)
    breached = [r for r in reminder if r.get("reminder_state") == "breached"] if reminder else []
    # Retry execution summary
    retry_execs = len(executor)
    # Retry outcome summary
    retry_success = sum(1 for o in outcome if o.get("result_state") == "success")
    retry_failed = sum(1 for o in outcome if o.get("result_state") == "failed")
    retry_blocked = sum(1 for o in outcome if o.get("result_state") in ("blocked", "skipped"))
    # Reconciliation summary
    reconciled = len(reconciliation)
    # Next-action queue: open, not resolved, not executed
    next_action = [c for c in open_cases if c.get("retry_state") != "executed"]
    return {
        "generated_at": now,
        "totals_by_state": totals,
        "open_unresolved_queue": [c["resolution_case_id"] for c in open_cases],
        "breached_queue": [r.get("resolution_case_id") for r in breached],
        "retry_execution_count": retry_execs,
        "retry_success_count": retry_success,
        "retry_failed_count": retry_failed,
        "retry_blocked_count": retry_blocked,
        "reconciliation_count": reconciled,
        "next_action_queue": [c["resolution_case_id"] for c in next_action],
    }

# === 4. Write Outputs ===
def write_json(path: str, obj: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_markdown(path: str, digest: Dict[str, Any]):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Manual-Intervention Operator Digest / Audit Summary\n\n")
        f.write(f"_Generated: {digest['generated_at']}_\n\n")
        f.write(f"## Totals by State\n")
        for k, v in digest["totals_by_state"].items():
            f.write(f"- {k}: {v}\n")
        f.write(f"\n## Open Unresolved Queue\n")
        for cid in digest["open_unresolved_queue"]:
            f.write(f"- {cid}\n")
        f.write(f"\n## Breached / Stale Queue\n")
        for cid in digest["breached_queue"]:
            f.write(f"- {cid}\n")
        f.write(f"\n## Retry Execution Summary\n")
        f.write(f"- Total Executions: {digest['retry_execution_count']}\n")
        f.write(f"- Success: {digest['retry_success_count']}\n")
        f.write(f"- Failed: {digest['retry_failed_count']}\n")
        f.write(f"- Blocked/Skipped: {digest['retry_blocked_count']}\n")
        f.write(f"\n## Reconciliation Summary\n")
        f.write(f"- Total Reconciliations: {digest['reconciliation_count']}\n")
        f.write(f"\n## Next-Action Queue\n")
        for cid in digest["next_action_queue"]:
            f.write(f"- {cid}\n")

# === 5. Entrypoint ===
def main():
    ledger = load_json(RECONCILED_LEDGER_PATH)
    reminder = load_json(REMINDER_PROJECTION_PATH)
    executor = load_json(RETRY_EXECUTOR_PATH)
    outcome = load_json(RETRY_OUTCOME_PATH)
    reconciliation = load_json(RECONCILIATION_AUDIT_PATH)
    digest = compute_digest(ledger, reminder, executor, outcome, reconciliation)
    write_json(DIGEST_JSON_PATH, digest)
    write_markdown(DIGEST_MD_PATH, digest)

if __name__ == "__main__":
    main()
