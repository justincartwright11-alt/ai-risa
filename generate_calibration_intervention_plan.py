#!/usr/bin/env python3
"""
AI-RISA v1.9 Calibration Interventions (slice 1): read-only intervention plan.

Builds a reviewable intervention plan from calibration diagnostics and action
queue artifacts. This script does not mutate model behavior, scheduler logic,
or pipeline outputs.
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
OUTPUT_DIR = Path("ops/calibration_interventions")
OUTPUT_JSON = "calibration_intervention_plan.json"
OUTPUT_MD = "calibration_intervention_plan.md"

CALIBRATION_REPORT_DEFAULT = Path("ops/calibration/model_calibration_report.json")
ACTION_QUEUE_DEFAULT = Path("ops/calibration_actions/calibration_action_queue.json")
RECONCILIATION_CSV_DEFAULT = Path("reports/reconciliation_history_match_report.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only calibration intervention plan artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument(
        "--calibration-report-json",
        default=str(CALIBRATION_REPORT_DEFAULT),
        help="Calibration report JSON path relative to repo root",
    )
    parser.add_argument(
        "--action-queue-json",
        default=str(ACTION_QUEUE_DEFAULT),
        help="Calibration action queue JSON path relative to repo root",
    )
    parser.add_argument(
        "--reconciliation-csv",
        default=str(RECONCILIATION_CSV_DEFAULT),
        help="Reconciliation history CSV path relative to repo root",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Intervention plan output directory relative to repo root",
    )
    return parser.parse_args()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_path(path: Path) -> str:
    return path.as_posix()


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


def add_intervention(
    interventions: list[dict[str, Any]],
    *,
    intervention_id: str,
    priority: int,
    intervention_type: str,
    title: str,
    objective: str,
    trigger_signals: dict[str, Any],
    proposal: str,
    validation_checks: list[str],
    prerequisites: list[str],
    source_paths: list[str],
) -> None:
    interventions.append(
        {
            "id": intervention_id,
            "priority": priority,
            "intervention_type": intervention_type,
            "title": title,
            "objective": objective,
            "trigger_signals": trigger_signals,
            "proposal": proposal,
            "validation_checks": validation_checks,
            "prerequisites": prerequisites,
            "source_paths": source_paths,
            "approval_status": "proposed",
        }
    )


def build_intervention_plan(
    calibration_report: dict[str, Any],
    action_queue: dict[str, Any],
    reconciliation_rows: list[dict[str, str]],
    source_paths: dict[str, str],
) -> dict[str, Any]:
    interventions: list[dict[str, Any]] = []

    eval_summary = calibration_report.get("evaluation_summary") or {}
    confidence = calibration_report.get("confidence_quality") or {}
    misses = calibration_report.get("miss_pattern_summary") or {}
    unevaluable = calibration_report.get("unevaluable_summary") or {}

    action_items = action_queue.get("actions") if isinstance(action_queue.get("actions"), list) else []
    action_ids = {str(row.get("id") or "") for row in action_items if isinstance(row, dict)}

    evaluated = as_int(eval_summary.get("total_evaluated_predictions"))
    winner_accuracy = as_float(eval_summary.get("winner_accuracy"))
    pending = as_int(unevaluable.get("prediction_queue_pending_count"))
    confidence_coverage = as_float(confidence.get("confidence_coverage"))

    # 1) Confidence-threshold review
    overconf = confidence.get("overconfidence_indicator") if isinstance(confidence.get("overconfidence_indicator"), dict) else {}
    calib_gap = as_float(confidence.get("overall_calibration_gap"))
    overconf_rate = as_float(overconf.get("incorrect_rate"))
    overconf_sample = as_int(overconf.get("sample_count"))
    if (
        "calibration-overconfidence-review" in action_ids
        or (calib_gap is not None and calib_gap >= 0.08)
        or (overconf_sample >= 5 and overconf_rate is not None and overconf_rate >= 0.20)
    ):
        add_intervention(
            interventions,
            intervention_id="intervention-confidence-threshold-review",
            priority=1,
            intervention_type="confidence_threshold_review",
            title="Review confidence threshold and scaling policy",
            objective="Reduce overconfident winner calls while preserving genuine high-confidence signal.",
            trigger_signals={
                "overall_calibration_gap": calib_gap,
                "high_confidence_sample": overconf_sample,
                "high_confidence_incorrect_rate": overconf_rate,
            },
            proposal="Draft candidate confidence-threshold adjustments and scaling rules for offline replay evaluation only.",
            validation_checks=[
                "No production model mutation in this slice",
                "Offline replay shows reduced high-confidence miss rate",
                "Net winner accuracy does not regress",
            ],
            prerequisites=[
                "Sufficient evaluated sample volume",
                "Review sign-off from calibration operator",
            ],
            source_paths=[source_paths["calibration_report_json"], source_paths["calibration_action_queue_json"]],
        )

    # 2) Confidence-bucket coverage review
    bucket_map = confidence.get("confidence_buckets") if isinstance(confidence.get("confidence_buckets"), dict) else {}
    sparse_buckets = sum(
        1
        for row in bucket_map.values()
        if isinstance(row, dict) and as_int(row.get("count")) == 0
    )
    if (
        "calibration-sparse-confidence-review" in action_ids
        or confidence_coverage is None
        or confidence_coverage < 0.70
        or sparse_buckets >= 3
    ):
        add_intervention(
            interventions,
            intervention_id="intervention-confidence-bucket-coverage",
            priority=2,
            intervention_type="confidence_bucket_coverage_review",
            title="Improve confidence-bucket coverage quality",
            objective="Increase calibration observability by improving confidence capture and bucket population.",
            trigger_signals={
                "confidence_coverage": confidence_coverage,
                "sparse_bucket_count": sparse_buckets,
                "evaluated_predictions": evaluated,
            },
            proposal="Define data and instrumentation review tasks that ensure confidence is consistently captured in reconciled outcomes.",
            validation_checks=[
                "Coverage trend improves over subsequent reconciled samples",
                "Bucket population broadens beyond a single band",
            ],
            prerequisites=[
                "Reconciliation schema remains unchanged",
                "Data-source owners confirm confidence field availability",
            ],
            source_paths=[source_paths["calibration_report_json"], source_paths["reconciliation_csv"]],
        )

    # 3) Recurring miss-family investigation
    top_patterns = misses.get("top_recurring_patterns") if isinstance(misses.get("top_recurring_patterns"), list) else []
    if "calibration-recurring-miss-investigation" in action_ids or top_patterns:
        add_intervention(
            interventions,
            intervention_id="intervention-recurring-miss-family",
            priority=2,
            intervention_type="recurring_miss_family_investigation",
            title="Investigate recurring miss families and rule targets",
            objective="Identify stable miss signatures and candidate weighting or rule-review targets.",
            trigger_signals={
                "total_incorrect": as_int(misses.get("total_incorrect")),
                "top_recurring_patterns": top_patterns[:5],
            },
            proposal="Map recurring miss signatures to candidate feature-weight and rule-review hypotheses for offline test design.",
            validation_checks=[
                "Hypotheses trace to explicit recurring miss evidence",
                "Offline tests include both hit-rate and false-positive guardrails",
            ],
            prerequisites=[
                "Pattern evidence remains above minimum recurrence threshold",
                "Action-queue review sign-off",
            ],
            source_paths=[
                source_paths["calibration_report_json"],
                source_paths["calibration_action_queue_json"],
                source_paths["reconciliation_csv"],
            ],
        )

    # 4) Data-gap cleanup prerequisites
    if "calibration-data-gap-cleanup" in action_ids or pending > 0:
        add_intervention(
            interventions,
            intervention_id="intervention-data-gap-prerequisites",
            priority=1,
            intervention_type="data_gap_cleanup_prerequisites",
            title="Define data-gap cleanup prerequisites",
            objective="Establish prerequisite data quality and backlog thresholds before any model-side interventions.",
            trigger_signals={
                "pending_backlog": pending,
                "reconciliation_unevaluable": as_int(unevaluable.get("reconciliation_unevaluable_count")),
                "winner_accuracy": winner_accuracy,
            },
            proposal="Set explicit backlog reduction and reconciliation completeness gates required before intervention execution.",
            validation_checks=[
                "Pending backlog trends downward",
                "Unevaluable cases are actively triaged and reduced",
                "Intervention execution remains blocked until prerequisites pass",
            ],
            prerequisites=[
                "Backlog owner assignment",
                "Weekly reconciliation throughput checkpoints",
            ],
            source_paths=[
                source_paths["calibration_report_json"],
                source_paths["calibration_action_queue_json"],
            ],
        )

    # 5) Candidate weighting/rule-review target plan
    if top_patterns or (winner_accuracy is not None and winner_accuracy < 0.80):
        add_intervention(
            interventions,
            intervention_id="intervention-candidate-weighting-rule-targets",
            priority=3,
            intervention_type="candidate_weighting_rule_review_targets",
            title="Prepare candidate weighting and rule-review target set",
            objective="Create a controlled shortlist of weighting/rule areas for offline evaluation proposals.",
            trigger_signals={
                "winner_accuracy": winner_accuracy,
                "evaluated_predictions": evaluated,
                "pattern_signal_count": len(top_patterns),
            },
            proposal="Draft non-production candidate weighting/rule review targets linked to recurring miss evidence and queue priorities.",
            validation_checks=[
                "Target set maps to explicit calibration/action evidence",
                "No direct model mutation in this slice",
            ],
            prerequisites=[
                "Intervention governance checklist approved",
                "Offline test harness readiness",
            ],
            source_paths=[
                source_paths["calibration_report_json"],
                source_paths["calibration_action_queue_json"],
                source_paths["reconciliation_csv"],
            ],
        )

    if not interventions:
        add_intervention(
            interventions,
            intervention_id="intervention-monitoring-baseline",
            priority=4,
            intervention_type="monitoring_baseline",
            title="Maintain intervention-monitoring baseline",
            objective="Keep intervention planning in observe-only mode until stronger signals emerge.",
            trigger_signals={
                "evaluated_predictions": evaluated,
                "winner_accuracy": winner_accuracy,
            },
            proposal="Re-run calibration diagnostics on next reconciliation window before proposing interventions.",
            validation_checks=["No production behavior changes"],
            prerequisites=["Next reconciliation refresh"],
            source_paths=[source_paths["calibration_report_json"]],
        )

    interventions.sort(
        key=lambda row: (
            as_int(row.get("priority"), 99),
            str(row.get("intervention_type") or ""),
            str(row.get("title") or ""),
        )
    )

    priority_counts: dict[str, int] = {"1": 0, "2": 0, "3": 0, "4": 0}
    for row in interventions:
        key = str(as_int(row.get("priority"), 4))
        priority_counts[key] = priority_counts.get(key, 0) + 1

    top = interventions[0] if interventions else None

    return {
        "generated_at_utc": now_utc_iso(),
        "calibration_intervention_plan_version": "v1.9-slice-1",
        "source_versions": {
            "calibration_report_version": calibration_report.get("calibration_report_version") if isinstance(calibration_report, dict) else None,
            "calibration_action_queue_version": action_queue.get("calibration_action_queue_version") if isinstance(action_queue, dict) else None,
        },
        "plan_summary": {
            "total_interventions": len(interventions),
            "priority_counts": priority_counts,
            "top_intervention": {
                "id": top.get("id") if isinstance(top, dict) else None,
                "title": top.get("title") if isinstance(top, dict) else None,
                "priority": top.get("priority") if isinstance(top, dict) else None,
                "intervention_type": top.get("intervention_type") if isinstance(top, dict) else None,
            },
        },
        "intervention_readiness_snapshot": {
            "evaluated_predictions": evaluated,
            "winner_accuracy": winner_accuracy,
            "confidence_coverage": confidence_coverage,
            "pending_or_unevaluable": as_int(unevaluable.get("total_unevaluable_or_pending")),
            "action_queue_items": len(action_items),
            "reconciliation_rows": len(reconciliation_rows),
        },
        "interventions": interventions,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("plan_summary") if isinstance(payload.get("plan_summary"), dict) else {}
    snapshot = payload.get("intervention_readiness_snapshot") if isinstance(payload.get("intervention_readiness_snapshot"), dict) else {}
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    interventions = payload.get("interventions") if isinstance(payload.get("interventions"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Calibration Intervention Plan (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Intervention Plan Version: {payload.get('calibration_intervention_plan_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Plan Summary")
    lines.append(f"- Total Interventions: {summary.get('total_interventions')}")
    lines.append(f"- Priority Counts: {summary.get('priority_counts')}")
    lines.append(f"- Top Intervention: {summary.get('top_intervention')}")
    lines.append("")
    lines.append("## Intervention Readiness Snapshot")
    lines.append(f"- Evaluated Predictions: {snapshot.get('evaluated_predictions')}")
    lines.append(f"- Winner Accuracy: {snapshot.get('winner_accuracy')}")
    lines.append(f"- Confidence Coverage: {snapshot.get('confidence_coverage')}")
    lines.append(f"- Pending/Unevaluable: {snapshot.get('pending_or_unevaluable')}")
    lines.append(f"- Action Queue Items: {snapshot.get('action_queue_items')}")
    lines.append(f"- Reconciliation Rows: {snapshot.get('reconciliation_rows')}")
    lines.append("")
    lines.append("## Proposed Interventions")

    if interventions:
        for row in interventions:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- [P{row.get('priority')}] {row.get('title')} ({row.get('intervention_type')})"
            )
            lines.append(f"  Objective: {row.get('objective')}")
            lines.append(f"  Proposal: {row.get('proposal')}")
            lines.append(f"  Trigger Signals: {row.get('trigger_signals')}")
            lines.append(f"  Validation Checks: {row.get('validation_checks')}")
            lines.append(f"  Prerequisites: {row.get('prerequisites')}")
            lines.append(f"  Approval Status: {row.get('approval_status')}")
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
    action_queue_path = Path(args.action_queue_json)
    reconciliation_csv_path = Path(args.reconciliation_csv)
    output_dir = Path(args.output_dir)

    calibration_report, calibration_err = safe_read_json(repo_root / calibration_report_path)
    action_queue, action_err = safe_read_json(repo_root / action_queue_path)
    reconciliation_rows, reconciliation_err = safe_read_csv(repo_root / reconciliation_csv_path)

    if calibration_err is not None:
        print(f"ERROR: calibration report unavailable: {calibration_err}", file=sys.stderr)
        return 1
    if action_err is not None:
        print(f"ERROR: action queue unavailable: {action_err}", file=sys.stderr)
        return 1

    if not isinstance(calibration_report, dict):
        print("ERROR: calibration report JSON is not an object", file=sys.stderr)
        return 1
    if not isinstance(action_queue, dict):
        print("ERROR: action queue JSON is not an object", file=sys.stderr)
        return 1

    source_paths = {
        "calibration_report_json": normalize_path(calibration_report_path),
        "calibration_action_queue_json": normalize_path(action_queue_path),
        "reconciliation_csv": normalize_path(reconciliation_csv_path),
    }

    payload = build_intervention_plan(
        calibration_report=calibration_report,
        action_queue=action_queue,
        reconciliation_rows=reconciliation_rows,
        source_paths=source_paths,
    )

    payload["source_status"] = {
        "calibration_report_json_error": calibration_err,
        "calibration_action_queue_json_error": action_err,
        "reconciliation_csv_error": reconciliation_err,
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
        "[STATUS] total_interventions={total} top_intervention={top}".format(
            total=((payload.get("plan_summary") or {}).get("total_interventions")),
            top=(((payload.get("plan_summary") or {}).get("top_intervention") or {}).get("title")),
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
