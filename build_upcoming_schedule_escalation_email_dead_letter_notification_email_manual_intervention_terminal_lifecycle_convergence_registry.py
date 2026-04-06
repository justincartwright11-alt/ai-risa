"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_terminal_lifecycle_convergence_registry.py

v77.7: Terminal lifecycle convergence registry.
Reads the latest frozen delivery summary, reconciled dispatch, and reconciliation audit, and emits a canonical terminal registry per root operator case (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Input artifacts
DELIVERY_SUMMARY_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_delivery_summary.json")
RECONCILED_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_dispatch_reconciled.json")
RECONCILIATION_AUDIT_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_completion_finalization_completion_finalization_completion_dispatch_reconciliation_audit.json")

# Output artifacts
TERMINAL_REGISTRY_JSON = Path("ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_convergence_registry.json")
TERMINAL_REGISTRY_MD = Path("ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_convergence_registry.md")

def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_terminal_registry(delivery_summary, reconciled_dispatch, reconciliation_audit) -> List[Dict[str, Any]]:
    registry = []
    # Defensive: if no delivery summary, nothing to do
    if not delivery_summary or not delivery_summary.get("finalization_items_queued"):
        return []
    # For demo, assume one root case per dedupe_key in reconciled_dispatch
    seen = set()
    for rec in reconciled_dispatch:
        dedupe_key = rec["dedupe_key"]
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        root_case_id = rec["completion_queue_item_id"]
        # Determine terminal state
        if rec.get("dispatch_state") == "success":
            terminal_state = "terminal-success"
            terminal_reason = "Completion dispatched and reconciled successfully."
            manual_override_required = False
            open_dependency_count = 0
            next_action = None
        elif rec.get("dispatch_state") == "failure":
            terminal_state = "terminal-failure"
            terminal_reason = "Completion dispatch failed. Manual intervention required."
            manual_override_required = True
            open_dependency_count = 0
            next_action = "manual-override"
        else:
            terminal_state = "open-blocked"
            terminal_reason = "Completion not terminal; dependency or reconciliation incomplete."
            manual_override_required = False
            open_dependency_count = 1
            next_action = "await-dependency"
        registry.append({
            "terminal_registry_item_id": f"TRID-{root_case_id}",
            "root_case_id": root_case_id,
            "latest_branch_stage": "completion-dispatch-reconciled",
            "terminal_state": terminal_state,
            "terminal_reason": terminal_reason,
            "manual_override_required": manual_override_required,
            "open_dependency_count": open_dependency_count,
            "last_successful_artifact_family": "completion-dispatch-reconciled" if terminal_state == "terminal-success" else None,
            "next_action": next_action,
            "dedupe_key": dedupe_key
        })
    return registry

def deterministic_sort(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def sort_key(item):
        return (
            item.get("root_case_id", "")
        )
    return sorted(records, key=sort_key)

def write_json(records: List[Dict[str, Any]]):
    with open(TERMINAL_REGISTRY_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def write_md(records: List[Dict[str, Any]]):
    with open(TERMINAL_REGISTRY_MD, "w", encoding="utf-8") as f:
        f.write(f"# Terminal Lifecycle Convergence Registry\n\n")
        if not records:
            f.write("_No terminal registry items._\n")
            return
        for rec in records:
            f.write(f"- **Terminal Registry Item ID:** {rec['terminal_registry_item_id']}\n")
            f.write(f"  - Root Case ID: {rec['root_case_id']}\n")
            f.write(f"  - Latest Branch Stage: {rec['latest_branch_stage']}\n")
            f.write(f"  - Terminal State: {rec['terminal_state']}\n")
            f.write(f"  - Terminal Reason: {rec['terminal_reason']}\n")
            f.write(f"  - Manual Override Required: {rec['manual_override_required']}\n")
            f.write(f"  - Open Dependency Count: {rec['open_dependency_count']}\n")
            f.write(f"  - Last Successful Artifact Family: {rec['last_successful_artifact_family']}\n")
            f.write(f"  - Next Action: {rec['next_action']}\n")
            f.write(f"  - Dedupe Key: {rec['dedupe_key']}\n")
            f.write("\n")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    delivery_summary = load_json(DELIVERY_SUMMARY_JSON)
    reconciled_dispatch = load_json(RECONCILED_DISPATCH_JSON) or []
    reconciliation_audit = load_json(RECONCILIATION_AUDIT_JSON) or []
    registry = build_terminal_registry(delivery_summary, reconciled_dispatch, reconciliation_audit)
    registry = deterministic_sort(registry)
    write_json(registry)
    write_md(registry)
    print(f"Wrote terminal lifecycle convergence registry.")
    print(f"SHA256 (JSON): {sha256_file(TERMINAL_REGISTRY_JSON)}")
    print(f"SHA256 (MD):   {sha256_file(TERMINAL_REGISTRY_MD)}")

if __name__ == "__main__":
    main()
