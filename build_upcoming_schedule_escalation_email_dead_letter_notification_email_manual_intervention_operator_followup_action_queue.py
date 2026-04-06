"""
v73.7-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-operator-followup-action-queue

Purpose: Deterministic, canonical operator follow-up action queue. Reads v73.6 operator daily-digest delivery summary (and optionally v73.5/v73.4 for context) and produces a queue of required operator actions for unresolved/blocked/failed digest targets.

Artifacts:
- ops/events/upcoming_schedule_manual_intervention_operator_followup_action_queue.json
- ops/events/upcoming_schedule_manual_intervention_operator_followup_action_queue.md

Inclusion: Only targets requiring follow-up (failed, blocked, unresolved, not fully reconciled). No duplicates. Deterministic ordering.
"""


import json
import hashlib
from pathlib import Path

# === 1. Constants and Enums ===
SUMMARY_PATH = "ops/events/upcoming_schedule_manual_intervention_daily_digest_operator_delivery_summary.json"
QUEUE_JSON = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_queue.json"
QUEUE_MD = "ops/events/upcoming_schedule_manual_intervention_operator_followup_action_queue.md"

STATE_ORDER = {"blocked": 0, "failed": 1, "unresolved": 2}
PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}

# === 2. Upstream Loader ===
def load_json(path):
	if not Path(path).exists():
		return {}
	with open(path, encoding="utf-8") as f:
		content = f.read().strip()
		if not content:
			return {}
		return json.loads(content)

# === 3. Inclusion Filter and Queue Builder ===
def build_queue():
	summary = load_json(SUMMARY_PATH)
	queue = []
	followup_queue = summary.get("followup_queue", [])
	digest_date = summary.get("digest_date", "")
	source_summary_id = summary.get("summary_id", "")
	for item in followup_queue:
		# Build dedupe_key and followup_action_id
		dedupe_key = f"{item['digest_dispatch_id']}|{item['dispatch_target']}|{item['next_action']}"
		followup_action_id = hashlib.sha256(dedupe_key.encode()).hexdigest()[:16]
		delivery_state = item.get("delivery_state") or "unresolved"
		# Priority: blocked/failed = high, unresolved = normal
		if delivery_state in ("blocked", "failed"):
			action_priority = "high"
		else:
			action_priority = "normal"
		queue.append({
			"followup_action_id": followup_action_id,
			"digest_date": digest_date,
			"digest_dispatch_id": item["digest_dispatch_id"],
			"dispatch_target": item["dispatch_target"],
			"delivery_state": delivery_state,
			"result_summary": item.get("result_summary", ""),
			"action_state": "open",
			"action_priority": action_priority,
			"next_action": item["next_action"],
			"action_reason": reason_for_action(delivery_state, item),
			"source_summary_id": source_summary_id,
			"dedupe_key": dedupe_key
		})
	# Deterministic ordering
	def queue_sort_key(q):
		return (
			STATE_ORDER.get(q["delivery_state"], 99),
			PRIORITY_ORDER.get(q["action_priority"], 99),
			q["digest_dispatch_id"],
			q["dispatch_target"]
		)
	queue = sorted(queue, key=queue_sort_key)
	validate_queue(queue)
	return queue

def reason_for_action(delivery_state, item):
	if delivery_state == "blocked":
		return "Delivery was blocked. Manual intervention required."
	elif delivery_state == "failed":
		return "Delivery failed. Manual intervention required."
	else:
		return "Dispatch remains unresolved after outcome capture. Manual review required."

# === 4. Invariant Validator ===
def validate_queue(queue):
	seen = set()
	for q in queue:
		assert q["dedupe_key"] not in seen, f"Duplicate dedupe_key: {q['dedupe_key']}"
		seen.add(q["dedupe_key"])
	# No successful/reconciled targets
	for q in queue:
		assert q["delivery_state"] != "sent", "Successful/reconciled targets must not be in queue"

# === 5. Writers ===
def write_json(path, obj):
	with open(path, "w", encoding="utf-8") as f:
		json.dump(obj, f, indent=2, ensure_ascii=False)

def write_markdown(path, queue):
	with open(path, "w", encoding="utf-8") as f:
		f.write(f"# Operator Follow-up Action Queue\n\n")
		f.write(f"Total Actions: {len(queue)}\n\n")
		if not queue:
			f.write("No follow-up actions required.\n")
		else:
			for q in queue:
				f.write(f"- Action ID: {q['followup_action_id']} | Dispatch ID: {q['digest_dispatch_id']} | Target: {q['dispatch_target']} | State: {q['delivery_state']} | Priority: {q['action_priority']} | Next: {q['next_action']} | Reason: {q['action_reason']}\n")

# === 6. Entrypoint ===
def main():
	queue = build_queue()
	write_json(QUEUE_JSON, queue)
	write_markdown(QUEUE_MD, queue)

if __name__ == "__main__":
	main()
