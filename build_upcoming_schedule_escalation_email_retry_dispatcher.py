"""
build_upcoming_schedule_escalation_email_retry_dispatcher.py

v69.2: Deterministic escalation email retry dispatcher
- Reads retry policy, delivery, and delivery state artifacts
- Consumes only retry-eligible failed escalation email deliveries
- Re-attempts delivery through the existing escalation email transport path
- Records per-retry result as sent/failed/skipped
- Emits machine-readable retry-dispatch artifact and Markdown report
- Emits retry-dispatch state/ledger for exact-once dedupe
"""
import json
from pathlib import Path
from datetime import datetime
import os
import importlib.util

RETRY_POLICY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_policy.json")
RETRY_POLICY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_policy_state.json")
DELIVERY_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_notification_delivery.json")
DELIVERY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_notification_delivery_state.json")
RETRY_DISPATCH_JSON_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_dispatch.json")
RETRY_DISPATCH_MD_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_dispatch.md")
RETRY_DISPATCH_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_retry_dispatch_state.json")


def load_json(path, default=None):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def main():
    retry_policy = load_json(RETRY_POLICY_JSON_PATH, [])
    retry_policy_state = load_json(RETRY_POLICY_STATE_PATH, {})
    delivery = load_json(DELIVERY_JSON_PATH, [])
    delivery_state = load_json(DELIVERY_STATE_PATH, {})
    now = datetime.utcnow().isoformat() + "Z"
    # Index delivery by delivery_id
    delivery_by_id = {d["delivery_id"]: d for d in delivery}
    # Load previous retry-dispatch state for dedupe
    retry_dispatch_state = load_json(RETRY_DISPATCH_STATE_PATH, {"attempts": {}})
    attempts = retry_dispatch_state.get("attempts", {})
    results = []
    for p in retry_policy:
        delivery_id = p["delivery_id"]
        notification_id = p["notification_id"]
        eligible = p.get("eligible", False)
        status = p.get("status", "")
        # Only retry eligible failed
        if not eligible or status != "failed":
            continue
        # Dedupe: skip if already retried for this attempt count
        attempt_key = f"{delivery_id}:{p['attempts']}"
        if attempts.get(attempt_key):
            continue
        # Prepare for retry
        entry = delivery_by_id.get(delivery_id, {})
        outbox_entry = entry.get("outbox_entry", {})
        routing = entry.get("routing", {})
        recipients = routing.get("recipients", [])
        # Use real email adapter for retry
        email_adapter_path = os.path.join(os.path.dirname(__file__), "build_upcoming_schedule_escalation_email_adapter.py")
        spec = importlib.util.spec_from_file_location("escalation_email_adapter", email_adapter_path)
        email_adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(email_adapter)
        try:
            send_result = email_adapter.send_notification_email(outbox_entry, recipients=recipients)
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
            "retried_at": now,
            "attempt": p["attempts"],
            "outbox_entry": outbox_entry,
            "routing": routing,
        }
        results.append(record)
        attempts[attempt_key] = record
    save_json(RETRY_DISPATCH_JSON_PATH, results)
    # Markdown report
    with open(RETRY_DISPATCH_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Escalation Email Retry Dispatch\n\n")
        for r in results:
            f.write(f"- Delivery: {r['delivery_id']} | Notification: {r['notification_id']} | Attempt: {r['attempt']} | Result: {r['result']} | Reason: {r['reason']} | Time: {r['retried_at']}\n")
    # State artifact for dedupe
    save_json(RETRY_DISPATCH_STATE_PATH, {"attempts": attempts, "generated_at": now})

if __name__ == "__main__":
    main()
