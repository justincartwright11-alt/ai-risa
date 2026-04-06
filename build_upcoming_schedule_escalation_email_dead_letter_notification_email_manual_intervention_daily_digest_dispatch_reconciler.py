"""
v73.5-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-daily-digest-dispatch-reconciler
Deterministic reconciler: applies settled delivery outcomes to the daily digest dispatch artifact.
"""

import json
import hashlib
from typing import List, Dict, Any

# === 4. Build Outcome-to-Dispatch Matching ===
def match_outcomes_to_dispatch(dispatches: List[Dict[str, Any]], outcomes: List[Dict[str, Any]]):
    
    dispatch_map = {d["digest_dispatch_id"]: d for d in dispatches}
    matches = []
    for o in outcomes:
        if o["delivery_state"] in TERMINAL_DELIVERY_STATES and o["digest_dispatch_id"] in dispatch_map:
            matches.append((dispatch_map[o["digest_dispatch_id"]], o))
    return matches

# === 5. Suppress Already-Applied Reconciliations ===
def already_applied(dispatch: Dict[str, Any], outcome: Dict[str, Any]) -> bool:
    if outcome["delivery_state"] == "sent":
        return dispatch.get("dispatch_state") == "delivered"
    elif outcome["delivery_state"] == "failed":
        return dispatch.get("dispatch_state") == "delivery_failed"
    return True  # skipped/blocked: always no-op
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# === 1. Constants/Paths ===
DELIVERY_OUTCOME_PATH = "ops/events/upcoming_schedule_manual_intervention_daily_digest_delivery_outcome_ledger.json"
DISPATCH_PATH = "ops/events/upcoming_schedule_manual_intervention_daily_digest_dispatch.json"
RECONCILED_DISPATCH_JSON = "ops/events/upcoming_schedule_manual_intervention_daily_digest_dispatch_reconciled.json"
RECONCILED_DISPATCH_MD = "ops/events/upcoming_schedule_manual_intervention_daily_digest_dispatch_reconciled.md"
RECONCILIATION_AUDIT_JSON = "ops/events/upcoming_schedule_manual_intervention_daily_digest_dispatch_reconciliation_audit.json"
RECONCILIATION_AUDIT_MD = "ops/events/upcoming_schedule_manual_intervention_daily_digest_dispatch_reconciliation_audit.md"

TERMINAL_DELIVERY_STATES = {"sent", "failed", "skipped", "blocked"}

# === 2. Reconciliation Rules ===
def reconcile_dispatch(dispatch: Dict[str, Any], outcome: Dict[str, Any]) -> Dict[str, Any]:
    prior = dispatch.copy()
    new = dispatch.copy()
    # Only apply if outcome is terminal and matches dispatch
    if outcome["delivery_state"] == "sent":
        new["dispatch_state"] = "delivered"
    elif outcome["delivery_state"] == "failed":
        new["dispatch_state"] = "delivery_failed"
    # skipped/blocked: no-op
    return prior, new

# === 3. Load Artifacts ===
def load_json(path: str) -> Any:
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)


def write_audit_markdown(path: str, audit: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Daily Digest Dispatch Reconciliation Audit\n\n")
        f.write(f"_Generated: {datetime.utcnow().isoformat()}Z_\n\n")
        if not audit:
            f.write("_No reconciliation actions applied in this run._\n")
        else:
            for a in audit:
                f.write(f"- **Action ID:** {a['reconciliation_action_id']}\n")
                f.write(f"  - Dispatch: `{a['digest_dispatch_id']}` | Outcome: `{a['digest_delivery_outcome_id']}`\n")
                f.write(f"  - Attempt: {a['attempt_number']} | Applied: {a['applied_at']}\n")
                f.write(f"  - Dispatch State: {a['prior_dispatch_state']} → {a['new_dispatch_state']}\n")
                f.write(f"  - Result: {a['reconciliation_result']}\n\n")

def write_dispatch_markdown(path: str, dispatches: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Daily Digest Dispatch (Reconciled)\n\n")
        f.write(f"_Generated: {datetime.utcnow().isoformat()}Z_\n\n")
        if not dispatches:
            f.write("_No dispatch records in this run._\n")
        else:
            for d in dispatches:
                f.write(f"- **Dispatch ID:** {d['digest_dispatch_id']}\n")
                f.write(f"  - Date: {d['digest_date']} | Target: {d['dispatch_target']}\n")
                f.write(f"  - State: {d['dispatch_state']} | Suppression: {d.get('suppression_reason')}\n")
                f.write(f"  - Totals: {d.get('summary_totals')}\n")
                f.write(f"  - Created: {d.get('created_at')} | Updated: {d.get('updated_at')}\n\n")

# === 6. Apply State Transitions and Build Audit ===
def apply_reconciliation(dispatches: List[Dict[str, Any]], outcomes: List[Dict[str, Any]]):
    audit = []
    now = datetime.utcnow().isoformat() + "Z"
    for dispatch, outcome in match_outcomes_to_dispatch(dispatches, outcomes):
        if already_applied(dispatch, outcome):
            continue
        prior, new = reconcile_dispatch(dispatch, outcome)
        idx = dispatches.index(dispatch)
        dispatches[idx] = new
        audit.append({
            "reconciliation_action_id": hashlib.sha256(f"{outcome['digest_delivery_outcome_id']}|{now}".encode()).hexdigest()[:16],
            "digest_dispatch_id": dispatch["digest_dispatch_id"],
            "digest_delivery_outcome_id": outcome["digest_delivery_outcome_id"],
            "digest_date": dispatch["digest_date"],
            "dispatch_target": dispatch["dispatch_target"],
            "attempt_number": outcome["attempt_number"],
            "prior_dispatch_state": prior.get("dispatch_state"),
            "new_dispatch_state": new.get("dispatch_state"),
            "applied_at": now,
            "reconciliation_result": "applied"
        })
    return dispatches, audit

# === 7. Validate Dispatch Invariants ===
def validate_dispatches(dispatches: List[Dict[str, Any]]):
    seen = set()
    for d in dispatches:
        did = d["digest_dispatch_id"]
        assert did not in seen, f"Duplicate dispatch ID: {did}"
        seen.add(did)
        # Add more invariants as needed

# === 8. Write Outputs ===
def write_json(path: str, records: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_markdown(path: str, audit: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Daily Digest Dispatch Reconciliation Audit\n\n")
        f.write(f"_Generated: {datetime.utcnow().isoformat()}Z_\n\n")
        if not audit:
            f.write("_No reconciliation actions applied in this run._\n")
        else:
            for a in audit:
                f.write(f"- **Action ID:** {a['reconciliation_action_id']}\n")
                f.write(f"  - Dispatch: `{a['digest_dispatch_id']}` | Outcome: `{a['digest_delivery_outcome_id']}`\n")
                f.write(f"  - Attempt: {a['attempt_number']} | Applied: {a['applied_at']}\n")
                f.write(f"  - Dispatch State: {a['prior_dispatch_state']} → {a['new_dispatch_state']}\n")
                f.write(f"  - Result: {a['reconciliation_result']}\n\n")

    def write_dispatch_markdown(path: str, dispatches: List[Dict[str, Any]]):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# Daily Digest Dispatch (Reconciled)\n\n")
            f.write(f"_Generated: {datetime.utcnow().isoformat()}Z_\n\n")
            if not dispatches:
                f.write("_No dispatch records in this run._\n")
            else:
                for d in dispatches:
                    f.write(f"- **Dispatch ID:** {d['digest_dispatch_id']}\n")
                    f.write(f"  - Date: {d['digest_date']} | Target: {d['dispatch_target']}\n")
                    f.write(f"  - State: {d['dispatch_state']} | Suppression: {d.get('suppression_reason')}\n")
                    f.write(f"  - Totals: {d.get('summary_totals')}\n")
                    f.write(f"  - Created: {d.get('created_at')} | Updated: {d.get('updated_at')}\n\n")


# === 9. Entrypoint ===
def main():
    dispatches = load_json(DISPATCH_PATH)
    outcomes = load_json(DELIVERY_OUTCOME_PATH)
    orig_dispatches = [d.copy() for d in dispatches]
    dispatches, audit = apply_reconciliation(dispatches, outcomes)
    validate_dispatches(dispatches)
    write_json(RECONCILED_DISPATCH_JSON, dispatches)
    write_dispatch_markdown(RECONCILED_DISPATCH_MD, dispatches)
    write_json(RECONCILIATION_AUDIT_JSON, audit)
    write_audit_markdown(RECONCILIATION_AUDIT_MD, audit)

if __name__ == "__main__":
    main()
