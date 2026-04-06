"""
build_upcoming_schedule_heartbeat_alert.py

Deterministic alert-state tracker for upcoming schedule heartbeat.

Reads heartbeat, maps health to alert state, tracks incident lifecycle, deduplicates incidents, emits alert artifacts.
"""
import json
import uuid
from pathlib import Path
from datetime import datetime

HEARTBEAT_PATH = Path("ops/events/upcoming_schedule_heartbeat.json")
ALERT_JSON_PATH = Path("ops/events/upcoming_schedule_alert.json")
ALERT_MD_PATH = Path("ops/events/upcoming_schedule_alert.md")
ALERT_STATE_PATH = Path("ops/events/upcoming_schedule_alert_state.json")  # for stable incident tracking

def load_json(path, default=None):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def emit_alert_artifacts(alert):
    with open(ALERT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(alert, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(ALERT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Upcoming Schedule Alert\n\n")
        f.write(f"Alert at: {alert['timestamp']} UTC\n\n")
        f.write(f"Alert active: {alert['alert_active']}\n")
        f.write(f"Alert reason: {alert['alert_reason']}\n")
        f.write(f"Incident ID: {alert['incident_id']}\n")
        f.write(f"Incident status: {alert['incident_status']}\n")
        f.write(f"Opened at: {alert['opened_at']}\n")
        f.write(f"Last seen at: {alert['last_seen_at']}\n")
        f.write(f"Cleared at: {alert['cleared_at']}\n")
        f.write(f"Heartbeat health: {alert['heartbeat_health']}\n")
        f.write(f"Heartbeat timestamp: {alert['heartbeat_timestamp']}\n")
        f.write("\n")

def main():
    now = datetime.utcnow().isoformat() + "Z"
    heartbeat = load_json(HEARTBEAT_PATH, {})
    prev_state = load_json(ALERT_STATE_PATH, {})
    health = heartbeat.get("health", "unknown")
    hb_ts = heartbeat.get("timestamp")
    # Map health to alert
    if health == "healthy":
        alert_active = False
        alert_reason = None
    elif health == "stale":
        alert_active = True
        alert_reason = "stale"
    elif health == "failed":
        alert_active = True
        alert_reason = "failed"
    else:
        alert_active = False
        alert_reason = None
    # Incident tracking
    incident_id = prev_state.get("incident_id")
    incident_status = prev_state.get("incident_status")
    opened_at = prev_state.get("opened_at")
    last_seen_at = now
    cleared_at = prev_state.get("cleared_at")
    # Open new incident if alert just became active
    if alert_active:
        if not prev_state.get("alert_active") or prev_state.get("alert_reason") != alert_reason:
            # New incident
            incident_id = str(uuid.uuid4())
            incident_status = "opened"
            opened_at = now
            cleared_at = None
        else:
            # Ongoing incident
            incident_status = "active"
        # Always update last_seen_at
        last_seen_at = now
        cleared_at = None
    else:
        # If previously active, mark as cleared
        if prev_state.get("alert_active"):
            incident_status = "cleared"
            cleared_at = now
        # else, no incident
    alert = {
        "timestamp": now,
        "alert_active": alert_active,
        "alert_reason": alert_reason,
        "incident_id": incident_id,
        "incident_status": incident_status,
        "opened_at": opened_at,
        "last_seen_at": last_seen_at,
        "cleared_at": cleared_at,
        "heartbeat_health": health,
        "heartbeat_timestamp": hb_ts
    }
    # Save state for next run
    save_json(ALERT_STATE_PATH, alert)
    emit_alert_artifacts(alert)

if __name__ == "__main__":
    main()
