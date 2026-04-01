#!/usr/bin/env python3
"""
AI-RISA v2.6 Controlled Application Authorizations (slice 1): read-only governance layer.

Builds authorization records from proposals, approval-ledger state, validation
manifests, application gates, application packets, and dry-run plans. This script
does not apply adjustments or mutate model behavior, source artifacts, scheduler
logic, or pipeline outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")
OUTPUT_DIR = Path("ops/model_adjustments")
OUTPUT_JSON = "model_adjustment_application_authorizations.json"
OUTPUT_MD = "model_adjustment_application_authorizations.md"

PROPOSALS_DEFAULT = Path("ops/model_adjustments/controlled_model_adjustment_proposals.json")
APPROVAL_LEDGER_DEFAULT = Path("ops/model_adjustments/model_adjustment_approval_ledger.json")
VALIDATION_MANIFESTS_DEFAULT = Path("ops/model_adjustments/model_adjustment_validation_manifests.json")
APPLICATION_GATES_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_gates.json")
APPLICATION_PACKETS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_packets.json")
APPLICATION_DRY_RUNS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_dry_runs.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled application authorization artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--proposals-json", default=str(PROPOSALS_DEFAULT))
    parser.add_argument("--approval-ledger-json", default=str(APPROVAL_LEDGER_DEFAULT))
    parser.add_argument("--validation-manifests-json", default=str(VALIDATION_MANIFESTS_DEFAULT))
    parser.add_argument("--application-gates-json", default=str(APPLICATION_GATES_DEFAULT))
    parser.add_argument("--application-packets-json", default=str(APPLICATION_PACKETS_DEFAULT))
    parser.add_argument("--application-dry-runs-json", default=str(APPLICATION_DRY_RUNS_DEFAULT))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    return parser.parse_args()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_utc_iso() -> str:
    return now_utc().isoformat()


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


def index_by_proposal_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = str(row.get("proposal_id") or "").strip()
        if pid:
            out[pid] = row
    return out


def authorization_state_for_gate(gate_status: str) -> tuple[str, str, str]:
    if gate_status == "eligible_for_controlled_application":
        return (
            "pending_signoff",
            "eligibility_detected_but_manual_signoff_required",
            "eligible_but_not_authorized",
        )
    if gate_status == "conditionally_eligible":
        return (
            "pending_conditions",
            "additional_conditions_required_before_signoff",
            "conditional_without_signoff",
        )
    return (
        "blocked",
        "gate_status_blocked",
        "blocked_by_application_gate",
    )


def required_signoffs(gate_status: str) -> list[str]:
    base = ["ops_approver_signoff", "ml_lead_signoff"]
    if gate_status == "conditionally_eligible":
        return base + ["risk_review_signoff"]
    if gate_status == "eligible_for_controlled_application":
        return base + ["change_control_signoff"]
    return base


def authorization_window(gate_status: str) -> str:
    if gate_status == "eligible_for_controlled_application":
        return "24h_review_window"
    if gate_status == "conditionally_eligible":
        return "12h_conditional_review_window"
    return "no_active_window"


def authorization_expiry(gate_status: str) -> str | None:
    if gate_status == "blocked":
        return None
    return (now_utc() + timedelta(hours=24)).isoformat()


def final_pre_execution_conditions(gate_status: str) -> list[str]:
    conditions = [
        "All required signoffs completed",
        "No schema/pipeline drift since dry-run rehearsal",
        "Rollback and monitoring plans acknowledged",
    ]
    if gate_status == "conditionally_eligible":
        conditions.append("Conditional requirements resolved and re-verified")
    return conditions


def required_operator_role(packet_row: dict[str, Any], dry_run_row: dict[str, Any]) -> str:
    if isinstance(packet_row, dict) and packet_row.get("operator_role_required"):
        return str(packet_row.get("operator_role_required"))
    if isinstance(dry_run_row, dict) and dry_run_row.get("required_operator_role"):
        return str(dry_run_row.get("required_operator_role"))
    return "ops_reviewer"


def build_authorizations(
    proposals_payload: dict[str, Any],
    approval_payload: dict[str, Any],
    manifests_payload: dict[str, Any],
    gates_payload: dict[str, Any],
    packets_payload: dict[str, Any],
    dry_runs_payload: dict[str, Any],
    source_paths: dict[str, str],
) -> dict[str, Any]:
    proposals = proposals_payload.get("proposals") if isinstance(proposals_payload.get("proposals"), list) else []
    approval_rows = approval_payload.get("approval_ledger") if isinstance(approval_payload.get("approval_ledger"), list) else []
    manifest_rows = manifests_payload.get("validation_manifests") if isinstance(manifests_payload.get("validation_manifests"), list) else []
    gate_rows = gates_payload.get("application_gates") if isinstance(gates_payload.get("application_gates"), list) else []
    packet_rows = packets_payload.get("application_packets") if isinstance(packets_payload.get("application_packets"), list) else []
    dry_rows = dry_runs_payload.get("application_dry_runs") if isinstance(dry_runs_payload.get("application_dry_runs"), list) else []

    approval_by_pid = index_by_proposal_id(approval_rows)
    manifests_by_pid = index_by_proposal_id(manifest_rows)
    gates_by_pid = index_by_proposal_id(gate_rows)
    packets_by_pid = index_by_proposal_id(packet_rows)
    dry_by_pid = index_by_proposal_id(dry_rows)

    rows: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {"not_authorized": 0}
    authority_counts: dict[str, int] = {"none": 0}

    for idx, proposal in enumerate(proposals, start=1):
        if not isinstance(proposal, dict):
            continue

        proposal_id = str(proposal.get("proposal_id") or "").strip()
        proposal_family = proposal_family_from_id(proposal_id)
        adjustment_target = proposal.get("adjustment_target")

        gate_row = gates_by_pid.get(proposal_id, {})
        packet_row = packets_by_pid.get(proposal_id, {})
        dry_row = dry_by_pid.get(proposal_id, {})
        approval_row = approval_by_pid.get(proposal_id, {})
        manifest_row = manifests_by_pid.get(proposal_id, {})

        gate_status = str(gate_row.get("application_gate_status") or "blocked")
        packet_status = str(packet_row.get("packet_status") or "draft")
        dry_run_status = str(dry_row.get("dry_run_status") or "planned")

        auth_state, auth_notes, blocking_reason = authorization_state_for_gate(gate_status)

        status_counts["not_authorized"] = status_counts.get("not_authorized", 0) + 1
        authority_counts["none"] = authority_counts.get("none", 0) + 1

        rows.append(
            {
                "authorization_id": f"auth-{idx:03d}",
                "proposal_id": proposal_id,
                "packet_id": packet_row.get("packet_id"),
                "dry_run_id": dry_row.get("dry_run_id"),
                "proposal_family": proposal_family,
                "adjustment_target": adjustment_target,
                "application_gate_status": gate_status,
                "packet_status": packet_status,
                "dry_run_status": dry_run_status,
                "authorization_status": "not_authorized",
                "authorization_state": auth_state,
                "required_signoffs": required_signoffs(gate_status),
                "required_operator_role": required_operator_role(packet_row, dry_row),
                "authorization_window": authorization_window(gate_status),
                "authorization_expiry": authorization_expiry(gate_status),
                "final_pre_execution_conditions": final_pre_execution_conditions(gate_status),
                "authorization_notes": auth_notes,
                "execution_authority": "none",
                "blocking_reason": blocking_reason,
                "source_paths": {
                    "controlled_model_adjustment_proposals_json": source_paths["controlled_model_adjustment_proposals_json"],
                    "model_adjustment_approval_ledger_json": source_paths["model_adjustment_approval_ledger_json"],
                    "model_adjustment_validation_manifests_json": source_paths["model_adjustment_validation_manifests_json"],
                    "model_adjustment_application_gates_json": source_paths["model_adjustment_application_gates_json"],
                    "model_adjustment_application_packets_json": source_paths["model_adjustment_application_packets_json"],
                    "model_adjustment_application_dry_runs_json": source_paths["model_adjustment_application_dry_runs_json"],
                    "approval_ledger_entry_id": approval_row.get("ledger_item_id"),
                    "validation_manifest_id": manifest_row.get("manifest_id"),
                    "application_gate_id": gate_row.get("gate_id"),
                    "application_packet_id": packet_row.get("packet_id"),
                    "application_dry_run_id": dry_row.get("dry_run_id"),
                },
            }
        )

    proposal_ids = [str(x.get("proposal_id") or "") for x in proposals if isinstance(x, dict)]
    auth_ids = [str(x.get("proposal_id") or "") for x in rows if isinstance(x, dict)]

    summary = {
        "total_proposals_in_source": len(proposal_ids),
        "total_authorizations": len(rows),
        "all_proposals_represented_exactly_once": (
            len(proposal_ids) == len(auth_ids) == len(set(auth_ids))
            and set(proposal_ids) == set(auth_ids)
        ),
        "authorization_status_counts": status_counts,
        "execution_authority_counts": authority_counts,
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_application_authorizations_version": "v2.6-slice-1",
        "source_versions": {
            "controlled_model_adjustment_proposals_version": proposals_payload.get("controlled_model_adjustment_proposals_version"),
            "model_adjustment_approval_ledger_version": approval_payload.get("model_adjustment_approval_ledger_version"),
            "model_adjustment_validation_manifests_version": manifests_payload.get("model_adjustment_validation_manifests_version"),
            "model_adjustment_application_gates_version": gates_payload.get("model_adjustment_application_gates_version"),
            "model_adjustment_application_packets_version": packets_payload.get("model_adjustment_application_packets_version"),
            "model_adjustment_application_dry_runs_version": dry_runs_payload.get("model_adjustment_application_dry_runs_version"),
        },
        "application_authorization_summary": summary,
        "application_authorizations": rows,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("application_authorization_summary") if isinstance(payload.get("application_authorization_summary"), dict) else {}
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    rows = payload.get("application_authorizations") if isinstance(payload.get("application_authorizations"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Application Authorizations (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Authorization Version: {payload.get('model_adjustment_application_authorizations_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Authorization Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Authorization Records: {summary.get('total_authorizations')}")
    lines.append(f"- Exact Once Representation: {summary.get('all_proposals_represented_exactly_once')}")
    lines.append(f"- Authorization Status Counts: {summary.get('authorization_status_counts')}")
    lines.append(f"- Execution Authority Counts: {summary.get('execution_authority_counts')}")
    lines.append("")
    lines.append("## Authorization Records")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(f"- {row.get('authorization_id')}: {row.get('proposal_id')} -> {row.get('adjustment_target')}")
            lines.append(f"  Packet ID: {row.get('packet_id')} | Dry Run ID: {row.get('dry_run_id')}")
            lines.append(f"  Gate Status: {row.get('application_gate_status')}")
            lines.append(f"  Authorization Status: {row.get('authorization_status')}")
            lines.append(f"  Authorization State: {row.get('authorization_state')}")
            lines.append(f"  Required Signoffs: {row.get('required_signoffs')}")
            lines.append(f"  Required Operator Role: {row.get('required_operator_role')}")
            lines.append(f"  Authorization Window: {row.get('authorization_window')}")
            lines.append(f"  Authorization Expiry: {row.get('authorization_expiry')}")
            lines.append(f"  Final Pre-Execution Conditions: {row.get('final_pre_execution_conditions')}")
            lines.append(f"  Authorization Notes: {row.get('authorization_notes')}")
            lines.append(f"  Execution Authority: {row.get('execution_authority')}")
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
    approval_path = Path(args.approval_ledger_json)
    manifests_path = Path(args.validation_manifests_json)
    gates_path = Path(args.application_gates_json)
    packets_path = Path(args.application_packets_json)
    dry_runs_path = Path(args.application_dry_runs_json)
    output_dir = Path(args.output_dir)

    proposals_payload, proposals_err = safe_read_json(repo_root / proposals_path)
    approval_payload, approval_err = safe_read_json(repo_root / approval_path)
    manifests_payload, manifests_err = safe_read_json(repo_root / manifests_path)
    gates_payload, gates_err = safe_read_json(repo_root / gates_path)
    packets_payload, packets_err = safe_read_json(repo_root / packets_path)
    dry_runs_payload, dry_runs_err = safe_read_json(repo_root / dry_runs_path)

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
    if packets_err is not None:
        print(f"ERROR: model-adjustment application packets unavailable: {packets_err}", file=sys.stderr)
        return 1
    if dry_runs_err is not None:
        print(f"ERROR: model-adjustment application dry runs unavailable: {dry_runs_err}", file=sys.stderr)
        return 1

    if not all(isinstance(x, dict) for x in [proposals_payload, approval_payload, manifests_payload, gates_payload, packets_payload, dry_runs_payload]):
        print("ERROR: one or more source artifacts are not valid JSON objects", file=sys.stderr)
        return 1

    source_paths = {
        "controlled_model_adjustment_proposals_json": normalize_path(proposals_path),
        "model_adjustment_approval_ledger_json": normalize_path(approval_path),
        "model_adjustment_validation_manifests_json": normalize_path(manifests_path),
        "model_adjustment_application_gates_json": normalize_path(gates_path),
        "model_adjustment_application_packets_json": normalize_path(packets_path),
        "model_adjustment_application_dry_runs_json": normalize_path(dry_runs_path),
    }

    payload = build_authorizations(
        proposals_payload=proposals_payload,
        approval_payload=approval_payload,
        manifests_payload=manifests_payload,
        gates_payload=gates_payload,
        packets_payload=packets_payload,
        dry_runs_payload=dry_runs_payload,
        source_paths=source_paths,
    )

    payload["source_status"] = {
        "controlled_model_adjustment_proposals_json_error": proposals_err,
        "model_adjustment_approval_ledger_json_error": approval_err,
        "model_adjustment_validation_manifests_json_error": manifests_err,
        "model_adjustment_application_gates_json_error": gates_err,
        "model_adjustment_application_packets_json_error": packets_err,
        "model_adjustment_application_dry_runs_json_error": dry_runs_err,
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
        "[STATUS] authorizations={total} exact_once={exact_once}".format(
            total=((payload.get("application_authorization_summary") or {}).get("total_authorizations")),
            exact_once=((payload.get("application_authorization_summary") or {}).get("all_proposals_represented_exactly_once")),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())