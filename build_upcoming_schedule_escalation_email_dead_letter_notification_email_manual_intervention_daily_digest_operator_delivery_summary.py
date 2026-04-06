"""
v73.6-upcoming-schedule-escalation-email-dead-letter-notification-email-manual-intervention-daily-digest-operator-delivery-summary

Purpose: Deterministic, pure reporting slice. Reads v73.2 operator digest, v73.3 dispatch artifact, v73.4 delivery outcome ledger, v73.5 reconciled dispatch + reconciliation audit. Produces a canonical operator-facing delivery summary answering:
- Was today’s digest dispatched?
- Was delivery sent, failed, skipped, or blocked?
- Was dispatch reconciliation applied?
- Which targets succeeded or failed?
- What follow-up is still required?

Scope: Pure reporting only. No mutation of dispatch state, delivery outcomes, resolution ledger, or reminder/retry layers. Artifacts in → summary out.
"""


import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# === 1. Constants and Enums ===
DISPATCH_PATH = "ops/events/upcoming_schedule_manual_intervention_daily_digest_dispatch.json"
DELIVERY_OUTCOME_PATH = "ops/events/upcoming_schedule_manual_intervention_daily_digest_delivery_outcome_ledger.json"
RECONCILED_DISPATCH_PATH = "ops/events/upcoming_schedule_manual_intervention_daily_digest_dispatch_reconciled.json"
RECONCILIATION_AUDIT_PATH = "ops/events/upcoming_schedule_manual_intervention_daily_digest_dispatch_reconciliation_audit.json"
OPERATOR_DIGEST_PATH = "ops/events/upcoming_schedule_manual_intervention_operator_digest.json"
SUMMARY_JSON = "ops/events/upcoming_schedule_manual_intervention_daily_digest_operator_delivery_summary.json"
SUMMARY_MD = "ops/events/upcoming_schedule_manual_intervention_daily_digest_operator_delivery_summary.md"

TERMINAL_STATES = ["sent", "failed", "skipped", "blocked"]
FOLLOWUP_ORDER = {"blocked": 0, "failed": 1, "skipped": 2}

# === 2. Loaders ===
def load_json(path: str):
	if not Path(path).exists():
		return []
	with open(path, encoding="utf-8") as f:
		content = f.read().strip()
		if not content:
			return []
		return json.loads(content)

# === 3. Index Builders ===
def build_dispatch_index(dispatches):
	return {d["digest_dispatch_id"]: d for d in dispatches}

def build_outcome_index(outcomes):
	idx = {}
	for o in outcomes:
		idx.setdefault(o["digest_dispatch_id"], []).append(o)
	return idx

def build_reconciliation_index(audit):
	return {a["digest_dispatch_id"]: a for a in audit}

# === 4. Main Summary Logic ===
def build_summary():
	operator_digest = load_json(OPERATOR_DIGEST_PATH)
	dispatches = load_json(DISPATCH_PATH)
	outcomes = load_json(DELIVERY_OUTCOME_PATH)
	reconciled_dispatches = load_json(RECONCILED_DISPATCH_PATH)
	reconciliation_audit = load_json(RECONCILIATION_AUDIT_PATH)

	dispatch_idx = build_dispatch_index(dispatches)
	outcome_idx = build_outcome_index(outcomes)
	reconciled_idx = build_dispatch_index(reconciled_dispatches)
	audit_idx = build_reconciliation_index(reconciliation_audit)

	# Assume all for a single digest_date (take from first dispatch if present)
	digest_date = None
	if dispatches:
		digest_date = dispatches[0]["digest_date"]
	elif reconciled_dispatches:
		digest_date = reconciled_dispatches[0]["digest_date"]
	else:
		digest_date = ""

	targets = set(d["dispatch_target"] for d in dispatches)
	dispatch_target_count = len(targets)
	dispatch_total = len(dispatches)

	sent, failed, skipped, blocked = 0, 0, 0, 0
	targets_succeeded, targets_failed, targets_blocked = [], [], []
	reconciliation_applied_count = 0
	followup_queue = []

	for d in dispatches:
		did = d["digest_dispatch_id"]
		target = d["dispatch_target"]
		rec = reconciled_idx.get(did, d)
		state = rec.get("dispatch_state", d.get("dispatch_state"))
		# Find latest outcome for this dispatch
		olist = outcome_idx.get(did, [])
		latest_outcome = olist[-1] if olist else None
		delivery_state = latest_outcome["delivery_state"] if latest_outcome else None
		result_summary = latest_outcome["result_summary"] if latest_outcome else None
		# Tally
		if delivery_state == "sent":
			sent += 1
			targets_succeeded.append(target)
		elif delivery_state == "failed":
			failed += 1
			targets_failed.append(target)
		elif delivery_state == "blocked":
			blocked += 1
			targets_blocked.append(target)
		elif delivery_state == "skipped":
			skipped += 1
		# Reconciliation
		if did in audit_idx:
			reconciliation_applied_count += 1
		# Follow-up rules
		needs_followup = False
		next_action = None
		if delivery_state in ("failed", "blocked"):
			needs_followup = True
			next_action = "investigate_failure" if delivery_state == "failed" else "resolve_blocked"
		elif not delivery_state or state not in ("delivered", "delivery_failed"):  # unresolved
			needs_followup = True
			next_action = "manual_review"
		if needs_followup:
			followup_queue.append({
				"digest_dispatch_id": did,
				"dispatch_target": target,
				"delivery_state": delivery_state,
				"result_summary": result_summary,
				"next_action": next_action
			})

	# Deterministic ordering
	def followup_sort_key(item):
		return (
			FOLLOWUP_ORDER.get(item["delivery_state"], 99),
			item["digest_dispatch_id"],
			item["dispatch_target"]
		)
	followup_queue = sorted(followup_queue, key=followup_sort_key)

	summary_id = hashlib.sha256(f"{digest_date}|{dispatch_total}".encode()).hexdigest()[:16]
	summary = {
		"summary_id": summary_id,
		"digest_date": digest_date,
		"dispatch_target_count": dispatch_target_count,
		"dispatch_total": dispatch_total,
		"dispatch_sent": sent,
		"dispatch_failed": failed,
		"dispatch_skipped": skipped,
		"dispatch_blocked": blocked,
		"reconciliation_applied_count": reconciliation_applied_count,
		"targets_succeeded": sorted(targets_succeeded),
		"targets_failed": sorted(targets_failed),
		"targets_blocked": sorted(targets_blocked),
		"followup_required_count": len(followup_queue),
		"followup_queue": followup_queue
	}
	validate_summary(summary, dispatches, outcomes, reconciliation_audit)
	return summary

# === 5. Invariant Validator ===
def validate_summary(summary, dispatches, outcomes, reconciliation_audit):
	assert summary["dispatch_total"] == len(dispatches)
	assert summary["dispatch_sent"] + summary["dispatch_failed"] + summary["dispatch_skipped"] + summary["dispatch_blocked"] <= summary["dispatch_total"]
	assert len(set(f["digest_dispatch_id"] for f in summary["followup_queue"])) == len(summary["followup_queue"])
	# Add more invariants as needed

# === 6. Writers ===
def write_json(path, obj):
	with open(path, "w", encoding="utf-8") as f:
		json.dump(obj, f, indent=2, ensure_ascii=False)

def write_markdown(path, summary):
	with open(path, "w", encoding="utf-8") as f:
		f.write(f"# Operator Daily Digest Delivery Summary\n\n")
		f.write(f"**Digest Date:** {summary['digest_date']}\n\n")
		f.write(f"**Dispatch Targets:** {summary['dispatch_target_count']}\n")
		f.write(f"**Total Dispatches:** {summary['dispatch_total']}\n")
		f.write(f"**Sent:** {summary['dispatch_sent']} | **Failed:** {summary['dispatch_failed']} | **Skipped:** {summary['dispatch_skipped']} | **Blocked:** {summary['dispatch_blocked']}\n")
		f.write(f"**Reconciliation Applied:** {summary['reconciliation_applied_count']}\n\n")
		f.write(f"**Targets Succeeded:** {', '.join(summary['targets_succeeded']) or 'None'}\n")
		f.write(f"**Targets Failed:** {', '.join(summary['targets_failed']) or 'None'}\n")
		f.write(f"**Targets Blocked:** {', '.join(summary['targets_blocked']) or 'None'}\n\n")
		f.write(f"**Follow-up Required:** {summary['followup_required_count']}\n\n")
		if summary['followup_queue']:
			for item in summary['followup_queue']:
				f.write(f"- Dispatch ID: {item['digest_dispatch_id']} | Target: {item['dispatch_target']} | State: {item['delivery_state']} | Reason: {item['result_summary']} | Next: {item['next_action']}\n")
		else:
			f.write("No follow-up required.\n")

# === 7. Entrypoint ===
def main():
	summary = build_summary()
	write_json(SUMMARY_JSON, summary)
	write_markdown(SUMMARY_MD, summary)

if __name__ == "__main__":
	main()
