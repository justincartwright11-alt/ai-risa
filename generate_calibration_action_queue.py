#!/usr/bin/env python3
"""
AI-RISA v1.8 Calibration Actions (slice 1): read-only calibration action queue.

Builds a prioritized calibration action queue from the v1.7 calibration report,
reconciliation history, and pending prediction backlog. This script does not
mutate model behavior, pipeline logic, or scheduler behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")
OUTPUT_DIR = Path("ops/calibration_actions")
OUTPUT_JSON = "calibration_action_queue.json"
OUTPUT_MD = "calibration_action_queue.md"

CALIBRATION_REPORT_DEFAULT = Path("ops/calibration/model_calibration_report.json")
RECONCILIATION_CSV_DEFAULT = Path("reports/reconciliation_history_match_report.csv")
PREDICTION_QUEUE_DEFAULT = Path("output/prediction_queue.json")

PRIORITY_CRITICAL = 1
PRIORITY_HIGH = 2
PRIORITY_MEDIUM = 3
PRIORITY_LOW = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only calibration action queue artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument(
        "--calibration-report-json",
        default=str(CALIBRATION_REPORT_DEFAULT),
        help="Calibration report JSON path relative to repo root",
    )
    parser.add_argument(
        "--reconciliation-csv",
        default=str(RECONCILIATION_CSV_DEFAULT),
        help="Reconciliation history CSV path relative to repo root",
    )
    parser.add_argument(
        "--prediction-queue-json",
        default=str(PREDICTION_QUEUE_DEFAULT),
        help="Prediction queue JSON path relative to repo root",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Action queue output directory relative to repo root",
    )
    return parser.parse_args()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_path(path: Path) -> str:
    return path.as_posix()


def safe_read_json(path: Path) -> tuple[Any, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as exc:
        return None, f"unreadable: {exc}"


def safe_read_csv(path: Path) -> tuple[list[dict[str, str]], str | None]:
    if not path.exists():
        return [], "missing"
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f)), None
    except Exception as exc:
        return [], f"unreadable: {exc}"


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def add_action(
    items: list[dict[str, Any]],
    *,
    action_id: str,
    priority: int,
    action_type: str,
    title: str,
    rationale: str,
    evidence: dict[str, Any],
    recommendation: str,
    source_paths: list[str],
) -> None:
    items.append(
        {
            "id": action_id,
            "priority": priority,
            "action_type": action_type,
            "title": title,
            "rationale": rationale,
            "evidence": evidence,
            "recommendation": recommendation,
            "source_paths": source_paths,
        }
    )


def build_action_queue(
    calibration_report: dict[str, Any],
    reconciliation_rows: list[dict[str, str]],
    pending_rows: list[dict[str, Any]],
    source_paths: dict[str, str],
) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []

    evaluation_summary = calibration_report.get("evaluation_summary") if isinstance(calibration_report, dict) else {}
    confidence_quality = calibration_report.get("confidence_quality") if isinstance(calibration_report, dict) else {}
    miss_summary = calibration_report.get("miss_pattern_summary") if isinstance(calibration_report, dict) else {}
    unevaluable_summary = calibration_report.get("unevaluable_summary") if isinstance(calibration_report, dict) else {}

    total_evaluated = as_int((evaluation_summary or {}).get("total_evaluated_predictions"))
    incorrect_count = as_int((evaluation_summary or {}).get("incorrect_count"))
    winner_accuracy = as_float((evaluation_summary or {}).get("winner_accuracy"))

    # 1) Overconfidence correction review
    overconfidence = (confidence_quality or {}).get("overconfidence_indicator") or {}
    overconf_sample = as_int(overconfidence.get("sample_count"))
    overconf_incorrect = as_int(overconfidence.get("incorrect_count"))
    overconf_rate = as_float(overconfidence.get("incorrect_rate"))
    overall_gap = as_float((confidence_quality or {}).get("overall_calibration_gap"))

    if (overconf_sample >= 5 and (overconf_rate is not None and overconf_rate >= 0.20)) or (
        overall_gap is not None and overall_gap >= 0.08
    ):
        add_action(
            actions,
            action_id="calibration-overconfidence-review",
            priority=PRIORITY_CRITICAL,
            action_type="overconfidence_review",
            title="Review overconfidence drift in winner predictions",
            rationale="Confidence appears overstated relative to observed outcome accuracy.",
            evidence={
                "overall_calibration_gap": overall_gap,
                "high_confidence_sample": overconf_sample,
                "high_confidence_incorrect": overconf_incorrect,
                "high_confidence_incorrect_rate": overconf_rate,
            },
            recommendation="Audit high-confidence misses by matchup family and propose a confidence scaling patch candidate.",
            source_paths=[source_paths["calibration_report_json"], source_paths["reconciliation_csv"]],
        )

    # 2) Sparse-confidence bucket review
    confidence_coverage = as_float((confidence_quality or {}).get("confidence_coverage"))
    rows_with_confidence = as_int((confidence_quality or {}).get("rows_with_confidence"))
    confidence_buckets = (confidence_quality or {}).get("confidence_buckets")
    sparse_buckets = 0
    if isinstance(confidence_buckets, dict):
        for row in confidence_buckets.values():
            if isinstance(row, dict) and as_int(row.get("count")) == 0:
                sparse_buckets += 1

    if confidence_coverage is None or confidence_coverage < 0.70 or sparse_buckets >= 3:
        add_action(
            actions,
            action_id="calibration-sparse-confidence-review",
            priority=PRIORITY_HIGH,
            action_type="sparse_confidence_bucket_review",
            title="Review sparse or missing confidence coverage",
            rationale="Confidence buckets are under-populated, reducing calibration signal quality.",
            evidence={
                "confidence_coverage": confidence_coverage,
                "rows_with_confidence": rows_with_confidence,
                "total_evaluated": total_evaluated,
                "sparse_bucket_count": sparse_buckets,
            },
            recommendation="Backfill confidence in resolved records and enforce confidence capture on future reconciled outcomes.",
            source_paths=[source_paths["calibration_report_json"], source_paths["reconciliation_csv"]],
        )

    # 3) Recurring miss-pattern investigation
    top_patterns = (miss_summary or {}).get("top_recurring_patterns")
    if isinstance(top_patterns, list) and top_patterns:
        strongest = top_patterns[:3]
        max_pattern_count = max(as_int(row.get("count")) for row in strongest if isinstance(row, dict))
        priority = PRIORITY_HIGH if max_pattern_count >= 3 else PRIORITY_MEDIUM
        add_action(
            actions,
            action_id="calibration-recurring-miss-investigation",
            priority=priority,
            action_type="recurring_miss_pattern_investigation",
            title="Investigate recurring prediction miss patterns",
            rationale="Incorrect outcomes show repeatable miss signatures that can guide targeted correction.",
            evidence={
                "total_incorrect": as_int((miss_summary or {}).get("total_incorrect")),
                "top_patterns": strongest,
            },
            recommendation="Perform feature-level error analysis on top miss patterns and draft controlled remediation hypotheses.",
            source_paths=[source_paths["calibration_report_json"], source_paths["reconciliation_csv"]],
        )

    # 4) Data-gap / unevaluable cleanup
    pending_count = as_int((unevaluable_summary or {}).get("prediction_queue_pending_count"))
    unevaluable_count = as_int((unevaluable_summary or {}).get("reconciliation_unevaluable_count"))
    pending_reasons = (unevaluable_summary or {}).get("prediction_queue_pending_reasons")
    if pending_count > 0 or unevaluable_count > 0:
        priority = PRIORITY_HIGH if (pending_count + unevaluable_count) >= max(5, total_evaluated) else PRIORITY_MEDIUM
        add_action(
            actions,
            action_id="calibration-data-gap-cleanup",
            priority=priority,
            action_type="data_gap_cleanup",
            title="Reduce pending and unevaluable calibration backlog",
            rationale="Calibration quality is constrained by unresolved outcomes and unevaluable records.",
            evidence={
                "pending_count": pending_count,
                "unevaluable_count": unevaluable_count,
                "pending_reasons": pending_reasons if isinstance(pending_reasons, dict) else {},
                "reconciliation_rows": len(reconciliation_rows),
            },
            recommendation="Prioritize reconciliation of pending prediction outcomes and resolve unevaluable records blocking calibration feedback.",
            source_paths=[
                source_paths["calibration_report_json"],
                source_paths["prediction_queue_json"],
                source_paths["reconciliation_csv"],
            ],
        )

    # 5) Baseline monitoring action if no pressing items surfaced.
    if not actions:
        add_action(
            actions,
            action_id="calibration-monitoring-baseline",
            priority=PRIORITY_LOW,
            action_type="monitoring_baseline",
            title="Maintain calibration monitoring baseline",
            rationale="No acute calibration action triggers were detected from current sources.",
            evidence={
                "total_evaluated": total_evaluated,
                "winner_accuracy": winner_accuracy,
                "pending_count": pending_count,
            },
            recommendation="Continue routine monitoring and wait for larger evaluated sample before model-side changes.",
            source_paths=[source_paths["calibration_report_json"]],
        )

    actions.sort(
        key=lambda row: (
            as_int(row.get("priority"), 99),
            str(row.get("action_type") or ""),
            str(row.get("title") or ""),
        )
    )

    priority_counts: dict[str, int] = {"1": 0, "2": 0, "3": 0, "4": 0}
    for row in actions:
        key = str(as_int(row.get("priority"), 4))
        priority_counts[key] = priority_counts.get(key, 0) + 1

    top_action = actions[0] if actions else None

    return {
        "generated_at_utc": now_utc_iso(),
        "calibration_action_queue_version": "v1.8-slice-1",
        "source_calibration_report_version": calibration_report.get("calibration_report_version") if isinstance(calibration_report, dict) else None,
        "queue_summary": {
            "total_actions": len(actions),
            "priority_counts": priority_counts,
            "top_action": {
                "id": top_action.get("id") if isinstance(top_action, dict) else None,
                "title": top_action.get("title") if isinstance(top_action, dict) else None,
                "priority": top_action.get("priority") if isinstance(top_action, dict) else None,
                "action_type": top_action.get("action_type") if isinstance(top_action, dict) else None,
            },
        },
        "calibration_snapshot": {
            "evaluated_predictions": total_evaluated,
            "incorrect_predictions": incorrect_count,
            "winner_accuracy": winner_accuracy,
            "confidence_coverage": confidence_coverage,
            "pending_or_unevaluable": pending_count + unevaluable_count,
        },
        "actions": actions,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("queue_summary") if isinstance(payload.get("queue_summary"), dict) else {}
    snapshot = payload.get("calibration_snapshot") if isinstance(payload.get("calibration_snapshot"), dict) else {}
    actions = payload.get("actions") if isinstance(payload.get("actions"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Calibration Action Queue (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Action Queue Version: {payload.get('calibration_action_queue_version')}")
    lines.append(f"Source Calibration Report Version: {payload.get('source_calibration_report_version')}")
    lines.append("")
    lines.append("## Queue Summary")
    lines.append(f"- Total Actions: {summary.get('total_actions')}")
    lines.append(f"- Priority Counts: {summary.get('priority_counts')}")
    lines.append(f"- Top Action: {summary.get('top_action')}")
    lines.append("")
    lines.append("## Calibration Snapshot")
    lines.append(f"- Evaluated Predictions: {snapshot.get('evaluated_predictions')}")
    lines.append(f"- Incorrect Predictions: {snapshot.get('incorrect_predictions')}")
    lines.append(f"- Winner Accuracy: {snapshot.get('winner_accuracy')}")
    lines.append(f"- Confidence Coverage: {snapshot.get('confidence_coverage')}")
    lines.append(f"- Pending/Unevaluable: {snapshot.get('pending_or_unevaluable')}")
    lines.append("")
    lines.append("## Prioritized Actions")

    if actions:
        for row in actions:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- [P{row.get('priority')}] {row.get('title')} ({row.get('action_type')})"
            )
            lines.append(f"  Rationale: {row.get('rationale')}")
            lines.append(f"  Recommendation: {row.get('recommendation')}")
            lines.append(f"  Evidence: {row.get('evidence')}")
            lines.append(f"  Sources: {row.get('source_paths')}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Source Paths")
    lines.append(f"- {payload.get('source_paths')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)
    if not repo_root.exists():
        print(f"ERROR: repo root not found: {repo_root}", file=sys.stderr)
        return 1

    calibration_report_path = Path(args.calibration_report_json)
    reconciliation_csv_path = Path(args.reconciliation_csv)
    prediction_queue_path = Path(args.prediction_queue_json)
    output_dir = Path(args.output_dir)

    calibration_report, calibration_err = safe_read_json(repo_root / calibration_report_path)
    reconciliation_rows, reconciliation_err = safe_read_csv(repo_root / reconciliation_csv_path)
    pending_payload, pending_err = safe_read_json(repo_root / prediction_queue_path)

    if calibration_err is not None:
        print(f"ERROR: calibration report unavailable: {calibration_err}", file=sys.stderr)
        return 1

    if not isinstance(calibration_report, dict):
        print("ERROR: calibration report JSON is not an object", file=sys.stderr)
        return 1

    pending_rows = pending_payload if isinstance(pending_payload, list) else []

    source_paths = {
        "calibration_report_json": normalize_path(calibration_report_path),
        "reconciliation_csv": normalize_path(reconciliation_csv_path),
        "prediction_queue_json": normalize_path(prediction_queue_path),
    }

    payload = build_action_queue(
        calibration_report=calibration_report,
        reconciliation_rows=reconciliation_rows,
        pending_rows=pending_rows,
        source_paths=source_paths,
    )

    payload["source_status"] = {
        "reconciliation_csv_error": reconciliation_err,
        "prediction_queue_json_error": pending_err,
    }

    out_root = repo_root / output_dir
    out_root.mkdir(parents=True, exist_ok=True)

    out_json = out_root / OUTPUT_JSON
    out_md = out_root / OUTPUT_MD

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    out_md.write_text(render_markdown(payload), encoding="utf-8")

    print(f"[WRITE] {out_json}")
    print(f"[WRITE] {out_md}")
    print(
        "[STATUS] total_actions={total} top_action={top}".format(
            total=((payload.get("queue_summary") or {}).get("total_actions")),
            top=(((payload.get("queue_summary") or {}).get("top_action") or {}).get("title")),
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
