"""
v73.1-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-resolution-ledger-reconciler
Deterministic reconciler: applies settled retry outcomes to the canonical resolution ledger.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# === 1. Constants/Paths ===
V72_7_LEDGER_PATH = "ops/events/upcoming_schedule_manual_intervention_resolution_ledger.json"
V73_0_OUTCOME_PATH = "ops/events/upcoming_schedule_manual_intervention_retry_requeue_outcome_ledger.json"
V73_1_RECONCILED_LEDGER_PATH = "ops/events/upcoming_schedule_manual_intervention_resolution_ledger_reconciled.json"
V73_1_RECONCILIATION_AUDIT_JSON = "ops/events/upcoming_schedule_manual_intervention_resolution_reconciliation_audit.json"
V73_1_RECONCILIATION_AUDIT_MD = "ops/events/upcoming_schedule_manual_intervention_resolution_reconciliation_audit.md"

TERMINAL_RESULTS = {"success", "failed", "skipped", "blocked"}

# === 2. Reconciliation Rules ===
def reconcile_case(case: Dict[str, Any], outcome: Dict[str, Any]) -> Dict[str, Any]:
    prior = case.copy()
    new = case.copy()
    # Only apply if outcome is terminal and matches case
    if outcome["result_state"] == "success":
        new["retry_state"] = "executed"
        new["resolution_state"] = "resolved_no_retry"
        # Optionally auto-close if policy allows (not default)
    elif outcome["result_state"] == "failed":
        new["retry_state"] = "blocked"
        # resolution_state remains unchanged
    # skipped/blocked: no-op
    return prior, new

# === 3. Load Ledgers ===
def load_json(path: str) -> Any:
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# === 4. Build Outcome-to-Case Matching ===
def match_outcomes_to_cases(ledger: List[Dict[str, Any]], outcomes: List[Dict[str, Any]]):
    case_map = {c["resolution_case_id"]: c for c in ledger}
    matches = []
    for o in outcomes:
        if o["result_state"] in TERMINAL_RESULTS and o["resolution_case_id"] in case_map:
            matches.append((case_map[o["resolution_case_id"]], o))
    return matches

# === 5. Suppress Already-Applied Reconciliations ===
def already_applied(case: Dict[str, Any], outcome: Dict[str, Any]) -> bool:
    # Simple check: if retry_state/resolution_state already match outcome, skip
    if outcome["result_state"] == "success":
        return case.get("retry_state") == "executed" and case.get("resolution_state") == "resolved_no_retry"
    elif outcome["result_state"] == "failed":
        return case.get("retry_state") == "blocked"
    return True  # skipped/blocked: always no-op

# === 6. Apply State Transitions and Build Audit ===
def apply_reconciliation(ledger: List[Dict[str, Any]], outcomes: List[Dict[str, Any]]):
    audit = []
    now = datetime.utcnow().isoformat() + "Z"
    for case, outcome in match_outcomes_to_cases(ledger, outcomes):
        if already_applied(case, outcome):
            continue
        prior, new = reconcile_case(case, outcome)
        # Update ledger in place
        idx = ledger.index(case)
        ledger[idx] = new
        audit.append({
            "reconciliation_action_id": hashlib.sha256(f"{outcome['retry_execution_outcome_id']}|{now}".encode()).hexdigest()[:16],
            "resolution_case_id": case["resolution_case_id"],
            "retry_execution_outcome_id": outcome["retry_execution_outcome_id"],
            "retry_execution_id": outcome["retry_execution_id"],
            "attempt_number": outcome["attempt_number"],
            "prior_resolution_state": prior.get("resolution_state"),
            "new_resolution_state": new.get("resolution_state"),
            "prior_retry_state": prior.get("retry_state"),
            "new_retry_state": new.get("retry_state"),
            "prior_closure_state": prior.get("closure_state"),
            "new_closure_state": new.get("closure_state"),
            "applied_at": now,
            "reconciliation_result": "applied"
        })
    return ledger, audit

# === 7. Validate Ledger Invariants ===
def validate_ledger(ledger: List[Dict[str, Any]]):
    seen = set()
    for c in ledger:
        cid = c["resolution_case_id"]
        assert cid not in seen, f"Duplicate case ID: {cid}"
        seen.add(cid)
        # Add more invariants as needed

# === 8. Write Outputs ===
def write_json(path: str, records: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_markdown(path: str, audit: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Manual-Intervention Resolution Reconciliation Audit\n\n")
        f.write(f"_Generated: {datetime.utcnow().isoformat()}Z_\n\n")
        for a in audit:
            f.write(f"- **Action ID:** {a['reconciliation_action_id']}\n")
            f.write(f"  - Case: `{a['resolution_case_id']}` | Outcome: `{a['retry_execution_outcome_id']}`\n")
            f.write(f"  - Attempt: {a['attempt_number']} | Applied: {a['applied_at']}\n")
            f.write(f"  - Resolution: {a['prior_resolution_state']} → {a['new_resolution_state']}\n")
            f.write(f"  - Retry: {a['prior_retry_state']} → {a['new_retry_state']}\n")
            f.write(f"  - Closure: {a['prior_closure_state']} → {a['new_closure_state']}\n")
            f.write(f"  - Result: {a['reconciliation_result']}\n\n")

# === 9. Entrypoint ===
def main():
    ledger = load_json(V72_7_LEDGER_PATH)
    outcomes = load_json(V73_0_OUTCOME_PATH)
    orig_ledger = [c.copy() for c in ledger]
    ledger, audit = apply_reconciliation(ledger, outcomes)
    validate_ledger(ledger)
    write_json(V73_1_RECONCILED_LEDGER_PATH, ledger)
    write_json(V73_1_RECONCILIATION_AUDIT_JSON, audit)
    write_markdown(V73_1_RECONCILIATION_AUDIT_MD, audit)

if __name__ == "__main__":
    main()
