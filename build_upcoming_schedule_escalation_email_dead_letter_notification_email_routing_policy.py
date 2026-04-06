#!/usr/bin/env python3
"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_routing_policy.py

v70.2: Deterministic recipient routing policy for escalation dead-letter notification email delivery
- Reads dead-letter ledger, notification outbox, and email adapter config
- Computes deterministic To/CC/BCC for opened/cleared notifications
- Applies subject severity/prefix treatment
- Emits machine-readable routing artifact and Markdown report
- Supports rerun dedupe and fixed-input determinism
"""
import json
from pathlib import Path

LEDGER_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_ledger.json")
OUTBOX_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_outbox.json")
CONFIG_PATH = Path("ops/config/upcoming_schedule_escalation_email_dead_letter_notification_email_adapter.json")
ROUTING_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_routing.json")
ROUTING_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_routing.md")
ROUTING_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_routing_state.json")

# Deterministic routing policy
SEVERITY_TO = {
    "critical": ["operator@example.com"],
    "high": ["operator@example.com"],
    "default": ["ops@example.com"]
}
SEVERITY_CC = {
    "critical": ["supervisor@example.com"],
    "high": [],
    "default": []
}
SEVERITY_BCC = {
    "critical": ["audit@example.com"],
    "high": [],
    "default": []
}

SUBJECT_PREFIX = {
    "critical": "[CRITICAL] ",
    "high": "[HIGH] ",
    "default": "[INFO] "
}

def get_severity(entry):
    return entry.get("escalation_level") or "default"

def compute_routing(notification):
    severity = get_severity(notification)
    to = SEVERITY_TO.get(severity, SEVERITY_TO["default"])
    cc = SEVERITY_CC.get(severity, SEVERITY_CC["default"])
    bcc = SEVERITY_BCC.get(severity, SEVERITY_BCC["default"])
    subject_prefix = SUBJECT_PREFIX.get(severity, SUBJECT_PREFIX["default"])
    return {
        "to": to,
        "cc": cc,
        "bcc": bcc,
        "subject_prefix": subject_prefix
    }

def main():
    if not LEDGER_PATH.exists() or not OUTBOX_PATH.exists() or not CONFIG_PATH.exists():
        print("[INFO] Required input missing, skipping routing.")
        return
    ledger = json.load(open(LEDGER_PATH, encoding="utf-8"))
    outbox = json.load(open(OUTBOX_PATH, encoding="utf-8"))
    config = json.load(open(CONFIG_PATH, encoding="utf-8"))
    routing = []
    routing_state = {}
    for n in outbox:
        notification_id = n["notification_id"]
        r = compute_routing(n)
        entry = {
            "notification_id": notification_id,
            "dead_letter_id": n["dead_letter_id"],
            "delivery_id": n["delivery_id"],
            "notification_type": n["notification_type"],
            "escalation_level": n.get("escalation_level"),
            "to": r["to"],
            "cc": r["cc"],
            "bcc": r["bcc"],
            "subject_prefix": r["subject_prefix"],
            "dedupe_key": n["dedupe_key"]
        }
        routing.append(entry)
        routing_state[notification_id] = entry
    with open(ROUTING_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(routing, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(ROUTING_MD_PATH, "w", encoding="utf-8") as f:
        f.write("# Dead-Letter Notification Email Routing Report\n\n")
        for r in routing:
            f.write(f"- Notification: {r['notification_id']} | To: {', '.join(r['to'])} | CC: {', '.join(r['cc'])} | BCC: {', '.join(r['bcc'])} | Prefix: {r['subject_prefix']} | Level: {r['escalation_level']}\n")
    with open(ROUTING_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"routing": routing_state}, f, indent=2, ensure_ascii=False)
        f.write("\n")

if __name__ == "__main__":
    main()
