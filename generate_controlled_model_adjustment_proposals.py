#!/usr/bin/env python3
"""
AI-RISA v2.0 Controlled Model Adjustments (slice 1): read-only proposal layer.

Builds explicit, reviewable model-adjustment proposal packages from calibration
reporting, action queue priorities, and intervention plans. This script does not
mutate model behavior, scheduler logic, or pipeline outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")
OUTPUT_DIR = Path("ops/model_adjustments")
OUTPUT_JSON = "controlled_model_adjustment_proposals.json"
OUTPUT_MD = "controlled_model_adjustment_proposals.md"

CALIBRATION_REPORT_DEFAULT = Path("ops/calibration/model_calibration_report.json")
ACTION_QUEUE_DEFAULT = Path("ops/calibration_actions/calibration_action_queue.json")
INTERVENTION_PLAN_DEFAULT = Path("ops/calibration_interventions/calibration_intervention_plan.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled model-adjustment proposal artifacts"
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
        "--intervention-plan-json",
        default=str(INTERVENTION_PLAN_DEFAULT),
        help="Calibration intervention plan JSON path relative to repo root",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Proposal output directory relative to repo root",
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


def add_proposal(
    proposals: list[dict[str, Any]],
    *,
    proposal_id: str,
    priority: int,
    source_intervention_id: str | None,
    source_action_id: str | None,
    adjustment_target: str,
    rationale: str,
    expected_benefit: str,
    risk_level: str,
    validation_requirements: list[str],
    source_paths: list[str],
) -> None:
    proposals.append(
        {
            "proposal_id": proposal_id,
            "priority": priority,
            "source_intervention_id": source_intervention_id,
            "source_action_id": source_action_id,
            "adjustment_target": adjustment_target,
            "rationale": rationale,
            "expected_benefit": expected_benefit,
            "risk_level": risk_level,
            "approval_status": "proposed",
            "validation_requirements": validation_requirements,
            "source_paths": source_paths,
        }
    )


def first_by_id(rows: list[dict[str, Any]], row_id: str) -> dict[str, Any] | None:
    for row in rows:
        if isinstance(row, dict) and str(row.get("id") or "") == row_id:
            return row
    return None


def build_proposals(
    calibration_report: dict[str, Any],
    action_queue: dict[str, Any],
    intervention_plan: dict[str, Any],
    source_paths: dict[str, str],
) -> dict[str, Any]:
    proposals: list[dict[str, Any]] = []

    calibration_eval = calibration_report.get("evaluation_summary") if isinstance(calibration_report.get("evaluation_summary"), dict) else {}
    calibration_conf = calibration_report.get("confidence_quality") if isinstance(calibration_report.get("confidence_quality"), dict) else {}
    calibration_miss = calibration_report.get("miss_pattern_summary") if isinstance(calibration_report.get("miss_pattern_summary"), dict) else {}
    calibration_unevaluable = calibration_report.get("unevaluable_summary") if isinstance(calibration_report.get("unevaluable_summary"), dict) else {}

    actions = action_queue.get("actions") if isinstance(action_queue.get("actions"), list) else []
    interventions = intervention_plan.get("interventions") if isinstance(intervention_plan.get("interventions"), list) else []

    action_data_gap = first_by_id(actions, "calibration-data-gap-cleanup")
    action_sparse = first_by_id(actions, "calibration-sparse-confidence-review")
    action_miss = first_by_id(actions, "calibration-recurring-miss-investigation")

    intervention_data_gap = first_by_id(interventions, "intervention-data-gap-prerequisites")
    intervention_bucket = first_by_id(interventions, "intervention-confidence-bucket-coverage")
    intervention_miss = first_by_id(interventions, "intervention-recurring-miss-family")
    intervention_weighting = first_by_id(interventions, "intervention-candidate-weighting-rule-targets")
    intervention_threshold = first_by_id(interventions, "intervention-confidence-threshold-review")

    confidence_coverage = as_float(calibration_conf.get("confidence_coverage"))
    overall_gap = as_float(calibration_conf.get("overall_calibration_gap"))
    pending = as_int(calibration_unevaluable.get("prediction_queue_pending_count"))
    total_incorrect = as_int(calibration_miss.get("total_incorrect"))
    winner_accuracy = as_float(calibration_eval.get("winner_accuracy"))

    # 1) Confidence-threshold tuning review
    if intervention_threshold is not None or overall_gap is not None:
        add_proposal(
            proposals,
            proposal_id="proposal-confidence-threshold-tuning-review",
            priority=1,
            source_intervention_id="intervention-confidence-threshold-review" if intervention_threshold else None,
            source_action_id="calibration-overconfidence-review",
            adjustment_target="confidence_threshold_policy",
            rationale="Calibration gap and/or confidence-threshold intervention signal indicates threshold policy should be reviewed offline.",
            expected_benefit="Reduce confidence miscalibration and high-confidence error risk without immediate production mutation.",
            risk_level="medium",
            validation_requirements=[
                "Offline replay with threshold candidates",
                "No regression in winner accuracy on validation slice",
                "Approval sign-off before any future application",
            ],
            source_paths=[
                source_paths["calibration_report_json"],
                source_paths["action_queue_json"],
                source_paths["intervention_plan_json"],
            ],
        )

    # 2) Confidence-bucket coverage threshold review
    if intervention_bucket is not None or action_sparse is not None or (confidence_coverage is not None and confidence_coverage < 0.70):
        add_proposal(
            proposals,
            proposal_id="proposal-confidence-bucket-coverage-threshold-review",
            priority=1,
            source_intervention_id="intervention-confidence-bucket-coverage" if intervention_bucket else None,
            source_action_id="calibration-sparse-confidence-review" if action_sparse else None,
            adjustment_target="confidence_capture_and_coverage_thresholds",
            rationale="Sparse confidence coverage weakens calibration observability; coverage thresholds and data-capture rules need review packaging.",
            expected_benefit="Improve confidence-signal completeness, enabling stronger future calibration decisions.",
            risk_level="low",
            validation_requirements=[
                "Coverage target definition and monitoring plan",
                "Reconciliation feed compatibility validation",
                "Approval sign-off before any future application",
            ],
            source_paths=[
                source_paths["calibration_report_json"],
                source_paths["action_queue_json"],
                source_paths["intervention_plan_json"],
            ],
        )

    # 3) Miss-family weighting review
    if intervention_miss is not None or action_miss is not None or total_incorrect > 0:
        add_proposal(
            proposals,
            proposal_id="proposal-miss-family-weighting-review",
            priority=2,
            source_intervention_id="intervention-recurring-miss-family" if intervention_miss else None,
            source_action_id="calibration-recurring-miss-investigation" if action_miss else None,
            adjustment_target="miss_family_weighting_candidates",
            rationale="Recurring miss signatures indicate candidate family-weighting hypotheses should be prepared for controlled offline testing.",
            expected_benefit="Targeted reduction of recurring error patterns while preserving guardrails against overfitting.",
            risk_level="high",
            validation_requirements=[
                "Explicit miss-family hypothesis traceability",
                "Offline A/B replay versus baseline",
                "False-positive risk review and approval sign-off",
            ],
            source_paths=[
                source_paths["calibration_report_json"],
                source_paths["action_queue_json"],
                source_paths["intervention_plan_json"],
            ],
        )

    # 4) Rule-review target package
    if intervention_weighting is not None or (winner_accuracy is not None and winner_accuracy < 0.80):
        add_proposal(
            proposals,
            proposal_id="proposal-rule-review-target-package",
            priority=2,
            source_intervention_id="intervention-candidate-weighting-rule-targets" if intervention_weighting else None,
            source_action_id="calibration-recurring-miss-investigation" if action_miss else None,
            adjustment_target="rule_review_target_package",
            rationale="Intervention planning highlights candidate rule-target packages for offline review and governance.",
            expected_benefit="Structured rule-review backlog linked to evidence and priorities, enabling controlled future adjustment cycles.",
            risk_level="medium",
            validation_requirements=[
                "Rule-target package maps to intervention evidence",
                "Offline scenario checks against regression risks",
                "Approval sign-off before any future application",
            ],
            source_paths=[
                source_paths["intervention_plan_json"],
                source_paths["calibration_report_json"],
            ],
        )

    # 5) Data-gap prerequisite package
    if intervention_data_gap is not None or action_data_gap is not None or pending > 0:
        add_proposal(
            proposals,
            proposal_id="proposal-data-gap-prerequisite-package",
            priority=1,
            source_intervention_id="intervention-data-gap-prerequisites" if intervention_data_gap else None,
            source_action_id="calibration-data-gap-cleanup" if action_data_gap else None,
            adjustment_target="data_gap_prerequisite_gates",
            rationale="Backlog and unevaluable conditions require prerequisite gate packaging before model-side adjustments are considered.",
            expected_benefit="Prevents premature adjustment attempts on low-quality or incomplete feedback data.",
            risk_level="low",
            validation_requirements=[
                "Pending backlog threshold definition",
                "Prerequisite gate checklist verification",
                "Approval sign-off before any future application",
            ],
            source_paths=[
                source_paths["calibration_report_json"],
                source_paths["action_queue_json"],
                source_paths["intervention_plan_json"],
            ],
        )

    proposals.sort(
        key=lambda row: (
            as_int(row.get("priority"), 99),
            str(row.get("adjustment_target") or ""),
            str(row.get("proposal_id") or ""),
        )
    )

    priority_counts: dict[str, int] = {"1": 0, "2": 0, "3": 0, "4": 0}
    risk_counts: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
    for row in proposals:
        pkey = str(as_int(row.get("priority"), 4))
        priority_counts[pkey] = priority_counts.get(pkey, 0) + 1
        rkey = str(row.get("risk_level") or "low")
        risk_counts[rkey] = risk_counts.get(rkey, 0) + 1

    top = proposals[0] if proposals else None

    return {
        "generated_at_utc": now_utc_iso(),
        "controlled_model_adjustment_proposals_version": "v2.0-slice-1",
        "source_versions": {
            "calibration_report_version": calibration_report.get("calibration_report_version") if isinstance(calibration_report, dict) else None,
            "calibration_action_queue_version": action_queue.get("calibration_action_queue_version") if isinstance(action_queue, dict) else None,
            "calibration_intervention_plan_version": intervention_plan.get("calibration_intervention_plan_version") if isinstance(intervention_plan, dict) else None,
        },
        "proposal_summary": {
            "total_proposals": len(proposals),
            "priority_counts": priority_counts,
            "risk_level_counts": risk_counts,
            "top_proposal": {
                "proposal_id": top.get("proposal_id") if isinstance(top, dict) else None,
                "adjustment_target": top.get("adjustment_target") if isinstance(top, dict) else None,
                "priority": top.get("priority") if isinstance(top, dict) else None,
                "risk_level": top.get("risk_level") if isinstance(top, dict) else None,
            },
        },
        "proposal_readiness_snapshot": {
            "evaluated_predictions": as_int(calibration_eval.get("total_evaluated_predictions")),
            "winner_accuracy": winner_accuracy,
            "confidence_coverage": confidence_coverage,
            "pending_or_unevaluable": as_int(calibration_unevaluable.get("total_unevaluable_or_pending")),
            "action_queue_items": len(actions),
            "intervention_items": len(interventions),
        },
        "proposals": proposals,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("proposal_summary") if isinstance(payload.get("proposal_summary"), dict) else {}
    snapshot = payload.get("proposal_readiness_snapshot") if isinstance(payload.get("proposal_readiness_snapshot"), dict) else {}
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    proposals = payload.get("proposals") if isinstance(payload.get("proposals"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Model Adjustment Proposals (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Proposals Version: {payload.get('controlled_model_adjustment_proposals_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Proposal Summary")
    lines.append(f"- Total Proposals: {summary.get('total_proposals')}")
    lines.append(f"- Priority Counts: {summary.get('priority_counts')}")
    lines.append(f"- Risk Level Counts: {summary.get('risk_level_counts')}")
    lines.append(f"- Top Proposal: {summary.get('top_proposal')}")
    lines.append("")
    lines.append("## Readiness Snapshot")
    lines.append(f"- Evaluated Predictions: {snapshot.get('evaluated_predictions')}")
    lines.append(f"- Winner Accuracy: {snapshot.get('winner_accuracy')}")
    lines.append(f"- Confidence Coverage: {snapshot.get('confidence_coverage')}")
    lines.append(f"- Pending/Unevaluable: {snapshot.get('pending_or_unevaluable')}")
    lines.append(f"- Action Queue Items: {snapshot.get('action_queue_items')}")
    lines.append(f"- Intervention Items: {snapshot.get('intervention_items')}")
    lines.append("")
    lines.append("## Proposed Adjustment Packages")

    if proposals:
        for row in proposals:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- [P{row.get('priority')}] {row.get('proposal_id')} -> {row.get('adjustment_target')}"
            )
            lines.append(f"  Source Intervention: {row.get('source_intervention_id')}")
            lines.append(f"  Source Action: {row.get('source_action_id')}")
            lines.append(f"  Rationale: {row.get('rationale')}")
            lines.append(f"  Expected Benefit: {row.get('expected_benefit')}")
            lines.append(f"  Risk Level: {row.get('risk_level')}")
            lines.append(f"  Approval Status: {row.get('approval_status')}")
            lines.append(f"  Validation Requirements: {row.get('validation_requirements')}")
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
    intervention_plan_path = Path(args.intervention_plan_json)
    output_dir = Path(args.output_dir)

    calibration_report, calibration_err = safe_read_json(repo_root / calibration_report_path)
    action_queue, action_err = safe_read_json(repo_root / action_queue_path)
    intervention_plan, intervention_err = safe_read_json(repo_root / intervention_plan_path)

    if calibration_err is not None:
        print(f"ERROR: calibration report unavailable: {calibration_err}", file=sys.stderr)
        return 1
    if action_err is not None:
        print(f"ERROR: action queue unavailable: {action_err}", file=sys.stderr)
        return 1
    if intervention_err is not None:
        print(f"ERROR: intervention plan unavailable: {intervention_err}", file=sys.stderr)
        return 1

    if not isinstance(calibration_report, dict) or not isinstance(action_queue, dict) or not isinstance(intervention_plan, dict):
        print("ERROR: one or more source artifacts are not valid JSON objects", file=sys.stderr)
        return 1

    source_paths = {
        "calibration_report_json": normalize_path(calibration_report_path),
        "action_queue_json": normalize_path(action_queue_path),
        "intervention_plan_json": normalize_path(intervention_plan_path),
    }

    payload = build_proposals(
        calibration_report=calibration_report,
        action_queue=action_queue,
        intervention_plan=intervention_plan,
        source_paths=source_paths,
    )

    payload["source_status"] = {
        "calibration_report_json_error": calibration_err,
        "action_queue_json_error": action_err,
        "intervention_plan_json_error": intervention_err,
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
        "[STATUS] total_proposals={total} top_proposal={top}".format(
            total=((payload.get("proposal_summary") or {}).get("total_proposals")),
            top=(((payload.get("proposal_summary") or {}).get("top_proposal") or {}).get("proposal_id")),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
