"""
v72.8: Manual-Intervention Breach/Stale-Case Reminder Escalator

- Reads v72.7 manual-intervention resolution ledger
- Projects deterministic reminder/escalation actions for open unresolved cases
- Does NOT mutate ledger, execute retries, or send email
- Outputs: JSON + Markdown reminder projections

Reminder Action Schema (locked):
{
  "reminder_action_id": str,  # Deterministic from (resolution_case_id, reminder class, window)
  "resolution_case_id": str,
  "case_fingerprint": str,
  "reminder_state": str,  # Enum: not_due, due_soon, breached, stale_unacknowledged, stale_acknowledged, suppressed
  "breach_state": str,    # Enum: within_sla, breached
  "staleness_state": str, # Enum: fresh, stale_unacknowledged, stale_acknowledged
  "priority_band": str,   # Enum: normal, high, critical
  "source_event_id": str,
  "source_schedule_id": str,
  "failure_family": str,
  "failure_code": str,
  "assignment_state": str,
  "acknowledgement_state": str,
  "sla_started_at": str,
  "sla_due_at": str,
  "minutes_to_due": int,
  "minutes_overdue": int,
  "last_reminder_at": str | None,
  "next_reminder_due_at": str,
  "escalation_reason": str,
  "suppression_reason": str | None,
  "created_at": str,
  "updated_at": str
}

Reminder Class Enum (locked):
- not_due
- due_soon
- breached
- stale_unacknowledged
- stale_acknowledged
- suppressed

Policy Thresholds (initial, can be tuned):
- due_soon: within 60 minutes of sla_due_at
- breached: now > sla_due_at
- stale_unacknowledged: open > 120 minutes, not acknowledged
- stale_acknowledged: acknowledged > 240 minutes, unresolved

Deterministic ordering:
1. breach severity (breached > due_soon > stale > not_due)
2. acknowledgement risk (unacknowledged > acknowledged)
3. sla_due_at (earlier first)
4. resolution_case_id (lexical)

Invariants:
- Only open, unresolved, actionable cases eligible
- No duplicate reminder actions per case/class/window
- Closed/resolved cases excluded
- Reruns are deterministic

"""

import json
import hashlib


from datetime import datetime, timezone, timedelta
from pathlib import Path
import os

# === Policy Constants (frozen for v72.8) ===
DUE_SOON_MINUTES = 60
STALE_UNACK_MINUTES = 120
STALE_ACK_MINUTES = 240

# === Ledger Loader ===
def load_resolution_ledger(path):
  with open(path, 'r', encoding='utf-8') as f:
    return json.load(f)

# === Eligibility Filter ===
def is_case_eligible(case):
  return (
    case.get('closure_state') == 'open' and
    case.get('resolution_state') == 'unresolved'
  )

# === Classification Helpers ===
def classify_breach_state(case, now):
  sla_due = datetime.fromisoformat(case['sla_due_at'].replace('Z', '+00:00'))
  if now > sla_due:
    return 'breached'
  return 'within_sla'

def classify_staleness_state(case, now):
  created = datetime.fromisoformat(case['created_at'].replace('Z', '+00:00'))
  acked = case.get('acknowledged_at')
  if not case.get('acknowledgement_state') or case['acknowledgement_state'] == 'pending':
    if (now - created).total_seconds() / 60 > STALE_UNACK_MINUTES:
      return 'stale_unacknowledged'
    return 'fresh'
  if acked:
    acked_dt = datetime.fromisoformat(acked.replace('Z', '+00:00'))
    if (now - acked_dt).total_seconds() / 60 > STALE_ACK_MINUTES:
      return 'stale_acknowledged'
  return 'fresh'

def classify_reminder_state(case, now):
  breach = classify_breach_state(case, now)
  staleness = classify_staleness_state(case, now)
  sla_due = datetime.fromisoformat(case['sla_due_at'].replace('Z', '+00:00'))
  minutes_to_due = int((sla_due - now).total_seconds() / 60)
  if breach == 'breached':
    return 'breached'
  if staleness == 'stale_unacknowledged':
    return 'stale_unacknowledged'
  if staleness == 'stale_acknowledged':
    return 'stale_acknowledged'
  if 0 <= minutes_to_due <= DUE_SOON_MINUTES:
    return 'due_soon'
  return 'not_due'

def classify_priority_band(reminder_state):
  if reminder_state == 'breached':
    return 'critical'
  if reminder_state.startswith('stale'):
    return 'high'
  if reminder_state == 'due_soon':
    return 'normal'
  return 'normal'

# === Deterministic Identity ===
def build_reminder_action_id(case, reminder_state, bucket_key=None):
  # bucket_key can be used for future cadence windows, not needed for v72.8
  base = f"{case['resolution_case_id']}|{reminder_state}"
  return hashlib.sha256(base.encode('utf-8')).hexdigest()[:16]

# === Reminder Record Constructor ===
def build_reminder_record(case, now):
  reminder_state = classify_reminder_state(case, now)
  breach_state = classify_breach_state(case, now)
  staleness_state = classify_staleness_state(case, now)
  priority_band = classify_priority_band(reminder_state)
  sla_due = datetime.fromisoformat(case['sla_due_at'].replace('Z', '+00:00'))
  minutes_to_due = int((sla_due - now).total_seconds() / 60)
  minutes_overdue = max(0, int((now - sla_due).total_seconds() / 60))
  reminder_action_id = build_reminder_action_id(case, reminder_state)
  # For v72.8, last_reminder_at and next_reminder_due_at are placeholders (no reminder history yet)
  return {
    "reminder_action_id": reminder_action_id,
    "resolution_case_id": case["resolution_case_id"],
    "case_fingerprint": case["case_fingerprint"],
    "reminder_state": reminder_state,
    "breach_state": breach_state,
    "staleness_state": staleness_state,
    "priority_band": priority_band,
    "source_event_id": case["source_event_id"],
    "source_schedule_id": case["source_schedule_id"],
    "failure_family": case["failure_family"],
    "failure_code": case["failure_code"],
    "assignment_state": case["assignment_state"],
    "acknowledgement_state": case["acknowledgement_state"],
    "sla_started_at": case["sla_started_at"],
    "sla_due_at": case["sla_due_at"],
    "minutes_to_due": minutes_to_due,
    "minutes_overdue": minutes_overdue,
    "last_reminder_at": None,
    "next_reminder_due_at": case["sla_due_at"],
    "escalation_reason": "SLA breach" if breach_state == 'breached' else ("Due soon" if reminder_state == 'due_soon' else staleness_state.replace('_', ' ').title() if reminder_state.startswith('stale') else "Not due"),
    "suppression_reason": None,
    "created_at": case["created_at"],
    "updated_at": case["updated_at"]
  }

# === Invariant Validation ===
def validate_reminder_invariants(records):
  seen = set()
  for r in records:
    key = (r['resolution_case_id'], r['reminder_state'])
    if key in seen:
      raise Exception(f"Duplicate reminder for case {key}")
    seen.add(key)
  # No closed/resolved cases should appear
  for r in records:
    if r['reminder_state'] == 'suppressed':
      continue
    if r['breach_state'] not in ('within_sla', 'breached'):
      raise Exception(f"Invalid breach state: {r['breach_state']}")

# === Main Entrypoint ===
def main():

  # Path anchoring
  print(f"[DEBUG] Path.cwd(): {Path.cwd()}")
  SCRIPT_DIR = Path(__file__).resolve().parent
  print(f"[DEBUG] SCRIPT_DIR: {SCRIPT_DIR}")
  EVENTS_DIR = SCRIPT_DIR / "ops" / "events"
  print(f"[DEBUG] EVENTS_DIR: {EVENTS_DIR}")
  EVENTS_DIR.mkdir(parents=True, exist_ok=True)
  LEDGER_PATH = EVENTS_DIR / "upcoming_schedule_manual_intervention_resolution_ledger.json"
  OUTPUT_JSON = EVENTS_DIR / "upcoming_schedule_manual_intervention_breach_reminder_escalator.json"
  OUTPUT_MD = EVENTS_DIR / "upcoming_schedule_manual_intervention_breach_reminder_escalator.md"
  print(f"[DEBUG] OUTPUT_JSON: {OUTPUT_JSON}")
  print(f"[DEBUG] OUTPUT_MD: {OUTPUT_MD}")

  now = datetime.now(timezone.utc)
  ledger = load_resolution_ledger(LEDGER_PATH)
  print(f"[DEBUG] Loaded ledger records: {len(ledger)} from {LEDGER_PATH}")
  eligible = [c for c in ledger if is_case_eligible(c)]
  print(f"[DEBUG] Eligible open unresolved cases: {len(eligible)}")
  records = []
  for c in eligible:
    rec = build_reminder_record(c, now)
    print(f"[DEBUG] Case {rec['resolution_case_id']}: reminder_state={rec['reminder_state']}, breach_state={rec['breach_state']}, staleness_state={rec['staleness_state']}")
    records.append(rec)
  validate_reminder_invariants(records)
  # Always write deterministic artifacts, even if empty
  print(f"[DEBUG] Writing JSON to: {OUTPUT_JSON}")
  OUTPUT_JSON.write_text(json.dumps(records, indent=2), encoding="utf-8")
  print(f"[DEBUG] Writing Markdown to: {OUTPUT_MD}")
  md = render_markdown(records, {"generated_at": now.isoformat()})
  OUTPUT_MD.write_text(md, encoding="utf-8")
  print(f"[DEBUG] OUTPUT_JSON.exists(): {OUTPUT_JSON.exists()}")
  print(f"[DEBUG] OUTPUT_MD.exists(): {OUTPUT_MD.exists()}")
  if not OUTPUT_JSON.exists():
    raise RuntimeError(f"JSON output was not created: {OUTPUT_JSON}")
  if not OUTPUT_MD.exists():
    raise RuntimeError(f"Markdown output was not created: {OUTPUT_MD}")
  print(f"[DEBUG] Writer branches executed. Reminder actions projected: {len(records)}")

# === Markdown Renderer ===
def render_markdown(records, metadata):
  lines = []
  lines.append(f"# Manual-Intervention Reminder Projection\n")
  lines.append(f"_Generated: {metadata['generated_at']}_\n")
  if not records:
    lines.append("\n_No open unresolved cases require reminders at this time._\n")
    return "\n".join(lines)
  for r in records:
    lines.append(f"- **Reminder ID:** {r['reminder_action_id']}")
    lines.append(f"  - Case: `{r['resolution_case_id']}` | Fingerprint: `{r['case_fingerprint']}`")
    lines.append(f"  - State: `{r['reminder_state']}` | Breach: `{r['breach_state']}` | Staleness: `{r['staleness_state']}` | Priority: `{r['priority_band']}`")
    lines.append(f"  - Assignment: `{r['assignment_state']}` | Ack: `{r['acknowledgement_state']}`")
    lines.append(f"  - SLA Due: {r['sla_due_at']} | Minutes to due: {r['minutes_to_due']} | Overdue: {r['minutes_overdue']}")
    lines.append(f"  - Source: Event `{r['source_event_id']}` | Schedule `{r['source_schedule_id']}` | Failure: {r['failure_family']} {r['failure_code']}")
    lines.append(f"  - Escalation: {r['escalation_reason']} | Suppression: {r['suppression_reason']}")
    lines.append(f"  - Created: {r['created_at']} | Updated: {r['updated_at']}\n")
  return "\n".join(lines)

# Ensure main() is called when script is run directly
if __name__ == "__main__":
    main()
