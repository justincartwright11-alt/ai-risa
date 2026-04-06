"""
build_upcoming_schedule_escalation_policy_engine.py

Deterministic escalation policy engine for upcoming schedule (v68.0).
Reads alert state and runtime history, computes escalation state, and emits artifacts.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

ALERT_JSON = Path("ops/events/upcoming_schedule_alert.json")
ALERT_STATE_JSON = Path("ops/events/upcoming_schedule_alert_state.json")
HISTORY_JSON = Path("ops/events/upcoming_schedule_runtime_history.json")
ESCALATION_JSON = Path("ops/events/upcoming_schedule_escalation.json")
ESCALATION_MD = Path("ops/events/upcoming_schedule_escalation.md")
ESCALATION_STATE_JSON = Path("ops/events/upcoming_schedule_escalation_state.json")

# Policy thresholds
FAILED_RUNS_THRESHOLD = 3
STALE_RUNS_THRESHOLD = 2
BLOCKED_RUNS_THRESHOLD = 2
INCIDENT_AGE_THRESHOLD_MIN = 120


def load_json(path, default=None):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def stable_id(*args):
    s = ":".join(str(a) for a in args)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def compute_escalation():
    alert = load_json(ALERT_JSON, {})
    alert_state = load_json(ALERT_STATE_JSON, {})
    history = load_json(HISTORY_JSON, {"history": []})["history"]
    prev_state = load_json(ESCALATION_STATE_JSON, {})
    now = datetime.utcnow()
    # Compute metrics
    consecutive_failed = 0
    consecutive_stale = 0
    blocked_count = 0
    incident_age_min = 0
    last_status = None
    for run in reversed(history):
        if run["cycle_status"].startswith("fail"):
            consecutive_failed += 1
        else:
            break
    for run in reversed(history):
        if run["heartbeat_health"] == "stale":
            consecutive_stale += 1
        else:
            break
    for run in reversed(history):
        if run["lock_status"].startswith("fail") or run["lock_status"] == "blocked":
            blocked_count += 1
        else:
            break
    # Incident age
    incident_opened = alert.get("opened_at")
    if incident_opened:
        try:
            opened_dt = datetime.fromisoformat(incident_opened.replace("Z", ""))
            incident_age_min = int((now - opened_dt).total_seconds() // 60)
        except Exception:
            incident_age_min = 0
    # Escalation logic
    escalation_active = False
    escalation_reason = None
    escalation_level = None
    escalation_status = "none"
    opened_at = None
    cleared_at = None
    last_seen_at = now.isoformat() + "Z"
    if consecutive_failed >= FAILED_RUNS_THRESHOLD:
        escalation_active = True
        escalation_reason = "consecutive_failed_runs"
        escalation_level = "critical"
        escalation_status = "opened"
        opened_at = prev_state.get("opened_at") or now.isoformat() + "Z"
    elif consecutive_stale >= STALE_RUNS_THRESHOLD:
        escalation_active = True
        escalation_reason = "consecutive_stale_runs"
        escalation_level = "warning"
        escalation_status = "opened"
        opened_at = prev_state.get("opened_at") or now.isoformat() + "Z"
    elif blocked_count >= BLOCKED_RUNS_THRESHOLD:
        escalation_active = True
        escalation_reason = "blocked_runs"
        escalation_level = "warning"
        escalation_status = "opened"
        opened_at = prev_state.get("opened_at") or now.isoformat() + "Z"
    elif incident_age_min >= INCIDENT_AGE_THRESHOLD_MIN:
        escalation_active = True
        escalation_reason = "incident_age"
        escalation_level = "warning"
        escalation_status = "opened"
        opened_at = prev_state.get("opened_at") or now.isoformat() + "Z"
    else:
        escalation_active = False
        escalation_reason = None
        escalation_level = None
        escalation_status = "cleared" if prev_state.get("escalation_active") else "none"
        opened_at = prev_state.get("opened_at")
        cleared_at = now.isoformat() + "Z" if prev_state.get("escalation_active") else None
    escalation_id = stable_id(opened_at, escalation_reason, escalation_level) if escalation_active or opened_at else None
    # Build state
    state = {
        "escalation_active": escalation_active,
        "escalation_reason": escalation_reason,
        "escalation_level": escalation_level,
        "escalation_id": escalation_id,
        "escalation_status": escalation_status,
        "opened_at": opened_at,
        "last_seen_at": last_seen_at,
        "cleared_at": cleared_at,
        "trigger_metrics": {
            "consecutive_failed_runs": consecutive_failed,
            "consecutive_stale_runs": consecutive_stale,
            "blocked_run_count": blocked_count,
            "incident_age_minutes": incident_age_min
        }
    }
    save_json(ESCALATION_STATE_JSON, state)
    # Emit artifact
    artifact = {
        "escalation": state,
        "alert": alert,
        "alert_state": alert_state,
        "history_tail": history[-5:] if len(history) > 5 else history
    }
    save_json(ESCALATION_JSON, artifact)
    # Emit Markdown
    with open(ESCALATION_MD, "w", encoding="utf-8") as f:
        f.write(f"# Upcoming Schedule Escalation Report\n\n")
        f.write(f"Escalation Active: {state['escalation_active']}\n")
        f.write(f"Reason: {state['escalation_reason']}\n")
        f.write(f"Level: {state['escalation_level']}\n")
        f.write(f"Status: {state['escalation_status']}\n")
        f.write(f"Opened at: {state['opened_at']}\n")
        f.write(f"Last seen at: {state['last_seen_at']}\n")
        f.write(f"Cleared at: {state['cleared_at']}\n")
        f.write(f"Trigger metrics: {state['trigger_metrics']}\n")

if __name__ == "__main__":
    compute_escalation()
