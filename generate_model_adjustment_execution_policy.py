#!/usr/bin/env python3
"""
AI-RISA v3.0 Controlled Execution Policy (slice 1): read-only governance layer.

Builds per-proposal execution policy records that define current non-mutating policy
state, prohibited actions, and enablement conditions required before any future
execution mode could be introduced. This script does not execute adjustments,
auto-promote records, write configs, or mutate model behavior.
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
OUTPUT_JSON = "model_adjustment_execution_policy.json"
OUTPUT_MD = "model_adjustment_execution_policy.md"

PROPOSALS_DEFAULT = Path("ops/model_adjustments/controlled_model_adjustment_proposals.json")
APPROVAL_LEDGER_DEFAULT = Path("ops/model_adjustments/model_adjustment_approval_ledger.json")
VALIDATION_MANIFESTS_DEFAULT = Path("ops/model_adjustments/model_adjustment_validation_manifests.json")
APPLICATION_GATES_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_gates.json")
APPLICATION_PACKETS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_packets.json")
APPLICATION_DRY_RUNS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_dry_runs.json")
APPLICATION_AUTH_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_authorizations.json")
EXECUTION_INTENTS_DEFAULT = Path("ops/model_adjustments/model_adjustment_execution_intents.json")
PREFLIGHT_RECORDS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_preflight_records.json")
READINESS_DECISIONS_DEFAULT = Path("ops/model_adjustments/model_adjustment_readiness_decisions.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled execution policy artifacts"
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
    parser.add_argument("--application-preflight-records-json", default=str(PREFLIGHT_RECORDS_DEFAULT))
    parser.add_argument("--readiness-decisions-json", default=str(READINESS_DECISIONS_DEFAULT))
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


def index_by_proposal_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = str(row.get("proposal_id") or "").strip()
        if pid:
            indexed[pid] = row
    return indexed


def derive_policy(
    readiness_decision: str,
    decision_state: str,
    gate_status: str,
    authorization_status: str,
    intent_status: str,
    preflight_status: str,
) -> tuple[str, str, str, list[str], list[str]]:
    """
    Returns:
      (execution_policy_state, policy_mode, execution_permission,
       policy_blockers, required_enablement_conditions)
    """
    blockers: list[str] = []
    conditions: list[str] = []

    policy_mode = "governance_only"
    execution_permission = "denied"
    execution_policy_state = "execution_disabled"

    if decision_state != "blocked":
        blockers.append("decision_state_not_blocked")
        conditions.append("Reconcile readiness decision state to blocked governance state")

    if readiness_decision == "not_ready":
        blockers.append("readiness_not_ready")
        conditions.append("Advance readiness from not_ready to conditionally_ready")
    elif readiness_decision == "conditionally_ready":
        blockers.append("readiness_conditionally_ready")
        conditions.append("Resolve all conditional readiness requirements")
    elif readiness_decision == "governance_ready_but_execution_disabled":
        blockers.append("governance_ready_execution_still_disabled")
        conditions.append("Adopt explicit execution-enable policy in a future governed slice")
    else:
        blockers.append("readiness_decision_unrecognized")
        conditions.append("Normalize readiness decision taxonomy")

    if gate_status != "eligible_for_controlled_application":
        blockers.append("application_gate_not_eligible")
        conditions.append("Set application gate to eligible_for_controlled_application")
    if authorization_status != "authorized":
        blockers.append("authorization_not_active")
        conditions.append("Obtain active authorization with required signoffs")
    if intent_status != "authorization_ready_intent":
        blockers.append("execution_intent_not_authorization_ready")
        conditions.append("Resolve execution intent to authorization_ready_intent")
    if preflight_status != "blocked":
        blockers.append("preflight_state_unexpected")
        conditions.append("Reconcile preflight status to governance defaults")

    conditions.extend(
        [
            "Define explicit execution policy controls and audit requirements",
            "Introduce execution path only via separately approved governed slice",
            "Preserve rollback reference integrity and operator acknowledgment",
        ]
    )
    blockers.append("execution_path_not_enabled_in_v3_0")

    # Deduplicate while preserving order.
    seen_b: set[str] = set()
    dedup_blockers: list[str] = []
    for b in blockers:
        if b not in seen_b:
            seen_b.add(b)
            dedup_blockers.append(b)

    seen_c: set[str] = set()
    dedup_conditions: list[str] = []
    for c in conditions:
        if c not in seen_c:
            seen_c.add(c)
            dedup_conditions.append(c)

    return execution_policy_state, policy_mode, execution_permission, dedup_blockers, dedup_conditions


def prohibited_actions() -> list[str]:
    return [
        "apply_model_adjustment",
        "enable_live_execution_mode",
        "auto_promote_readiness_to_executable",
        "write_runtime_execution_config",
        "mutate_model_weights_or_rules",
        "bypass_approval_authorization_or_preflight_controls",
    ]


def build_execution_policy(
    proposals_payload: dict[str, Any],
    approval_payload: dict[str, Any],
    manifests_payload: dict[str, Any],
    gates_payload: dict[str, Any],
    packets_payload: dict[str, Any],
    dry_runs_payload: dict[str, Any],
    auth_payload: dict[str, Any],
    intents_payload: dict[str, Any],
    preflight_payload: dict[str, Any],
    decisions_payload: dict[str, Any],
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
    preflight_rows = preflight_payload.get("application_preflight_records") if isinstance(preflight_payload.get("application_preflight_records"), list) else []
    decision_rows = decisions_payload.get("readiness_decisions") if isinstance(decisions_payload.get("readiness_decisions"), list) else []

    approval_by_pid = index_by_proposal_id(approval_rows)
    manifest_by_pid = index_by_proposal_id(manifest_rows)
    gates_by_pid = index_by_proposal_id(gate_rows)
    packets_by_pid = index_by_proposal_id(packet_rows)
    dry_by_pid = index_by_proposal_id(dry_rows)
    auth_by_pid = index_by_proposal_id(auth_rows)
    intents_by_pid = index_by_proposal_id(intent_rows)
    preflight_by_pid = index_by_proposal_id(preflight_rows)
    decisions_by_pid = index_by_proposal_id(decision_rows)

    policies: list[dict[str, Any]] = []
    state_counts: dict[str, int] = {}
    permission_counts: dict[str, int] = {}

    for idx, proposal in enumerate(proposals, start=1):
        if not isinstance(proposal, dict):
            continue
        proposal_id = str(proposal.get("proposal_id") or "").strip()

        approval_row = approval_by_pid.get(proposal_id, {})
        manifest_row = manifest_by_pid.get(proposal_id, {})
        gate_row = gates_by_pid.get(proposal_id, {})
        packet_row = packets_by_pid.get(proposal_id, {})
        dry_row = dry_by_pid.get(proposal_id, {})
        auth_row = auth_by_pid.get(proposal_id, {})
        intent_row = intents_by_pid.get(proposal_id, {})
        preflight_row = preflight_by_pid.get(proposal_id, {})
        decision_row = decisions_by_pid.get(proposal_id, {})

        readiness_decision = str(decision_row.get("readiness_decision") or "not_ready")
        decision_state = str(decision_row.get("decision_state") or "blocked")
        gate_status = str(gate_row.get("application_gate_status") or "blocked")
        authorization_status = str(auth_row.get("authorization_status") or "not_authorized")
        intent_status = str(intent_row.get("execution_intent_status") or "blocked_intent")
        preflight_status = str(preflight_row.get("preflight_status") or "blocked")

        (
            execution_policy_state,
            policy_mode,
            execution_permission,
            policy_blockers,
            required_enablement_conditions,
        ) = derive_policy(
            readiness_decision=readiness_decision,
            decision_state=decision_state,
            gate_status=gate_status,
            authorization_status=authorization_status,
            intent_status=intent_status,
            preflight_status=preflight_status,
        )

        state_counts[execution_policy_state] = state_counts.get(execution_policy_state, 0) + 1
        permission_counts[execution_permission] = permission_counts.get(execution_permission, 0) + 1

        decision_id = decision_row.get("decision_id")
        packet_id = packet_row.get("packet_id")

        required_operator_role = str(
            decision_row.get("required_operator_role")
            or auth_row.get("required_operator_role")
            or packet_row.get("operator_role_required")
            or dry_row.get("required_operator_role")
            or "ops_reviewer"
        )

        policies.append(
            {
                "policy_id": f"policy-{idx:03d}",
                "proposal_id": proposal_id,
                "decision_id": decision_id,
                "execution_policy_state": execution_policy_state,
                "policy_mode": policy_mode,
                "execution_permission": execution_permission,
                "policy_blockers": policy_blockers,
                "required_enablement_conditions": required_enablement_conditions,
                "required_operator_role": required_operator_role,
                "prohibited_actions": prohibited_actions(),
                "rollback_reference": f"rollback-from-{packet_id or proposal_id}",
                "policy_notes": "governance_policy_only_execution_denied_in_v3_0",
                "source_paths": {
                    "controlled_model_adjustment_proposals_json": source_paths["controlled_model_adjustment_proposals_json"],
                    "model_adjustment_approval_ledger_json": source_paths["model_adjustment_approval_ledger_json"],
                    "model_adjustment_validation_manifests_json": source_paths["model_adjustment_validation_manifests_json"],
                    "model_adjustment_application_gates_json": source_paths["model_adjustment_application_gates_json"],
                    "model_adjustment_application_packets_json": source_paths["model_adjustment_application_packets_json"],
                    "model_adjustment_application_dry_runs_json": source_paths["model_adjustment_application_dry_runs_json"],
                    "model_adjustment_application_authorizations_json": source_paths["model_adjustment_application_authorizations_json"],
                    "model_adjustment_execution_intents_json": source_paths["model_adjustment_execution_intents_json"],
                    "model_adjustment_application_preflight_records_json": source_paths["model_adjustment_application_preflight_records_json"],
                    "model_adjustment_readiness_decisions_json": source_paths["model_adjustment_readiness_decisions_json"],
                    "approval_ledger_entry_id": approval_row.get("ledger_item_id"),
                    "validation_manifest_id": manifest_row.get("manifest_id"),
                    "application_gate_id": gate_row.get("gate_id"),
                    "application_packet_id": packet_id,
                    "application_dry_run_id": dry_row.get("dry_run_id"),
                    "application_authorization_id": auth_row.get("authorization_id"),
                    "execution_intent_id": intent_row.get("intent_id"),
                    "application_preflight_id": preflight_row.get("preflight_id"),
                    "readiness_decision_id": decision_id,
                },
            }
        )

    proposal_ids = [str(x.get("proposal_id") or "") for x in proposals if isinstance(x, dict)]
    policy_pids = [str(x.get("proposal_id") or "") for x in policies if isinstance(x, dict)]

    summary = {
        "total_proposals_in_source": len(proposal_ids),
        "total_execution_policy_records": len(policies),
        "all_proposals_represented_exactly_once": (
            len(proposal_ids) == len(policy_pids) == len(set(policy_pids))
            and set(proposal_ids) == set(policy_pids)
        ),
        "execution_policy_state_counts": state_counts,
        "execution_permission_counts": permission_counts,
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_execution_policy_version": "v3.0-slice-1",
        "source_versions": {
            "controlled_model_adjustment_proposals_version": proposals_payload.get("controlled_model_adjustment_proposals_version"),
            "model_adjustment_approval_ledger_version": approval_payload.get("model_adjustment_approval_ledger_version"),
            "model_adjustment_validation_manifests_version": manifests_payload.get("model_adjustment_validation_manifests_version"),
            "model_adjustment_application_gates_version": gates_payload.get("model_adjustment_application_gates_version"),
            "model_adjustment_application_packets_version": packets_payload.get("model_adjustment_application_packets_version"),
            "model_adjustment_application_dry_runs_version": dry_runs_payload.get("model_adjustment_application_dry_runs_version"),
            "model_adjustment_application_authorizations_version": auth_payload.get("model_adjustment_application_authorizations_version"),
            "model_adjustment_execution_intents_version": intents_payload.get("model_adjustment_execution_intents_version"),
            "model_adjustment_application_preflight_records_version": preflight_payload.get("model_adjustment_application_preflight_records_version"),
            "model_adjustment_readiness_decisions_version": decisions_payload.get("model_adjustment_readiness_decisions_version"),
        },
        "execution_policy_summary": summary,
        "execution_policy_records": policies,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("execution_policy_summary") if isinstance(payload.get("execution_policy_summary"), dict) else {}
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    rows = payload.get("execution_policy_records") if isinstance(payload.get("execution_policy_records"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Execution Policy (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Policy Version: {payload.get('model_adjustment_execution_policy_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Policy Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Policy Records: {summary.get('total_execution_policy_records')}")
    lines.append(f"- Exact Once Representation: {summary.get('all_proposals_represented_exactly_once')}")
    lines.append(f"- Execution Policy State Counts: {summary.get('execution_policy_state_counts')}")
    lines.append(f"- Execution Permission Counts: {summary.get('execution_permission_counts')}")
    lines.append("")
    lines.append("## Policy Records")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(f"- {row.get('policy_id')}: {row.get('proposal_id')} | decision={row.get('decision_id')}")
            lines.append(f"  Policy State: {row.get('execution_policy_state')} | Mode: {row.get('policy_mode')} | Execution Permission: {row.get('execution_permission')}")
            lines.append(f"  Policy Blockers: {row.get('policy_blockers')}")
            lines.append(f"  Required Enablement Conditions: {row.get('required_enablement_conditions')}")
            lines.append(f"  Required Operator Role: {row.get('required_operator_role')}")
            lines.append(f"  Prohibited Actions: {row.get('prohibited_actions')}")
            lines.append(f"  Rollback Reference: {row.get('rollback_reference')}")
            lines.append(f"  Policy Notes: {row.get('policy_notes')}")
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
    preflight_path = Path(args.application_preflight_records_json)
    decisions_path = Path(args.readiness_decisions_json)
    output_dir = Path(args.output_dir)

    proposals_payload, proposals_err = safe_read_json(repo_root / proposals_path)
    approval_payload, approval_err = safe_read_json(repo_root / approval_path)
    manifests_payload, manifests_err = safe_read_json(repo_root / manifests_path)
    gates_payload, gates_err = safe_read_json(repo_root / gates_path)
    packets_payload, packets_err = safe_read_json(repo_root / packets_path)
    dry_runs_payload, dry_runs_err = safe_read_json(repo_root / dry_runs_path)
    auth_payload, auth_err = safe_read_json(repo_root / auth_path)
    intents_payload, intents_err = safe_read_json(repo_root / intents_path)
    preflight_payload, preflight_err = safe_read_json(repo_root / preflight_path)
    decisions_payload, decisions_err = safe_read_json(repo_root / decisions_path)

    errors = [
        ("controlled model-adjustment proposals", proposals_err),
        ("model-adjustment approval ledger", approval_err),
        ("model-adjustment validation manifests", manifests_err),
        ("model-adjustment application gates", gates_err),
        ("model-adjustment application packets", packets_err),
        ("model-adjustment application dry runs", dry_runs_err),
        ("model-adjustment application authorizations", auth_err),
        ("model-adjustment execution intents", intents_err),
        ("model-adjustment application preflight records", preflight_err),
        ("model-adjustment readiness decisions", decisions_err),
    ]
    for label, err in errors:
        if err is not None:
            print(f"ERROR: {label} unavailable: {err}", file=sys.stderr)
            return 1

    payloads = [
        proposals_payload,
        approval_payload,
        manifests_payload,
        gates_payload,
        packets_payload,
        dry_runs_payload,
        auth_payload,
        intents_payload,
        preflight_payload,
        decisions_payload,
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
        "model_adjustment_application_preflight_records_json": normalize_path(preflight_path),
        "model_adjustment_readiness_decisions_json": normalize_path(decisions_path),
    }

    payload = build_execution_policy(
        proposals_payload=proposals_payload,
        approval_payload=approval_payload,
        manifests_payload=manifests_payload,
        gates_payload=gates_payload,
        packets_payload=packets_payload,
        dry_runs_payload=dry_runs_payload,
        auth_payload=auth_payload,
        intents_payload=intents_payload,
        preflight_payload=preflight_payload,
        decisions_payload=decisions_payload,
        source_paths=source_paths,
    )

    payload["source_status"] = {
        f"{k}_error": v
        for k, v in [
            ("controlled_model_adjustment_proposals_json", proposals_err),
            ("model_adjustment_approval_ledger_json", approval_err),
            ("model_adjustment_validation_manifests_json", manifests_err),
            ("model_adjustment_application_gates_json", gates_err),
            ("model_adjustment_application_packets_json", packets_err),
            ("model_adjustment_application_dry_runs_json", dry_runs_err),
            ("model_adjustment_application_authorizations_json", auth_err),
            ("model_adjustment_execution_intents_json", intents_err),
            ("model_adjustment_application_preflight_records_json", preflight_err),
            ("model_adjustment_readiness_decisions_json", decisions_err),
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
    s = payload.get("execution_policy_summary") or {}
    print(
        "[STATUS] policies={total} exact_once={exact_once} permission={perm}".format(
            total=s.get("total_execution_policy_records"),
            exact_once=s.get("all_proposals_represented_exactly_once"),
            perm=s.get("execution_permission_counts"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
