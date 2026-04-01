#!/usr/bin/env python3
"""
AI-RISA v1.1 Ops Visibility: scheduler verification.

Validates required tasks exist, are enabled, are in acceptable state, and point
at expected script wrappers.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")
TASK_FOLDER_DEFAULT = "\\AI-RISA\\"

OUTPUT_JSON = Path("ops/verification/scheduler_verification.json")
OUTPUT_MD = Path("ops/verification/scheduler_verification.md")

ALLOWED_STATES = {"Ready", "Running", "Queued"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify AI-RISA scheduled task wiring")
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--task-folder", default=TASK_FOLDER_DEFAULT)
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def expected_tasks(repo_root: Path) -> dict[str, dict[str, str]]:
    return {
        "AI-RISA-Pipeline-Dry-Run": {"script": str((repo_root / "schedule_full_pipeline_dry_run.ps1").resolve())},
        "AI-RISA-Pipeline-Normal-Run": {"script": str((repo_root / "schedule_full_pipeline_run.ps1").resolve())},
        "AI-RISA-Latest-Run-Alert-Check": {"script": str((repo_root / "schedule_latest_run_alert_check.ps1").resolve())},
        "AI-RISA-Daily-Health-Summary": {"script": str((repo_root / "schedule_daily_health_summary.ps1").resolve())},
        "AI-RISA-Weekly-Health-Rollup": {"script": str((repo_root / "schedule_weekly_health_rollup.ps1").resolve())},
    }


def fetch_tasks(task_folder: str) -> list[dict[str, Any]]:
    ps_cmd = (
        "$tasks = Get-ScheduledTask -TaskPath '" + task_folder + "' -ErrorAction SilentlyContinue;"
        "if ($null -eq $tasks) { '[]'; exit 0 };"
        "$rows = @();"
        "foreach ($t in $tasks) {"
        "  $action = $t.Actions | Select-Object -First 1;"
        "  $principal = $t.Principal;"
        "  $enabled = $true;"
        "  if ($t.PSObject.Properties.Name -contains 'Enabled') { $enabled = [bool]$t.Enabled }"
        "  elseif ($t.Settings -and ($t.Settings.PSObject.Properties.Name -contains 'Enabled')) { $enabled = [bool]$t.Settings.Enabled };"
        "  $rows += [PSCustomObject]@{"
        "    TaskName=$t.TaskName; State=[string]$t.State; Enabled=$enabled;"
        "    Execute=[string]$action.Execute; Arguments=[string]$action.Arguments; WorkingDirectory=[string]$action.WorkingDirectory;"
        "    UserId=[string]$principal.UserId; LogonType=[string]$principal.LogonType"
        "  }"
        "};"
        "$rows | ConvertTo-Json -Depth 5 -Compress"
    )

    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_cmd],
        capture_output=True,
        text=True,
    )

    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "Unable to query scheduled tasks")

    raw = proc.stdout.strip()
    if not raw:
        return []

    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def extract_file_argument(arguments: str | None) -> str | None:
    if not arguments:
        return None

    m = re.search(r"-File\s+\"([^\"]+)\"", arguments, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    m = re.search(r"-File\s+([^\s]+)", arguments, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    return None


def norm_path(p: str | None) -> str | None:
    if p is None:
        return None
    try:
        return str(Path(p).resolve()).lower()
    except Exception:
        return str(p).strip().lower()


def evaluate_tasks(repo_root: Path, task_folder: str) -> dict[str, Any]:
    expected = expected_tasks(repo_root)

    try:
        actual_list = fetch_tasks(task_folder)
        fetch_error = None
    except Exception as exc:
        actual_list = []
        fetch_error = str(exc)

    actual = {str(row.get("TaskName")): row for row in actual_list if isinstance(row, dict)}

    fail_count = 0
    warn_count = 0
    task_results: list[dict[str, Any]] = []

    for task_name, exp in expected.items():
        checks: list[dict[str, str]] = []
        status = "pass"

        row = actual.get(task_name)
        if row is None:
            status = "fail"
            checks.append({"level": "fail", "code": "missing_task", "message": "Task not found."})
        else:
            enabled = bool(row.get("Enabled"))
            state = str(row.get("State") or "")
            execute = str(row.get("Execute") or "")
            arguments = str(row.get("Arguments") or "")
            working_dir = str(row.get("WorkingDirectory") or "")
            user_id = str(row.get("UserId") or "")
            logon_type = str(row.get("LogonType") or "")

            if not enabled:
                status = "fail"
                checks.append({"level": "fail", "code": "disabled_task", "message": "Task is disabled."})

            if state not in ALLOWED_STATES:
                if status != "fail":
                    status = "warn"
                checks.append(
                    {
                        "level": "warn",
                        "code": "unexpected_state",
                        "message": f"Task state '{state}' not in acceptable set {sorted(ALLOWED_STATES)}.",
                    }
                )

            expected_script = norm_path(exp.get("script"))
            found_script = norm_path(extract_file_argument(arguments))
            if expected_script and found_script != expected_script:
                status = "fail"
                checks.append(
                    {
                        "level": "fail",
                        "code": "unexpected_action_path",
                        "message": f"Expected script '{exp.get('script')}', got '{extract_file_argument(arguments)}'.",
                    }
                )

            if "powershell" not in execute.lower():
                if status != "fail":
                    status = "warn"
                checks.append(
                    {
                        "level": "warn",
                        "code": "unexpected_execute",
                        "message": f"Expected PowerShell execute target, got '{execute}'.",
                    }
                )

            if working_dir:
                if status != "fail":
                    status = "warn"
                checks.append(
                    {
                        "level": "warn",
                        "code": "unexpected_working_directory",
                        "message": f"Working directory is set to '{working_dir}'.",
                    }
                )

            if "SYSTEM" not in user_id.upper():
                if status != "fail":
                    status = "warn"
                checks.append(
                    {
                        "level": "warn",
                        "code": "unexpected_principal",
                        "message": f"Principal user is '{user_id}' (expected SYSTEM).",
                    }
                )

            if logon_type and logon_type.lower() != "serviceaccount":
                if status != "fail":
                    status = "warn"
                checks.append(
                    {
                        "level": "warn",
                        "code": "unexpected_logon_type",
                        "message": f"LogonType is '{logon_type}' (expected ServiceAccount).",
                    }
                )

            if not checks:
                checks.append({"level": "pass", "code": "task_ok", "message": "Task configuration validated."})

        if status == "fail":
            fail_count += 1
        elif status == "warn":
            warn_count += 1

        task_results.append(
            {
                "task_name": task_name,
                "status": status,
                "checks": checks,
            }
        )

    overall = "fail" if fail_count > 0 else ("warn" if warn_count > 0 else "pass")

    return {
        "generated_at": now_iso(),
        "task_folder": task_folder,
        "overall_status": overall,
        "summary": {
            "required_tasks": len(expected),
            "fail_count": fail_count,
            "warn_count": warn_count,
            "pass_count": len(expected) - fail_count - warn_count,
        },
        "errors": [fetch_error] if fetch_error else [],
        "tasks": task_results,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# AI-RISA Scheduler Verification",
        "",
        f"Generated at: {payload.get('generated_at')}",
        f"Task Folder: {payload.get('task_folder')}",
        f"Overall Status: {payload.get('overall_status')}",
        "",
        "## Summary",
        f"- Required Tasks: {payload.get('summary', {}).get('required_tasks')}",
        f"- Pass: {payload.get('summary', {}).get('pass_count')}",
        f"- Warn: {payload.get('summary', {}).get('warn_count')}",
        f"- Fail: {payload.get('summary', {}).get('fail_count')}",
        "",
        "## Task Checks",
    ]

    for task in payload.get("tasks", []):
        lines.append(f"- {task.get('task_name')}: {task.get('status')}")
        for check in task.get("checks", []):
            lines.append(f"  - [{check.get('level')}] {check.get('code')}: {check.get('message')}")

    errors = payload.get("errors", [])
    if errors:
        lines.extend(["", "## Errors"])
        for err in errors:
            lines.append(f"- {err}")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)

    payload = evaluate_tasks(repo_root, args.task_folder)

    out_json = repo_root / OUTPUT_JSON
    out_md = repo_root / OUTPUT_MD
    out_json.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    out_md.write_text(render_markdown(payload), encoding="utf-8")

    print(f"[WRITE] {out_json}")
    print(f"[WRITE] {out_md}")
    print(f"[STATUS] overall={payload.get('overall_status')}")

    if payload.get("overall_status") == "fail":
        return 2
    if payload.get("overall_status") == "warn":
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
