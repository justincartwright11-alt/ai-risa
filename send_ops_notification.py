#!/usr/bin/env python3
"""
AI-RISA v1.1 Ops Visibility: optional notification hooks.

Local-first notification on alert state transition:
- false -> true: alert notice
- true -> false: recovery notice
- unchanged: no notice unless forced
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")

DEFAULT_ALERT_FILE = Path("ops/alerts/latest_run_alert.json")
DEFAULT_STATE_FILE = Path("ops/state/notification_state.json")
DEFAULT_OUT_DIR = Path("ops/notifications")
DEFAULT_CONFIG = Path("ops/config/notification_config.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send optional ops notification on alert-state transitions")
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--alert-file", default=str(DEFAULT_ALERT_FILE))
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--force", action="store_true", help="Send notification even when alert state is unchanged")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def render_markdown(event: dict[str, Any]) -> str:
    lines = [
        "# AI-RISA Ops Notification Event",
        "",
        f"Generated at: {event.get('generated_at')}",
        f"Notification Sent: {event.get('sent')}",
        f"Notification Type: {event.get('notification_type')}",
        f"Reason: {event.get('reason')}",
        "",
        "## Alert Snapshot",
        f"- Alert: {event.get('alert', {}).get('alert')}",
        f"- Reason Codes: {', '.join(event.get('alert', {}).get('reason_codes') or []) or 'none'}",
        f"- Message: {event.get('alert', {}).get('message')}",
        "",
        "## Sink Results",
        f"- stdout: {event.get('sinks', {}).get('stdout')}",
        f"- local_artifact: {event.get('sinks', {}).get('local_artifact')}",
        f"- webhook: {event.get('sinks', {}).get('webhook')}",
        "",
    ]
    return "\n".join(lines)


def post_webhook(url: str, payload: dict[str, Any], timeout: int = 10) -> tuple[bool, str]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        return False, f"HTTPError {exc.code}"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)

    alert_file = repo_root / Path(args.alert_file)
    state_file = repo_root / Path(args.state_file)
    out_dir = repo_root / Path(args.out_dir)
    config_file = repo_root / Path(args.config)

    alert = read_json(alert_file, default={})
    if not isinstance(alert, dict):
        print("ERROR: alert payload unreadable", file=sys.stderr)
        return 1

    current_alert = bool(alert.get("alert"))
    prev_state = read_json(state_file, default={})
    if not isinstance(prev_state, dict):
        prev_state = {}
    previous_alert = prev_state.get("last_alert")

    should_send = False
    notification_type = "none"
    reason = "state_unchanged"

    if args.force:
        should_send = True
        notification_type = "forced"
        reason = "forced"
    elif previous_alert is None:
        should_send = False
        notification_type = "none"
        reason = "state_initialized"
    elif (previous_alert is False) and (current_alert is True):
        should_send = True
        notification_type = "alert"
        reason = "alert_transition"
    elif (previous_alert is True) and (current_alert is False):
        should_send = True
        notification_type = "recovery"
        reason = "recovery_transition"

    event = {
        "generated_at": now_iso(),
        "sent": should_send,
        "notification_type": notification_type,
        "reason": reason,
        "previous_alert": previous_alert,
        "current_alert": current_alert,
        "alert": {
            "alert": alert.get("alert"),
            "reason_codes": alert.get("reason_codes", []),
            "message": alert.get("message"),
            "latest_run_id": alert.get("latest_run_id"),
            "latest_run_status": alert.get("latest_run_status"),
            "latest_exit_code": alert.get("latest_exit_code"),
        },
        "sinks": {
            "stdout": "not_sent",
            "local_artifact": "not_sent",
            "webhook": "disabled",
        },
    }

    if should_send:
        print(f"[NOTIFY] type={notification_type} alert={current_alert} reasons={alert.get('reason_codes', [])}")
        event["sinks"]["stdout"] = "sent"
        event["sinks"]["local_artifact"] = "sent"

        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        event_json = out_dir / f"notification_{stamp}.json"
        event_md = out_dir / f"notification_{stamp}.md"
        latest_json = out_dir / "latest_notification.json"
        latest_md = out_dir / "latest_notification.md"

        write_json(event_json, event)
        event_md.write_text(render_markdown(event), encoding="utf-8")
        write_json(latest_json, event)
        latest_md.write_text(render_markdown(event), encoding="utf-8")

        config = read_json(config_file, default={})
        if isinstance(config, dict) and config.get("enabled") and config.get("webhook_url"):
            ok, detail = post_webhook(str(config.get("webhook_url")), event)
            event["sinks"]["webhook"] = f"sent:{detail}" if ok else f"failed:{detail}"
            write_json(latest_json, event)
            latest_md.write_text(render_markdown(event), encoding="utf-8")

    else:
        print(f"[NOTIFY] no_send reason={reason} current_alert={current_alert}")

    next_state = {
        "updated_at": now_iso(),
        "last_alert": current_alert,
        "last_notification_type": notification_type if should_send else "none",
        "last_reason": reason,
        "last_alert_snapshot": {
            "alert": alert.get("alert"),
            "reason_codes": alert.get("reason_codes", []),
            "latest_run_id": alert.get("latest_run_id"),
        },
    }
    write_json(state_file, next_state)

    print(f"[WRITE] {state_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
