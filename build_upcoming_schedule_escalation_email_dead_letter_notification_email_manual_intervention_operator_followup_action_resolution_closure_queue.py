"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_operator_followup_action_resolution_closure_queue.py

v74.7: Build deterministic operator follow-up action resolution closure queue.
Reads the frozen v74.6 summary and emits canonical closure queue artifacts (JSON/MD).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Input: v74.6 summary artifact
SUMMARY_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_delivery_summary.json")
# Outputs: v74.7 closure queue artifacts
CLOSURE_QUEUE_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_queue.json")
CLOSURE_QUEUE_MD = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_closure_queue.md")

CLOSURE_PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}
CLOSURE_STATE_ORDER = {"completed-success": 0, "pending-close": 1}

REQUIRED_FIELDS = [
    "closure_queue_item_id",
    "resolution_queue_item_id",
    "resolution_dispatch_id",
    "dispatch_target",
    "delivery_state",
    "closure_state",
    "closure_priority",
    "next_closure_action",
    "closure_reason",
    "dedupe_key",
]


def load_summary_object() -> Dict[str, Any]:
    if not SUMMARY_JSON.exists():
        return {}
    with open(SUMMARY_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

# Fallback sources for closure candidates
RECONCILED_DISPATCH_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch_reconciled.json")
RECONCILIATION_AUDIT_JSON = Path("ops/events/upcoming_schedule_manual_intervention_operator_followup_action_resolution_dispatch_reconciliation_audit.json")

def extract_closure_candidates_from_summary(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    # If summary contains an explicit item array, use it
    for key in ("closure_candidates", "items", "records", "candidates"):
        if key in summary and isinstance(summary[key], list):
            return summary[key]
    return []

def load_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Try to extract a list from a known key
            for key in ("items", "records", "candidates"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []

def derive_closure_candidates_from_reconciled_dispatch() -> List[Dict[str, Any]]:
    # Use reconciled dispatch and audit to find closure-eligible items
    dispatches = load_json_array(RECONCILED_DISPATCH_JSON)
    audits = load_json_array(RECONCILIATION_AUDIT_JSON)
    # Build lookup for audit by dispatch id
    audit_by_dispatch = {a.get("resolution_dispatch_id"): a for a in audits}
    candidates = []
    for d in dispatches:
        audit = audit_by_dispatch.get(d.get("resolution_dispatch_id"))
        if not audit:
            continue
        # Closure eligibility: delivered-success, reconciliation complete, no unresolved/failure/block
        if (
            d.get("delivery_state") == "delivered-success"
            and audit.get("reconciliation_state") == "reconciled-complete"
            and not d.get("blocked", False)
            and not d.get("failed", False)
            and not d.get("unresolved", False)
            and not d.get("has_open_dependency", False)
        ):
            # Merge fields from both sources for output
            merged = {**d, **audit}
            candidates.append(merged)
    return candidates

def is_closure_eligible(item: Dict[str, Any]) -> bool:
    # Only include items that are closure-eligible
    # Example logic: delivered successfully, reconciliation complete, no outstanding work, no blocked/failed/unresolved
    return (
        item.get("delivery_state") == "delivered-success"
        and item.get("closure_state") in ("completed-success", "pending-close")
        and not item.get("blocked", False)
        and not item.get("failed", False)
        and not item.get("unresolved", False)
        and not item.get("has_open_dependency", False)
    )

def build_closure_queue(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    queue = []
    seen_dedupe = set()
    for item in records:
        if not is_closure_eligible(item):
            continue
        dedupe_key = item["dedupe_key"]
        if dedupe_key in seen_dedupe:
            continue
        seen_dedupe.add(dedupe_key)
        # Deterministic closure_queue_item_id: SHA256 of dedupe_key
        import hashlib
        closure_queue_item_id = hashlib.sha256(dedupe_key.encode("utf-8")).hexdigest()
        queue_item = {field: item.get(field) for field in REQUIRED_FIELDS}
        queue_item["closure_queue_item_id"] = closure_queue_item_id
        queue.append(queue_item)
    # Deterministic ordering
    queue.sort(key=lambda x: (
        CLOSURE_PRIORITY_ORDER.get(x["closure_priority"], 99),
        CLOSURE_STATE_ORDER.get(x["closure_state"], 99),
        x["resolution_queue_item_id"],
        x["dispatch_target"]
    ))
    return queue

def write_json(queue: List[Dict[str, Any]]):
    with open(CLOSURE_QUEUE_JSON, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

def write_md(queue: List[Dict[str, Any]]):
    with open(CLOSURE_QUEUE_MD, "w", encoding="utf-8") as f:
        f.write(f"# Operator Follow-Up Action Resolution Closure Queue\n\n")
        if not queue:
            f.write("_No closure-eligible items found._\n")
            return
        headers = REQUIRED_FIELDS
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "---|" * len(headers) + "\n")
        for item in queue:
            row = [str(item.get(h, "")) for h in headers]
            f.write("| " + " | ".join(row) + " |\n")

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
    summary = load_summary_object()
    # Try to extract closure candidates from summary
    candidates = extract_closure_candidates_from_summary(summary)
    # If not found, derive from reconciled dispatch and audit
    if not candidates:
        candidates = derive_closure_candidates_from_reconciled_dispatch()
    # If still none, default to empty
    queue = build_closure_queue(candidates or [])
    write_json(queue)
    write_md(queue)
    print(f"Wrote {len(queue)} closure-eligible items.")
    print(f"SHA256 (JSON): {sha256_file(CLOSURE_QUEUE_JSON)}")
    print(f"SHA256 (MD):   {sha256_file(CLOSURE_QUEUE_MD)}")

if __name__ == "__main__":
    main()
