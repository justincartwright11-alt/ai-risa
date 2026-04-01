#!/usr/bin/env python3
"""
AI-RISA v3.8 Controlled Execution Release Decisions (slice 1): read-only governance layer.

Builds a canonical release-decision register that emits the final governance verdict for
release readiness per proposal and release-gate lineage. This script is governance-only and
does not execute adjustments, auto-promote state, write configs, or mutate model behavior.
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
OUTPUT_JSON = "model_adjustment_execution_release_decisions.json"
OUTPUT_MD = "model_adjustment_execution_release_decisions.md"

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
EXECUTION_PROHIBITION_MATRIX_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_prohibition_matrix.json"
)
EXECUTION_RELEASE_CONDITIONS_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_release_conditions.json"
)
EXECUTION_RELEASE_AUTHORITY_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_release_authority.json"
)
EXECUTION_RELEASE_GATE_ASSESSMENTS_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_release_gate_assessments.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled execution release decision artifacts"
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
    parser.add_argument(
        "--execution-prohibition-matrix-json",
        default=str(EXECUTION_PROHIBITION_MATRIX_DEFAULT),
    )
    parser.add_argument(
        "--execution-release-conditions-json",
        default=str(EXECUTION_RELEASE_CONDITIONS_DEFAULT),
    )
    parser.add_argument(
        "--execution-release-authority-json",
        default=str(EXECUTION_RELEASE_AUTHORITY_DEFAULT),
    )
    parser.add_argument(
        "--execution-release-gate-assessments-json",
        default=str(EXECUTION_RELEASE_GATE_ASSESSMENTS_DEFAULT),
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


def group_by_proposal_id(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = str(row.get("proposal_id") or "").strip()
        if not pid:
            continue
        grouped.setdefault(pid, []).append(row)
    return grouped


def derive_release_decision(
    gate_state: str,
    gate_status: str,
    authority_availability: str,
    ineligibility_state: str,
) -> tuple[str, str]:
    if gate_state == "structurally_unavailable" or authority_availability in {
        "absent",
        "expired",
        "structurally_unavailable",
    }:
        return (
            "structurally_unreleasable",
            "release_gate_structurally_unavailable_due_to_authority_or_governance_constraints",
        )
    if ineligibility_state != "eligible_for_execution":
        return (
            "release_not_eligible",
            "proposal_remains_ineligible_for_execution_under_current_governance_layers",
        )
    if gate_state in {"blocked", "closed"}:
        return (
            "release_denied",
            f"release_gate_status_{gate_status}_prevents_release_decision_approval",
        )
    return (
        "release_denied",
        "governance_only_release_decisions_do_not_authorize_execution_in_v3_8",
    )


def build_release_decisions(
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
    prohibition_payload: dict[str, Any],
    release_conditions_payload: dict[str, Any],
    release_authority_payload: dict[str, Any],
    release_gate_payload: dict[str, Any],
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
    readiness_rows = (
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
    blocker_rows = (
        blocker_payload.get("execution_blocker_registry")
        if isinstance(blocker_payload.get("execution_blocker_registry"), list)
        else []
    )
    inelig_rows = (
        inelig_payload.get("execution_ineligibility_register")
        if isinstance(inelig_payload.get("execution_ineligibility_register"), list)
        else []
    )
    prohibition_rows = (
        prohibition_payload.get("execution_prohibition_matrix")
        if isinstance(prohibition_payload.get("execution_prohibition_matrix"), list)
        else []
    )
    release_condition_rows = (
        release_conditions_payload.get("execution_release_conditions")
        if isinstance(release_conditions_payload.get("execution_release_conditions"), list)
        else []
    )
    release_authority_rows = (
        release_authority_payload.get("execution_release_authority")
        if isinstance(release_authority_payload.get("execution_release_authority"), list)
        else []
    )
    release_gate_rows = (
        release_gate_payload.get("execution_release_gate_assessments")
        if isinstance(release_gate_payload.get("execution_release_gate_assessments"), list)
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
    readiness_by_pid = index_by_proposal_id(readiness_rows)
    policy_by_pid = index_by_proposal_id(policy_rows)
    criteria_by_pid = index_by_proposal_id(criteria_rows)
    inelig_by_pid = index_by_proposal_id(inelig_rows)
    blockers_by_pid = group_by_proposal_id(blocker_rows)

    prohibition_by_id = {
        str(r.get("prohibition_id") or ""): r
        for r in prohibition_rows
        if isinstance(r, dict)
    }
    release_conditions_by_id = {
        str(r.get("release_condition_id") or ""): r
        for r in release_condition_rows
        if isinstance(r, dict)
    }
    release_authority_by_id = {
        str(r.get("release_authority_id") or ""): r
        for r in release_authority_rows
        if isinstance(r, dict)
    }

    records: list[dict[str, Any]] = []
    release_decision_state_counts: dict[str, int] = {}
    proposals_covered: list[str] = []

    seq = 0
    for gate_row in release_gate_rows:
        if not isinstance(gate_row, dict):
            continue

        proposal_id = str(gate_row.get("proposal_id") or "").strip()
        if not proposal_id:
            continue

        seq += 1
        proposals_covered.append(proposal_id)

        policy_id = gate_row.get("policy_id")
        criteria_id = gate_row.get("criteria_id")
        ineligibility_id = gate_row.get("ineligibility_id")
        prohibition_id = gate_row.get("prohibition_id")
        release_condition_id = gate_row.get("release_condition_id")
        release_authority_id = gate_row.get("release_authority_id")
        release_gate_id = gate_row.get("release_gate_id")

        inelig_row = inelig_by_pid.get(proposal_id, {})
        release_condition_row = release_conditions_by_id.get(str(release_condition_id or ""), {})
        release_authority_row = release_authority_by_id.get(str(release_authority_id or ""), {})
        prohibition_row = prohibition_by_id.get(str(prohibition_id or ""), {})

        gate_state = str(gate_row.get("release_gate_state") or "structurally_unavailable")
        gate_status = str(gate_row.get("gate_assessment_status") or "gate_blocked")
        authority_availability = str(
            release_authority_row.get("authority_availability") or "structurally_unavailable"
        )
        ineligibility_state = str(
            inelig_row.get("ineligibility_state") or "ineligible_for_execution"
        )

        release_decision_state, release_decision_reason = derive_release_decision(
            gate_state=gate_state,
            gate_status=gate_status,
            authority_availability=authority_availability,
            ineligibility_state=ineligibility_state,
        )

        required_remaining_actions = list(gate_row.get("unmet_gate_requirements") or [])
        if authority_availability != "available":
            required_remaining_actions.append(
                f"release_authority_availability_must_be_resolved:{authority_availability}"
            )
        required_remaining_actions.append(
            f"release_gate_state_must_not_be_{gate_state}"
        )

        required_release_evidence = list(gate_row.get("required_gate_evidence") or [])
        required_release_authority = str(
            gate_row.get("required_release_authority")
            or release_authority_row.get("required_release_authority")
            or release_condition_row.get("required_release_authority")
            or "governance_release_board"
        )
        required_operator_role = str(
            gate_row.get("required_operator_role")
            or release_authority_row.get("required_operator_role")
            or release_condition_row.get("required_operator_role")
            or "ops_reviewer"
        )

        release_decision_blockers = set(str(x) for x in (gate_row.get("gate_blockers") or []))
        release_decision_blockers.update(
            str(x)
            for x in (release_condition_row.get("release_blockers") or [])
            if str(x).strip()
        )
        release_decision_blockers.update(
            str(x)
            for x in (release_authority_row.get("authority_blockers") or [])
            if str(x).strip()
        )
        release_decision_blockers.add(f"release_decision_state:{release_decision_state}")

        release_decision_state_counts[release_decision_state] = (
            release_decision_state_counts.get(release_decision_state, 0) + 1
        )

        approval_row = approval_by_pid.get(proposal_id, {})
        manifest_row = manifest_by_pid.get(proposal_id, {})
        app_gate_row = gates_by_pid.get(proposal_id, {})
        packet_row = packets_by_pid.get(proposal_id, {})
        dry_row = dry_by_pid.get(proposal_id, {})
        auth_row = auth_by_pid.get(proposal_id, {})
        intent_row = intents_by_pid.get(proposal_id, {})
        preflight_row = preflight_by_pid.get(proposal_id, {})
        readiness_row = readiness_by_pid.get(proposal_id, {})
        policy_row = policy_by_pid.get(proposal_id, {})
        criteria_row = criteria_by_pid.get(proposal_id, {})
        blockers_rows = blockers_by_pid.get(proposal_id, [])

        packet_id = packet_row.get("packet_id")
        rollback_reference = f"rollback-from-{packet_id or proposal_id}"

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
            "model_adjustment_execution_prohibition_matrix_json": source_paths[
                "model_adjustment_execution_prohibition_matrix_json"
            ],
            "model_adjustment_execution_release_conditions_json": source_paths[
                "model_adjustment_execution_release_conditions_json"
            ],
            "model_adjustment_execution_release_authority_json": source_paths[
                "model_adjustment_execution_release_authority_json"
            ],
            "model_adjustment_execution_release_gate_assessments_json": source_paths[
                "model_adjustment_execution_release_gate_assessments_json"
            ],
            "approval_ledger_entry_id": approval_row.get("ledger_item_id"),
            "validation_manifest_id": manifest_row.get("manifest_id"),
            "application_gate_id": app_gate_row.get("gate_id"),
            "application_packet_id": packet_id,
            "application_dry_run_id": dry_row.get("dry_run_id"),
            "application_authorization_id": auth_row.get("authorization_id"),
            "execution_intent_id": intent_row.get("intent_id"),
            "application_preflight_id": preflight_row.get("preflight_id"),
            "readiness_decision_id": readiness_row.get("decision_id"),
            "execution_policy_id": policy_row.get("policy_id"),
            "execution_enablement_criteria_id": criteria_row.get("criteria_id"),
            "execution_blocker_ids": [
                str(x.get("blocker_id") or "")
                for x in blockers_rows
                if isinstance(x, dict) and str(x.get("blocker_id") or "").strip()
            ],
            "prohibited_action_type": prohibition_row.get("prohibited_action_type"),
        }

        records.append(
            {
                "release_decision_id": f"decision-{seq:04d}",
                "proposal_id": proposal_id,
                "policy_id": policy_id,
                "criteria_id": criteria_id,
                "ineligibility_id": ineligibility_id,
                "prohibition_id": prohibition_id,
                "release_condition_id": release_condition_id,
                "release_authority_id": release_authority_id,
                "release_gate_id": release_gate_id,
                "release_decision_state": release_decision_state,
                "release_decision_reason": release_decision_reason,
                "required_remaining_actions": sorted(set(required_remaining_actions)),
                "required_release_evidence": sorted(set(str(x) for x in required_release_evidence)),
                "required_release_authority": required_release_authority,
                "required_operator_role": required_operator_role,
                "release_decision_blockers": sorted(set(release_decision_blockers)),
                "rollback_reference": rollback_reference,
                "release_decision_notes": (
                    "governance_release_decision_assessment_only_no_execution_in_v3_8"
                ),
                "source_paths": record_source_paths,
            }
        )

    proposal_ids_in_source = [
        str(x.get("proposal_id") or "")
        for x in proposals
        if isinstance(x, dict) and str(x.get("proposal_id") or "").strip()
    ]

    expected_records = len(release_gate_rows) if release_gate_rows else len(proposal_ids_in_source)

    summary = {
        "total_proposals_in_source": len(proposal_ids_in_source),
        "total_release_decision_records": len(records),
        "proposals_covered": len(set(proposals_covered)),
        "all_proposals_covered": set(proposal_ids_in_source) == set(proposals_covered),
        "expected_records": expected_records,
        "record_count_matches_expected": len(records) == expected_records,
        "release_decision_state_counts": release_decision_state_counts,
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_execution_release_decisions_version": "v3.8-slice-1",
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
            "model_adjustment_execution_prohibition_matrix_version": prohibition_payload.get(
                "model_adjustment_execution_prohibition_matrix_version"
            ),
            "model_adjustment_execution_release_conditions_version": release_conditions_payload.get(
                "model_adjustment_execution_release_conditions_version"
            ),
            "model_adjustment_execution_release_authority_version": release_authority_payload.get(
                "model_adjustment_execution_release_authority_version"
            ),
            "model_adjustment_execution_release_gate_assessments_version": release_gate_payload.get(
                "model_adjustment_execution_release_gate_assessments_version"
            ),
        },
        "execution_release_decisions_summary": summary,
        "execution_release_decisions": records,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("execution_release_decisions_summary") or {}
    source_versions = payload.get("source_versions") or {}
    rows = payload.get("execution_release_decisions") or []

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Execution Release Decisions (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(
        "Release Decisions Version: "
        f"{payload.get('model_adjustment_execution_release_decisions_version')}"
    )
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Release Decisions Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Total Release Decision Records: {summary.get('total_release_decision_records')}")
    lines.append(f"- Proposals Covered: {summary.get('proposals_covered')}")
    lines.append(f"- All Proposals Covered: {summary.get('all_proposals_covered')}")
    lines.append(f"- Expected Records: {summary.get('expected_records')}")
    lines.append(f"- Record Count Matches Expected: {summary.get('record_count_matches_expected')}")
    lines.append(f"- Release Decision State Counts: {summary.get('release_decision_state_counts')}")
    lines.append("")
    lines.append("## Execution Release Decision Records")

    if rows:
        for row in rows:
            lines.append(
                f"- {row.get('release_decision_id')}: {row.get('proposal_id')} | "
                f"policy={row.get('policy_id')} | criteria={row.get('criteria_id')} | "
                f"ineligibility={row.get('ineligibility_id')} | prohibition={row.get('prohibition_id')} | "
                f"release_condition={row.get('release_condition_id')} | "
                f"release_authority={row.get('release_authority_id')} | "
                f"release_gate={row.get('release_gate_id')}"
            )
            lines.append(
                f"  State: {row.get('release_decision_state')} | "
                f"Reason: {row.get('release_decision_reason')}"
            )
            lines.append(f"  Required Remaining Actions: {row.get('required_remaining_actions')}")
            lines.append(f"  Required Release Evidence: {row.get('required_release_evidence')}")
            lines.append(f"  Required Release Authority: {row.get('required_release_authority')}")
            lines.append(f"  Required Operator Role: {row.get('required_operator_role')}")
            lines.append(f"  Release Decision Blockers: {row.get('release_decision_blockers')}")
            lines.append(f"  Rollback Reference: {row.get('rollback_reference')}")
            lines.append(f"  Release Decision Notes: {row.get('release_decision_notes')}")
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
    prohibition_path = Path(args.execution_prohibition_matrix_json)
    release_conditions_path = Path(args.execution_release_conditions_json)
    release_authority_path = Path(args.execution_release_authority_json)
    release_gate_path = Path(args.execution_release_gate_assessments_json)
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
    prohibition_payload, prohibition_err = safe_read_json(repo_root / prohibition_path)
    release_conditions_payload, release_conditions_err = safe_read_json(repo_root / release_conditions_path)
    release_authority_payload, release_authority_err = safe_read_json(repo_root / release_authority_path)
    release_gate_payload, release_gate_err = safe_read_json(repo_root / release_gate_path)

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
        ("model-adjustment execution prohibition matrix", prohibition_err),
        ("model-adjustment execution release conditions", release_conditions_err),
        ("model-adjustment execution release authority", release_authority_err),
        ("model-adjustment execution release gate assessments", release_gate_err),
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
        policy_payload,
        criteria_payload,
        blocker_payload,
        inelig_payload,
        prohibition_payload,
        release_conditions_payload,
        release_authority_payload,
        release_gate_payload,
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
        "model_adjustment_execution_policy_json": normalize_path(policy_path),
        "model_adjustment_execution_enablement_criteria_json": normalize_path(criteria_path),
        "model_adjustment_execution_blocker_registry_json": normalize_path(blocker_path),
        "model_adjustment_execution_ineligibility_register_json": normalize_path(inelig_path),
        "model_adjustment_execution_prohibition_matrix_json": normalize_path(prohibition_path),
        "model_adjustment_execution_release_conditions_json": normalize_path(release_conditions_path),
        "model_adjustment_execution_release_authority_json": normalize_path(release_authority_path),
        "model_adjustment_execution_release_gate_assessments_json": normalize_path(release_gate_path),
    }

    payload = build_release_decisions(
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
        prohibition_payload=prohibition_payload,
        release_conditions_payload=release_conditions_payload,
        release_authority_payload=release_authority_payload,
        release_gate_payload=release_gate_payload,
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
            ("model_adjustment_execution_prohibition_matrix_json", prohibition_err),
            ("model_adjustment_execution_release_conditions_json", release_conditions_err),
            ("model_adjustment_execution_release_authority_json", release_authority_err),
            ("model_adjustment_execution_release_gate_assessments_json", release_gate_err),
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
    s = payload.get("execution_release_decisions_summary") or {}
    print(
        "[STATUS] release_decisions={total} proposals_covered={covered} all_covered={all_covered} "
        "record_count_matches_expected={match} release_decision_state={state}".format(
            total=s.get("total_release_decision_records"),
            covered=s.get("proposals_covered"),
            all_covered=s.get("all_proposals_covered"),
            match=s.get("record_count_matches_expected"),
            state=s.get("release_decision_state_counts"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
