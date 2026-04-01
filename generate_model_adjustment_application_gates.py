#!/usr/bin/env python3
"""
AI-RISA v2.3 Adjustment Application Gates (slice 1): read-only control-state layer.

Builds application-gate records from controlled model-adjustment proposals,
approval-ledger state, and validation-manifest state. This script does not mutate
model behavior, source artifacts, scheduler logic, or pipeline outputs.
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
OUTPUT_JSON = "model_adjustment_application_gates.json"
OUTPUT_MD = "model_adjustment_application_gates.md"

PROPOSALS_DEFAULT = Path("ops/model_adjustments/controlled_model_adjustment_proposals.json")
APPROVAL_LEDGER_DEFAULT = Path("ops/model_adjustments/model_adjustment_approval_ledger.json")
VALIDATION_MANIFESTS_DEFAULT = Path("ops/model_adjustments/model_adjustment_validation_manifests.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only model-adjustment application-gate artifacts"
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
        "--validation-manifests-json",
        default=str(VALIDATION_MANIFESTS_DEFAULT),
        help="Model-adjustment validation manifests JSON path relative to repo root",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Application-gate output directory relative to repo root",
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


def index_by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_key = str(row.get(key) or "").strip()
        if row_key:
            indexed[row_key] = row
    return indexed


def required_operator_role_for_gate(
    ledger_row: dict[str, Any],
    gate_status: str,
) -> str:
    base_role = str(ledger_row.get("required_reviewer_role") or "ops_reviewer")
    if gate_status == "eligible_for_controlled_application":
        return "ops_approver_and_ml_lead"
    if gate_status == "conditionally_eligible":
        return "ops_approver"
    return base_role


def gate_status_from_state(
    approval_status: str,
    review_outcome: str,
    validation_status: str,
    validation_scope: str,
) -> tuple[str, str, str, str, str]:
    approved = approval_status == "approved" and review_outcome == "approved"
    validation_complete = validation_status == "validation_complete"
    simulation_only = validation_scope == "simulation_only"

    if not approved:
        return (
            "blocked",
            "block_unapproved",
            "Not explicitly approved in approval ledger.",
            "blocked",
            "not_explicitly_approved",
        )

    if not validation_complete:
        return (
            "blocked",
            "block_validation_incomplete",
            "Validation is not complete, so application gate remains blocked.",
            "blocked",
            "validation_incomplete",
        )

    if simulation_only:
        return (
            "conditionally_eligible",
            "conditional_simulation_complete",
            "Validation complete in simulation scope; additional pre-application checks still required.",
            "blocked",
            "simulation_only_requires_pre_application_checks",
        )

    return (
        "eligible_for_controlled_application",
        "eligible_controlled_application",
        "Approval and non-simulation validation are complete; record is eligible for controlled application review.",
        "review_required",
        "read_only_record_not_executed",
    )


def pre_application_checks_for_gate(gate_status: str) -> list[str]:
    checks = [
        "Confirm no pipeline/scheduler schema drift since validation",
        "Confirm rollback plan is current and approved",
    ]
    if gate_status in {"conditionally_eligible", "eligible_for_controlled_application"}:
        checks.extend(
            [
                "Operator sign-off on pre-application checklist",
                "Change-control approval ticket linked",
            ]
        )
    return checks


def build_application_gates(
    proposals_payload: dict[str, Any],
    approval_ledger_payload: dict[str, Any],
    validation_manifests_payload: dict[str, Any],
    source_paths: dict[str, str],
) -> dict[str, Any]:
    proposals = (
        proposals_payload.get("proposals")
        if isinstance(proposals_payload.get("proposals"), list)
        else []
    )
    approval_rows = (
        approval_ledger_payload.get("approval_ledger")
        if isinstance(approval_ledger_payload.get("approval_ledger"), list)
        else []
    )
    manifest_rows = (
        validation_manifests_payload.get("validation_manifests")
        if isinstance(validation_manifests_payload.get("validation_manifests"), list)
        else []
    )

    approval_by_proposal = index_by_key(approval_rows, "proposal_id")
    manifest_by_proposal = index_by_key(manifest_rows, "proposal_id")

    gate_rows: list[dict[str, Any]] = []
    status_counts = {
        "blocked": 0,
        "conditionally_eligible": 0,
        "eligible_for_controlled_application": 0,
    }
    linked_to_approval = 0
    linked_to_manifest = 0

    for idx, row in enumerate(proposals, start=1):
        if not isinstance(row, dict):
            continue

        proposal_id = str(row.get("proposal_id") or "").strip()
        proposal_family = proposal_family_from_id(proposal_id)
        adjustment_target = row.get("adjustment_target")

        approval_row = approval_by_proposal.get(proposal_id, {})
        approval_status = str(approval_row.get("approval_status") or "pending_review")
        review_outcome = str(approval_row.get("review_outcome") or "undecided")

        manifest_row = manifest_by_proposal.get(proposal_id, {})
        validation_status = str(manifest_row.get("validation_status") or "pending_validation")
        validation_scope = str(manifest_row.get("validation_scope") or "simulation_only")

        (
            gate_status,
            gate_decision,
            gate_reason,
            application_readiness,
            blocking_reason,
        ) = gate_status_from_state(
            approval_status=approval_status,
            review_outcome=review_outcome,
            validation_status=validation_status,
            validation_scope=validation_scope,
        )

        status_counts[gate_status] = status_counts.get(gate_status, 0) + 1
        if approval_row:
            linked_to_approval += 1
        if manifest_row:
            linked_to_manifest += 1

        gate_rows.append(
            {
                "gate_id": f"gate-{idx:03d}",
                "proposal_id": proposal_id,
                "proposal_family": proposal_family,
                "adjustment_target": adjustment_target,
                "approval_status": approval_status,
                "review_outcome": review_outcome,
                "validation_status": validation_status,
                "application_gate_status": gate_status,
                "gate_decision": gate_decision,
                "gate_reason": gate_reason,
                "required_pre_application_checks": pre_application_checks_for_gate(gate_status),
                "required_operator_role": required_operator_role_for_gate(approval_row, gate_status),
                "application_readiness": application_readiness,
                "blocking_reason": blocking_reason,
                "source_paths": {
                    "controlled_model_adjustment_proposals_json": source_paths[
                        "controlled_model_adjustment_proposals_json"
                    ],
                    "model_adjustment_approval_ledger_json": source_paths[
                        "model_adjustment_approval_ledger_json"
                    ],
                    "model_adjustment_validation_manifests_json": source_paths[
                        "model_adjustment_validation_manifests_json"
                    ],
                    "approval_ledger_entry_id": approval_row.get("ledger_item_id"),
                    "validation_manifest_id": manifest_row.get("manifest_id"),
                },
            }
        )

    proposal_ids = [str(r.get("proposal_id") or "") for r in proposals if isinstance(r, dict)]
    gate_ids = [str(r.get("proposal_id") or "") for r in gate_rows if isinstance(r, dict)]

    summary = {
        "total_proposals_in_source": len(proposal_ids),
        "total_application_gates": len(gate_rows),
        "all_proposals_represented_exactly_once": (
            len(proposal_ids) == len(gate_ids) == len(set(gate_ids))
            and set(proposal_ids) == set(gate_ids)
        ),
        "application_gate_status_counts": status_counts,
        "linked_to_approval_ledger_count": linked_to_approval,
        "linked_to_validation_manifest_count": linked_to_manifest,
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_application_gates_version": "v2.3-slice-1",
        "source_versions": {
            "controlled_model_adjustment_proposals_version": proposals_payload.get(
                "controlled_model_adjustment_proposals_version"
            ),
            "model_adjustment_approval_ledger_version": approval_ledger_payload.get(
                "model_adjustment_approval_ledger_version"
            ),
            "model_adjustment_validation_manifests_version": validation_manifests_payload.get(
                "model_adjustment_validation_manifests_version"
            ),
        },
        "application_gate_summary": summary,
        "application_gates": gate_rows,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = (
        payload.get("application_gate_summary")
        if isinstance(payload.get("application_gate_summary"), dict)
        else {}
    )
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    rows = payload.get("application_gates") if isinstance(payload.get("application_gates"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Model Adjustment Application Gates (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Gate Version: {payload.get('model_adjustment_application_gates_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Gate Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Application Gates: {summary.get('total_application_gates')}")
    lines.append(
        f"- Exact Once Representation: {summary.get('all_proposals_represented_exactly_once')}"
    )
    lines.append(f"- Gate Status Counts: {summary.get('application_gate_status_counts')}")
    lines.append(f"- Linked To Approval Ledger Count: {summary.get('linked_to_approval_ledger_count')}")
    lines.append(f"- Linked To Validation Manifest Count: {summary.get('linked_to_validation_manifest_count')}")
    lines.append("")
    lines.append("## Application Gate Items")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- {row.get('gate_id')}: {row.get('proposal_id')} -> {row.get('adjustment_target')}"
            )
            lines.append(f"  Proposal Family: {row.get('proposal_family')}")
            lines.append(f"  Approval Status: {row.get('approval_status')}")
            lines.append(f"  Review Outcome: {row.get('review_outcome')}")
            lines.append(f"  Validation Status: {row.get('validation_status')}")
            lines.append(f"  Application Gate Status: {row.get('application_gate_status')}")
            lines.append(f"  Gate Decision: {row.get('gate_decision')}")
            lines.append(f"  Gate Reason: {row.get('gate_reason')}")
            lines.append(f"  Required Pre-Application Checks: {row.get('required_pre_application_checks')}")
            lines.append(f"  Required Operator Role: {row.get('required_operator_role')}")
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
    validation_manifests_path = Path(args.validation_manifests_json)
    output_dir = Path(args.output_dir)

    proposals_payload, proposals_err = safe_read_json(repo_root / proposals_path)
    approval_ledger_payload, approval_ledger_err = safe_read_json(repo_root / approval_ledger_path)
    validation_manifests_payload, validation_manifests_err = safe_read_json(
        repo_root / validation_manifests_path
    )

    if proposals_err is not None:
        print(f"ERROR: controlled model-adjustment proposals unavailable: {proposals_err}", file=sys.stderr)
        return 1
    if approval_ledger_err is not None:
        print(f"ERROR: model-adjustment approval ledger unavailable: {approval_ledger_err}", file=sys.stderr)
        return 1
    if validation_manifests_err is not None:
        print(
            f"ERROR: model-adjustment validation manifests unavailable: {validation_manifests_err}",
            file=sys.stderr,
        )
        return 1

    if (
        not isinstance(proposals_payload, dict)
        or not isinstance(approval_ledger_payload, dict)
        or not isinstance(validation_manifests_payload, dict)
    ):
        print("ERROR: one or more source artifacts are not valid JSON objects", file=sys.stderr)
        return 1

    source_paths = {
        "controlled_model_adjustment_proposals_json": normalize_path(proposals_path),
        "model_adjustment_approval_ledger_json": normalize_path(approval_ledger_path),
        "model_adjustment_validation_manifests_json": normalize_path(validation_manifests_path),
    }

    payload = build_application_gates(
        proposals_payload=proposals_payload,
        approval_ledger_payload=approval_ledger_payload,
        validation_manifests_payload=validation_manifests_payload,
        source_paths=source_paths,
    )

    payload["source_status"] = {
        "controlled_model_adjustment_proposals_json_error": proposals_err,
        "model_adjustment_approval_ledger_json_error": approval_ledger_err,
        "model_adjustment_validation_manifests_json_error": validation_manifests_err,
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
        "[STATUS] gates={total} exact_once={exact_once}".format(
            total=((payload.get("application_gate_summary") or {}).get("total_application_gates")),
            exact_once=((payload.get("application_gate_summary") or {}).get("all_proposals_represented_exactly_once")),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())