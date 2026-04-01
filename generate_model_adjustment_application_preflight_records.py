#!/usr/bin/env python3
"""
AI-RISA v2.8 Controlled Application Preflight Records (slice 1): read-only governance layer.

Builds per-proposal application preflight records that consolidate the final go/no-go
state from proposals, approval-ledger, validation manifests, application gates, application
packets, dry-run plans, authorization records, and execution-intent records. This script
does not apply adjustments, create an execution path, auto-promote any item to runnable,
or mutate upstream artifacts, model behavior, scheduler logic, or pipeline outputs.
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
OUTPUT_JSON = "model_adjustment_application_preflight_records.json"
OUTPUT_MD = "model_adjustment_application_preflight_records.md"

PROPOSALS_DEFAULT = Path("ops/model_adjustments/controlled_model_adjustment_proposals.json")
APPROVAL_LEDGER_DEFAULT = Path("ops/model_adjustments/model_adjustment_approval_ledger.json")
VALIDATION_MANIFESTS_DEFAULT = Path("ops/model_adjustments/model_adjustment_validation_manifests.json")
APPLICATION_GATES_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_gates.json")
APPLICATION_PACKETS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_packets.json")
APPLICATION_DRY_RUNS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_dry_runs.json")
APPLICATION_AUTH_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_authorizations.json")
EXECUTION_INTENTS_DEFAULT = Path("ops/model_adjustments/model_adjustment_execution_intents.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled application preflight record artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--proposals-json", default=str(PROPOSALS_DEFAULT))
    parser.add_argument("--approval-ledger-json", default=str(APPROVAL_LEDGER_DEFAULT))
    parser.add_argument("--validation-manifests-json", default=str(VALIDATION_MANIFESTS_DEFAULT))
    parser.add_argument("--application-gates-json", default=str(APPLICATION_GATES_DEFAULT))
    parser.add_argument("--application-packets-json", default=str(APPLICATION_PACKETS_DEFAULT))
    parser.add_argument("--application-dry-runs-json", default=str(APPLICATION_DRY_RUNS_DEFAULT))
    parser.add_argument("--application-authorizations-json", default=str(APPLICATION_AUTH_DEFAULT))
    parser.add_argument("--execution-intents-json", default=str(EXECUTION_INTENTS_DEFAULT))
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
        return token[len("proposal-"):]
    return token or "unknown"


def index_by_proposal_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = str(row.get("proposal_id") or "").strip()
        if pid:
            indexed[pid] = row
    return indexed


def derive_go_no_go(
    gate_status: str,
    authorization_status: str,
    intent_status: str,
    approval_status: str,
    review_outcome: str,
) -> tuple[str, str, list[str], list[str]]:
    """
    Returns (preflight_status, go_no_go_state, required_open_checks, stop_conditions).
    Conservative: defaults to blocked / no-go unless all conditions are fully resolved.
    No execution path is enabled in v2.8.
    """
    stop_conditions: list[str] = []
    open_checks: list[str] = []

    if gate_status != "eligible_for_controlled_application":
        stop_conditions.append("application_gate_not_eligible")
        open_checks.append("Resolve application gate to eligible_for_controlled_application")

    if authorization_status != "authorized":
        stop_conditions.append("authorization_not_active")
        open_checks.append("Obtain active authorization with required signoffs")

    if intent_status == "blocked_intent":
        stop_conditions.append("execution_intent_blocked")
        open_checks.append("Resolve all execution-intent blockers before preflight can advance")

    if approval_status != "approved":
        stop_conditions.append("approval_not_granted")
        open_checks.append("Complete approval review and record approved outcome in ledger")

    if review_outcome not in ("approved", "conditionally_approved"):
        stop_conditions.append("review_outcome_not_approved")
        open_checks.append("Record a positive review outcome in the approval ledger")

    # Execution path is not enabled in v2.8 governance layer regardless of upstream state.
    stop_conditions.append("execution_path_not_enabled_in_v2_8")
    open_checks.append("Confirm execution remains disabled in governance-only phase")

    if stop_conditions:
        return "blocked", "no_go", open_checks, stop_conditions

    # This branch is unreachable in v2.8 because execution_path_not_enabled_in_v2_8 is
    # always appended, but it documents the intended promotion semantics for future slices.
    return "blocked", "no_go", open_checks, stop_conditions


def required_evidence(
    gate_status: str,
    authorization_status: str,
    approval_status: str,
) -> list[str]:
    evidence = [
        "Validated approval-ledger record with approved outcome",
        "Active authorization record with all required signoffs",
        "Application gate at eligible_for_controlled_application",
        "Validation manifest with all required test classes completed",
        "Dry-run record showing completed simulation with no abort conditions triggered",
        "Rollback plan reviewed and confirmed present in application packet",
        "Execution intent confirmed governance-record-only, no auto-execution path open",
    ]
    if approval_status != "approved":
        evidence.append("Approval signoff from designated reviewer role")
    if authorization_status != "authorized":
        evidence.append("Authorization signoff from required operator role")
    if gate_status != "eligible_for_controlled_application":
        evidence.append("Gate condition resolution evidence")
    return evidence


def build_preflight_records(
    proposals_payload: dict[str, Any],
    approval_payload: dict[str, Any],
    manifests_payload: dict[str, Any],
    gates_payload: dict[str, Any],
    packets_payload: dict[str, Any],
    dry_runs_payload: dict[str, Any],
    auth_payload: dict[str, Any],
    intents_payload: dict[str, Any],
    source_paths: dict[str, str],
) -> dict[str, Any]:
    proposals = proposals_payload.get("proposals") if isinstance(proposals_payload.get("proposals"), list) else []
    approval_rows = approval_payload.get("approval_ledger") if isinstance(approval_payload.get("approval_ledger"), list) else []
    manifest_rows = manifests_payload.get("validation_manifests") if isinstance(manifests_payload.get("validation_manifests"), list) else []
    gate_rows = gates_payload.get("application_gates") if isinstance(gates_payload.get("application_gates"), list) else []
    packet_rows = packets_payload.get("application_packets") if isinstance(packets_payload.get("application_packets"), list) else []
    dry_rows = dry_runs_payload.get("application_dry_runs") if isinstance(dry_runs_payload.get("application_dry_runs"), list) else []
    auth_rows = auth_payload.get("application_authorizations") if isinstance(auth_payload.get("application_authorizations"), list) else []
    intent_rows = intents_payload.get("execution_intents") if isinstance(intents_payload.get("execution_intents"), list) else []

    approval_by_pid = index_by_proposal_id(approval_rows)
    manifest_by_pid = index_by_proposal_id(manifest_rows)
    gates_by_pid = index_by_proposal_id(gate_rows)
    packets_by_pid = index_by_proposal_id(packet_rows)
    dry_by_pid = index_by_proposal_id(dry_rows)
    auth_by_pid = index_by_proposal_id(auth_rows)
    intents_by_pid = index_by_proposal_id(intent_rows)

    records: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    go_no_go_counts: dict[str, int] = {}

    for idx, proposal in enumerate(proposals, start=1):
        if not isinstance(proposal, dict):
            continue

        proposal_id = str(proposal.get("proposal_id") or "").strip()
        proposal_family = proposal_family_from_id(proposal_id)
        adjustment_target = proposal.get("adjustment_target")

        approval_row = approval_by_pid.get(proposal_id, {})
        manifest_row = manifest_by_pid.get(proposal_id, {})
        gate_row = gates_by_pid.get(proposal_id, {})
        packet_row = packets_by_pid.get(proposal_id, {})
        dry_row = dry_by_pid.get(proposal_id, {})
        auth_row = auth_by_pid.get(proposal_id, {})
        intent_row = intents_by_pid.get(proposal_id, {})

        gate_status = str(gate_row.get("application_gate_status") or "blocked")
        authorization_status = str(auth_row.get("authorization_status") or "not_authorized")
        intent_status_val = str(intent_row.get("execution_intent_status") or "blocked_intent")
        approval_status = str(approval_row.get("approval_status") or "pending_review")
        review_outcome = str(approval_row.get("review_outcome") or "undecided")

        preflight_status, go_no_go_state, open_checks, stop_conds = derive_go_no_go(
            gate_status=gate_status,
            authorization_status=authorization_status,
            intent_status=intent_status_val,
            approval_status=approval_status,
            review_outcome=review_outcome,
        )

        status_counts[preflight_status] = status_counts.get(preflight_status, 0) + 1
        go_no_go_counts[go_no_go_state] = go_no_go_counts.get(go_no_go_state, 0) + 1

        authorization_id = auth_row.get("authorization_id")
        intent_id = intent_row.get("intent_id")
        packet_id = packet_row.get("packet_id")

        records.append(
            {
                "preflight_id": f"preflight-{idx:03d}",
                "proposal_id": proposal_id,
                "authorization_id": authorization_id,
                "intent_id": intent_id,
                "proposal_family": proposal_family,
                "adjustment_target": adjustment_target,
                "execution_intent_status": intent_status_val,
                "authorization_status": authorization_status,
                "preflight_status": preflight_status,
                "go_no_go_state": go_no_go_state,
                "required_open_checks": open_checks,
                "required_evidence": required_evidence(gate_status, authorization_status, approval_status),
                "required_operator_role": str(
                    auth_row.get("required_operator_role")
                    or packet_row.get("operator_role_required")
                    or dry_row.get("required_operator_role")
                    or "ops_reviewer"
                ),
                "stop_conditions": stop_conds,
                "rollback_reference": f"rollback-from-{packet_id or proposal_id}",
                "preflight_notes": "governance_record_only_no_execution_path_in_v2_8",
                "source_paths": {
                    "controlled_model_adjustment_proposals_json": source_paths["controlled_model_adjustment_proposals_json"],
                    "model_adjustment_approval_ledger_json": source_paths["model_adjustment_approval_ledger_json"],
                    "model_adjustment_validation_manifests_json": source_paths["model_adjustment_validation_manifests_json"],
                    "model_adjustment_application_gates_json": source_paths["model_adjustment_application_gates_json"],
                    "model_adjustment_application_packets_json": source_paths["model_adjustment_application_packets_json"],
                    "model_adjustment_application_dry_runs_json": source_paths["model_adjustment_application_dry_runs_json"],
                    "model_adjustment_application_authorizations_json": source_paths["model_adjustment_application_authorizations_json"],
                    "model_adjustment_execution_intents_json": source_paths["model_adjustment_execution_intents_json"],
                    "approval_ledger_entry_id": approval_row.get("ledger_item_id"),
                    "validation_manifest_id": manifest_row.get("manifest_id"),
                    "application_gate_id": gate_row.get("gate_id"),
                    "application_packet_id": packet_id,
                    "application_dry_run_id": dry_row.get("dry_run_id"),
                    "application_authorization_id": authorization_id,
                    "execution_intent_id": intent_id,
                },
            }
        )

    proposal_ids = [str(x.get("proposal_id") or "") for x in proposals if isinstance(x, dict)]
    record_pids = [str(x.get("proposal_id") or "") for x in records if isinstance(x, dict)]

    summary = {
        "total_proposals_in_source": len(proposal_ids),
        "total_preflight_records": len(records),
        "all_proposals_represented_exactly_once": (
            len(proposal_ids) == len(record_pids) == len(set(record_pids))
            and set(proposal_ids) == set(record_pids)
        ),
        "preflight_status_counts": status_counts,
        "go_no_go_counts": go_no_go_counts,
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_application_preflight_records_version": "v2.8-slice-1",
        "source_versions": {
            "controlled_model_adjustment_proposals_version": proposals_payload.get("controlled_model_adjustment_proposals_version"),
            "model_adjustment_approval_ledger_version": approval_payload.get("model_adjustment_approval_ledger_version"),
            "model_adjustment_validation_manifests_version": manifests_payload.get("model_adjustment_validation_manifests_version"),
            "model_adjustment_application_gates_version": gates_payload.get("model_adjustment_application_gates_version"),
            "model_adjustment_application_packets_version": packets_payload.get("model_adjustment_application_packets_version"),
            "model_adjustment_application_dry_runs_version": dry_runs_payload.get("model_adjustment_application_dry_runs_version"),
            "model_adjustment_application_authorizations_version": auth_payload.get("model_adjustment_application_authorizations_version"),
            "model_adjustment_execution_intents_version": intents_payload.get("model_adjustment_execution_intents_version"),
        },
        "preflight_summary": summary,
        "application_preflight_records": records,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("preflight_summary") if isinstance(payload.get("preflight_summary"), dict) else {}
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    rows = payload.get("application_preflight_records") if isinstance(payload.get("application_preflight_records"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Application Preflight Records (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Preflight Version: {payload.get('model_adjustment_application_preflight_records_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Preflight Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Preflight Records: {summary.get('total_preflight_records')}")
    lines.append(f"- Exact Once Representation: {summary.get('all_proposals_represented_exactly_once')}")
    lines.append(f"- Preflight Status Counts: {summary.get('preflight_status_counts')}")
    lines.append(f"- Go/No-Go Counts: {summary.get('go_no_go_counts')}")
    lines.append("")
    lines.append("## Preflight Records")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(f"- {row.get('preflight_id')}: {row.get('proposal_id')} -> {row.get('adjustment_target')}")
            lines.append(f"  Authorization ID: {row.get('authorization_id')} | Intent ID: {row.get('intent_id')}")
            lines.append(f"  Intent Status: {row.get('execution_intent_status')} | Authorization Status: {row.get('authorization_status')}")
            lines.append(f"  Preflight Status: {row.get('preflight_status')} | Go/No-Go: {row.get('go_no_go_state')}")
            lines.append(f"  Required Open Checks: {row.get('required_open_checks')}")
            lines.append(f"  Required Evidence: {row.get('required_evidence')}")
            lines.append(f"  Required Operator Role: {row.get('required_operator_role')}")
            lines.append(f"  Stop Conditions: {row.get('stop_conditions')}")
            lines.append(f"  Rollback Reference: {row.get('rollback_reference')}")
            lines.append(f"  Preflight Notes: {row.get('preflight_notes')}")
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
    auth_path = Path(args.application_authorizations_json)
    intents_path = Path(args.execution_intents_json)
    output_dir = Path(args.output_dir)

    proposals_payload, proposals_err = safe_read_json(repo_root / proposals_path)
    approval_payload, approval_err = safe_read_json(repo_root / approval_path)
    manifests_payload, manifests_err = safe_read_json(repo_root / manifests_path)
    gates_payload, gates_err = safe_read_json(repo_root / gates_path)
    packets_payload, packets_err = safe_read_json(repo_root / packets_path)
    dry_runs_payload, dry_runs_err = safe_read_json(repo_root / dry_runs_path)
    auth_payload, auth_err = safe_read_json(repo_root / auth_path)
    intents_payload, intents_err = safe_read_json(repo_root / intents_path)

    errors = [
        ("controlled model-adjustment proposals", proposals_err),
        ("model-adjustment approval ledger", approval_err),
        ("model-adjustment validation manifests", manifests_err),
        ("model-adjustment application gates", gates_err),
        ("model-adjustment application packets", packets_err),
        ("model-adjustment application dry runs", dry_runs_err),
        ("model-adjustment application authorizations", auth_err),
        ("model-adjustment execution intents", intents_err),
    ]
    for label, err in errors:
        if err is not None:
            print(f"ERROR: {label} unavailable: {err}", file=sys.stderr)
            return 1

    payloads = [
        proposals_payload, approval_payload, manifests_payload, gates_payload,
        packets_payload, dry_runs_payload, auth_payload, intents_payload,
    ]
    if not all(isinstance(x, dict) for x in payloads):
        print("ERROR: one or more source artifacts are not valid JSON objects", file=sys.stderr)
        return 1

    source_paths = {
        "controlled_model_adjustment_proposals_json": normalize_path(proposals_path),
        "model_adjustment_approval_ledger_json": normalize_path(approval_path),
        "model_adjustment_validation_manifests_json": normalize_path(manifests_path),
        "model_adjustment_application_gates_json": normalize_path(gates_path),
        "model_adjustment_application_packets_json": normalize_path(packets_path),
        "model_adjustment_application_dry_runs_json": normalize_path(dry_runs_path),
        "model_adjustment_application_authorizations_json": normalize_path(auth_path),
        "model_adjustment_execution_intents_json": normalize_path(intents_path),
    }

    payload = build_preflight_records(
        proposals_payload=proposals_payload,
        approval_payload=approval_payload,
        manifests_payload=manifests_payload,
        gates_payload=gates_payload,
        packets_payload=packets_payload,
        dry_runs_payload=dry_runs_payload,
        auth_payload=auth_payload,
        intents_payload=intents_payload,
        source_paths=source_paths,
    )

    payload["source_status"] = {
        f"{k}_error": v for k, v in [
            ("controlled_model_adjustment_proposals_json", proposals_err),
            ("model_adjustment_approval_ledger_json", approval_err),
            ("model_adjustment_validation_manifests_json", manifests_err),
            ("model_adjustment_application_gates_json", gates_err),
            ("model_adjustment_application_packets_json", packets_err),
            ("model_adjustment_application_dry_runs_json", dry_runs_err),
            ("model_adjustment_application_authorizations_json", auth_err),
            ("model_adjustment_execution_intents_json", intents_err),
        ]
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
    s = payload.get("preflight_summary") or {}
    print(
        "[STATUS] records={total} exact_once={exact_once} go_no_go={go_no_go}".format(
            total=s.get("total_preflight_records"),
            exact_once=s.get("all_proposals_represented_exactly_once"),
            go_no_go=s.get("go_no_go_counts"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
