"""
build_upcoming_schedule_cadence_runner.py

Deterministic cadence-controlled runner for the full upcoming schedule cycle.

Reads cadence state/config, decides if a cycle is due, and invokes build_upcoming_schedule_cycle_lock_guard.py only when due.
Emits:
- ops/events/upcoming_schedule_cadence_run.json
- ops/events/upcoming_schedule_cadence_run.md

See v66.9 locked spec for full requirements.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

HEARTBEAT_JSON_PATH = Path("ops/events/upcoming_schedule_heartbeat.json")
HEARTBEAT_MD_PATH = Path("ops/events/upcoming_schedule_heartbeat.md")
HEARTBEAT_STALE_MINUTES = 90  # If last due invocation >90min ago, consider stale

CADENCE_STATE_PATH = Path("ops/events/upcoming_schedule_cadence_state.json")
CADENCE_CONFIG_PATH = Path("ops/events/upcoming_schedule_cadence_config.json")
RUN_JSON_PATH = Path("ops/events/upcoming_schedule_cadence_run.json")
RUN_MD_PATH = Path("ops/events/upcoming_schedule_cadence_run.md")
LOCK_GUARD = "build_upcoming_schedule_cycle_lock_guard.py"
PYTHON = r"C:\\Users\\jusin\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe"

# Default cadence config: run every 1 hour
DEFAULT_CONFIG = {
    "interval_minutes": 60
}

def load_json(path, default=None):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def emit_run_artifacts(result):
    with open(RUN_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(RUN_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Upcoming Schedule Cadence Runner\n\n")
        f.write(f"Run at: {result['timestamp']} UTC\n\n")
        f.write(f"Cadence config: {result['cadence_config']}\n\n")
        f.write(f"Last run: {result['last_run']}\n")
        f.write(f"Next run: {result['next_run']}\n\n")
        f.write(f"Due: {result['due']}\n\n")
        f.write(f"Cycle invoked: {result['cycle_invoked']}\n\n")
        if result['cycle_invoked']:
            f.write(f"Cycle result: {result['cycle_result']}\n")
            f.write(f"Lock guard artifact: {result.get('lock_guard_json', 'N/A')}\n")
            f.write(f"Lock guard report: {result.get('lock_guard_md', 'N/A')}\n")
        f.write("\n")

def emit_heartbeat_artifacts(hb):
    with open(HEARTBEAT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(hb, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(HEARTBEAT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Upcoming Schedule Heartbeat\n\n")
        f.write(f"Heartbeat at: {hb['timestamp']} UTC\n\n")
        f.write(f"Health: {hb['health']}\n\n")
        f.write(f"Last due invocation: {hb['last_due_invocation']}\n")
        f.write(f"Last not-due invocation: {hb['last_not_due_invocation']}\n")
        f.write(f"Last cycle invoked: {hb['last_cycle_invoked']}\n")
        f.write(f"Last cycle result: {hb['last_cycle_result']}\n")
        f.write(f"Last outcome: {hb['last_outcome']}\n")
        f.write(f"Stale: {hb['stale']}\n")
        f.write(f"Failure: {hb['failure']}\n")
        f.write(f"Invocation source: {hb['invocation_source']}\n")
        f.write(f"Due: {hb['due']}\n")
        f.write(f"Cycle invoked: {hb['cycle_invoked']}\n")
        f.write(f"Cycle result: {hb['cycle_result']}\n")
        f.write(f"Next run: {hb['next_run']}\n")
        f.write("\n")

def main():
    now = datetime.utcnow()
    config = load_json(CADENCE_CONFIG_PATH, DEFAULT_CONFIG)
    state = load_json(CADENCE_STATE_PATH, {})
    last_run = state.get("last_run")
    next_run = state.get("next_run")
    interval = timedelta(minutes=config.get("interval_minutes", 60))
    # Parse last_run and next_run as datetimes if present
    last_run_dt = None
    next_run_dt = None
    if last_run:
        try:
            last_run_dt = datetime.fromisoformat(last_run.replace("Z", ""))
        except Exception:
            last_run_dt = None
    if next_run:
        try:
            next_run_dt = datetime.fromisoformat(next_run.replace("Z", ""))
        except Exception:
            next_run_dt = None
    due = False
    if not next_run_dt or now >= next_run_dt:
        due = True
    result = {
        "timestamp": now.isoformat() + "Z",
        "cadence_config": config,
        "last_run": last_run,
        "next_run": None,
        "due": due,
        "cycle_invoked": False,
        "cycle_result": None,
        "lock_guard_json": None,
        "lock_guard_md": None,
    }
    # --- Heartbeat logic ---
    # Load previous heartbeat
    prev_hb = None
    if HEARTBEAT_JSON_PATH.exists():
        try:
            with open(HEARTBEAT_JSON_PATH, "r", encoding="utf-8") as f:
                prev_hb = json.load(f)
        except Exception:
            prev_hb = None

    invocation_source = "manual" if any(arg in sys.argv for arg in ["--manual", "-m"]) else "scheduled"
    last_due_invocation = prev_hb["last_due_invocation"] if prev_hb else None
    last_not_due_invocation = prev_hb["last_not_due_invocation"] if prev_hb else None
    last_cycle_invoked = prev_hb["last_cycle_invoked"] if prev_hb else None
    last_cycle_result = prev_hb["last_cycle_result"] if prev_hb else None
    last_outcome = prev_hb["last_outcome"] if prev_hb else None
    # If due, update last_due_invocation, last_cycle_invoked, last_cycle_result, last_outcome
    # If not due, update last_not_due_invocation, last_outcome

    if due:
        # Update state for next run
        result["last_run"] = now.isoformat() + "Z"
        result["next_run"] = (now + interval).isoformat() + "Z"
        # Save new state before invoking cycle
        save_json(CADENCE_STATE_PATH, {"last_run": result["last_run"], "next_run": result["next_run"]})
        # Invoke lock guard
        proc = subprocess.run([PYTHON, LOCK_GUARD], capture_output=True, text=True, check=False)
        result["cycle_invoked"] = True
        result["cycle_result"] = "success" if proc.returncode == 0 else f"fail (code {proc.returncode})"
        # Record lock guard artifacts if present
        lg_json = Path("ops/events/upcoming_schedule_cycle_lock_guard.json")
        lg_md = Path("ops/events/upcoming_schedule_cycle_lock_guard.md")
        if lg_json.exists():
            result["lock_guard_json"] = str(lg_json)
        if lg_md.exists():
            result["lock_guard_md"] = str(lg_md)
        # If lock guard succeeded, invoke alerting orchestrator
        alerting_json = None
        alerting_md = None
        if proc.returncode == 0:
            alerting_proc = subprocess.run([PYTHON, "build_upcoming_schedule_alerting_orchestrator.py"], capture_output=True, text=True, check=False)
            result["alerting_result"] = "success" if alerting_proc.returncode == 0 else f"fail (code {alerting_proc.returncode})"
            alerting_json_path = Path("ops/events/upcoming_schedule_alerting_cycle_summary.json")
            alerting_md_path = Path("ops/events/upcoming_schedule_alerting_cycle_report.md")
            if alerting_json_path.exists():
                alerting_json = str(alerting_json_path)
            if alerting_md_path.exists():
                alerting_md = str(alerting_md_path)
            result["alerting_json"] = alerting_json
            result["alerting_md"] = alerting_md
        else:
            result["alerting_result"] = "skipped (lock guard failed)"
        # Heartbeat update for due path
        last_due_invocation = now.isoformat() + "Z"
        last_cycle_invoked = now.isoformat() + "Z"
        last_cycle_result = result["cycle_result"]
        last_outcome = result["cycle_result"]
    else:
        # Not due: next_run remains as previously scheduled or computed from now
        if next_run_dt:
            result["next_run"] = next_run_dt.isoformat() + "Z"
        else:
            result["next_run"] = (now + interval).isoformat() + "Z"
        # Save state (no change to last_run)
        save_json(CADENCE_STATE_PATH, {"last_run": last_run, "next_run": result["next_run"]})
        # Heartbeat update for not-due path
        last_not_due_invocation = now.isoformat() + "Z"
        last_outcome = "not-due"

    # --- Stale/failure detection ---
    stale = False
    failure = False
    health = "healthy"
    # Stale if last_due_invocation is too old
    if last_due_invocation:
        try:
            last_due_dt = datetime.fromisoformat(last_due_invocation.replace("Z", ""))
            if (now - last_due_dt) > timedelta(minutes=HEARTBEAT_STALE_MINUTES):
                stale = True
                health = "stale"
        except Exception:
            pass
    # Failure if last_cycle_result is a fail
    if last_cycle_result and last_cycle_result.startswith("fail"):
        failure = True
        health = "failed"

    # Emit heartbeat artifact
    heartbeat = {
        "timestamp": now.isoformat() + "Z",
        "health": health,
        "last_due_invocation": last_due_invocation,
        "last_not_due_invocation": last_not_due_invocation,
        "last_cycle_invoked": last_cycle_invoked,
        "last_cycle_result": last_cycle_result,
        "last_outcome": last_outcome,
        "stale": stale,
        "failure": failure,
        "invocation_source": invocation_source,
        "due": due,
        "cycle_invoked": result["cycle_invoked"],
        "cycle_result": result["cycle_result"],
        "next_run": result["next_run"]
    }
    emit_heartbeat_artifacts(heartbeat)
    emit_run_artifacts(result)

    # --- Runtime history ledger integration (v67.9) ---
    # Import and call ledger after all runtime+alerting logic

    from build_upcoming_schedule_runtime_history_ledger import append_history
    run_id = result["timestamp"] + ":" + heartbeat["invocation_source"]
    entry = {
        "run_id": run_id,
        "invoked_at": result["timestamp"],
        "invocation_source": heartbeat["invocation_source"],
        "due_decision": result["due"],
        "cycle_invoked": result["cycle_invoked"],
        "cycle_status": result["cycle_result"],
        "alerting_status": result.get("alerting_result", "N/A"),
        "heartbeat_health": heartbeat["health"],
        "lock_status": result["cycle_result"] if result["cycle_invoked"] else "not-invoked",
        "notification_summary": result.get("alerting_json", "N/A"),
        "terminal_status": (result["cycle_result"] if result["cycle_invoked"] else "not-invoked")
    }
    append_history(entry)

    # --- Escalation policy engine integration (v68.1) ---
    # Import and call escalation policy engine after history ledger is updated
    try:
        esc_proc = subprocess.run([
            PYTHON,
            "build_upcoming_schedule_escalation_policy_engine.py"
        ], capture_output=True, text=True, check=False)
        result["escalation_policy_result"] = "success" if esc_proc.returncode == 0 else f"fail (code {esc_proc.returncode})"
    except Exception as e:
        result["escalation_policy_result"] = f"exception: {e}"

    # --- Escalation notification outbox and dispatcher integration (v68.4) ---
    escalation_notification_outbox_result = None
    escalation_notification_dispatch_result = None
    escalation_notification_delivery_json = None
    escalation_notification_delivery_md = None
    if due and result["cycle_result"] == "success" and result["escalation_policy_result"] == "success":
        # Outbox
        outbox_proc = subprocess.run([
            PYTHON,
            "build_upcoming_schedule_escalation_notification_outbox.py"
        ], capture_output=True, text=True, check=False)
        escalation_notification_outbox_result = "success" if outbox_proc.returncode == 0 else f"fail (code {outbox_proc.returncode})"
        # Dispatcher (only if outbox succeeded)
        if outbox_proc.returncode == 0:
            dispatch_proc = subprocess.run([
                PYTHON,
                "build_upcoming_schedule_escalation_notification_dispatcher.py"
            ], capture_output=True, text=True, check=False)
            escalation_notification_dispatch_result = "success" if dispatch_proc.returncode == 0 else f"fail (code {dispatch_proc.returncode})"
            # Artifacts
            delivery_json_path = Path("ops/events/upcoming_schedule_escalation_notification_delivery.json")
            delivery_md_path = Path("ops/events/upcoming_schedule_escalation_notification_delivery.md")
            if delivery_json_path.exists():
                escalation_notification_delivery_json = str(delivery_json_path)
            if delivery_md_path.exists():
                escalation_notification_delivery_md = str(delivery_md_path)
        else:
            escalation_notification_dispatch_result = "skipped (outbox failed)"
    else:
        escalation_notification_outbox_result = "skipped (not due or prior failure)"
        escalation_notification_dispatch_result = "skipped (not due or prior failure)"

    # Emit unified runtime+alerting+escalation+notification summary
    summary_json_path = Path("ops/events/upcoming_schedule_runtime_escalation_notification_summary.json")
    summary_md_path = Path("ops/events/upcoming_schedule_runtime_escalation_notification_summary.md")
    summary = {
        "timestamp": now.isoformat() + "Z",
        "due": due,
        "cycle_result": result["cycle_result"],
        "alerting_result": result.get("alerting_result"),
        "escalation_policy_result": result.get("escalation_policy_result"),
        "escalation_notification_outbox_result": escalation_notification_outbox_result,
        "escalation_notification_dispatch_result": escalation_notification_dispatch_result,
        "escalation_notification_delivery_json": escalation_notification_delivery_json,
        "escalation_notification_delivery_md": escalation_notification_delivery_md
    }
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(summary_md_path, "w", encoding="utf-8") as f:
        f.write(f"# Runtime + Escalation Notification Summary\n\n")
        for k, v in summary.items():
            f.write(f"- {k}: {v}\n")

    if due and result["cycle_result"] != "success":
        sys.exit(1)

if __name__ == "__main__":
    main()
