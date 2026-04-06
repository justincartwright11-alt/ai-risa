"""
v73.9-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-operator-followup-action-dispatch-outcome-ledger

Purpose: Deterministic, canonical ledger of operator follow-up action dispatch outcomes. Reads v73.8 operator follow-up action dispatch artifact and produces a settled outcome record for each dispatch attempt.

Artifacts:
- ops/events/upcoming_schedule_manual_intervention_operator_followup_action_dispatch_outcome_ledger.json
- ops/events/upcoming_schedule_manual_intervention_operator_followup_action_dispatch_outcome_ledger.md

Inclusion: One settled outcome per followup_dispatch_id + attempt_number. No duplicates. Deterministic ordering. No upstream mutation.
"""


import json
import hashlib
from pathlib import Path
from datetime import datetime

# === 1. Constants and Enums ===
DISPATCH_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_dispatch.json"
OUTCOME_JSON = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_dispatch_outcome_ledger.json"
OUTCOME_MD = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_dispatch_outcome_ledger.md"
TERMINAL_STATES = ["sent", "failed", "skipped", "blocked"]

# === 2. Loader ===
def load_json(path):
	if not Path(path).exists():
		return []
	with open(path, encoding="utf-8") as f:
		content = f.read().strip()
		if not content:
			return []
		return json.loads(content)

# === 3. Outcome Builder ===
def build_outcomes():
	dispatches = load_json(DISPATCH_PATH)
	outcomes = []
	now = "2026-04-06T00:00:00Z"  # Use a fixed timestamp for determinism
	for d in dispatches:
		# Only one attempt per dispatch in this slice
		attempt_number = 1
		dedupe_key = f"{d['followup_dispatch_id']}|{attempt_number}"
		followup_dispatch_outcome_id = hashlib.sha256(dedupe_key.encode()).hexdigest()[:16]
		# For demo: all dispatches are 'sent' unless suppressed (can be extended for real delivery logic)
		dispatch_state = d["dispatch_state"]
		delivery_state = "sent" if dispatch_state == "dispatch" else "skipped"
		result_code = "250" if delivery_state == "sent" else "0"
		result_summary = "Operator notified successfully." if delivery_state == "sent" else "Dispatch skipped."
		suppression_reason = d.get("suppression_reason", "")
		outcomes.append({
			"followup_dispatch_outcome_id": followup_dispatch_outcome_id,
			"followup_dispatch_id": d["followup_dispatch_id"],
			"followup_action_id": d["followup_action_id"],
			"dedupe_key": dedupe_key,
			"dispatch_target": d["dispatch_target"],
			"dispatch_channel": d["dispatch_channel"],
			"dispatch_state": dispatch_state,
			"delivery_state": delivery_state,
			"result_code": result_code,
			"result_summary": result_summary,
			"attempt_number": attempt_number,
			"attempted_at": now,
			"completed_at": now,
			"suppression_reason": suppression_reason
		})
	# Deterministic ordering
	outcomes = sorted(outcomes, key=lambda o: (o["followup_dispatch_id"], o["attempt_number"], o["dispatch_target"]))
	validate_outcomes(outcomes)
	return outcomes

# === 4. Invariant Validator ===
def validate_outcomes(outcomes):
	seen = set()
	for o in outcomes:
		key = (o["followup_dispatch_id"], o["attempt_number"])
		assert key not in seen, f"Duplicate outcome: {key}"
		seen.add(key)
		assert o["delivery_state"] in TERMINAL_STATES, f"Non-terminal delivery state: {o['delivery_state']}"

# === 5. Writers ===
def write_json(path, obj):
	with open(path, "w", encoding="utf-8") as f:
		json.dump(obj, f, indent=2, ensure_ascii=False)

def write_markdown(path, outcomes):
	with open(path, "w", encoding="utf-8") as f:
		f.write(f"# Operator Follow-up Action Dispatch Outcome Ledger\n\n")
		f.write(f"Total Outcomes: {len(outcomes)}\n\n")
		if not outcomes:
			f.write("No dispatch outcomes recorded.\n")
		else:
			for o in outcomes:
				f.write(f"- Outcome ID: {o['followup_dispatch_outcome_id']} | Dispatch ID: {o['followup_dispatch_id']} | Target: {o['dispatch_target']} | Channel: {o['dispatch_channel']} | Delivery: {o['delivery_state']} | Code: {o['result_code']} | Summary: {o['result_summary']} | Attempt: {o['attempt_number']} | State: {o['dispatch_state']} | Suppression: {o['suppression_reason']}\n")

# === 6. Entrypoint ===
def main():
	outcomes = build_outcomes()
	write_json(OUTCOME_JSON, outcomes)
	write_markdown(OUTCOME_MD, outcomes)

if __name__ == "__main__":
	main()
