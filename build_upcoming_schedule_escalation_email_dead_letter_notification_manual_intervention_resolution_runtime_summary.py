#!/usr/bin/env python3
"""
build_upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_runtime_summary.py

Deterministically emits a runtime summary/report for the manual-intervention resolution path in the upcoming schedule escalation email dead-letter notification pipeline.

Reads:
- ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_state.json

Emits:
- ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_runtime_summary.json
- ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_runtime_summary.md

Constraints:
- v66.3 through v72.4 interfaces are frozen
- No schema redesign, new transport/channel, or daemon/service changes
- Summary/report only
"""
import json
import os
from collections import Counter, OrderedDict

RESOLUTION_STATE_JSON = "ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_state.json"
SUMMARY_JSON = "ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_runtime_summary.json"
SUMMARY_MD = "ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_runtime_summary.md"

# Helper: load JSON

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

resolution_rows = load_json(RESOLUTION_STATE_JSON)

# Count statuses
total = len(resolution_rows)
status_counter = Counter(row.get("resolution_status") for row in resolution_rows)

unresolved_count = status_counter.get("unresolved", 0)
resolved_count = status_counter.get("resolved", 0)
cleared_count = status_counter.get("cleared", 0)

deduped_ids = set()
deduped = True
for row in resolution_rows:
    iid = row.get("intervention_id")
    if iid in deduped_ids:
        deduped = False
        break
    deduped_ids.add(iid)

deduped_status = "deduped" if deduped else "duplicate_ids_found"

# Failure isolation: if any unresolved, not terminal
total_terminal = (unresolved_count == 0)
failure_isolation_status = "isolated" if total_terminal else "active_unresolved"

# Terminal runtime status: all resolved or cleared
total_terminal_status = "terminal" if total_terminal else "active"

summary = OrderedDict([
    ("total_items", total),
    ("unresolved_count", unresolved_count),
    ("resolved_count", resolved_count),
    ("cleared_count", cleared_count),
    ("dedupe_status", deduped_status),
    ("failure_isolation_status", failure_isolation_status),
    ("terminal_runtime_status", total_terminal_status),
])

with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

with open(SUMMARY_MD, "w", encoding="utf-8") as f:
    f.write("# Manual-Intervention Resolution Runtime Summary\n\n")
    f.write(f"- **Total Items:** {total}\n")
    f.write(f"- **Unresolved:** {unresolved_count}\n")
    f.write(f"- **Resolved:** {resolved_count}\n")
    f.write(f"- **Cleared:** {cleared_count}\n")
    f.write(f"- **Dedupe Status:** `{deduped_status}`\n")
    f.write(f"- **Failure Isolation Status:** `{failure_isolation_status}`\n")
    f.write(f"- **Terminal Runtime Status:** `{total_terminal_status}`\n")
