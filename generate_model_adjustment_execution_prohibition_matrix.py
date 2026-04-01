#!/usr/bin/env python3
"""
AI-RISA v3.4 Controlled Execution Prohibition Matrix (slice 1): read-only governance layer.

Builds a canonical matrix stating which execution action types are explicitly prohibited,
by which governance layer, and under what condition. Each record is anchored to a proposal
and cross-linked to the policy, criteria, and ineligibility layers. This script does not
execute adjustments, create an execution path, auto-promote records, write configs, or
mutate model behavior.
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
OUTPUT_JSON = "model_adjustment_execution_prohibition_matrix.json"
OUTPUT_MD = "model_adjustment_execution_prohibition_matrix.md"

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
EXECUTION_POLICY_DEFAULT = Path("ops/model_adjustments/model_adjustment_execution_policy.json")
EXECUTION_ENABLEMENT_CRITERIA_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_enablement_criteria.json"
)
EXECUTION_BLOCKER_REGISTRY_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_blocker_registry.json"
)
EXECUTION_INELIGIBILITY_REGISTER_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_ineligibility_register.json"
)

# Canonical prohibited action types — fixed across all proposals in governance-only mode
CANONICAL_PROHIBITED_ACTIONS = [
    "direct_model_weight_mutation",
    "automated_confidence_threshold_adjustment",
    "pipeline_parameter_write",
    "execution_auto_promotion",
    "config_file_write",
    "prediction_rule_modification",
    "scheduler_execution_trigger",
    "model_adjustment_self_application",
    "rollback_procedure_initiation_without_operator_approval",
    "execution_bypass_of_governance_gate",
]

# Source layer that prohibits each action type
PROHIBITION_SOURCE_MAP = {
    "direct_model_weight_mutation": "execution_policy",
    "automated_confidence_threshold_adjustment": "execution_policy",
    "pipeline_parameter_write": "execution_enablement_criteria",
    "execution_auto_promotion": "execution_policy",
    "config_file_write": "execution_enablement_criteria",
    "prediction_rule_modification": "execution_ineligibility_register",
    "scheduler_execution_trigger": "execution_policy",
    "model_adjustment_self_application": "execution_ineligibility_register",
    "rollback_procedure_initiation_without_operator_approval": "execution_blocker_registry",
    "execution_bypass_of_governance_gate": "execution_policy",
}

# Release condition required to lift each prohibition
RELEASE_CONDITION_MAP = {
    "direct_model_weight_mutation": (
        "dedicated_execution_enablement_release_with_explicit_mutation_permission_required"
    ),
    "automated_confidence_threshold_adjustment": (
        "dedicated_execution_enablement_release_with_threshold_adjustment_permission_required"
    ),
    "pipeline_parameter_write": (
        "all_enablement_criteria_must_be_satisfied_and_enablement_release_required"
    ),
    "execution_auto_promotion": (
        "execution_policy_must_explicitly_permit_auto_promotion_and_enablement_release_required"
    ),
    "config_file_write": (
        "all_enablement_criteria_must_be_satisfied_and_enablement_release_required"
    ),
    "prediction_rule_modification": (
        "ineligibility_must_be_resolved_and_enablement_release_required"
    ),
    "scheduler_execution_trigger": (
        "execution_policy_must_explicitly_permit_scheduler_trigger_and_enablement_release_required"
    ),
    "model_adjustment_self_application": (
        "ineligibility_must_be_resolved_and_enablement_release_required"
    ),
    "rollback_procedure_initiation_without_operator_approval": (
        "operator_approval_required_before_rollback_initiation_and_enablement_release_required"
    ),
    "execution_bypass_of_governance_gate": (
        "governance_gate_bypass_is_unconditionally_prohibited_enablement_release_insufficient"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled execution prohibition matrix artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--proposals-json", default=str(PROPOSALS_DEFAULT))
    parser.add_argument("--approval-ledger-json", default=str(APPROVAL_LEDGER_DEFAULT))
    parser.add_argument("--validation-manifests-json", default=str(VALIDATION_MANIFESTS_DEFAULT))
    parser.add_argument("--application-gates-json", default=str(APPLICATION_GATES_DEFAULT))
    parser.add_argument("--application-packets-json", default=str(APPLICATION_PACKETS_DEFAULT))
    parser.add_argument("--application-dry-runs-json", default=str(APPLICATION_DRY_RUNS_DEFAULT))
    parser.add_argument(
        "--application-authorizations-json", default=str(APPLICATION_AUTH_DEFAULT)
    )
    parser.add_argument("--execution-intents-json", default=str(EXECUTION_INTENTS_DEFAULT))
    parser.add_argument(
        "--application-preflight-records-json", default=str(PREFLIGHT_RECORDS_DEFAULT)
    )
    parser.add_argument("--readiness-decisions-json", default=str(READINESS_DECISIONS_DEFAULT))
    parser.add_argument("--execution-policy-json", default=str(EXECUTION_POLICY_DEFAULT))
    parser.add_argument(
        "--execution-enablement-criteria-json",
        default=str(EXECUTION_ENABLEMENT_CRITERIA_DEFAULT),
    )
    parser.add_argument(
        "--execution-blocker-registry-json",
        default=str(EXECUTION_BLOCKER_REGISTRY_DEFAULT),
    )
    parser.add_argument(
        "--execution-ineligibility-register-json",
        default=str(EXECUTION_INELIGIBILITY_REGISTER_DEFAULT),
    )
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


def derive_prohibition_reason(
    action_type: str,
    policy_row: dict[str, Any],
    criteria_row: dict[str, Any],
    inelig_row: dict[str, Any],
    execution_permission: str,
    enablement_state: str,
    ineligibility_state: str,
) -> str:
    """Derive a specific reason string for why this action type is prohibited."""
    policy_mode = str(policy_row.get("policy_mode") or "governance_only")
    inelig_class = str(inelig_row.get("ineligibility_class") or "ineligible_for_execution")

    if action_type == "execution_bypass_of_governance_gate":
        return "governance_gate_bypass_is_unconditionally_prohibited_in_all_versions"
    if execution_permission != "allowed":
        return (
            f"execution_policy_mode_{policy_mode}_denies_{action_type.replace(' ', '_')}"
        )
    if enablement_state != "enablement_met":
        return (
            f"enablement_criteria_unmet_prohibits_{action_type.replace(' ', '_')}"
        )
    if ineligibility_state == "ineligible_for_execution":
        return (
            f"proposal_has_ineligibility_class_{inelig_class}_prohibiting_{action_type.replace(' ', '_')}"
        )
    return f"governance_only_mode_prohibits_{action_type.replace(' ', '_')}_in_v3_4"


def build_prohibition_matrix(
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
    policy_payload: dict[str, Any],
    criteria_payload: dict[str, Any],
    blocker_payload: dict[str, Any],
    inelig_payload: dict[str, Any],
    source_paths: dict[str, str],
) -> dict[str, Any]:
    proposals = (
        proposals_payload.get("proposals")
        if isinstance(proposals_payload.get("proposals"), list)
        else []
    )
    approval_rows = (
        approval_payload.get("approval_ledger")
        if isinstance(approval_payload.get("approval_ledger"), list)
        else []
    )
    manifest_rows = (
        manifests_payload.get("validation_manifests")
        if isinstance(manifests_payload.get("validation_manifests"), list)
        else []
    )
    gate_rows = (
        gates_payload.get("application_gates")
        if isinstance(gates_payload.get("application_gates"), list)
        else []
    )
    packet_rows = (
        packets_payload.get("application_packets")
        if isinstance(packets_payload.get("application_packets"), list)
        else []
    )
    dry_rows = (
        dry_runs_payload.get("application_dry_runs")
        if isinstance(dry_runs_payload.get("application_dry_runs"), list)
        else []
    )
    auth_rows = (
        auth_payload.get("application_authorizations")
        if isinstance(auth_payload.get("application_authorizations"), list)
        else []
    )
    intent_rows = (
        intents_payload.get("execution_intents")
        if isinstance(intents_payload.get("execution_intents"), list)
        else []
    )
    preflight_rows = (
        preflight_payload.get("application_preflight_records")
        if isinstance(preflight_payload.get("application_preflight_records"), list)
        else []
    )
    decision_rows = (
        decisions_payload.get("readiness_decisions")
        if isinstance(decisions_payload.get("readiness_decisions"), list)
        else []
    )
    policy_rows = (
        policy_payload.get("execution_policy_records")
        if isinstance(policy_payload.get("execution_policy_records"), list)
        else []
    )
    criteria_rows = (
        criteria_payload.get("execution_enablement_criteria")
        if isinstance(criteria_payload.get("execution_enablement_criteria"), list)
        else []
    )
    inelig_rows = (
        inelig_payload.get("execution_ineligibility_register")
        if isinstance(inelig_payload.get("execution_ineligibility_register"), list)
        else []
    )

    approval_by_pid = index_by_proposal_id(approval_rows)
    manifest_by_pid = index_by_proposal_id(manifest_rows)
    gates_by_pid = index_by_proposal_id(gate_rows)
    packets_by_pid = index_by_proposal_id(packet_rows)
    dry_by_pid = index_by_proposal_id(dry_rows)
    auth_by_pid = index_by_proposal_id(auth_rows)
    intents_by_pid = index_by_proposal_id(intent_rows)
    preflight_by_pid = index_by_proposal_id(preflight_rows)
    decisions_by_pid = index_by_proposal_id(decision_rows)
    policy_by_pid = index_by_proposal_id(policy_rows)
    criteria_by_pid = index_by_proposal_id(criteria_rows)
    inelig_by_pid = index_by_proposal_id(inelig_rows)

    matrix_records: list[dict[str, Any]] = []
    prohibition_state_counts: dict[str, int] = {}
    action_type_counts: dict[str, int] = {}
    proposals_covered: list[str] = []

    global_seq = 0

    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        proposal_id = str(proposal.get("proposal_id") or "").strip()
        if not proposal_id:
            continue

        approval_row = approval_by_pid.get(proposal_id, {})
        manifest_row = manifest_by_pid.get(proposal_id, {})
        gate_row = gates_by_pid.get(proposal_id, {})
        packet_row = packets_by_pid.get(proposal_id, {})
        dry_row = dry_by_pid.get(proposal_id, {})
        auth_row = auth_by_pid.get(proposal_id, {})
        intent_row = intents_by_pid.get(proposal_id, {})
        preflight_row = preflight_by_pid.get(proposal_id, {})
        decision_row = decisions_by_pid.get(proposal_id, {})
        policy_row = policy_by_pid.get(proposal_id, {})
        criteria_row = criteria_by_pid.get(proposal_id, {})
        inelig_row = inelig_by_pid.get(proposal_id, {})

        execution_permission = str(policy_row.get("execution_permission") or "denied")
        enablement_state = str(criteria_row.get("enablement_state") or "enablement_not_met")
        ineligibility_state = str(
            inelig_row.get("ineligibility_state") or "ineligible_for_execution"
        )

        policy_id = policy_row.get("policy_id")
        criteria_id = criteria_row.get("criteria_id")
        ineligibility_id = inelig_row.get("ineligibility_id")
        packet_id = packet_row.get("packet_id")

        required_operator_role = str(
            policy_row.get("required_operator_role")
            or criteria_row.get("required_operator_role")
            or inelig_row.get("required_operator_role")
            or auth_row.get("required_operator_role")
            or packet_row.get("operator_role_required")
            or "ops_reviewer"
        )
        rollback_reference = f"rollback-from-{packet_id or proposal_id}"

        proposals_covered.append(proposal_id)

        for action_type in CANONICAL_PROHIBITED_ACTIONS:
            global_seq += 1
            prohibition_state = "prohibited"

            prohibition_state_counts[prohibition_state] = (
                prohibition_state_counts.get(prohibition_state, 0) + 1
            )
            action_type_counts[action_type] = (
                action_type_counts.get(action_type, 0) + 1
            )

            prohibition_reason = derive_prohibition_reason(
                action_type=action_type,
                policy_row=policy_row,
                criteria_row=criteria_row,
                inelig_row=inelig_row,
                execution_permission=execution_permission,
                enablement_state=enablement_state,
                ineligibility_state=ineligibility_state,
            )

            record_source_paths: dict[str, Any] = {
                "controlled_model_adjustment_proposals_json": source_paths[
                    "controlled_model_adjustment_proposals_json"
                ],
                "model_adjustment_approval_ledger_json": source_paths[
                    "model_adjustment_approval_ledger_json"
                ],
                "model_adjustment_validation_manifests_json": source_paths[
                    "model_adjustment_validation_manifests_json"
                ],
                "model_adjustment_application_gates_json": source_paths[
                    "model_adjustment_application_gates_json"
                ],
                "model_adjustment_application_packets_json": source_paths[
                    "model_adjustment_application_packets_json"
                ],
                "model_adjustment_application_dry_runs_json": source_paths[
                    "model_adjustment_application_dry_runs_json"
                ],
                "model_adjustment_application_authorizations_json": source_paths[
                    "model_adjustment_application_authorizations_json"
                ],
                "model_adjustment_execution_intents_json": source_paths[
                    "model_adjustment_execution_intents_json"
                ],
                "model_adjustment_application_preflight_records_json": source_paths[
                    "model_adjustment_application_preflight_records_json"
                ],
                "model_adjustment_readiness_decisions_json": source_paths[
                    "model_adjustment_readiness_decisions_json"
                ],
                "model_adjustment_execution_policy_json": source_paths[
                    "model_adjustment_execution_policy_json"
                ],
                "model_adjustment_execution_enablement_criteria_json": source_paths[
                    "model_adjustment_execution_enablement_criteria_json"
                ],
                "model_adjustment_execution_blocker_registry_json": source_paths[
                    "model_adjustment_execution_blocker_registry_json"
                ],
                "model_adjustment_execution_ineligibility_register_json": source_paths[
                    "model_adjustment_execution_ineligibility_register_json"
                ],
                "approval_ledger_entry_id": approval_row.get("ledger_item_id"),
                "validation_manifest_id": manifest_row.get("manifest_id"),
                "application_gate_id": gate_row.get("gate_id"),
                "application_packet_id": packet_id,
                "application_dry_run_id": dry_row.get("dry_run_id"),
                "application_authorization_id": auth_row.get("authorization_id"),
                "execution_intent_id": intent_row.get("intent_id"),
                "application_preflight_id": preflight_row.get("preflight_id"),
                "readiness_decision_id": decision_row.get("decision_id"),
                "execution_policy_id": policy_id,
                "execution_enablement_criteria_id": criteria_id,
                "execution_ineligibility_id": ineligibility_id,
            }

            matrix_records.append(
                {
                    "prohibition_id": f"prohib-{global_seq:04d}",
                    "proposal_id": proposal_id,
                    "policy_id": policy_id,
                    "criteria_id": criteria_id,
                    "ineligibility_id": ineligibility_id,
                    "prohibited_action_type": action_type,
                    "prohibition_state": prohibition_state,
                    "prohibition_source": PROHIBITION_SOURCE_MAP[action_type],
                    "prohibition_reason": prohibition_reason,
                    "required_release_condition": RELEASE_CONDITION_MAP[action_type],
                    "required_operator_role": required_operator_role,
                    "rollback_reference": rollback_reference,
                    "prohibition_notes": (
                        "governance_prohibition_matrix_assessment_only_no_execution_in_v3_4"
                    ),
                    "source_paths": record_source_paths,
                }
            )

    proposal_ids_in_source = [
        str(x.get("proposal_id") or "")
        for x in proposals
        if isinstance(x, dict) and str(x.get("proposal_id") or "").strip()
    ]

    summary = {
        "total_proposals_in_source": len(proposal_ids_in_source),
        "canonical_prohibited_action_types": len(CANONICAL_PROHIBITED_ACTIONS),
        "total_prohibition_records": len(matrix_records),
        "proposals_covered": len(set(proposals_covered)),
        "all_proposals_covered": set(proposal_ids_in_source) == set(proposals_covered),
        "expected_records": len(proposal_ids_in_source) * len(CANONICAL_PROHIBITED_ACTIONS),
        "record_count_matches_expected": (
            len(matrix_records)
            == len(proposal_ids_in_source) * len(CANONICAL_PROHIBITED_ACTIONS)
        ),
        "prohibition_state_counts": prohibition_state_counts,
        "action_type_counts": action_type_counts,
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_execution_prohibition_matrix_version": "v3.4-slice-1",
        "source_versions": {
            "controlled_model_adjustment_proposals_version": proposals_payload.get(
                "controlled_model_adjustment_proposals_version"
            ),
            "model_adjustment_approval_ledger_version": approval_payload.get(
                "model_adjustment_approval_ledger_version"
            ),
            "model_adjustment_validation_manifests_version": manifests_payload.get(
                "model_adjustment_validation_manifests_version"
            ),
            "model_adjustment_application_gates_version": gates_payload.get(
                "model_adjustment_application_gates_version"
            ),
            "model_adjustment_application_packets_version": packets_payload.get(
                "model_adjustment_application_packets_version"
            ),
            "model_adjustment_application_dry_runs_version": dry_runs_payload.get(
                "model_adjustment_application_dry_runs_version"
            ),
            "model_adjustment_application_authorizations_version": auth_payload.get(
                "model_adjustment_application_authorizations_version"
            ),
            "model_adjustment_execution_intents_version": intents_payload.get(
                "model_adjustment_execution_intents_version"
            ),
            "model_adjustment_application_preflight_records_version": preflight_payload.get(
                "model_adjustment_application_preflight_records_version"
            ),
            "model_adjustment_readiness_decisions_version": decisions_payload.get(
                "model_adjustment_readiness_decisions_version"
            ),
            "model_adjustment_execution_policy_version": policy_payload.get(
                "model_adjustment_execution_policy_version"
            ),
            "model_adjustment_execution_enablement_criteria_version": criteria_payload.get(
                "model_adjustment_execution_enablement_criteria_version"
            ),
            "model_adjustment_execution_blocker_registry_version": blocker_payload.get(
                "model_adjustment_execution_blocker_registry_version"
            ),
            "model_adjustment_execution_ineligibility_register_version": inelig_payload.get(
                "model_adjustment_execution_ineligibility_register_version"
            ),
        },
        "execution_prohibition_summary": summary,
        "execution_prohibition_matrix": matrix_records,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = (
        payload.get("execution_prohibition_summary")
        if isinstance(payload.get("execution_prohibition_summary"), dict)
        else {}
    )
    source_versions = (
        payload.get("source_versions")
        if isinstance(payload.get("source_versions"), dict)
        else {}
    )
    rows = (
        payload.get("execution_prohibition_matrix")
        if isinstance(payload.get("execution_prohibition_matrix"), list)
        else []
    )

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Execution Prohibition Matrix (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(
        f"Matrix Version: {payload.get('model_adjustment_execution_prohibition_matrix_version')}"
    )
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Prohibition Matrix Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(
        f"- Canonical Prohibited Action Types: {summary.get('canonical_prohibited_action_types')}"
    )
    lines.append(f"- Total Prohibition Records: {summary.get('total_prohibition_records')}")
    lines.append(f"- Proposals Covered: {summary.get('proposals_covered')}")
    lines.append(f"- All Proposals Covered: {summary.get('all_proposals_covered')}")
    lines.append(
        f"- Expected Records (proposals x actions): {summary.get('expected_records')}"
    )
    lines.append(
        f"- Record Count Matches Expected: {summary.get('record_count_matches_expected')}"
    )
    lines.append(f"- Prohibition State Counts: {summary.get('prohibition_state_counts')}")
    lines.append(f"- Action Type Counts: {summary.get('action_type_counts')}")
    lines.append("")
    lines.append("## Execution Prohibition Matrix Records")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- {row.get('prohibition_id')}: {row.get('proposal_id')} | "
                f"policy={row.get('policy_id')} | criteria={row.get('criteria_id')} | "
                f"ineligibility={row.get('ineligibility_id')}"
            )
            lines.append(
                f"  Action Type: {row.get('prohibited_action_type')} | "
                f"State: {row.get('prohibition_state')} | "
                f"Source: {row.get('prohibition_source')}"
            )
            lines.append(f"  Prohibition Reason: {row.get('prohibition_reason')}")
            lines.append(
                f"  Required Release Condition: {row.get('required_release_condition')}"
            )
            lines.append(f"  Required Operator Role: {row.get('required_operator_role')}")
            lines.append(f"  Rollback Reference: {row.get('rollback_reference')}")
            lines.append(f"  Prohibition Notes: {row.get('prohibition_notes')}")
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
    policy_path = Path(args.execution_policy_json)
    criteria_path = Path(args.execution_enablement_criteria_json)
    blocker_path = Path(args.execution_blocker_registry_json)
    inelig_path = Path(args.execution_ineligibility_register_json)
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
    policy_payload, policy_err = safe_read_json(repo_root / policy_path)
    criteria_payload, criteria_err = safe_read_json(repo_root / criteria_path)
    blocker_payload, blocker_err = safe_read_json(repo_root / blocker_path)
    inelig_payload, inelig_err = safe_read_json(repo_root / inelig_path)

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
        ("model-adjustment execution policy", policy_err),
        ("model-adjustment execution enablement criteria", criteria_err),
        ("model-adjustment execution blocker registry", blocker_err),
        ("model-adjustment execution ineligibility register", inelig_err),
    ]
    for label, err in errors:
        if err is not None:
            print(f"ERROR: {label} unavailable: {err}", file=sys.stderr)
            return 1

    payloads = [
        proposals_payload, approval_payload, manifests_payload, gates_payload,
        packets_payload, dry_runs_payload, auth_payload, intents_payload,
        preflight_payload, decisions_payload, policy_payload, criteria_payload,
        blocker_payload, inelig_payload,
    ]
    if not all(isinstance(x, dict) for x in payloads):
        print(
            "ERROR: one or more source artifacts are not valid JSON objects", file=sys.stderr
        )
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
        "model_adjustment_execution_policy_json": normalize_path(policy_path),
        "model_adjustment_execution_enablement_criteria_json": normalize_path(criteria_path),
        "model_adjustment_execution_blocker_registry_json": normalize_path(blocker_path),
        "model_adjustment_execution_ineligibility_register_json": normalize_path(inelig_path),
    }

    payload = build_prohibition_matrix(
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
        policy_payload=policy_payload,
        criteria_payload=criteria_payload,
        blocker_payload=blocker_payload,
        inelig_payload=inelig_payload,
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
            ("model_adjustment_execution_policy_json", policy_err),
            ("model_adjustment_execution_enablement_criteria_json", criteria_err),
            ("model_adjustment_execution_blocker_registry_json", blocker_err),
            ("model_adjustment_execution_ineligibility_register_json", inelig_err),
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
    s = payload.get("execution_prohibition_summary") or {}
    print(
        "[STATUS] prohibitions={total} proposals_covered={covered} all_covered={all_covered} "
        "count_matches_expected={match} prohibition_state={state}".format(
            total=s.get("total_prohibition_records"),
            covered=s.get("proposals_covered"),
            all_covered=s.get("all_proposals_covered"),
            match=s.get("record_count_matches_expected"),
            state=s.get("prohibition_state_counts"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
