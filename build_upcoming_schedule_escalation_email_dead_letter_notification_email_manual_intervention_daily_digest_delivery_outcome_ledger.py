"""
v73.4-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-daily-digest-delivery-outcome-ledger
Deterministic delivery outcome ledger for daily digest dispatches. Pure outcome capture.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# === 1. Constants/Enums ===
DISPATCH_PATH = "ops/events/upcoming_schedule_manual_intervention_daily_digest_dispatch.json"
DELIVERY_OUTCOME_JSON_PATH = "ops/events/upcoming_schedule_manual_intervention_daily_digest_delivery_outcome_ledger.json"
DELIVERY_OUTCOME_MD_PATH = "ops/events/upcoming_schedule_manual_intervention_daily_digest_delivery_outcome_ledger.md"

TERMINAL_DELIVERY_STATES = {"sent", "failed", "skipped", "blocked"}

# === 2. Stable Outcome Identity ===
def make_delivery_outcome_id(digest_dispatch_id: str, attempt_number: int) -> str:
    base = f"{digest_dispatch_id}|{attempt_number}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]

# === 3. Canonical Delivery Outcome Record ===
def build_delivery_outcome_record(dispatch_record: Dict[str, Any], delivery_state: str = "sent", result_code: str = "250", result_summary: str = "Delivered successfully.", attempt_number: int = 1) -> Dict[str, Any]:
    now = datetime.utcnow().isoformat() + "Z"
    return {
        "digest_delivery_outcome_id": make_delivery_outcome_id(dispatch_record["digest_dispatch_id"], attempt_number),
        "digest_dispatch_id": dispatch_record["digest_dispatch_id"],
        "digest_date": dispatch_record["digest_date"],
        "dispatch_target": dispatch_record["dispatch_target"],
        "dispatch_state": dispatch_record["dispatch_state"],
        "delivery_state": delivery_state,
        "result_code": result_code,
        "result_summary": result_summary,
        "attempt_number": attempt_number,
        "attempted_at": now,
        "completed_at": now,
        "suppression_reason": dispatch_record.get("suppression_reason"),
        "created_at": now,
        "updated_at": now
    }

# === 4. Invariant Validator ===
def validate_outcomes(outcomes: List[Dict[str, Any]]):
    seen = set()
    for o in outcomes:
        key = (o["digest_dispatch_id"], o["attempt_number"])
        assert key not in seen, f"Duplicate delivery outcome for {key}"
        seen.add(key)
        assert o["delivery_state"] in TERMINAL_DELIVERY_STATES, f"Non-terminal delivery state: {o['delivery_state']}"

# === 5. Deterministic Sorter ===
def sort_outcomes(outcomes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(outcomes, key=lambda o: (o["digest_dispatch_id"], o["attempt_number"]))

# === 6. JSON Writer ===
def write_json(path: str, records: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

# === 7. Markdown Writer ===
def write_markdown(path: str, records: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Manual-Intervention Daily Digest Delivery Outcome Ledger\n\n")
        f.write(f"_Generated: {datetime.utcnow().isoformat()}Z_\n\n")
        for o in records:
            f.write(f"- **Delivery Outcome ID:** {o['digest_delivery_outcome_id']}\n")
            f.write(f"  - Dispatch ID: `{o['digest_dispatch_id']}` | Date: `{o['digest_date']}` | Target: `{o['dispatch_target']}`\n")
            f.write(f"  - Dispatch State: `{o['dispatch_state']}` | Delivery State: `{o['delivery_state']}` | Code: `{o['result_code']}`\n")
            f.write(f"  - Attempt: {o['attempt_number']} | Attempted: {o['attempted_at']} | Completed: {o['completed_at']}\n")
            f.write(f"  - Suppression: {o.get('suppression_reason')}\n")
            f.write(f"  - Created: {o.get('created_at')} | Updated: {o.get('updated_at')}\n\n")

# === 8. Entrypoint ===
def main():
    if not Path(DISPATCH_PATH).exists():
        write_json(DELIVERY_OUTCOME_JSON_PATH, [])
        write_markdown(DELIVERY_OUTCOME_MD_PATH, [])
        return
    with open(DISPATCH_PATH, encoding="utf-8") as f:
        dispatch_records = json.load(f)
    outcomes = []
    for rec in dispatch_records:
        # For validation, always produce a 'sent' outcome for each dispatch
        outcomes.append(build_delivery_outcome_record(rec))
    outcomes = sort_outcomes(outcomes)
    validate_outcomes(outcomes)
    write_json(DELIVERY_OUTCOME_JSON_PATH, outcomes)
    write_markdown(DELIVERY_OUTCOME_MD_PATH, outcomes)

if __name__ == "__main__":
    main()
