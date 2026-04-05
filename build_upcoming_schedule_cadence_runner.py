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
    else:
        # Not due: next_run remains as previously scheduled or computed from now
        if next_run_dt:
            result["next_run"] = next_run_dt.isoformat() + "Z"
        else:
            result["next_run"] = (now + interval).isoformat() + "Z"
        # Save state (no change to last_run)
        save_json(CADENCE_STATE_PATH, {"last_run": last_run, "next_run": result["next_run"]})
    emit_run_artifacts(result)
    if due and result["cycle_result"] != "success":
        sys.exit(1)

if __name__ == "__main__":
    main()
