#!/usr/bin/env python3
"""
AI-RISA v3.3 Controlled Execution Ineligibility Register (slice 1): read-only governance layer.

Builds per-proposal ineligibility records that give a single normalized ineligibility
classification explaining why each proposal is presently ineligible for execution.
This is distinct from the raw blocker registry: it derives a final ineligibility class
and reason per proposal, making the no-execution state explicit and unambiguous.
This script does not execute adjustments, create an execution path, auto-promote
records, write configs, or mutate model behavior.
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
OUTPUT_JSON = "model_adjustment_execution_ineligibility_register.json"
OUTPUT_MD = "model_adjustment_execution_ineligibility_register.md"

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

# Ineligibility classification constants
INELIG_GOVERNANCE_LAYER_HARD_STOP = "governance_layer_hard_stop"
INELIG_POLICY_DENIED = "policy_execution_denied"
INELIG_CRITERIA_UNMET = "enablement_criteria_unmet"
INELIG_READINESS_BLOCKED = "readiness_decision_blocked"
INELIG_PREFLIGHT_NO_GO = "preflight_no_go"
INELIG_INTENT_BLOCKED = "execution_intent_blocked"
INELIG_AUTHORIZATION_BLOCKED = "authorization_blocked"
INELIG_COMPOSITE = "composite_multi_layer_ineligibility"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled execution ineligibility register artifacts"
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


def index_blocker_refs_by_proposal(
    blocker_rows: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Return {proposal_id: [blocker_id, ...]} from the blocker registry records."""
    refs: dict[str, list[str]] = {}
    for row in blocker_rows:
        if not isinstance(row, dict):
            continue
        pid = str(row.get("proposal_id") or "").strip()
        bid = str(row.get("blocker_id") or "").strip()
        if pid and bid:
            refs.setdefault(pid, []).append(bid)
    return refs


def derive_ineligibility_class(
    execution_permission: str,
    enablement_state: str,
    readiness_decision: str,
    preflight_status: str,
    go_no_go_state: str,
    intent_status: str,
    authorization_status: str,
    has_blocker_refs: bool,
) -> tuple[str, str]:
    """
    Return (ineligibility_class, ineligibility_reason).
    Classification priority order (highest to lowest):
      1. governance_layer_hard_stop  — v3.3 hard stop always applies
      2. composite                   — multiple upstream layers are blocked
      3. policy_execution_denied     — policy is the sole driver
      4. enablement_criteria_unmet   — criteria is the sole driver
      5. readiness_decision_blocked  — readiness is the sole driver
      6. preflight_no_go             — preflight is the sole driver
      7. execution_intent_blocked    — intent is the sole driver
      8. authorization_blocked       — authorization is the sole driver
    The governance hard stop always applies; composite is chosen when 2+ non-hard-stop
    layers independently block execution.
    """
    policy_blocked = execution_permission != "allowed"
    criteria_blocked = enablement_state != "enablement_met"
    readiness_blocked = readiness_decision != "governance_ready_but_execution_disabled"
    preflight_blocked = preflight_status != "ready_for_execution" or go_no_go_state != "go"
    intent_blocked = intent_status != "authorization_ready_intent"
    auth_blocked = authorization_status != "authorized"

    independent_blocks = sum([
        policy_blocked,
        criteria_blocked,
        readiness_blocked,
        preflight_blocked,
        intent_blocked,
        auth_blocked,
    ])

    # Hard stop is always the top-level class; reason distinguishes composite vs single
    if independent_blocks >= 2:
        inelig_class = INELIG_COMPOSITE
        reason = (
            "multiple_governance_layers_independently_block_execution: "
            + ", ".join(filter(None, [
                "execution_policy_denied" if policy_blocked else "",
                "enablement_criteria_unmet" if criteria_blocked else "",
                "readiness_decision_blocked" if readiness_blocked else "",
                "preflight_no_go" if preflight_blocked else "",
                "execution_intent_blocked" if intent_blocked else "",
                "authorization_blocked" if auth_blocked else "",
            ]))
        )
    elif policy_blocked:
        inelig_class = INELIG_POLICY_DENIED
        reason = "execution_policy_explicitly_denies_execution_permission"
    elif criteria_blocked:
        inelig_class = INELIG_CRITERIA_UNMET
        reason = "one_or_more_enablement_criteria_are_currently_unmet"
    elif readiness_blocked:
        inelig_class = INELIG_READINESS_BLOCKED
        reason = "readiness_decision_has_not_reached_governance_ready_but_execution_disabled"
    elif preflight_blocked:
        inelig_class = INELIG_PREFLIGHT_NO_GO
        reason = "preflight_state_remains_no_go"
    elif intent_blocked:
        inelig_class = INELIG_INTENT_BLOCKED
        reason = "execution_intent_is_not_authorization_ready"
    elif auth_blocked:
        inelig_class = INELIG_AUTHORIZATION_BLOCKED
        reason = "authorization_status_is_not_authorized"
    else:
        # Governance hard stop is always present regardless of upstream state
        inelig_class = INELIG_GOVERNANCE_LAYER_HARD_STOP
        reason = "execution_path_not_enabled_in_v3_3_governance_only_mode_active"

    return inelig_class, reason


def derive_resolution_path(inelig_class: str) -> str:
    paths = {
        INELIG_GOVERNANCE_LAYER_HARD_STOP: (
            "dedicated_execution_enablement_release_required_for_v3_3_hard_stop"
        ),
        INELIG_POLICY_DENIED: (
            "execution_policy_must_be_revised_to_permit_execution_mode_and_enablement_release_required"
        ),
        INELIG_CRITERIA_UNMET: (
            "all_enablement_criteria_must_be_satisfied_and_enablement_release_required"
        ),
        INELIG_READINESS_BLOCKED: (
            "readiness_decision_must_reach_governance_ready_but_execution_disabled_and_enablement_release_required"
        ),
        INELIG_PREFLIGHT_NO_GO: (
            "preflight_must_confirm_go_state_and_enablement_release_required"
        ),
        INELIG_INTENT_BLOCKED: (
            "execution_intent_must_reach_authorization_ready_intent_state_and_enablement_release_required"
        ),
        INELIG_AUTHORIZATION_BLOCKED: (
            "authorization_must_reach_authorized_state_and_enablement_release_required"
        ),
        INELIG_COMPOSITE: (
            "all_independently_blocking_governance_layers_must_be_resolved_and_enablement_release_required"
        ),
    }
    return paths.get(inelig_class, "enablement_release_and_full_governance_resolution_required")


def build_ineligibility_register(
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
    blocker_rows = (
        blocker_payload.get("execution_blocker_registry")
        if isinstance(blocker_payload.get("execution_blocker_registry"), list)
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
    blocker_refs_by_pid = index_blocker_refs_by_proposal(blocker_rows)

    register_records: list[dict[str, Any]] = []
    ineligibility_state_counts: dict[str, int] = {}
    ineligibility_class_counts: dict[str, int] = {}

    for idx, proposal in enumerate(proposals, start=1):
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
        blocker_refs = blocker_refs_by_pid.get(proposal_id, [])

        execution_permission = str(policy_row.get("execution_permission") or "denied")
        enablement_state = str(criteria_row.get("enablement_state") or "enablement_not_met")
        readiness_decision = str(decision_row.get("readiness_decision") or "not_ready")
        preflight_status = str(preflight_row.get("preflight_status") or "blocked")
        go_no_go_state = str(preflight_row.get("go_no_go_state") or "no_go")
        intent_status = str(intent_row.get("execution_intent_status") or "blocked_intent")
        authorization_status = str(auth_row.get("authorization_status") or "not_authorized")

        inelig_class, inelig_reason = derive_ineligibility_class(
            execution_permission=execution_permission,
            enablement_state=enablement_state,
            readiness_decision=readiness_decision,
            preflight_status=preflight_status,
            go_no_go_state=go_no_go_state,
            intent_status=intent_status,
            authorization_status=authorization_status,
            has_blocker_refs=bool(blocker_refs),
        )

        ineligibility_state = "ineligible_for_execution"
        resolution_path = derive_resolution_path(inelig_class)

        ineligibility_state_counts[ineligibility_state] = (
            ineligibility_state_counts.get(ineligibility_state, 0) + 1
        )
        ineligibility_class_counts[inelig_class] = (
            ineligibility_class_counts.get(inelig_class, 0) + 1
        )

        decision_id = decision_row.get("decision_id")
        policy_id = policy_row.get("policy_id")
        criteria_id = criteria_row.get("criteria_id")
        packet_id = packet_row.get("packet_id")

        required_operator_role = str(
            policy_row.get("required_operator_role")
            or criteria_row.get("required_operator_role")
            or decision_row.get("required_operator_role")
            or auth_row.get("required_operator_role")
            or packet_row.get("operator_role_required")
            or "ops_reviewer"
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
            "approval_ledger_entry_id": approval_row.get("ledger_item_id"),
            "validation_manifest_id": manifest_row.get("manifest_id"),
            "application_gate_id": gate_row.get("gate_id"),
            "application_packet_id": packet_id,
            "application_dry_run_id": dry_row.get("dry_run_id"),
            "application_authorization_id": auth_row.get("authorization_id"),
            "execution_intent_id": intent_row.get("intent_id"),
            "application_preflight_id": preflight_row.get("preflight_id"),
            "readiness_decision_id": decision_id,
            "execution_policy_id": policy_id,
            "execution_enablement_criteria_id": criteria_id,
        }

        register_records.append(
            {
                "ineligibility_id": f"inelig-{idx:03d}",
                "proposal_id": proposal_id,
                "decision_id": decision_id,
                "policy_id": policy_id,
                "criteria_id": criteria_id,
                "blocker_registry_refs": blocker_refs,
                "ineligibility_state": ineligibility_state,
                "ineligibility_class": inelig_class,
                "ineligibility_reason": inelig_reason,
                "required_resolution_path": resolution_path,
                "required_operator_role": required_operator_role,
                "rollback_reference": f"rollback-from-{packet_id or proposal_id}",
                "ineligibility_notes": (
                    "governance_ineligibility_assessment_only_no_execution_in_v3_3"
                ),
                "source_paths": record_source_paths,
            }
        )

    proposal_ids_in_source = [
        str(x.get("proposal_id") or "")
        for x in proposals
        if isinstance(x, dict) and str(x.get("proposal_id") or "").strip()
    ]
    register_pids = [str(r.get("proposal_id") or "") for r in register_records]

    summary = {
        "total_proposals_in_source": len(proposal_ids_in_source),
        "total_ineligibility_records": len(register_records),
        "all_proposals_represented_exactly_once": (
            len(proposal_ids_in_source) == len(register_pids) == len(set(register_pids))
            and set(proposal_ids_in_source) == set(register_pids)
        ),
        "ineligibility_state_counts": ineligibility_state_counts,
        "ineligibility_class_counts": ineligibility_class_counts,
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_execution_ineligibility_register_version": "v3.3-slice-1",
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
        },
        "execution_ineligibility_summary": summary,
        "execution_ineligibility_register": register_records,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = (
        payload.get("execution_ineligibility_summary")
        if isinstance(payload.get("execution_ineligibility_summary"), dict)
        else {}
    )
    source_versions = (
        payload.get("source_versions")
        if isinstance(payload.get("source_versions"), dict)
        else {}
    )
    rows = (
        payload.get("execution_ineligibility_register")
        if isinstance(payload.get("execution_ineligibility_register"), list)
        else []
    )

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Execution Ineligibility Register (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(
        f"Register Version: {payload.get('model_adjustment_execution_ineligibility_register_version')}"
    )
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Ineligibility Register Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Ineligibility Records: {summary.get('total_ineligibility_records')}")
    lines.append(
        f"- Exact Once Representation: {summary.get('all_proposals_represented_exactly_once')}"
    )
    lines.append(
        f"- Ineligibility State Counts: {summary.get('ineligibility_state_counts')}"
    )
    lines.append(
        f"- Ineligibility Class Counts: {summary.get('ineligibility_class_counts')}"
    )
    lines.append("")
    lines.append("## Execution Ineligibility Register Records")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- {row.get('ineligibility_id')}: {row.get('proposal_id')} | "
                f"decision={row.get('decision_id')} | policy={row.get('policy_id')} | "
                f"criteria={row.get('criteria_id')}"
            )
            lines.append(
                f"  Ineligibility State: {row.get('ineligibility_state')} | "
                f"Class: {row.get('ineligibility_class')}"
            )
            lines.append(f"  Ineligibility Reason: {row.get('ineligibility_reason')}")
            lines.append(
                f"  Required Resolution Path: {row.get('required_resolution_path')}"
            )
            lines.append(f"  Required Operator Role: {row.get('required_operator_role')}")
            lines.append(
                f"  Blocker Registry Refs: {row.get('blocker_registry_refs')}"
            )
            lines.append(f"  Rollback Reference: {row.get('rollback_reference')}")
            lines.append(f"  Ineligibility Notes: {row.get('ineligibility_notes')}")
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
    }

    payload = build_ineligibility_register(
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
    s = payload.get("execution_ineligibility_summary") or {}
    print(
        "[STATUS] ineligible={total} exact_once={exact_once} "
        "ineligibility_state={state} ineligibility_class={cls}".format(
            total=s.get("total_ineligibility_records"),
            exact_once=s.get("all_proposals_represented_exactly_once"),
            state=s.get("ineligibility_state_counts"),
            cls=s.get("ineligibility_class_counts"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
