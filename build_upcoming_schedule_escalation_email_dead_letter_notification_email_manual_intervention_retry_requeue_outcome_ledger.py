"""
v73.0-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-retry-requeue-outcome-ledger
Deterministic outcome ledger builder for retry/requeue executions (pure outcome capture).
Reads v72.9 executor artifact, writes canonical JSON + Markdown outcome artifacts.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# === 1. Constants/Enums ===

V72_9_EXECUTOR_PATH = "ops/events/upcoming_schedule_manual_intervention_retry_requeue_executor.json"
V73_0_OUTCOME_JSON_PATH = "ops/events/upcoming_schedule_manual_intervention_retry_requeue_outcome_ledger.json"
V73_0_OUTCOME_MD_PATH = "ops/events/upcoming_schedule_manual_intervention_retry_requeue_outcome_ledger.md"

TERMINAL_RESULTS = {"success", "failed", "skipped", "blocked"}

# === 2. Stable Outcome Identity ===
def make_outcome_id(retry_execution_id: str, attempt_number: int) -> str:
    base = f"{retry_execution_id}|{attempt_number}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]

# === 3. Canonical Outcome Record Builder ===
def build_outcome_record(exec_record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "retry_execution_outcome_id": make_outcome_id(exec_record["retry_execution_id"], exec_record["attempt_number"]),
        "retry_execution_id": exec_record["retry_execution_id"],
        "resolution_case_id": exec_record["resolution_case_id"],
        "dedupe_key": exec_record["dedupe_key"],
        "execution_state": exec_record["execution_state"],
        "result_state": exec_record.get("result_state", "unknown"),
        "result_code": exec_record.get("result_code"),
        "result_summary": exec_record.get("result_summary"),
        "attempt_number": exec_record["attempt_number"],
        "attempted_at": exec_record.get("requested_at"),
        "completed_at": exec_record.get("executed_at"),
        "followup_action": exec_record.get("followup_action"),
        "reopen_required": exec_record.get("reopen_required", False),
        "created_at": exec_record.get("created_at"),
        "updated_at": exec_record.get("updated_at"),
    }

# === 4. Invariant Validator ===
def validate_outcomes(outcomes: List[Dict[str, Any]]):
    seen = set()
    for o in outcomes:
        key = (o["retry_execution_id"], o["attempt_number"])
        assert key not in seen, f"Duplicate outcome for {key}"
        seen.add(key)
        assert o["result_state"] in TERMINAL_RESULTS, f"Non-terminal result: {o['result_state']}"

# === 5. Deterministic Sorter ===
def sort_outcomes(outcomes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(outcomes, key=lambda o: (o["retry_execution_id"], o["attempt_number"]))

# === 6. JSON Writer ===
def write_json(path: str, records: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

# === 7. Markdown Writer ===
def write_markdown(path: str, records: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Manual-Intervention Retry/Requeue Outcome Ledger\n\n")
        f.write(f"_Generated: {datetime.utcnow().isoformat()}Z_\n\n")
        for o in records:
            f.write(f"- **Outcome ID:** {o['retry_execution_outcome_id']}\n")
            f.write(f"  - Execution ID: `{o['retry_execution_id']}` | Case: `{o['resolution_case_id']}`\n")
            f.write(f"  - State: `{o['execution_state']}` | Result: `{o['result_state']}` | Code: `{o.get('result_code')}`\n")
            f.write(f"  - Attempt: {o['attempt_number']} | Attempted: {o.get('attempted_at')} | Completed: {o.get('completed_at')}\n")
            f.write(f"  - Dedupe: {o['dedupe_key']} | Followup: {o.get('followup_action')} | Reopen: {o.get('reopen_required')}\n")
            f.write(f"  - Created: {o.get('created_at')} | Updated: {o.get('updated_at')}\n\n")

# === 8. Entrypoint ===
def main():
    # Read v72.9 executor artifact
    if not Path(V72_9_EXECUTOR_PATH).exists():
        print(f"Input not found: {V72_9_EXECUTOR_PATH}")
        write_json(V73_0_OUTCOME_JSON_PATH, [])
        write_markdown(V73_0_OUTCOME_MD_PATH, [])
        return
    with open(V72_9_EXECUTOR_PATH, encoding="utf-8") as f:
        exec_records = json.load(f)
    # Build outcomes
    outcomes = []
    for rec in exec_records:
        # Only process records with terminal result_state
        if rec.get("result_state") in TERMINAL_RESULTS:
            outcomes.append(build_outcome_record(rec))
    outcomes = sort_outcomes(outcomes)
    validate_outcomes(outcomes)
    write_json(V73_0_OUTCOME_JSON_PATH, outcomes)
    write_markdown(V73_0_OUTCOME_MD_PATH, outcomes)

if __name__ == "__main__":
    main()
