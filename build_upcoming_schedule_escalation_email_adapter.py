"""
build_upcoming_schedule_escalation_email_adapter.py

v68.5: Real email transport adapter for escalation notifications
- Reads escalation notification outbox and delivery state
- Renders deterministic email subject/body for opened/cleared
- Sends via configured email transport
- Records delivery result (sent/failed/skipped) in delivery ledger
- Enforces exact-once, dedupe, and retry semantics
"""
import json
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

OUTBOX_PATH = "ops/events/upcoming_schedule_escalation_notification_outbox.json"
OUTBOX_STATE_PATH = "ops/events/upcoming_schedule_escalation_notification_outbox_state.json"
DELIVERY_STATE_PATH = "ops/events/upcoming_schedule_escalation_notification_delivery_state.json"
EMAIL_CONFIG_PATH = "ops/events/upcoming_schedule_escalation_email_config.json"

# Utility: load JSON
def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def make_delivery_id(notification_id):
    return f"delivery-{notification_id}"

def render_email(notification, escalation_state):
    typ = notification.get("notification_type")
    level = notification.get("escalation_level")
    escalation_id = notification.get("escalation_id")
    reason = notification.get("reason")
    subject = f"[AI-RISA Escalation {typ.upper()}] Escalation {escalation_id} ({level})"
    body = f"Escalation Notification\nType: {typ}\nLevel: {level}\nEscalation ID: {escalation_id}\nReason: {reason}\n\nState: {json.dumps(escalation_state, indent=2)}"
    return subject, body

def send_email(config, subject, body):
    msg = EmailMessage()
    msg["From"] = config["from"]
    msg["To"] = config["to"]
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(config["smtp_host"], config.get("smtp_port", 25)) as server:
        if config.get("smtp_tls"):
            server.starttls()
        if config.get("smtp_user") and config.get("smtp_pass"):
            server.login(config["smtp_user"], config["smtp_pass"])
        server.send_message(msg)

def main():
    outbox_data = load_json(OUTBOX_PATH) or {}
    outbox = outbox_data.get("notifications", [])
    outbox_state = load_json(OUTBOX_STATE_PATH) or {}
    delivery_state = load_json(DELIVERY_STATE_PATH) or {}
    escalation_state = load_json("ops/events/upcoming_schedule_escalation_state.json") or {}
    now = datetime.utcnow().isoformat() + "Z"
    config = load_json(EMAIL_CONFIG_PATH)
    if not config:
        print("ERROR: Missing escalation email config.")
        exit(2)
    delivery_state_out = dict(delivery_state)
    for entry in outbox:
        notification_id = entry.get("notification_id")
        delivery_id = make_delivery_id(notification_id)
        prev = delivery_state.get(delivery_id)
        if prev and prev.get("result") == "sent":
            continue
        subject, body = render_email(entry, escalation_state)
        try:
            send_email(config, subject, body)
            result = "sent"
            reason = "Email sent successfully"
        except Exception as e:
            result = "failed"
            reason = f"Email send failed: {e}"
        delivery_state_out[delivery_id] = {
            "result": result,
            "reason": reason,
            "dispatched_at": now,
        }
    save_json(DELIVERY_STATE_PATH, delivery_state_out)

if __name__ == "__main__":
    main()
