#!/usr/bin/env python3
"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_adapter.py

v70.1: Real email transport adapter for escalation dead-letter notifications
- Reads pending dead-letter notification outbox/state
- Renders deterministic subject/body for opened/cleared
- Sends via configured SMTP transport
- Records result as sent/failed/skipped in delivery semantics
- Fail-loud on missing config
- Never resend already delivered notifications
- Preserves retry eligibility for failed notifications
"""
import os
import smtplib
from email.message import EmailMessage

CONFIG_PATH = "ops/config/upcoming_schedule_escalation_email_dead_letter_notification_email_adapter.json"

# Deterministic subject/body rendering
SUBJECT_TEMPLATES = {
    "opened": "[ALERT] Escalation Email Dead-Letter: {delivery_id}",
    "cleared": "[RESOLVED] Escalation Email Dead-Letter Cleared: {delivery_id}"
}
BODY_TEMPLATES = {
    "opened": "Escalation email delivery failed terminally.\n\nDelivery ID: {delivery_id}\nTerminal Reason: {terminal_reason}\nEscalation Level: {escalation_level}\n",
    "cleared": "Escalation email dead-letter cleared.\n\nDelivery ID: {delivery_id}\nEscalation Level: {escalation_level}\n"
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise RuntimeError(f"Missing config: {CONFIG_PATH}")
    import json
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def render_email(notification):
    typ = notification["notification_type"]
    subject = SUBJECT_TEMPLATES[typ].format(**notification)
    body = BODY_TEMPLATES[typ].format(**notification)
    return subject, body

def send_email(smtp_cfg, recipients, subject, body):
    msg = EmailMessage()
    msg["From"] = smtp_cfg["from"]
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(smtp_cfg["host"], smtp_cfg.get("port", 25)) as s:
        if smtp_cfg.get("tls"):
            s.starttls()
        if smtp_cfg.get("user"):
            s.login(smtp_cfg["user"], smtp_cfg["password"])
        s.send_message(msg)

def main():
    import json
    from pathlib import Path
    OUTBOX_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_outbox.json")
    OUTBOX_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_outbox_state.json")
    DELIVERY_STATE_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_delivery_state.json")
    if not OUTBOX_PATH.exists():
        print("[INFO] No outbox present.")
        return
    outbox = json.load(open(OUTBOX_PATH, encoding="utf-8"))
    outbox_state = json.load(open(OUTBOX_STATE_PATH, encoding="utf-8")) if OUTBOX_STATE_PATH.exists() else {"notifications": {}}
    delivery_state = json.load(open(DELIVERY_STATE_PATH, encoding="utf-8")) if DELIVERY_STATE_PATH.exists() else {"delivered": {}}
    cfg = load_config()
    smtp_cfg = cfg["smtp"]
    # Load routing outputs if present
    ROUTING_PATH = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_email_routing.json")
    routing_by_id = {}
    if ROUTING_PATH.exists():
        routing = json.load(open(ROUTING_PATH, encoding="utf-8"))
        routing_by_id = {r["notification_id"]: r for r in routing}
    for n in outbox:
        notification_id = n["notification_id"]
        if delivery_state["delivered"].get(notification_id, {}).get("result") == "sent":
            continue
        # Use routing outputs if available
        routing = routing_by_id.get(notification_id)
        if routing:
            to = routing["to"]
            cc = routing["cc"]
            bcc = routing["bcc"]
            subject_prefix = routing["subject_prefix"]
        else:
            to = cfg.get("recipients", [])
            cc = []
            bcc = []
            subject_prefix = ""
        subject, body = render_email(n)
        subject = f"{subject_prefix}{subject}"
        recipients = to
        # Add CC/BCC if present
        msg_cc = cc if cc else None
        msg_bcc = bcc if bcc else None
        try:
            # send_email only supports To, so extend for CC/BCC
            msg = EmailMessage()
            msg["From"] = smtp_cfg["from"]
            msg["To"] = ", ".join(recipients)
            if msg_cc:
                msg["Cc"] = ", ".join(msg_cc)
            if msg_bcc:
                msg["Bcc"] = ", ".join(msg_bcc)
            msg["Subject"] = subject
            msg.set_content(body)
            with smtplib.SMTP(smtp_cfg["host"], smtp_cfg.get("port", 25)) as s:
                if smtp_cfg.get("tls"):
                    s.starttls()
                if smtp_cfg.get("user"):
                    s.login(smtp_cfg["user"], smtp_cfg["password"])
                s.send_message(msg)
            result = "sent"
            reason = "Email delivered"
        except Exception as e:
            result = "failed"
            reason = f"Email send error: {e}"
        delivery_state["delivered"][notification_id] = {
            "result": result,
            "reason": reason
        }
    with open(DELIVERY_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(delivery_state, f, indent=2, ensure_ascii=False)
        f.write("\n")

if __name__ == "__main__":
    main()
