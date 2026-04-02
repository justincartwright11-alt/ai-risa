#!/usr/bin/env python3
"""
AI-RISA v4.0 Controlled Release Prohibition Matrix (slice 1): read-only governance layer.

Builds a canonical per-proposal release prohibition matrix that normalizes which release
action types remain prohibited, which governance layers enforce the prohibition, and which
unresolved conditions keep release blocked.

This script is governance-only and does not execute adjustments, auto-promote state,
write configs, mutate model behavior, or mutate upstream governance artifacts.
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
OUTPUT_JSON = "model_adjustment_release_prohibition_matrix.json"
OUTPUT_MD = "model_adjustment_release_prohibition_matrix.md"

EXECUTION_RELEASE_CONDITIONS_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_release_conditions.json"
)
EXECUTION_RELEASE_AUTHORITY_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_release_authority.json"
)
EXECUTION_RELEASE_GATE_ASSESSMENTS_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_release_gate_assessments.json"
)
EXECUTION_RELEASE_DECISIONS_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_release_decisions.json"
)
RELEASE_INELIGIBILITY_DECISIONS_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_release_ineligibility_decisions.json"
)
EXECUTION_PROHIBITION_MATRIX_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_prohibition_matrix.json"
)
EXECUTION_BLOCKER_REGISTRY_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_blocker_registry.json"
)
EXECUTION_INELIGIBILITY_REGISTER_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_ineligibility_register.json"
)
EXECUTION_POLICY_DEFAULT = Path("ops/model_adjustments/model_adjustment_execution_policy.json")
EXECUTION_ENABLEMENT_CRITERIA_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_execution_enablement_criteria.json"
)
READINESS_DECISIONS_DEFAULT = Path("ops/model_adjustments/model_adjustment_readiness_decisions.json")
PREFLIGHT_RECORDS_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_application_preflight_records.json"
)
EXECUTION_INTENTS_DEFAULT = Path("ops/model_adjustments/model_adjustment_execution_intents.json")
APPLICATION_AUTH_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_application_authorizations.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled release prohibition matrix artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
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
    parser.add_argument(
        "--execution-release-decisions-json",
        default=str(EXECUTION_RELEASE_DECISIONS_DEFAULT),
    )
    parser.add_argument(
        "--release-ineligibility-decisions-json",
        default=str(RELEASE_INELIGIBILITY_DECISIONS_DEFAULT),
    )
    parser.add_argument(
        "--execution-prohibition-matrix-json",
        default=str(EXECUTION_PROHIBITION_MATRIX_DEFAULT),
    )
    parser.add_argument(
        "--execution-blocker-registry-json",
        default=str(EXECUTION_BLOCKER_REGISTRY_DEFAULT),
    )
    parser.add_argument(
        "--execution-ineligibility-register-json",
        default=str(EXECUTION_INELIGIBILITY_REGISTER_DEFAULT),
    )
    parser.add_argument("--execution-policy-json", default=str(EXECUTION_POLICY_DEFAULT))
    parser.add_argument(
        "--execution-enablement-criteria-json",
        default=str(EXECUTION_ENABLEMENT_CRITERIA_DEFAULT),
    )
    parser.add_argument("--readiness-decisions-json", default=str(READINESS_DECISIONS_DEFAULT))
    parser.add_argument(
        "--application-preflight-records-json", default=str(PREFLIGHT_RECORDS_DEFAULT)
    )
    parser.add_argument("--execution-intents-json", default=str(EXECUTION_INTENTS_DEFAULT))
    parser.add_argument(
        "--application-authorizations-json", default=str(APPLICATION_AUTH_DEFAULT)
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
        if pid:
            grouped.setdefault(pid, []).append(row)
    return grouped


def compact_join(values: list[Any], sep: str = "|") -> str:
    normalized = sorted({str(v).strip() for v in values if str(v).strip()})
    return sep.join(normalized)


def derive_reason(
    authority_availability: str,
    release_gate_state: str,
    release_decision_state: str,
    release_ineligibility_state: str,
    release_ineligibility_class: str,
    execution_permission: str,
) -> str:
    if authority_availability in {"absent", "expired", "structurally_unavailable"}:
        return "release_authority_unavailable"
    if release_gate_state in {"blocked", "closed", "structurally_unavailable"}:
        return f"release_gate_state_{release_gate_state}"
    if release_decision_state in {"structurally_unreleasable", "release_denied", "release_not_eligible"}:
        return f"release_decision_state_{release_decision_state}"
    if release_ineligibility_state == "release_ineligible":
        return f"release_ineligibility_class_{release_ineligibility_class or 'unspecified'}"
    if execution_permission != "allowed":
        return "execution_policy_denied"
    return "v4_0_governance_mode_release_actions_remain_prohibited"


def build_release_prohibition_matrix(
    release_conditions_payload: dict[str, Any],
    release_authority_payload: dict[str, Any],
    release_gate_payload: dict[str, Any],
    release_decisions_payload: dict[str, Any],
    release_ineligibility_payload: dict[str, Any],
    execution_prohibition_payload: dict[str, Any],
    blocker_registry_payload: dict[str, Any],
    ineligibility_register_payload: dict[str, Any],
    execution_policy_payload: dict[str, Any],
    enablement_payload: dict[str, Any],
    readiness_payload: dict[str, Any],
    preflight_payload: dict[str, Any],
    intents_payload: dict[str, Any],
    auth_payload: dict[str, Any],
    source_paths: dict[str, str],
) -> dict[str, Any]:
    release_conditions_rows = (
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
    release_decision_rows = (
        release_decisions_payload.get("execution_release_decisions")
        if isinstance(release_decisions_payload.get("execution_release_decisions"), list)
        else []
    )
    release_ineligibility_rows = (
        release_ineligibility_payload.get("release_ineligibility_decisions")
        if isinstance(release_ineligibility_payload.get("release_ineligibility_decisions"), list)
        else []
    )
    execution_prohibition_rows = (
        execution_prohibition_payload.get("execution_prohibition_matrix")
        if isinstance(execution_prohibition_payload.get("execution_prohibition_matrix"), list)
        else []
    )
    blocker_registry_rows = (
        blocker_registry_payload.get("execution_blocker_registry")
        if isinstance(blocker_registry_payload.get("execution_blocker_registry"), list)
        else []
    )
    ineligibility_rows = (
        ineligibility_register_payload.get("execution_ineligibility_register")
        if isinstance(ineligibility_register_payload.get("execution_ineligibility_register"), list)
        else []
    )
    execution_policy_rows = (
        execution_policy_payload.get("execution_policy_records")
        if isinstance(execution_policy_payload.get("execution_policy_records"), list)
        else []
    )
    enablement_rows = (
        enablement_payload.get("execution_enablement_criteria")
        if isinstance(enablement_payload.get("execution_enablement_criteria"), list)
        else []
    )
    readiness_rows = (
        readiness_payload.get("readiness_decisions")
        if isinstance(readiness_payload.get("readiness_decisions"), list)
        else []
    )
    preflight_rows = (
        preflight_payload.get("application_preflight_records")
        if isinstance(preflight_payload.get("application_preflight_records"), list)
        else []
    )
    intents_rows = (
        intents_payload.get("execution_intents")
        if isinstance(intents_payload.get("execution_intents"), list)
        else []
    )
    auth_rows = (
        auth_payload.get("application_authorizations")
        if isinstance(auth_payload.get("application_authorizations"), list)
        else []
    )

    release_conditions_by_pid = index_by_proposal_id(release_conditions_rows)
    release_authority_by_pid = index_by_proposal_id(release_authority_rows)
    release_gate_by_pid = index_by_proposal_id(release_gate_rows)
    release_decision_by_pid = index_by_proposal_id(release_decision_rows)
    release_ineligibility_by_pid = index_by_proposal_id(release_ineligibility_rows)
    execution_prohibition_by_pid = group_by_proposal_id(execution_prohibition_rows)
    blocker_registry_by_pid = group_by_proposal_id(blocker_registry_rows)
    ineligibility_by_pid = index_by_proposal_id(ineligibility_rows)
    execution_policy_by_pid = index_by_proposal_id(execution_policy_rows)
    enablement_by_pid = index_by_proposal_id(enablement_rows)
    readiness_by_pid = index_by_proposal_id(readiness_rows)
    preflight_by_pid = index_by_proposal_id(preflight_rows)
    intents_by_pid = index_by_proposal_id(intents_rows)
    auth_by_pid = index_by_proposal_id(auth_rows)

    proposal_ids = sorted(
        {
            str(r.get("proposal_id") or "").strip()
            for r in release_ineligibility_rows
            if isinstance(r, dict) and str(r.get("proposal_id") or "").strip()
        }
    )

    records: list[dict[str, Any]] = []
    state_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}

    for seq, proposal_id in enumerate(proposal_ids, start=1):
        release_condition_row = release_conditions_by_pid.get(proposal_id, {})
        release_authority_row = release_authority_by_pid.get(proposal_id, {})
        release_gate_row = release_gate_by_pid.get(proposal_id, {})
        release_decision_row = release_decision_by_pid.get(proposal_id, {})
        release_ineligibility_row = release_ineligibility_by_pid.get(proposal_id, {})
        execution_prohibitions = execution_prohibition_by_pid.get(proposal_id, [])
        blocker_rows = blocker_registry_by_pid.get(proposal_id, [])
        ineligibility_row = ineligibility_by_pid.get(proposal_id, {})
        policy_row = execution_policy_by_pid.get(proposal_id, {})
        criteria_row = enablement_by_pid.get(proposal_id, {})
        readiness_row = readiness_by_pid.get(proposal_id, {})
        preflight_row = preflight_by_pid.get(proposal_id, {})
        intent_row = intents_by_pid.get(proposal_id, {})
        auth_row = auth_by_pid.get(proposal_id, {})

        prohibition_ids = [r.get("prohibition_id") for r in execution_prohibitions if isinstance(r, dict)]
        prohibited_action_types = [
            r.get("prohibited_action_type") for r in execution_prohibitions if isinstance(r, dict)
        ]
        prohibited_action_types.extend(list(policy_row.get("prohibited_actions") or []))
        prohibited_release_action_type = compact_join(prohibited_action_types) or "release_publish"

        source_layers = [
            r.get("prohibition_source") for r in execution_prohibitions if isinstance(r, dict)
        ]
        source_layers.extend([
            f"release_gate:{release_gate_row.get('release_gate_state')}",
            f"release_decision:{release_decision_row.get('release_decision_state')}",
            f"release_ineligibility:{release_ineligibility_row.get('release_ineligibility_class')}",
        ])
        release_prohibition_source = compact_join(source_layers)

        release_prohibition_state = "prohibited"
        release_prohibition_reason = derive_reason(
            authority_availability=str(
                release_authority_row.get("authority_availability") or "structurally_unavailable"
            ),
            release_gate_state=str(release_gate_row.get("release_gate_state") or "blocked"),
            release_decision_state=str(
                release_decision_row.get("release_decision_state") or "release_denied"
            ),
            release_ineligibility_state=str(
                release_ineligibility_row.get("release_ineligibility_state") or "release_ineligible"
            ),
            release_ineligibility_class=str(
                release_ineligibility_row.get("release_ineligibility_class") or "release_ineligible"
            ),
            execution_permission=str(policy_row.get("execution_permission") or "denied"),
        )

        required_release_conditions = list(release_condition_row.get("required_release_conditions") or [])
        required_release_conditions.extend(
            [r.get("required_release_condition") for r in execution_prohibitions if isinstance(r, dict)]
        )
        required_release_condition = compact_join(required_release_conditions)

        required_release_authority = str(
            release_authority_row.get("required_release_authority")
            or release_decision_row.get("required_release_authority")
            or release_ineligibility_row.get("required_release_authority")
            or release_condition_row.get("required_release_authority")
            or "governance_release_board"
        )

        required_operator_role = str(
            release_ineligibility_row.get("required_operator_role")
            or release_decision_row.get("required_operator_role")
            or release_gate_row.get("required_operator_role")
            or release_authority_row.get("required_operator_role")
            or release_condition_row.get("required_operator_role")
            or ineligibility_row.get("required_operator_role")
            or policy_row.get("required_operator_role")
            or criteria_row.get("required_operator_role")
            or readiness_row.get("required_operator_role")
            or preflight_row.get("required_operator_role")
            or intent_row.get("required_operator_role")
            or auth_row.get("required_operator_role")
            or "ops_reviewer"
        )

        rollback_reference = str(
            release_ineligibility_row.get("rollback_reference")
            or release_decision_row.get("rollback_reference")
            or release_gate_row.get("rollback_reference")
            or release_authority_row.get("rollback_reference")
            or release_condition_row.get("rollback_reference")
            or ineligibility_row.get("rollback_reference")
            or policy_row.get("rollback_reference")
            or preflight_row.get("rollback_reference")
            or intent_row.get("rollback_reference")
            or f"rollback-from-{proposal_id}"
        )

        blocker_ids = [
            str(r.get("blocker_id") or "")
            for r in blocker_rows
            if isinstance(r, dict) and str(r.get("blocker_id") or "").strip()
        ]

        record_source_paths: dict[str, Any] = {
            "model_adjustment_execution_release_conditions_json": source_paths[
                "model_adjustment_execution_release_conditions_json"
            ],
            "model_adjustment_execution_release_authority_json": source_paths[
                "model_adjustment_execution_release_authority_json"
            ],
            "model_adjustment_execution_release_gate_assessments_json": source_paths[
                "model_adjustment_execution_release_gate_assessments_json"
            ],
            "model_adjustment_execution_release_decisions_json": source_paths[
                "model_adjustment_execution_release_decisions_json"
            ],
            "model_adjustment_release_ineligibility_decisions_json": source_paths[
                "model_adjustment_release_ineligibility_decisions_json"
            ],
            "model_adjustment_execution_prohibition_matrix_json": source_paths[
                "model_adjustment_execution_prohibition_matrix_json"
            ],
            "model_adjustment_execution_blocker_registry_json": source_paths[
                "model_adjustment_execution_blocker_registry_json"
            ],
            "model_adjustment_execution_ineligibility_register_json": source_paths[
                "model_adjustment_execution_ineligibility_register_json"
            ],
            "model_adjustment_execution_policy_json": source_paths[
                "model_adjustment_execution_policy_json"
            ],
            "model_adjustment_execution_enablement_criteria_json": source_paths[
                "model_adjustment_execution_enablement_criteria_json"
            ],
            "model_adjustment_readiness_decisions_json": source_paths[
                "model_adjustment_readiness_decisions_json"
            ],
            "model_adjustment_application_preflight_records_json": source_paths[
                "model_adjustment_application_preflight_records_json"
            ],
            "model_adjustment_execution_intents_json": source_paths[
                "model_adjustment_execution_intents_json"
            ],
            "model_adjustment_application_authorizations_json": source_paths[
                "model_adjustment_application_authorizations_json"
            ],
            "execution_blocker_ids": sorted({x for x in blocker_ids if x}),
            "readiness_decision_id": readiness_row.get("decision_id"),
            "preflight_id": preflight_row.get("preflight_id"),
            "intent_id": intent_row.get("intent_id"),
            "authorization_id": auth_row.get("authorization_id"),
        }

        record = {
            "release_prohibition_id": f"release-prohibition-{seq:04d}",
            "proposal_id": proposal_id,
            "policy_id": (
                release_ineligibility_row.get("policy_id")
                or policy_row.get("policy_id")
                or release_decision_row.get("policy_id")
            ),
            "criteria_id": (
                release_ineligibility_row.get("criteria_id")
                or criteria_row.get("criteria_id")
                or release_decision_row.get("criteria_id")
            ),
            "ineligibility_id": (
                release_ineligibility_row.get("ineligibility_id")
                or ineligibility_row.get("ineligibility_id")
                or release_decision_row.get("ineligibility_id")
            ),
            "prohibition_id": (
                release_ineligibility_row.get("prohibition_id")
                or release_decision_row.get("prohibition_id")
                or compact_join(prohibition_ids)
            ),
            "release_condition_id": (
                release_ineligibility_row.get("release_condition_id")
                or release_decision_row.get("release_condition_id")
                or release_condition_row.get("release_condition_id")
            ),
            "release_authority_id": (
                release_ineligibility_row.get("release_authority_id")
                or release_decision_row.get("release_authority_id")
                or release_authority_row.get("release_authority_id")
            ),
            "release_gate_id": (
                release_ineligibility_row.get("release_gate_id")
                or release_decision_row.get("release_gate_id")
                or release_gate_row.get("release_gate_id")
            ),
            "release_decision_id": (
                release_ineligibility_row.get("release_decision_id")
                or release_decision_row.get("release_decision_id")
            ),
            "release_ineligibility_decision_id": release_ineligibility_row.get(
                "release_ineligibility_decision_id"
            ),
            "prohibited_release_action_type": prohibited_release_action_type,
            "release_prohibition_state": release_prohibition_state,
            "release_prohibition_source": release_prohibition_source,
            "release_prohibition_reason": release_prohibition_reason,
            "required_release_condition": required_release_condition,
            "required_release_authority": required_release_authority,
            "required_operator_role": required_operator_role,
            "rollback_reference": rollback_reference,
            "release_prohibition_notes": (
                "v4_0_governance_only_release_actions_remain_prohibited_no_execution_or_model_mutation"
            ),
            "source_paths": record_source_paths,
        }
        records.append(record)

        state_counts[release_prohibition_state] = state_counts.get(release_prohibition_state, 0) + 1
        source_counts[release_prohibition_source] = source_counts.get(release_prohibition_source, 0) + 1

    summary = {
        "total_proposals_in_source": len(proposal_ids),
        "total_release_prohibition_records": len(records),
        "proposals_covered": len(
            {
                str(r.get("proposal_id") or "")
                for r in records
                if str(r.get("proposal_id") or "").strip()
            }
        ),
        "all_proposals_covered": len(records) == len(proposal_ids),
        "record_count_matches_expected": len(records) == len(proposal_ids),
        "release_prohibition_state_counts": state_counts,
        "deterministic_ordering": proposal_ids
        == sorted(
            [str(r.get("proposal_id") or "") for r in records if str(r.get("proposal_id") or "").strip()]
        ),
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_release_prohibition_matrix_version": "v4.0-slice-1",
        "source_versions": {
            "model_adjustment_execution_release_conditions_version": release_conditions_payload.get(
                "model_adjustment_execution_release_conditions_version"
            ),
            "model_adjustment_execution_release_authority_version": release_authority_payload.get(
                "model_adjustment_execution_release_authority_version"
            ),
            "model_adjustment_execution_release_gate_assessments_version": release_gate_payload.get(
                "model_adjustment_execution_release_gate_assessments_version"
            ),
            "model_adjustment_execution_release_decisions_version": release_decisions_payload.get(
                "model_adjustment_execution_release_decisions_version"
            ),
            "model_adjustment_release_ineligibility_decisions_version": release_ineligibility_payload.get(
                "model_adjustment_release_ineligibility_decisions_version"
            ),
            "model_adjustment_execution_prohibition_matrix_version": execution_prohibition_payload.get(
                "model_adjustment_execution_prohibition_matrix_version"
            ),
            "model_adjustment_execution_blocker_registry_version": blocker_registry_payload.get(
                "model_adjustment_execution_blocker_registry_version"
            ),
            "model_adjustment_execution_ineligibility_register_version": ineligibility_register_payload.get(
                "model_adjustment_execution_ineligibility_register_version"
            ),
            "model_adjustment_execution_policy_version": execution_policy_payload.get(
                "model_adjustment_execution_policy_version"
            ),
            "model_adjustment_execution_enablement_criteria_version": enablement_payload.get(
                "model_adjustment_execution_enablement_criteria_version"
            ),
            "model_adjustment_readiness_decisions_version": readiness_payload.get(
                "model_adjustment_readiness_decisions_version"
            ),
            "model_adjustment_application_preflight_records_version": preflight_payload.get(
                "model_adjustment_application_preflight_records_version"
            ),
            "model_adjustment_execution_intents_version": intents_payload.get(
                "model_adjustment_execution_intents_version"
            ),
            "model_adjustment_application_authorizations_version": auth_payload.get(
                "model_adjustment_application_authorizations_version"
            ),
        },
        "release_prohibition_matrix_summary": summary,
        "release_prohibition_matrix": records,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("release_prohibition_matrix_summary") or {}
    rows = payload.get("release_prohibition_matrix") or []

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Release Prohibition Matrix (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(
        "Release Prohibition Matrix Version: "
        f"{payload.get('model_adjustment_release_prohibition_matrix_version')}"
    )
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Total Records: {summary.get('total_release_prohibition_records')}")
    lines.append(f"- Proposals Covered: {summary.get('proposals_covered')}")
    lines.append(f"- All Proposals Covered: {summary.get('all_proposals_covered')}")
    lines.append(f"- Record Count Matches Expected: {summary.get('record_count_matches_expected')}")
    lines.append(f"- Deterministic Ordering: {summary.get('deterministic_ordering')}")
    lines.append(f"- Release Prohibition State Counts: {summary.get('release_prohibition_state_counts')}")
    lines.append("")
    lines.append("## Release Prohibition Records")

    if rows:
        for row in rows:
            lines.append(
                f"- {row.get('release_prohibition_id')}: {row.get('proposal_id')} | "
                f"policy={row.get('policy_id')} | criteria={row.get('criteria_id')} | "
                f"ineligibility={row.get('ineligibility_id')} | prohibition={row.get('prohibition_id')}"
            )
            lines.append(
                f"  linkage: release_condition={row.get('release_condition_id')} | "
                f"release_authority={row.get('release_authority_id')} | "
                f"release_gate={row.get('release_gate_id')} | release_decision={row.get('release_decision_id')} | "
                f"release_ineligibility_decision={row.get('release_ineligibility_decision_id')}"
            )
            lines.append(
                f"  prohibited_release_action_type={row.get('prohibited_release_action_type')} | "
                f"state={row.get('release_prohibition_state')}"
            )
            lines.append(
                f"  source={row.get('release_prohibition_source')} | "
                f"reason={row.get('release_prohibition_reason')}"
            )
            lines.append(
                f"  required_release_condition={row.get('required_release_condition')} | "
                f"required_release_authority={row.get('required_release_authority')}"
            )
            lines.append(f"  required_operator_role={row.get('required_operator_role')}")
            lines.append(f"  rollback_reference={row.get('rollback_reference')}")
            lines.append(f"  notes={row.get('release_prohibition_notes')}")
            lines.append(f"  source_paths={row.get('source_paths')}")
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

    release_conditions_path = Path(args.execution_release_conditions_json)
    release_authority_path = Path(args.execution_release_authority_json)
    release_gate_path = Path(args.execution_release_gate_assessments_json)
    release_decisions_path = Path(args.execution_release_decisions_json)
    release_ineligibility_path = Path(args.release_ineligibility_decisions_json)
    execution_prohibition_path = Path(args.execution_prohibition_matrix_json)
    blocker_registry_path = Path(args.execution_blocker_registry_json)
    ineligibility_path = Path(args.execution_ineligibility_register_json)
    execution_policy_path = Path(args.execution_policy_json)
    enablement_path = Path(args.execution_enablement_criteria_json)
    readiness_path = Path(args.readiness_decisions_json)
    preflight_path = Path(args.application_preflight_records_json)
    intents_path = Path(args.execution_intents_json)
    auth_path = Path(args.application_authorizations_json)
    output_dir = Path(args.output_dir)

    release_conditions_payload, release_conditions_err = safe_read_json(repo_root / release_conditions_path)
    release_authority_payload, release_authority_err = safe_read_json(repo_root / release_authority_path)
    release_gate_payload, release_gate_err = safe_read_json(repo_root / release_gate_path)
    release_decisions_payload, release_decisions_err = safe_read_json(repo_root / release_decisions_path)
    release_ineligibility_payload, release_ineligibility_err = safe_read_json(
        repo_root / release_ineligibility_path
    )
    execution_prohibition_payload, execution_prohibition_err = safe_read_json(
        repo_root / execution_prohibition_path
    )
    blocker_registry_payload, blocker_registry_err = safe_read_json(repo_root / blocker_registry_path)
    ineligibility_payload, ineligibility_err = safe_read_json(repo_root / ineligibility_path)
    execution_policy_payload, execution_policy_err = safe_read_json(repo_root / execution_policy_path)
    enablement_payload, enablement_err = safe_read_json(repo_root / enablement_path)
    readiness_payload, readiness_err = safe_read_json(repo_root / readiness_path)
    preflight_payload, preflight_err = safe_read_json(repo_root / preflight_path)
    intents_payload, intents_err = safe_read_json(repo_root / intents_path)
    auth_payload, auth_err = safe_read_json(repo_root / auth_path)

    errors = [
        ("model-adjustment execution release conditions", release_conditions_err),
        ("model-adjustment execution release authority", release_authority_err),
        ("model-adjustment execution release gate assessments", release_gate_err),
        ("model-adjustment execution release decisions", release_decisions_err),
        ("model-adjustment release ineligibility decisions", release_ineligibility_err),
        ("model-adjustment execution prohibition matrix", execution_prohibition_err),
        ("model-adjustment execution blocker registry", blocker_registry_err),
        ("model-adjustment execution ineligibility register", ineligibility_err),
        ("model-adjustment execution policy", execution_policy_err),
        ("model-adjustment execution enablement criteria", enablement_err),
        ("model-adjustment readiness decisions", readiness_err),
        ("model-adjustment application preflight records", preflight_err),
        ("model-adjustment execution intents", intents_err),
        ("model-adjustment application authorizations", auth_err),
    ]
    for label, err in errors:
        if err is not None:
            print(f"ERROR: {label} unavailable: {err}", file=sys.stderr)
            return 1

    payloads = [
        release_conditions_payload,
        release_authority_payload,
        release_gate_payload,
        release_decisions_payload,
        release_ineligibility_payload,
        execution_prohibition_payload,
        blocker_registry_payload,
        ineligibility_payload,
        execution_policy_payload,
        enablement_payload,
        readiness_payload,
        preflight_payload,
        intents_payload,
        auth_payload,
    ]
    if not all(isinstance(x, dict) for x in payloads):
        print("ERROR: one or more source artifacts are not valid JSON objects", file=sys.stderr)
        return 1

    source_paths = {
        "model_adjustment_execution_release_conditions_json": normalize_path(release_conditions_path),
        "model_adjustment_execution_release_authority_json": normalize_path(release_authority_path),
        "model_adjustment_execution_release_gate_assessments_json": normalize_path(release_gate_path),
        "model_adjustment_execution_release_decisions_json": normalize_path(release_decisions_path),
        "model_adjustment_release_ineligibility_decisions_json": normalize_path(release_ineligibility_path),
        "model_adjustment_execution_prohibition_matrix_json": normalize_path(execution_prohibition_path),
        "model_adjustment_execution_blocker_registry_json": normalize_path(blocker_registry_path),
        "model_adjustment_execution_ineligibility_register_json": normalize_path(ineligibility_path),
        "model_adjustment_execution_policy_json": normalize_path(execution_policy_path),
        "model_adjustment_execution_enablement_criteria_json": normalize_path(enablement_path),
        "model_adjustment_readiness_decisions_json": normalize_path(readiness_path),
        "model_adjustment_application_preflight_records_json": normalize_path(preflight_path),
        "model_adjustment_execution_intents_json": normalize_path(intents_path),
        "model_adjustment_application_authorizations_json": normalize_path(auth_path),
    }

    payload = build_release_prohibition_matrix(
        release_conditions_payload=release_conditions_payload,
        release_authority_payload=release_authority_payload,
        release_gate_payload=release_gate_payload,
        release_decisions_payload=release_decisions_payload,
        release_ineligibility_payload=release_ineligibility_payload,
        execution_prohibition_payload=execution_prohibition_payload,
        blocker_registry_payload=blocker_registry_payload,
        ineligibility_register_payload=ineligibility_payload,
        execution_policy_payload=execution_policy_payload,
        enablement_payload=enablement_payload,
        readiness_payload=readiness_payload,
        preflight_payload=preflight_payload,
        intents_payload=intents_payload,
        auth_payload=auth_payload,
        source_paths=source_paths,
    )

    payload["source_status"] = {
        f"{k}_error": v
        for k, v in [
            ("model_adjustment_execution_release_conditions_json", release_conditions_err),
            ("model_adjustment_execution_release_authority_json", release_authority_err),
            ("model_adjustment_execution_release_gate_assessments_json", release_gate_err),
            ("model_adjustment_execution_release_decisions_json", release_decisions_err),
            ("model_adjustment_release_ineligibility_decisions_json", release_ineligibility_err),
            ("model_adjustment_execution_prohibition_matrix_json", execution_prohibition_err),
            ("model_adjustment_execution_blocker_registry_json", blocker_registry_err),
            ("model_adjustment_execution_ineligibility_register_json", ineligibility_err),
            ("model_adjustment_execution_policy_json", execution_policy_err),
            ("model_adjustment_execution_enablement_criteria_json", enablement_err),
            ("model_adjustment_readiness_decisions_json", readiness_err),
            ("model_adjustment_application_preflight_records_json", preflight_err),
            ("model_adjustment_execution_intents_json", intents_err),
            ("model_adjustment_application_authorizations_json", auth_err),
        ]
    }

    out_root = repo_root / output_dir
    out_root.mkdir(parents=True, exist_ok=True)

    out_json = out_root / OUTPUT_JSON
    out_md = out_root / OUTPUT_MD

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    out_md.write_text(render_markdown(payload), encoding="utf-8")

    summary = payload.get("release_prohibition_matrix_summary") or {}
    print(f"[WRITE] {out_json}")
    print(f"[WRITE] {out_md}")
    print(
        "[STATUS] release_prohibition_records={total} proposals_covered={covered} "
        "all_covered={all_covered} record_count_matches_expected={match} "
        "deterministic_ordering={ordered} release_prohibition_state={state}".format(
            total=summary.get("total_release_prohibition_records"),
            covered=summary.get("proposals_covered"),
            all_covered=summary.get("all_proposals_covered"),
            match=summary.get("record_count_matches_expected"),
            ordered=summary.get("deterministic_ordering"),
            state=summary.get("release_prohibition_state_counts"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())