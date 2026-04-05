"""
build_upcoming_schedule_alerting_orchestrator.py

Deterministic orchestrator for the upcoming schedule alerting pipeline (v67.7).

Runs the alerting chain in strict order:
1. build_upcoming_schedule_heartbeat_alert.py
2. build_upcoming_schedule_notification_outbox.py
3. build_upcoming_schedule_notification_dispatcher.py

Emits a machine-readable summary and a Markdown report.
Fails fast if any stage fails. No notification dispatch if alert/outbox fails.
"""
import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path

SUMMARY_JSON = Path("ops/events/upcoming_schedule_alerting_cycle_summary.json")
SUMMARY_MD = Path("ops/events/upcoming_schedule_alerting_cycle_report.md")

STAGES = [
    ("heartbeat_alert", [sys.executable, "build_upcoming_schedule_heartbeat_alert.py"]),
    ("notification_outbox", [sys.executable, "build_upcoming_schedule_notification_outbox.py"]),
    ("notification_dispatcher", [sys.executable, "build_upcoming_schedule_notification_dispatcher.py"]),
]

def run_stage(name, cmd):
    start = datetime.utcnow().isoformat() + "Z"
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        status = "success"
        error = None
    except subprocess.CalledProcessError as e:
        status = "fail"
        error = e.stderr or str(e)
    end = datetime.utcnow().isoformat() + "Z"
    return {
        "stage": name,
        "status": status,
        "start": start,
        "end": end,
        "error": error,
        "stdout": result.stdout if status == "success" else None,
        "stderr": result.stderr if status == "success" else error,
        "cmd": cmd
    }

def main():
    cycle = {"stages": [], "start": datetime.utcnow().isoformat() + "Z"}
    for name, cmd in STAGES:
        stage_result = run_stage(name, cmd)
        cycle["stages"].append(stage_result)
        if stage_result["status"] != "success":
            cycle["end"] = datetime.utcnow().isoformat() + "Z"
            cycle["result"] = "fail"
            with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
                json.dump(cycle, f, indent=2, ensure_ascii=False)
                f.write("\n")
            with open(SUMMARY_MD, "w", encoding="utf-8") as f:
                f.write(f"# Alerting Cycle Report\n\n")
                for s in cycle["stages"]:
                    f.write(f"- {s['stage']}: {s['status']}\n")
                    if s['status'] != 'success':
                        f.write(f"  - Error: {s['error']}\n")
            sys.exit(1)
    cycle["end"] = datetime.utcnow().isoformat() + "Z"
    cycle["result"] = "success"
    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(cycle, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write(f"# Alerting Cycle Report\n\n")
        for s in cycle["stages"]:
            f.write(f"- {s['stage']}: {s['status']}\n")
    
if __name__ == "__main__":
    main()
