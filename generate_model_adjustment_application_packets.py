#!/usr/bin/env python3
"""
AI-RISA v2.4 Controlled Application Packets (slice 1): read-only control-state layer.

Builds operator-ready application packet artifacts from proposals, approval-ledger
state, validation-manifest state, and application-gate state. This script does not
apply adjustments or mutate model behavior, source artifacts, scheduler logic, or
pipeline outputs.
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
OUTPUT_JSON = "model_adjustment_application_packets.json"
OUTPUT_MD = "model_adjustment_application_packets.md"

PROPOSALS_DEFAULT = Path("ops/model_adjustments/controlled_model_adjustment_proposals.json")
APPROVAL_LEDGER_DEFAULT = Path("ops/model_adjustments/model_adjustment_approval_ledger.json")
VALIDATION_MANIFESTS_DEFAULT = Path("ops/model_adjustments/model_adjustment_validation_manifests.json")
APPLICATION_GATES_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_gates.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled application packet artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--proposals-json", default=str(PROPOSALS_DEFAULT))
    parser.add_argument("--approval-ledger-json", default=str(APPROVAL_LEDGER_DEFAULT))
    parser.add_argument("--validation-manifests-json", default=str(VALIDATION_MANIFESTS_DEFAULT))
    parser.add_argument("--application-gates-json", default=str(APPLICATION_GATES_DEFAULT))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
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


def index_by_proposal_id(rows: list[dict[str, Any]], key: str = "proposal_id") -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = str(row.get(key) or "").strip()
        if pid:
            out[pid] = row
    return out


def packet_status_for_gate(gate_status: str) -> tuple[str, str, str]:
    if gate_status == "eligible_for_controlled_application":
        return (
            "draft",
            "ready_for_controlled_review_packet",
            "read_only_packet_not_authorized_for_execution",
        )
    if gate_status == "conditionally_eligible":
        return (
            "draft",
            "conditional_gate_requires_additional_pre_apply_checks",
            "conditionally_eligible_but_manual_review_only",
        )
    return (
        "draft",
        "blocked_by_gate",
        "gate_status_blocked",
    )


def required_source_files(adjustment_target: str) -> list[str]:
    target = str(adjustment_target or "")
    files = [
        "config/model_adjustments/",
        "ops/model_adjustments/",
    ]
    if "rule" in target or "weight" in target:
        files.append("engine/rules/")
    if "confidence" in target:
        files.append("engine/confidence/")
    return files


def required_backups() -> list[str]:
    return [
        "Backup current model-adjustment configuration bundle",
        "Backup latest validated baseline artifacts",
        "Backup rollback reference manifest",
    ]


def required_pre_apply_checks(gate_row: dict[str, Any]) -> list[str]:
    checks = [
        "Confirm packet remains read-only and manual-review only",
        "Confirm linked approval, validation, and gate records are unchanged",
    ]
    extra = gate_row.get("required_pre_application_checks")
    if isinstance(extra, list):
        checks.extend([str(x) for x in extra if x is not None])
    return checks


def required_post_apply_checks() -> list[str]:
    return [
        "Define post-apply monitoring plan before any future execution authorization",
        "Define regression watchlist and alert thresholds",
        "Define operator rollback trigger confirmation checklist",
    ]


def rollback_plan() -> list[str]:
    return [
        "Restore previous baseline configuration from backups",
        "Re-run validation replay against baseline",
        "Document rollback incident and sign-off",
    ]


def build_packets(
    proposals_payload: dict[str, Any],
    approval_ledger_payload: dict[str, Any],
    validation_manifests_payload: dict[str, Any],
    application_gates_payload: dict[str, Any],
    source_paths: dict[str, str],
) -> dict[str, Any]:
    proposals = proposals_payload.get("proposals") if isinstance(proposals_payload.get("proposals"), list) else []
    approval_rows = approval_ledger_payload.get("approval_ledger") if isinstance(approval_ledger_payload.get("approval_ledger"), list) else []
    manifest_rows = validation_manifests_payload.get("validation_manifests") if isinstance(validation_manifests_payload.get("validation_manifests"), list) else []
    gate_rows = application_gates_payload.get("application_gates") if isinstance(application_gates_payload.get("application_gates"), list) else []

    approval_by_pid = index_by_proposal_id(approval_rows)
    manifests_by_pid = index_by_proposal_id(manifest_rows)
    gates_by_pid = index_by_proposal_id(gate_rows)

    packets: list[dict[str, Any]] = []
    status_counts = {"draft": 0}

    for idx, proposal in enumerate(proposals, start=1):
        if not isinstance(proposal, dict):
            continue

        proposal_id = str(proposal.get("proposal_id") or "").strip()
        proposal_family = proposal_family_from_id(proposal_id)
        adjustment_target = proposal.get("adjustment_target")

        approval_row = approval_by_pid.get(proposal_id, {})
        manifest_row = manifests_by_pid.get(proposal_id, {})
        gate_row = gates_by_pid.get(proposal_id, {})

        approval_status = str(approval_row.get("approval_status") or "pending_review")
        review_outcome = str(approval_row.get("review_outcome") or "undecided")
        validation_status = str(manifest_row.get("validation_status") or "pending_validation")
        gate_status = str(gate_row.get("application_gate_status") or "blocked")

        packet_status, gate_reason, conservative_blocking = packet_status_for_gate(gate_status)
        status_counts[packet_status] = status_counts.get(packet_status, 0) + 1

        packets.append(
            {
                "packet_id": f"packet-{idx:03d}",
                "proposal_id": proposal_id,
                "proposal_family": proposal_family,
                "adjustment_target": adjustment_target,
                "application_gate_status": gate_status,
                "packet_status": "draft",
                "application_mode": "manual_review_only",
                "planned_change_scope": "control_packet_only_no_execution",
                "required_source_files": required_source_files(str(adjustment_target or "")),
                "required_backups": required_backups(),
                "required_pre_apply_checks": required_pre_apply_checks(gate_row),
                "required_post_apply_checks": required_post_apply_checks(),
                "rollback_plan": rollback_plan(),
                "operator_notes": None,
                "operator_role_required": str(gate_row.get("required_operator_role") or "ops_reviewer"),
                "execution_readiness": "blocked",
                "blocking_reason": conservative_blocking,
                "source_paths": {
                    "controlled_model_adjustment_proposals_json": source_paths["controlled_model_adjustment_proposals_json"],
                    "model_adjustment_approval_ledger_json": source_paths["model_adjustment_approval_ledger_json"],
                    "model_adjustment_validation_manifests_json": source_paths["model_adjustment_validation_manifests_json"],
                    "model_adjustment_application_gates_json": source_paths["model_adjustment_application_gates_json"],
                    "approval_ledger_entry_id": approval_row.get("ledger_item_id"),
                    "validation_manifest_id": manifest_row.get("manifest_id"),
                    "application_gate_id": gate_row.get("gate_id"),
                },
                "gate_reason": gate_reason,
                "approval_status": approval_status,
                "review_outcome": review_outcome,
                "validation_status": validation_status,
            }
        )

    proposal_ids = [str(x.get("proposal_id") or "") for x in proposals if isinstance(x, dict)]
    packet_ids = [str(x.get("proposal_id") or "") for x in packets if isinstance(x, dict)]

    summary = {
        "total_proposals_in_source": len(proposal_ids),
        "total_application_packets": len(packets),
        "all_proposals_represented_exactly_once": (
            len(proposal_ids) == len(packet_ids) == len(set(packet_ids))
            and set(proposal_ids) == set(packet_ids)
        ),
        "packet_status_counts": status_counts,
        "application_mode_counts": {"manual_review_only": len(packets)},
        "execution_readiness_counts": {"blocked": len(packets)},
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_application_packets_version": "v2.4-slice-1",
        "source_versions": {
            "controlled_model_adjustment_proposals_version": proposals_payload.get("controlled_model_adjustment_proposals_version"),
            "model_adjustment_approval_ledger_version": approval_ledger_payload.get("model_adjustment_approval_ledger_version"),
            "model_adjustment_validation_manifests_version": validation_manifests_payload.get("model_adjustment_validation_manifests_version"),
            "model_adjustment_application_gates_version": application_gates_payload.get("model_adjustment_application_gates_version"),
        },
        "application_packet_summary": summary,
        "application_packets": packets,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("application_packet_summary") if isinstance(payload.get("application_packet_summary"), dict) else {}
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    rows = payload.get("application_packets") if isinstance(payload.get("application_packets"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Application Packets (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Packet Version: {payload.get('model_adjustment_application_packets_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Packet Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Application Packets: {summary.get('total_application_packets')}")
    lines.append(f"- Exact Once Representation: {summary.get('all_proposals_represented_exactly_once')}")
    lines.append(f"- Packet Status Counts: {summary.get('packet_status_counts')}")
    lines.append(f"- Application Mode Counts: {summary.get('application_mode_counts')}")
    lines.append(f"- Execution Readiness Counts: {summary.get('execution_readiness_counts')}")
    lines.append("")
    lines.append("## Application Packets")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(f"- {row.get('packet_id')}: {row.get('proposal_id')} -> {row.get('adjustment_target')}")
            lines.append(f"  Gate Status: {row.get('application_gate_status')}")
            lines.append(f"  Packet Status: {row.get('packet_status')}")
            lines.append(f"  Application Mode: {row.get('application_mode')}")
            lines.append(f"  Planned Change Scope: {row.get('planned_change_scope')}")
            lines.append(f"  Required Source Files: {row.get('required_source_files')}")
            lines.append(f"  Required Backups: {row.get('required_backups')}")
            lines.append(f"  Required Pre-Apply Checks: {row.get('required_pre_apply_checks')}")
            lines.append(f"  Required Post-Apply Checks: {row.get('required_post_apply_checks')}")
            lines.append(f"  Rollback Plan: {row.get('rollback_plan')}")
            lines.append(f"  Operator Role Required: {row.get('operator_role_required')}")
            lines.append(f"  Execution Readiness: {row.get('execution_readiness')}")
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
    application_gates_path = Path(args.application_gates_json)
    output_dir = Path(args.output_dir)

    proposals_payload, proposals_err = safe_read_json(repo_root / proposals_path)
    approval_ledger_payload, approval_err = safe_read_json(repo_root / approval_ledger_path)
    validation_manifests_payload, manifests_err = safe_read_json(repo_root / validation_manifests_path)
    application_gates_payload, gates_err = safe_read_json(repo_root / application_gates_path)

    if proposals_err is not None:
        print(f"ERROR: controlled model-adjustment proposals unavailable: {proposals_err}", file=sys.stderr)
        return 1
    if approval_err is not None:
        print(f"ERROR: model-adjustment approval ledger unavailable: {approval_err}", file=sys.stderr)
        return 1
    if manifests_err is not None:
        print(f"ERROR: model-adjustment validation manifests unavailable: {manifests_err}", file=sys.stderr)
        return 1
    if gates_err is not None:
        print(f"ERROR: model-adjustment application gates unavailable: {gates_err}", file=sys.stderr)
        return 1

    if not all(isinstance(x, dict) for x in [proposals_payload, approval_ledger_payload, validation_manifests_payload, application_gates_payload]):
        print("ERROR: one or more source artifacts are not valid JSON objects", file=sys.stderr)
        return 1

    source_paths = {
        "controlled_model_adjustment_proposals_json": normalize_path(proposals_path),
        "model_adjustment_approval_ledger_json": normalize_path(approval_ledger_path),
        "model_adjustment_validation_manifests_json": normalize_path(validation_manifests_path),
        "model_adjustment_application_gates_json": normalize_path(application_gates_path),
    }

    payload = build_packets(
        proposals_payload=proposals_payload,
        approval_ledger_payload=approval_ledger_payload,
        validation_manifests_payload=validation_manifests_payload,
        application_gates_payload=application_gates_payload,
        source_paths=source_paths,
    )

    payload["source_status"] = {
        "controlled_model_adjustment_proposals_json_error": proposals_err,
        "model_adjustment_approval_ledger_json_error": approval_err,
        "model_adjustment_validation_manifests_json_error": manifests_err,
        "model_adjustment_application_gates_json_error": gates_err,
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
    print("[STATUS] packets={total} exact_once={exact_once}".format(total=((payload.get("application_packet_summary") or {}).get("total_application_packets")), exact_once=((payload.get("application_packet_summary") or {}).get("all_proposals_represented_exactly_once"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())