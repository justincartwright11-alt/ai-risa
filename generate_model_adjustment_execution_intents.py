#!/usr/bin/env python3
"""
AI-RISA v2.7 Controlled Application Execution Intents (slice 1): read-only governance layer.

Builds execution-intent records from proposals, approval-ledger state, validation
manifests, application gates, application packets, dry-run plans, and authorization
records. This script does not execute adjustments or mutate model behavior,
source artifacts, scheduler logic, or pipeline outputs.
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
OUTPUT_JSON = "model_adjustment_execution_intents.json"
OUTPUT_MD = "model_adjustment_execution_intents.md"

PROPOSALS_DEFAULT = Path("ops/model_adjustments/controlled_model_adjustment_proposals.json")
APPROVAL_LEDGER_DEFAULT = Path("ops/model_adjustments/model_adjustment_approval_ledger.json")
VALIDATION_MANIFESTS_DEFAULT = Path("ops/model_adjustments/model_adjustment_validation_manifests.json")
APPLICATION_GATES_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_gates.json")
APPLICATION_PACKETS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_packets.json")
APPLICATION_DRY_RUNS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_dry_runs.json")
APPLICATION_AUTH_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_authorizations.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled application execution-intent artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--proposals-json", default=str(PROPOSALS_DEFAULT))
    parser.add_argument("--approval-ledger-json", default=str(APPROVAL_LEDGER_DEFAULT))
    parser.add_argument("--validation-manifests-json", default=str(VALIDATION_MANIFESTS_DEFAULT))
    parser.add_argument("--application-gates-json", default=str(APPLICATION_GATES_DEFAULT))
    parser.add_argument("--application-packets-json", default=str(APPLICATION_PACKETS_DEFAULT))
    parser.add_argument("--application-dry-runs-json", default=str(APPLICATION_DRY_RUNS_DEFAULT))
    parser.add_argument("--application-authorizations-json", default=str(APPLICATION_AUTH_DEFAULT))
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


def index_by_proposal_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = str(row.get("proposal_id") or "").strip()
        if pid:
            indexed[pid] = row
    return indexed


def intent_status(
    gate_status: str,
    authorization_status: str,
) -> tuple[str, str, list[str]]:
    blockers: list[str] = []

    if authorization_status != "authorized":
        blockers.append("authorization_not_active")
    if gate_status == "blocked":
        blockers.append("application_gate_blocked")
    if gate_status == "conditionally_eligible":
        blockers.append("conditional_requirements_unresolved")

    if blockers:
        return "blocked_intent", "blocked", blockers

    # Even with favorable upstream state, this remains governance-only for v2.7.
    return "authorization_ready_intent", "draft_only", ["governance_only_no_execution_path"]


def required_final_checks(gate_status: str, authorization_status: str) -> list[str]:
    checks = [
        "Confirm latest linked artifacts are unchanged",
        "Confirm no pipeline/scheduler drift since dry-run and authorization snapshot",
        "Confirm rollback reference is present and reviewed",
        "Confirm execution remains disabled in governance-only phase",
    ]
    if authorization_status != "authorized":
        checks.append("Obtain explicit authorization signoffs")
    if gate_status != "eligible_for_controlled_application":
        checks.append("Resolve gate conditions to eligible state")
    return checks


def execution_blockers(gate_status: str, authorization_status: str) -> list[str]:
    blockers: list[str] = []
    if gate_status == "blocked":
        blockers.append("gate_blocked")
    elif gate_status == "conditionally_eligible":
        blockers.append("gate_conditional")
    if authorization_status != "authorized":
        blockers.append("not_authorized")
    blockers.append("execution_path_not_enabled_in_v2_7")
    return blockers


def build_execution_intents(
    proposals_payload: dict[str, Any],
    approval_payload: dict[str, Any],
    manifests_payload: dict[str, Any],
    gates_payload: dict[str, Any],
    packets_payload: dict[str, Any],
    dry_runs_payload: dict[str, Any],
    auth_payload: dict[str, Any],
    source_paths: dict[str, str],
) -> dict[str, Any]:
    proposals = proposals_payload.get("proposals") if isinstance(proposals_payload.get("proposals"), list) else []
    approval_rows = approval_payload.get("approval_ledger") if isinstance(approval_payload.get("approval_ledger"), list) else []
    manifest_rows = manifests_payload.get("validation_manifests") if isinstance(manifests_payload.get("validation_manifests"), list) else []
    gate_rows = gates_payload.get("application_gates") if isinstance(gates_payload.get("application_gates"), list) else []
    packet_rows = packets_payload.get("application_packets") if isinstance(packets_payload.get("application_packets"), list) else []
    dry_rows = dry_runs_payload.get("application_dry_runs") if isinstance(dry_runs_payload.get("application_dry_runs"), list) else []
    auth_rows = auth_payload.get("application_authorizations") if isinstance(auth_payload.get("application_authorizations"), list) else []

    approval_by_pid = index_by_proposal_id(approval_rows)
    manifest_by_pid = index_by_proposal_id(manifest_rows)
    gates_by_pid = index_by_proposal_id(gate_rows)
    packets_by_pid = index_by_proposal_id(packet_rows)
    dry_by_pid = index_by_proposal_id(dry_rows)
    auth_by_pid = index_by_proposal_id(auth_rows)

    intents: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    readiness_counts: dict[str, int] = {}

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

        gate_status = str(gate_row.get("application_gate_status") or "blocked")
        authorization_status = str(auth_row.get("authorization_status") or "not_authorized")

        exec_intent_status, intent_readiness, base_blockers = intent_status(
            gate_status,
            authorization_status,
        )

        status_counts[exec_intent_status] = status_counts.get(exec_intent_status, 0) + 1
        readiness_counts[intent_readiness] = readiness_counts.get(intent_readiness, 0) + 1

        blockers = base_blockers + execution_blockers(gate_status, authorization_status)
        # De-duplicate while preserving order.
        seen: set[str] = set()
        unique_blockers: list[str] = []
        for b in blockers:
            if b not in seen:
                seen.add(b)
                unique_blockers.append(b)

        intents.append(
            {
                "intent_id": f"intent-{idx:03d}",
                "proposal_id": proposal_id,
                "authorization_id": auth_row.get("authorization_id"),
                "packet_id": packet_row.get("packet_id"),
                "dry_run_id": dry_row.get("dry_run_id"),
                "proposal_family": proposal_family,
                "adjustment_target": adjustment_target,
                "application_gate_status": gate_status,
                "authorization_status": authorization_status,
                "execution_intent_status": exec_intent_status,
                "intent_readiness": intent_readiness,
                "required_final_checks": required_final_checks(gate_status, authorization_status),
                "required_operator_role": str(auth_row.get("required_operator_role") or packet_row.get("operator_role_required") or dry_row.get("required_operator_role") or "ops_reviewer"),
                "execution_blockers": unique_blockers,
                "rollback_reference": f"rollback-from-{packet_row.get('packet_id') or proposal_id}",
                "intent_notes": "governance_record_only_no_execution_enabled",
                "source_paths": {
                    "controlled_model_adjustment_proposals_json": source_paths["controlled_model_adjustment_proposals_json"],
                    "model_adjustment_approval_ledger_json": source_paths["model_adjustment_approval_ledger_json"],
                    "model_adjustment_validation_manifests_json": source_paths["model_adjustment_validation_manifests_json"],
                    "model_adjustment_application_gates_json": source_paths["model_adjustment_application_gates_json"],
                    "model_adjustment_application_packets_json": source_paths["model_adjustment_application_packets_json"],
                    "model_adjustment_application_dry_runs_json": source_paths["model_adjustment_application_dry_runs_json"],
                    "model_adjustment_application_authorizations_json": source_paths["model_adjustment_application_authorizations_json"],
                    "approval_ledger_entry_id": approval_row.get("ledger_item_id"),
                    "validation_manifest_id": manifest_row.get("manifest_id"),
                    "application_gate_id": gate_row.get("gate_id"),
                    "application_packet_id": packet_row.get("packet_id"),
                    "application_dry_run_id": dry_row.get("dry_run_id"),
                    "application_authorization_id": auth_row.get("authorization_id"),
                },
            }
        )

    proposal_ids = [str(x.get("proposal_id") or "") for x in proposals if isinstance(x, dict)]
    intent_ids = [str(x.get("proposal_id") or "") for x in intents if isinstance(x, dict)]

    summary = {
        "total_proposals_in_source": len(proposal_ids),
        "total_execution_intents": len(intents),
        "all_proposals_represented_exactly_once": (
            len(proposal_ids) == len(intent_ids) == len(set(intent_ids))
            and set(proposal_ids) == set(intent_ids)
        ),
        "execution_intent_status_counts": status_counts,
        "intent_readiness_counts": readiness_counts,
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_execution_intents_version": "v2.7-slice-1",
        "source_versions": {
            "controlled_model_adjustment_proposals_version": proposals_payload.get("controlled_model_adjustment_proposals_version"),
            "model_adjustment_approval_ledger_version": approval_payload.get("model_adjustment_approval_ledger_version"),
            "model_adjustment_validation_manifests_version": manifests_payload.get("model_adjustment_validation_manifests_version"),
            "model_adjustment_application_gates_version": gates_payload.get("model_adjustment_application_gates_version"),
            "model_adjustment_application_packets_version": packets_payload.get("model_adjustment_application_packets_version"),
            "model_adjustment_application_dry_runs_version": dry_runs_payload.get("model_adjustment_application_dry_runs_version"),
            "model_adjustment_application_authorizations_version": auth_payload.get("model_adjustment_application_authorizations_version"),
        },
        "execution_intent_summary": summary,
        "execution_intents": intents,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("execution_intent_summary") if isinstance(payload.get("execution_intent_summary"), dict) else {}
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    rows = payload.get("execution_intents") if isinstance(payload.get("execution_intents"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Application Execution Intents (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Intent Version: {payload.get('model_adjustment_execution_intents_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Intent Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Execution Intents: {summary.get('total_execution_intents')}")
    lines.append(f"- Exact Once Representation: {summary.get('all_proposals_represented_exactly_once')}")
    lines.append(f"- Intent Status Counts: {summary.get('execution_intent_status_counts')}")
    lines.append(f"- Intent Readiness Counts: {summary.get('intent_readiness_counts')}")
    lines.append("")
    lines.append("## Execution Intent Records")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(f"- {row.get('intent_id')}: {row.get('proposal_id')} -> {row.get('adjustment_target')}")
            lines.append(f"  Authorization ID: {row.get('authorization_id')} | Packet ID: {row.get('packet_id')} | Dry Run ID: {row.get('dry_run_id')}")
            lines.append(f"  Gate Status: {row.get('application_gate_status')} | Authorization Status: {row.get('authorization_status')}")
            lines.append(f"  Intent Status: {row.get('execution_intent_status')} | Intent Readiness: {row.get('intent_readiness')}")
            lines.append(f"  Required Final Checks: {row.get('required_final_checks')}")
            lines.append(f"  Required Operator Role: {row.get('required_operator_role')}")
            lines.append(f"  Execution Blockers: {row.get('execution_blockers')}")
            lines.append(f"  Rollback Reference: {row.get('rollback_reference')}")
            lines.append(f"  Intent Notes: {row.get('intent_notes')}")
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
    output_dir = Path(args.output_dir)

    proposals_payload, proposals_err = safe_read_json(repo_root / proposals_path)
    approval_payload, approval_err = safe_read_json(repo_root / approval_path)
    manifests_payload, manifests_err = safe_read_json(repo_root / manifests_path)
    gates_payload, gates_err = safe_read_json(repo_root / gates_path)
    packets_payload, packets_err = safe_read_json(repo_root / packets_path)
    dry_runs_payload, dry_runs_err = safe_read_json(repo_root / dry_runs_path)
    auth_payload, auth_err = safe_read_json(repo_root / auth_path)

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
    if auth_err is not None:
        print(f"ERROR: model-adjustment application authorizations unavailable: {auth_err}", file=sys.stderr)
        return 1

    if not all(
        isinstance(x, dict)
        for x in [
            proposals_payload,
            approval_payload,
            manifests_payload,
            gates_payload,
            packets_payload,
            dry_runs_payload,
            auth_payload,
        ]
    ):
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
    }

    payload = build_execution_intents(
        proposals_payload=proposals_payload,
        approval_payload=approval_payload,
        manifests_payload=manifests_payload,
        gates_payload=gates_payload,
        packets_payload=packets_payload,
        dry_runs_payload=dry_runs_payload,
        auth_payload=auth_payload,
        source_paths=source_paths,
    )

    payload["source_status"] = {
        "controlled_model_adjustment_proposals_json_error": proposals_err,
        "model_adjustment_approval_ledger_json_error": approval_err,
        "model_adjustment_validation_manifests_json_error": manifests_err,
        "model_adjustment_application_gates_json_error": gates_err,
        "model_adjustment_application_packets_json_error": packets_err,
        "model_adjustment_application_dry_runs_json_error": dry_runs_err,
        "model_adjustment_application_authorizations_json_error": auth_err,
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
        "[STATUS] intents={total} exact_once={exact_once}".format(
            total=((payload.get("execution_intent_summary") or {}).get("total_execution_intents")),
            exact_once=((payload.get("execution_intent_summary") or {}).get("all_proposals_represented_exactly_once")),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())