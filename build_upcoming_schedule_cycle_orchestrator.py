"""
build_upcoming_schedule_cycle_orchestrator.py

Deterministic orchestrator for the full upcoming schedule cycle.

Runs the following stages in order:
1. build_upcoming_schedule_auto.py
2. build_upcoming_schedule_dispatch_consumer.py
3. build_upcoming_schedule_dispatch_reconciliation.py
4. build_upcoming_schedule_queue_state_promotion.py

Emits:
- ops/events/upcoming_schedule_cycle_summary.json
- ops/events/upcoming_schedule_cycle_report.md

See v66.7 locked spec for full requirements.
"""
import subprocess
import json
import hashlib
from pathlib import Path
from datetime import datetime
import sys

STAGES = [
    ("discovery", "build_upcoming_schedule_auto.py"),
    ("dispatch_consumer", "build_upcoming_schedule_dispatch_consumer.py"),
    ("reconciliation", "build_upcoming_schedule_dispatch_reconciliation.py"),
    ("promotion", "build_upcoming_schedule_queue_state_promotion.py"),
]

SUMMARY_PATH = Path("ops/events/upcoming_schedule_cycle_summary.json")
REPORT_PATH = Path("ops/events/upcoming_schedule_cycle_report.md")
PYTHON = r"C:\\Users\\jusin\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe"


def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def run_stage(stage_name, script):
    result = {
        "stage": stage_name,
        "script": script,
        "status": None,
        "stdout": None,
        "stderr": None,
        "artifacts": [],
        "hashes": {},
        "start_time": datetime.utcnow().isoformat() + "Z",
        "end_time": None,
    }
    try:
        proc = subprocess.run([PYTHON, script], capture_output=True, text=True, check=False)
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        result["status"] = "success" if proc.returncode == 0 else f"fail (code {proc.returncode})"
        result["end_time"] = datetime.utcnow().isoformat() + "Z"
        return result, proc.returncode == 0
    except Exception as e:
        result["status"] = f"exception: {e}"
        result["end_time"] = datetime.utcnow().isoformat() + "Z"
        return result, False

def main():
    cycle = {
        "cycle_start": datetime.utcnow().isoformat() + "Z",
        "stages": [],
        "cycle_status": None,
        "cycle_end": None,
    }
    fail_fast = False
    for stage_name, script in STAGES:
        if fail_fast:
            cycle["stages"].append({
                "stage": stage_name,
                "script": script,
                "status": "skipped (prior failure)",
                "stdout": None,
                "stderr": None,
                "artifacts": [],
                "hashes": {},
                "start_time": None,
                "end_time": None,
            })
            continue
        result, ok = run_stage(stage_name, script)
        # Optionally, record known artifacts and hashes for each stage
        # (For this slice, just record the main outputs if present)
        if stage_name == "discovery":
            for f in ["ops/events/upcoming_schedule_auto_discovery.json", "ops/events/upcoming_schedule_auto_discovery.md"]:
                if Path(f).exists():
                    result["artifacts"].append(f)
                    result["hashes"][f] = hash_file(f)
        elif stage_name == "dispatch_consumer":
            for f in ["ops/events/upcoming_schedule_dispatch_outcome.json", "ops/events/upcoming_schedule_dispatch_outcome.md"]:
                if Path(f).exists():
                    result["artifacts"].append(f)
                    result["hashes"][f] = hash_file(f)
        elif stage_name == "reconciliation":
            for f in ["ops/events/upcoming_schedule_queue_sink_reconciled.json", "ops/events/upcoming_schedule_reconciliation_report.md"]:
                if Path(f).exists():
                    result["artifacts"].append(f)
                    result["hashes"][f] = hash_file(f)
        elif stage_name == "promotion":
            for f in ["ops/events/upcoming_schedule_queue_sink.json", "ops/events/upcoming_schedule_queue_promotion.json", "ops/events/upcoming_schedule_queue_promotion.md"]:
                if Path(f).exists():
                    result["artifacts"].append(f)
                    result["hashes"][f] = hash_file(f)
        cycle["stages"].append(result)
        if not ok:
            fail_fast = True
    cycle["cycle_end"] = datetime.utcnow().isoformat() + "Z"
    cycle["cycle_status"] = "success" if not fail_fast else "fail"
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(cycle, f, indent=2, ensure_ascii=False)
        f.write("\n")
    # Emit Markdown report
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Upcoming Schedule Cycle Orchestrator\n\n")
        f.write(f"Cycle run at: {cycle['cycle_start']} UTC\n\n")
        f.write(f"Cycle status: {cycle['cycle_status']}\n\n")
        for stage in cycle["stages"]:
            f.write(f"## Stage: {stage['stage']}\n")
            f.write(f"Script: {stage['script']}\n")
            f.write(f"Status: {stage['status']}\n")
            if stage["artifacts"]:
                f.write(f"Artifacts: {', '.join(stage['artifacts'])}\n")
            if stage["hashes"]:
                for k, v in stage["hashes"].items():
                    f.write(f"  - {k}: {v}\n")
            f.write("\n")
        f.write(f"Cycle end: {cycle['cycle_end']} UTC\n")
    # Exit nonzero if fail-fast
    if fail_fast:
        sys.exit(1)

if __name__ == "__main__":
    main()
