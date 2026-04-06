"""
v73.8-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-operator-followup-action-dispatcher

Purpose: Deterministic, canonical dispatcher for operator follow-up actions. Reads v73.7 operator follow-up action queue and produces a dispatch artifact for each actionable queue item.

Artifacts:
- ops/events/upcoming_schedule_manual_intervention_operator_followup_action_dispatch.json
- ops/events/upcoming_schedule_manual_intervention_operator_followup_action_dispatch.md

Inclusion: One dispatch record per actionable queue item. No duplicates. Deterministic ordering. No upstream mutation.
"""


import json
import hashlib
from pathlib import Path

# === 1. Constants and Enums ===
QUEUE_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_queue.json"
DISPATCH_JSON = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_dispatch.json"
DISPATCH_MD = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_dispatch.md"

CHANNEL = "operator_manual"  # Only one channel for this slice
PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}
STATE_ORDER = {"blocked": 0, "failed": 1, "unresolved": 2}

# === 2. Upstream Loader ===
def load_json(path):
	if not Path(path).exists():
		return []
	with open(path, encoding="utf-8") as f:
		content = f.read().strip()
		if not content:
			return []
		return json.loads(content)

# === 3. Dispatch Eligibility Filter and Builder ===
def build_dispatch_records():
	queue = load_json(QUEUE_PATH)
	records = []
	for item in queue:
		# Only actionable items (open, not suppressed, not already dispatched)
		if item.get("action_state") != "open":
			continue
		# Build dedupe_key for dispatch: followup_action_id|dispatch_target|dispatch_channel
		dedupe_key = f"{item['followup_action_id']}|{item['dispatch_target']}|{CHANNEL}"
		followup_dispatch_id = hashlib.sha256(dedupe_key.encode()).hexdigest()[:16]
		# Decide dispatch_state (always 'dispatch' for open, not suppressed)
		dispatch_state = "dispatch"
		suppression_reason = ""  # No suppression in this slice
		records.append({
			"followup_dispatch_id": followup_dispatch_id,
			"followup_action_id": item["followup_action_id"],
			"dedupe_key": dedupe_key,
			"dispatch_state": dispatch_state,
			"dispatch_target": item["dispatch_target"],
			"dispatch_channel": CHANNEL,
			"action_priority": item.get("action_priority", "normal"),
			"next_action": item["next_action"],
			"suppression_reason": suppression_reason,
			"digest_date": item["digest_date"]
		})
	# Deterministic ordering
	def dispatch_sort_key(r):
		return (
			PRIORITY_ORDER.get(r["action_priority"], 99),
			STATE_ORDER.get(item.get("delivery_state", "unresolved"), 99),
			r["followup_action_id"],
			r["dispatch_target"]
		)
	records = sorted(records, key=dispatch_sort_key)
	validate_dispatch(records)
	return records

# === 4. Invariant Validator ===
def validate_dispatch(records):
	seen = set()
	for r in records:
		key = (r["followup_action_id"], r["dispatch_target"], r["dispatch_channel"])
		assert key not in seen, f"Duplicate dispatch: {key}"
		seen.add(key)

# === 5. Writers ===
def write_json(path, obj):
	with open(path, "w", encoding="utf-8") as f:
		json.dump(obj, f, indent=2, ensure_ascii=False)

def write_markdown(path, records):
	with open(path, "w", encoding="utf-8") as f:
		f.write(f"# Operator Follow-up Action Dispatches\n\n")
		f.write(f"Total Dispatches: {len(records)}\n\n")
		if not records:
			f.write("No follow-up actions dispatched.\n")
		else:
			for r in records:
				f.write(f"- Dispatch ID: {r['followup_dispatch_id']} | Action ID: {r['followup_action_id']} | Target: {r['dispatch_target']} | Channel: {r['dispatch_channel']} | Priority: {r['action_priority']} | State: {r['dispatch_state']} | Next: {r['next_action']} | Reason: {r['suppression_reason']}\n")

# === 6. Entrypoint ===
def main():
	records = build_dispatch_records()
	write_json(DISPATCH_JSON, records)
	write_markdown(DISPATCH_MD, records)

if __name__ == "__main__":
	main()
