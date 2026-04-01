#!/usr/bin/env python3
"""
AI-RISA v2.2 Adjustment Validation Manifests (slice 1): read-only validation layer.

Builds validation-manifest records from controlled model-adjustment proposals and
approval-ledger control state. This script does not mutate model behavior,
proposal artifacts, approval-ledger artifacts, scheduler logic, or pipeline outputs.
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
OUTPUT_JSON = "model_adjustment_validation_manifests.json"
OUTPUT_MD = "model_adjustment_validation_manifests.md"

PROPOSALS_DEFAULT = Path("ops/model_adjustments/controlled_model_adjustment_proposals.json")
APPROVAL_LEDGER_DEFAULT = Path("ops/model_adjustments/model_adjustment_approval_ledger.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only model-adjustment validation manifests"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument(
        "--proposals-json",
        default=str(PROPOSALS_DEFAULT),
        help="Controlled model-adjustment proposals JSON path relative to repo root",
    )
    parser.add_argument(
        "--approval-ledger-json",
        default=str(APPROVAL_LEDGER_DEFAULT),
        help="Model-adjustment approval ledger JSON path relative to repo root",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Validation-manifest output directory relative to repo root",
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


def proposal_family_from_id(proposal_id: str) -> str:
    token = str(proposal_id or "").strip()
    if token.startswith("proposal-"):
        return token[len("proposal-") :]
    return token or "unknown"


def as_list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value:
        if item is None:
            continue
        output.append(str(item))
    return output


def required_test_classes_for_risk(risk_level: str) -> list[str]:
    risk = str(risk_level or "").lower()
    if risk == "high":
        return [
            "offline_replay",
            "ab_regression",
            "stress_edge_case_review",
        ]
    if risk == "medium":
        return [
            "offline_replay",
            "ab_regression",
        ]
    return [
        "offline_replay",
        "coherence_sanity_checks",
    ]


def required_metrics_for_target(adjustment_target: str) -> list[str]:
    target = str(adjustment_target or "")
    base = [
        "winner_accuracy",
        "confidence_calibration_gap",
        "high_confidence_error_rate",
    ]
    if "coverage" in target:
        return base + ["confidence_coverage"]
    if "weighting" in target or "rule" in target:
        return base + ["miss_family_error_rate"]
    if "data_gap" in target:
        return base + ["pending_or_unevaluable_rate"]
    return base


def pass_criteria_for_metrics(required_metrics: list[str]) -> list[str]:
    criteria = [
        "No regression on safety guardrails versus baseline",
        "No statistically meaningful degradation in winner_accuracy",
    ]
    if "confidence_calibration_gap" in required_metrics:
        criteria.append("confidence_calibration_gap does not worsen versus baseline")
    if "high_confidence_error_rate" in required_metrics:
        criteria.append("high_confidence_error_rate does not worsen versus baseline")
    if "confidence_coverage" in required_metrics:
        criteria.append("confidence_coverage meets defined minimum threshold")
    if "pending_or_unevaluable_rate" in required_metrics:
        criteria.append("pending_or_unevaluable_rate does not worsen versus baseline")
    if "miss_family_error_rate" in required_metrics:
        criteria.append("miss_family_error_rate improves or remains neutral versus baseline")
    return criteria


def rollback_requirements() -> list[str]:
    return [
        "Document rollback trigger thresholds before any future application",
        "Preserve baseline configuration snapshot for immediate restoration",
        "Require operator sign-off on rollback plan completeness",
    ]


def index_ledger_by_proposal_id(approval_ledger_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = (
        approval_ledger_payload.get("approval_ledger")
        if isinstance(approval_ledger_payload.get("approval_ledger"), list)
        else []
    )
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        proposal_id = str(row.get("proposal_id") or "").strip()
        if proposal_id:
            indexed[proposal_id] = row
    return indexed


def build_manifests(
    proposals_payload: dict[str, Any],
    approval_ledger_payload: dict[str, Any],
    source_paths: dict[str, str],
) -> dict[str, Any]:
    proposals = (
        proposals_payload.get("proposals")
        if isinstance(proposals_payload.get("proposals"), list)
        else []
    )
    ledger_by_proposal_id = index_ledger_by_proposal_id(approval_ledger_payload)

    manifest_rows: list[dict[str, Any]] = []
    blocked_non_approved = 0
    linked_to_ledger = 0

    for idx, row in enumerate(proposals, start=1):
        if not isinstance(row, dict):
            continue

        proposal_id = str(row.get("proposal_id") or "").strip()
        proposal_family = proposal_family_from_id(proposal_id)
        adjustment_target = row.get("adjustment_target")
        risk_level = str(row.get("risk_level") or "low")

        ledger_row = ledger_by_proposal_id.get(proposal_id, {})
        approval_status = str(ledger_row.get("approval_status") or "pending_review")
        review_outcome = str(ledger_row.get("review_outcome") or "undecided")

        validation_requirements = as_list_of_strings(row.get("validation_requirements"))
        required_test_classes = required_test_classes_for_risk(risk_level)
        required_metrics = required_metrics_for_target(str(adjustment_target or ""))
        pass_criteria = pass_criteria_for_metrics(required_metrics)

        is_explicitly_approved = approval_status == "approved" and review_outcome == "approved"

        if is_explicitly_approved:
            application_readiness = "blocked"
            blocking_reason = "validation_pending_simulation_only"
        else:
            blocked_non_approved += 1
            application_readiness = "blocked"
            blocking_reason = "not_explicitly_approved"

        if ledger_row:
            linked_to_ledger += 1

        manifest_rows.append(
            {
                "manifest_id": f"manifest-{idx:03d}",
                "proposal_id": proposal_id,
                "proposal_family": proposal_family,
                "adjustment_target": adjustment_target,
                "approval_status": approval_status,
                "review_outcome": review_outcome,
                "validation_status": "pending_validation",
                "validation_scope": "simulation_only",
                "required_test_classes": required_test_classes,
                "required_metrics": required_metrics,
                "pass_criteria": pass_criteria,
                "rollback_requirements": rollback_requirements(),
                "application_readiness": application_readiness,
                "blocking_reason": blocking_reason,
                "source_paths": {
                    "controlled_model_adjustment_proposals_json": source_paths[
                        "controlled_model_adjustment_proposals_json"
                    ],
                    "model_adjustment_approval_ledger_json": source_paths[
                        "model_adjustment_approval_ledger_json"
                    ],
                    "proposal_source_paths": as_list_of_strings(row.get("source_paths")),
                    "approval_ledger_entry_id": ledger_row.get("ledger_item_id"),
                },
                "validation_requirements": validation_requirements,
            }
        )

    proposal_ids = [str(r.get("proposal_id") or "") for r in proposals if isinstance(r, dict)]
    manifest_ids = [str(r.get("proposal_id") or "") for r in manifest_rows if isinstance(r, dict)]

    summary = {
        "total_proposals_in_source": len(proposal_ids),
        "total_validation_manifests": len(manifest_rows),
        "all_proposals_represented_exactly_once": (
            len(proposal_ids) == len(manifest_ids) == len(set(manifest_ids))
            and set(proposal_ids) == set(manifest_ids)
        ),
        "blocked_non_approved_count": blocked_non_approved,
        "linked_to_approval_ledger_count": linked_to_ledger,
        "validation_status_counts": {
            "pending_validation": len(manifest_rows),
        },
        "validation_scope_counts": {
            "simulation_only": len(manifest_rows),
        },
        "application_readiness_counts": {
            "blocked": len(manifest_rows),
        },
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_validation_manifests_version": "v2.2-slice-1",
        "source_versions": {
            "controlled_model_adjustment_proposals_version": proposals_payload.get(
                "controlled_model_adjustment_proposals_version"
            ),
            "model_adjustment_approval_ledger_version": approval_ledger_payload.get(
                "model_adjustment_approval_ledger_version"
            ),
        },
        "manifest_summary": summary,
        "validation_manifests": manifest_rows,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("manifest_summary") if isinstance(payload.get("manifest_summary"), dict) else {}
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    rows = (
        payload.get("validation_manifests")
        if isinstance(payload.get("validation_manifests"), list)
        else []
    )

    lines: list[str] = []
    lines.append("# AI-RISA Model Adjustment Validation Manifests (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Manifest Version: {payload.get('model_adjustment_validation_manifests_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Manifest Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Validation Manifests: {summary.get('total_validation_manifests')}")
    lines.append(
        f"- Exact Once Representation: {summary.get('all_proposals_represented_exactly_once')}"
    )
    lines.append(f"- Blocked Non-Approved Count: {summary.get('blocked_non_approved_count')}")
    lines.append(f"- Linked To Approval Ledger Count: {summary.get('linked_to_approval_ledger_count')}")
    lines.append(f"- Validation Status Counts: {summary.get('validation_status_counts')}")
    lines.append(f"- Validation Scope Counts: {summary.get('validation_scope_counts')}")
    lines.append(f"- Application Readiness Counts: {summary.get('application_readiness_counts')}")
    lines.append("")
    lines.append("## Validation Manifest Items")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- {row.get('manifest_id')}: {row.get('proposal_id')} -> {row.get('adjustment_target')}"
            )
            lines.append(f"  Proposal Family: {row.get('proposal_family')}")
            lines.append(f"  Approval Status: {row.get('approval_status')}")
            lines.append(f"  Review Outcome: {row.get('review_outcome')}")
            lines.append(f"  Validation Status: {row.get('validation_status')}")
            lines.append(f"  Validation Scope: {row.get('validation_scope')}")
            lines.append(f"  Required Test Classes: {row.get('required_test_classes')}")
            lines.append(f"  Required Metrics: {row.get('required_metrics')}")
            lines.append(f"  Pass Criteria: {row.get('pass_criteria')}")
            lines.append(f"  Rollback Requirements: {row.get('rollback_requirements')}")
            lines.append(f"  Application Readiness: {row.get('application_readiness')}")
            lines.append(f"  Blocking Reason: {row.get('blocking_reason')}")
            lines.append(f"  Source Paths: {row.get('source_paths')}")
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

    proposals_path = Path(args.proposals_json)
    approval_ledger_path = Path(args.approval_ledger_json)
    output_dir = Path(args.output_dir)

    proposals_payload, proposals_err = safe_read_json(repo_root / proposals_path)
    approval_ledger_payload, approval_ledger_err = safe_read_json(repo_root / approval_ledger_path)

    if proposals_err is not None:
        print(f"ERROR: controlled model-adjustment proposals unavailable: {proposals_err}", file=sys.stderr)
        return 1
    if approval_ledger_err is not None:
        print(f"ERROR: model-adjustment approval ledger unavailable: {approval_ledger_err}", file=sys.stderr)
        return 1

    if not isinstance(proposals_payload, dict) or not isinstance(approval_ledger_payload, dict):
        print("ERROR: one or more source artifacts are not valid JSON objects", file=sys.stderr)
        return 1

    source_paths = {
        "controlled_model_adjustment_proposals_json": normalize_path(proposals_path),
        "model_adjustment_approval_ledger_json": normalize_path(approval_ledger_path),
    }

    payload = build_manifests(
        proposals_payload=proposals_payload,
        approval_ledger_payload=approval_ledger_payload,
        source_paths=source_paths,
    )

    payload["source_status"] = {
        "controlled_model_adjustment_proposals_json_error": proposals_err,
        "model_adjustment_approval_ledger_json_error": approval_ledger_err,
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
        "[STATUS] manifests={total} exact_once={exact_once}".format(
            total=((payload.get("manifest_summary") or {}).get("total_validation_manifests")),
            exact_once=((payload.get("manifest_summary") or {}).get("all_proposals_represented_exactly_once")),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())