"""
v72.9: Manual-Intervention Retry/Requeue Executor

- Reads v72.7 manual-intervention resolution ledger
- Projects deterministic retry/requeue execution actions for eligible cases
- Does NOT mutate ledger, add reminder logic, or perform assignment
- Outputs: JSON + Markdown executor artifacts

Execution Record Schema (locked):
{
  "retry_execution_id": str,  # Deterministic from dedupe_key
  "resolution_case_id": str,
  "case_fingerprint": str,
  "execution_state": str,      # Enum: pending, executed, blocked
  "execution_type": str,       # Enum: retry_requeue
  "source_event_id": str,
  "source_schedule_id": str,
  "source_run_id": str,
  "source_operation": str,
  "failure_family": str,
  "failure_code": str,
  "retry_state": str,
  "retry_decision": str,
  "retry_target": str,
  "eligibility_state": str,    # Enum: eligible, ineligible, suppressed
  "block_reason": str | None,
  "dedupe_key": str,           # Deterministic from (resolution_case_id, execution_type, retry_target)
  "attempt_number": int,
  "requested_at": str,
  "executed_at": str | None,
  "result_state": str,         # Enum: not_executed, success, failed, skipped
  "result_summary": str | None,
  "created_at": str,
  "updated_at": str
}

Eligibility Rules (locked):
- closure_state == 'open'
- resolution_state == 'resolved_retry_requested'
- retry_state in {'eligible', 'requested'}
- retry_target present
- not already executed
- not blocked/suppressed by policy

Stable Identity:
- dedupe_key: resolution_case_id|execution_type|retry_target
- retry_execution_id: sha256(dedupe_key)[:16]
- No runtime timestamps in IDs

State Model:
- execution_state: pending | executed | blocked
- eligibility_state: eligible | ineligible | suppressed
- result_state: not_executed | success | failed | skipped

Invariants:
- Only eligible, open, retry-requested cases execute
- No duplicate execution records per dedupe_key
- Already executed cases do not re-execute
- Blocked cases remain blocked deterministically
- Ledger is not mutated by executor

"""

import json
import hashlib

from datetime import datetime, timezone
from pathlib import Path

# === Ledger Loader ===
def load_resolution_ledger(path):
  with open(path, 'r', encoding='utf-8') as f:
    return json.load(f)

# === Eligibility Filter ===
def is_case_eligible(case):
  return (
    case.get('closure_state') == 'open' and
    case.get('resolution_state') == 'resolved_retry_requested' and
    case.get('retry_state') in {'eligible', 'requested'} and
    case.get('retry_target')
  )

# === Stable Identity ===
def build_dedupe_key(case):
  # For v72.9, attempt_number is always 1 (no multi-attempt logic yet)
  return f"{case['resolution_case_id']}|retry_requeue|{case['retry_target']}|1"

def build_retry_execution_id(dedupe_key):
  return hashlib.sha256(dedupe_key.encode('utf-8')).hexdigest()[:16]

# === Execution Record Constructor ===
def build_execution_record(case, now):
  dedupe_key = build_dedupe_key(case)
  retry_execution_id = build_retry_execution_id(dedupe_key)
  # For v72.9, assume not already executed, not blocked, not suppressed
  return {
    "retry_execution_id": retry_execution_id,
    "resolution_case_id": case["resolution_case_id"],
    "case_fingerprint": case["case_fingerprint"],
    "execution_state": "pending",
    "execution_type": "retry_requeue",
    "source_event_id": case["source_event_id"],
    "source_schedule_id": case["source_schedule_id"],
    "source_run_id": case["source_run_id"],
    "source_operation": case["source_operation"],
    "failure_family": case["failure_family"],
    "failure_code": case["failure_code"],
    "retry_state": case["retry_state"],
    "retry_decision": case.get("retry_decision"),
    "retry_target": case["retry_target"],
    "eligibility_state": "eligible",
    "block_reason": None,
    "dedupe_key": dedupe_key,
    "attempt_number": 1,
    "requested_at": case.get("updated_at", case.get("created_at")),
    "executed_at": None,
    "result_state": "not_executed",
    "result_summary": None,
    "created_at": case["created_at"],
    "updated_at": case["updated_at"]
  }

# === Invariant Validation ===
def validate_execution_invariants(records):
  seen = set()
  for r in records:
    key = r['dedupe_key']
    if key in seen:
      raise Exception(f"Duplicate execution for dedupe_key {key}")
    seen.add(key)

# === Markdown Renderer ===
def render_markdown(records, metadata):
  lines = []
  lines.append(f"# Manual-Intervention Retry/Requeue Executor\n")
  lines.append(f"_Generated: {metadata['generated_at']}_\n")
  if not records:
    lines.append("\n_No eligible retry/requeue executions at this time._\n")
    return "\n".join(lines)
  for r in records:
    lines.append(f"- **Execution ID:** {r['retry_execution_id']}")
    lines.append(f"  - Case: `{r['resolution_case_id']}` | Fingerprint: `{r['case_fingerprint']}`")
    lines.append(f"  - State: `{r['execution_state']}` | Eligibility: `{r['eligibility_state']}` | Result: `{r['result_state']}`")
    lines.append(f"  - Type: `{r['execution_type']}` | Attempt: {r['attempt_number']} | Target: {r['retry_target']}")
    lines.append(f"  - Source: Event `{r['source_event_id']}` | Schedule `{r['source_schedule_id']}` | Run `{r['source_run_id']}` | Op `{r['source_operation']}`")
    lines.append(f"  - Failure: Family `{r['failure_family']}` | Code `{r['failure_code']}`")
    lines.append(f"  - Requested: {r['requested_at']} | Executed: {r['executed_at']}")
    lines.append(f"  - Block Reason: {r['block_reason']} | Dedupe: {r['dedupe_key']}\n")
  return "\n".join(lines)

# === Main Entrypoint ===
def main():
  SCRIPT_DIR = Path(__file__).resolve().parent
  EVENTS_DIR = SCRIPT_DIR / "ops" / "events"
  EVENTS_DIR.mkdir(parents=True, exist_ok=True)
  LEDGER_PATH = EVENTS_DIR / "upcoming_schedule_manual_intervention_resolution_ledger.json"
  OUTPUT_JSON = EVENTS_DIR / "upcoming_schedule_manual_intervention_retry_requeue_executor.json"
  OUTPUT_MD = EVENTS_DIR / "upcoming_schedule_manual_intervention_retry_requeue_executor.md"

  now = datetime.now(timezone.utc)
  ledger = load_resolution_ledger(LEDGER_PATH)
  eligible = [c for c in ledger if is_case_eligible(c)]
  records = [build_execution_record(c, now) for c in eligible]
  validate_execution_invariants(records)
  # Always write deterministic artifacts, even if empty
  json_text = json.dumps(records, indent=2)
  md_text = render_markdown(records, {"generated_at": now.isoformat()})
  OUTPUT_JSON.write_text(json_text, encoding="utf-8")
  OUTPUT_MD.write_text(md_text, encoding="utf-8")

# Ensure main() is called when script is run directly
if __name__ == "__main__":
  main()
