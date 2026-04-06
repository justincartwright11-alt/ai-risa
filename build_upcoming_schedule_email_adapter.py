"""
build_upcoming_schedule_email_adapter.py

Email transport adapter for upcoming schedule notification dispatcher (v67.6).

- Reads pending notifications from outbox
- Renders deterministic subject/body
- Sends via configured SMTP
- Records delivery result in dispatcher ledger format
"""
import json
import smtplib
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime
import sys

OUTBOX_PATH = Path("ops/events/upcoming_schedule_notification_outbox.json")
OUTBOX_STATE_PATH = Path("ops/events/upcoming_schedule_notification_outbox_state.json")
DELIVERY_STATE_PATH = Path("ops/events/upcoming_schedule_notification_delivery_state.json")

CONFIG_PATH = Path("ops/events/upcoming_schedule_email_config.json")

TRANSPORT = "email"

class ConfigError(Exception):
    pass

def load_json(path, default=None):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def get_config():
    config = load_json(CONFIG_PATH)
    if not config:
        raise ConfigError(f"Missing config: {CONFIG_PATH}")
    required = ["smtp_host", "smtp_port", "smtp_user", "smtp_password", "sender", "recipients"]
    for k in required:
        if k not in config or not config[k]:
            raise ConfigError(f"Missing required config key: {k}")
    return config

def render_email(notification, incident_state):
    ntype = notification["notification_type"]
    incident_id = notification["incident_id"]
    if ntype == "opened":
        subject = f"[ALERT] Incident {incident_id} OPENED"
        body = f"Incident {incident_id} has been opened.\n\nDetails: {incident_state}"
    elif ntype == "cleared":
        subject = f"[RESOLVED] Incident {incident_id} CLEARED"
        body = f"Incident {incident_id} has been cleared.\n\nDetails: {incident_state}"
    else:
        subject = f"[NOTIFICATION] Incident {incident_id}"
        body = f"Incident {incident_id} notification.\n\nDetails: {incident_state}"
    return subject, body

def send_email(config, subject, body):
    msg = EmailMessage()
    msg["From"] = config["sender"]
    msg["To"] = ", ".join(config["recipients"])
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(config["smtp_host"], config["smtp_port"]) as server:
            server.starttls()
            server.login(config["smtp_user"], config["smtp_password"])
            server.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    now = datetime.utcnow().isoformat() + "Z"
    outbox = load_json(OUTBOX_PATH, {"notifications": []})
    prev_delivery = load_json(DELIVERY_STATE_PATH, {"deliveries": []})
    deliveries = prev_delivery["deliveries"][:]
    delivered_ids = {d["notification_id"]: d for d in deliveries if d["delivery_status"] == "sent"}
    try:
        config = get_config()
    except ConfigError as e:
        print(f"CONFIG ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    for n in outbox["notifications"]:
        nid = n["notification_id"]
        if nid in delivered_ids:
            continue
        prev = next((d for d in deliveries if d["notification_id"] == nid), None)
        attempt_count = prev["attempt_count"] + 1 if prev else 1
        first_attempt_at = prev["first_attempt_at"] if prev else now
        # For demo, incident_state is just the notification dict
        subject, body = render_email(n, json.dumps(n, indent=2))
        sent, error = send_email(config, subject, body)
        status = "sent" if sent else "failed"
        delivered_at = now if status == "sent" else None
        record = {
            "notification_id": nid,
            "delivery_id": f"{nid}:email:{first_attempt_at}",
            "delivery_status": status,
            "transport": TRANSPORT,
            "attempt_count": attempt_count,
            "first_attempt_at": first_attempt_at,
            "last_attempt_at": now,
            "delivered_at": delivered_at,
            "failure_reason": error
        }
        if prev:
            deliveries = [d if d["notification_id"] != nid else record for d in deliveries]
        else:
            deliveries.append(record)
    result = {"deliveries": deliveries}
    with open(DELIVERY_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")

if __name__ == "__main__":
    main()
