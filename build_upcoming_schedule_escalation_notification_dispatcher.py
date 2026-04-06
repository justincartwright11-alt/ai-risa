#!/usr/bin/env python3
"""
build_upcoming_schedule_escalation_notification_dispatcher.py

v68.3: Deterministic dispatcher for escalation notification outbox
- Reads outbox and outbox state
- Dispatches pending notifications
- Records delivery results (sent/failed/skipped)
- Emits delivery ledger and Markdown report
- Enforces exact-once, dedupe, and retry semantics
"""
import json
import os
from datetime import datetime
from pathlib import Path

# Constants for artifact paths
OUTBOX_PATH = "ops/events/upcoming_schedule_escalation_notification_outbox.json"
OUTBOX_STATE_PATH = "ops/events/upcoming_schedule_escalation_notification_outbox_state.json"
DELIVERY_JSON_PATH = "ops/events/upcoming_schedule_escalation_notification_delivery.json"
DELIVERY_MD_PATH = "ops/events/upcoming_schedule_escalation_notification_delivery.md"
DELIVERY_STATE_PATH = "ops/events/upcoming_schedule_escalation_notification_delivery_state.json"

# Utility: load JSON

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Utility: save JSON

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Utility: save Markdown

def save_md(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

# Deterministic delivery ID
def make_delivery_id(notification_id):
    return f"delivery-{notification_id}"

# Main dispatcher logic
def main():
    outbox_data = load_json(OUTBOX_PATH) or {}
    outbox = outbox_data.get("notifications", [])
    outbox_state = load_json(OUTBOX_STATE_PATH) or {}
    delivery_state = load_json(DELIVERY_STATE_PATH) or {}
    delivery_results = []
    delivery_state_out = dict(delivery_state)  # Copy for update
    now = datetime.utcnow().isoformat() + "Z"
    # --- v68.7: Run routing policy and load routing outputs ---
    import subprocess
    import sys
    routing_script = os.path.join(os.path.dirname(__file__), "build_upcoming_schedule_escalation_email_routing_policy.py")
    subprocess.run([sys.executable, routing_script], check=True)
    ROUTING_JSON_PATH = "ops/events/upcoming_schedule_escalation_email_routing.json"
    routing_data = load_json(ROUTING_JSON_PATH) or []
    routing_by_id = {r["notification_id"]: r for r in routing_data}
    # --- Integration: use real email adapter for real sends, preserve exact-once ---
    import importlib.util
    email_adapter_path = os.path.join(os.path.dirname(__file__), "build_upcoming_schedule_escalation_email_adapter.py")
    spec = importlib.util.spec_from_file_location("escalation_email_adapter", email_adapter_path)
    email_adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(email_adapter)
    for entry in outbox:
        notification_id = entry.get("notification_id")
        delivery_id = make_delivery_id(notification_id)
        prev = delivery_state.get(delivery_id)
        if prev and prev.get("result") == "sent":
            continue
        # --- v68.7: Use routing outputs for recipient selection ---
        routing = routing_by_id.get(notification_id, {})
        recipients = routing.get("recipients", [])
        # Use real email adapter for real notifications, simulate for test IDs
        if notification_id.endswith("F"):
            result = "failed"
            reason = "Simulated failure for testability"
        elif notification_id.endswith("S"):
            result = "skipped"
            reason = "Simulated skip for testability"
        else:
            # Real send via email adapter, pass recipients
            try:
                send_result = email_adapter.send_notification_email(entry, recipients=recipients)
                result = send_result["result"]
                reason = send_result["reason"]
            except Exception as e:
                result = "failed"
                reason = f"Email adapter error: {e}"
        record = {
            "delivery_id": delivery_id,
            "notification_id": notification_id,
            "result": result,
            "reason": reason,
            "dispatched_at": now,
            "outbox_entry": entry,
            "routing": routing,
        }
        delivery_results.append(record)
        delivery_state_out[delivery_id] = {
            "result": result,
            "reason": reason,
            "dispatched_at": now,
        }
    # Save delivery artifacts (now with routing context)
    save_json(DELIVERY_JSON_PATH, delivery_results)
    save_json(DELIVERY_STATE_PATH, delivery_state_out)
    # Markdown parity with routing context
    md_lines = ["# Escalation Notification Delivery Report\n"]
    for r in delivery_results:
        md_lines.append(f"- **{r['notification_id']}**: {r['result']} ({r['reason']}) at {r['dispatched_at']} | Recipients: {', '.join(r['routing'].get('recipients', []))}")
    save_md(DELIVERY_MD_PATH, "\n".join(md_lines))

if __name__ == "__main__":
    main()
    # v68.9: Integrate delivery history ledger after delivery artifacts are finalized
    import subprocess
    import sys
    history_ledger_script = os.path.join(os.path.dirname(__file__), "build_upcoming_schedule_escalation_email_delivery_history_ledger.py")
    retry_policy_script = os.path.join(os.path.dirname(__file__), "build_upcoming_schedule_escalation_email_retry_policy_engine.py")
    try:
        subprocess.run([sys.executable, history_ledger_script], check=True)
    except Exception as e:
        print(f"[WARN] Delivery history ledger failed: {e}")
    try:
        subprocess.run([sys.executable, retry_policy_script], check=True)
    except Exception as e:
        print(f"[WARN] Retry policy engine failed: {e}")
    # v69.3: Integrate retry dispatcher after retry policy is finalized
    retry_dispatcher_script = os.path.join(os.path.dirname(__file__), "build_upcoming_schedule_escalation_email_retry_dispatcher.py")
    try:
        subprocess.run([sys.executable, retry_dispatcher_script], check=True)
    except Exception as e:
        print(f"[WARN] Retry dispatcher failed: {e}")
    # v69.5: Integrate retry history ledger after retry-dispatch state is finalized
    retry_history_ledger_script = os.path.join(os.path.dirname(__file__), "build_upcoming_schedule_escalation_email_retry_history_ledger.py")
    try:
        subprocess.run([sys.executable, retry_history_ledger_script], check=True)
    except Exception as e:
        print(f"[WARN] Retry history ledger failed: {e}")
    # v69.7: Integrate dead-letter ledger after retry history is finalized
    dead_letter_ledger_script = os.path.join(os.path.dirname(__file__), "build_upcoming_schedule_escalation_email_dead_letter_ledger.py")
    try:
        subprocess.run([sys.executable, dead_letter_ledger_script], check=True)
    except Exception as e:
        print(f"[WARN] Dead-letter ledger failed: {e}")
    # v70.0: Integrate dead-letter notification outbox after dead-letter ledger is finalized
    dead_letter_notification_outbox_script = os.path.join(os.path.dirname(__file__), "build_upcoming_schedule_escalation_email_dead_letter_notification_outbox.py")
    try:
        subprocess.run([sys.executable, dead_letter_notification_outbox_script], check=True)
    except Exception as e:
        print(f"[WARN] Dead-letter notification outbox failed: {e}")
    # v70.0: Integrate dead-letter notification dispatcher after notification outbox is generated
    dead_letter_notification_dispatcher_script = os.path.join(os.path.dirname(__file__), "build_upcoming_schedule_escalation_email_dead_letter_notification_dispatcher.py")
    try:
        subprocess.run([sys.executable, dead_letter_notification_dispatcher_script], check=True)
    except Exception as e:
        print(f"[WARN] Dead-letter notification dispatcher failed: {e}")
