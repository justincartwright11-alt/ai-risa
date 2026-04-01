#!/usr/bin/env python3
"""
AI-RISA v3.2 Controlled Execution Blocker Registry (slice 1): read-only governance layer.

Builds a canonical flat registry of all active execution blockers consolidated from
execution policy blockers, enablement blockers, unmet criteria, preflight stop
conditions, readiness blockers, and execution intent blockers. This script does not
execute adjustments, create an execution path, auto-promote records, write configs,
or mutate model behavior.
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
OUTPUT_JSON = "model_adjustment_execution_blocker_registry.json"
OUTPUT_MD = "model_adjustment_execution_blocker_registry.md"

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled execution blocker registry artifacts"
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


def derive_blocker_entries(
    proposal_id: str,
    policy_row: dict[str, Any],
    criteria_row: dict[str, Any],
    decision_row: dict[str, Any],
    preflight_row: dict[str, Any],
    intent_row: dict[str, Any],
    auth_row: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Return a list of raw blocker entries for a single proposal. Each entry carries
    blocker_category, blocker_source, blocking_condition, and required_resolution.
    The hard governance-layer entry is always appended last to ensure it is always present.
    """
    entries: list[dict[str, str]] = []

    # --- execution policy blockers ---
    policy_blockers = policy_row.get("policy_blockers")
    if isinstance(policy_blockers, list) and policy_blockers:
        for pb in policy_blockers:
            entries.append(
                {
                    "blocker_category": "execution_policy_blocker",
                    "blocker_source": "execution_policy",
                    "blocking_condition": str(pb),
                    "required_resolution": (
                        "execution_policy_must_be_revised_to_permit_execution_mode"
                    ),
                }
            )
    else:
        entries.append(
            {
                "blocker_category": "execution_policy_blocker",
                "blocker_source": "execution_policy",
                "blocking_condition": "execution_policy_in_governance_only_mode",
                "required_resolution": (
                    "execution_policy_must_be_revised_to_permit_execution_mode"
                ),
            }
        )

    # --- enablement criteria blockers ---
    enablement_blockers = criteria_row.get("enablement_blockers")
    if isinstance(enablement_blockers, list) and enablement_blockers:
        for eb in enablement_blockers:
            entries.append(
                {
                    "blocker_category": "enablement_criteria_blocker",
                    "blocker_source": "execution_enablement_criteria",
                    "blocking_condition": str(eb),
                    "required_resolution": (
                        "all_enablement_criteria_blockers_must_be_resolved"
                    ),
                }
            )

    # --- unmet enablement criteria ---
    unmet_criteria = criteria_row.get("currently_unmet_criteria")
    if isinstance(unmet_criteria, list) and unmet_criteria:
        for uc in unmet_criteria:
            entries.append(
                {
                    "blocker_category": "unmet_criteria_blocker",
                    "blocker_source": "execution_enablement_criteria",
                    "blocking_condition": str(uc),
                    "required_resolution": (
                        "criterion_must_be_satisfied_before_execution_pathway_opens"
                    ),
                }
            )

    # --- readiness decision blockers ---
    decision_blockers = decision_row.get("decision_blockers")
    if isinstance(decision_blockers, list) and decision_blockers:
        for db in decision_blockers:
            entries.append(
                {
                    "blocker_category": "readiness_decision_blocker",
                    "blocker_source": "readiness_decisions",
                    "blocking_condition": str(db),
                    "required_resolution": (
                        "readiness_decision_must_reach_governance_ready_state"
                    ),
                }
            )
    else:
        readiness_decision = str(decision_row.get("readiness_decision") or "not_ready")
        if readiness_decision != "governance_ready_but_execution_disabled":
            entries.append(
                {
                    "blocker_category": "readiness_decision_blocker",
                    "blocker_source": "readiness_decisions",
                    "blocking_condition": f"readiness_decision_is_{readiness_decision}",
                    "required_resolution": (
                        "readiness_decision_must_reach_governance_ready_but_execution_disabled"
                    ),
                }
            )

    # --- preflight stop conditions ---
    stop_conditions = preflight_row.get("stop_conditions")
    if isinstance(stop_conditions, list) and stop_conditions:
        for sc in stop_conditions:
            entries.append(
                {
                    "blocker_category": "preflight_stop_condition_blocker",
                    "blocker_source": "application_preflight_records",
                    "blocking_condition": str(sc),
                    "required_resolution": "all_preflight_stop_conditions_must_be_cleared",
                }
            )
    else:
        preflight_status = str(preflight_row.get("preflight_status") or "blocked")
        go_no_go = str(preflight_row.get("go_no_go_state") or "no_go")
        entries.append(
            {
                "blocker_category": "preflight_stop_condition_blocker",
                "blocker_source": "application_preflight_records",
                "blocking_condition": (
                    f"preflight_status_{preflight_status}_go_no_go_{go_no_go}"
                ),
                "required_resolution": "preflight_must_confirm_go_state",
            }
        )

    # --- execution intent blockers ---
    intent_blockers = intent_row.get("execution_blockers")
    if isinstance(intent_blockers, list) and intent_blockers:
        for ib in intent_blockers:
            entries.append(
                {
                    "blocker_category": "execution_intent_blocker",
                    "blocker_source": "execution_intents",
                    "blocking_condition": str(ib),
                    "required_resolution": (
                        "execution_intent_blockers_must_be_resolved_before_intent_activation"
                    ),
                }
            )
    else:
        intent_status = str(intent_row.get("execution_intent_status") or "blocked_intent")
        if intent_status != "authorization_ready_intent":
            entries.append(
                {
                    "blocker_category": "execution_intent_blocker",
                    "blocker_source": "execution_intents",
                    "blocking_condition": f"execution_intent_status_{intent_status}",
                    "required_resolution": (
                        "execution_intent_must_reach_authorization_ready_intent_state"
                    ),
                }
            )

    # --- hard governance-layer blocker — always present ---
    entries.append(
        {
            "blocker_category": "governance_layer_blocker",
            "blocker_source": "v3_2_controlled_execution_blocker_registry",
            "blocking_condition": "execution_path_not_enabled_in_v3_2",
            "required_resolution": "dedicated_execution_enablement_release_required",
        }
    )

    return entries


def build_blocker_registry(
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

    registry_records: list[dict[str, Any]] = []
    blocker_state_counts: dict[str, int] = {}
    blocker_category_counts: dict[str, int] = {}
    proposal_ids_covered: list[str] = []

    global_blocker_seq = 0

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

        rollback_reference = f"rollback-from-{packet_id or proposal_id}"

        blocker_entries = derive_blocker_entries(
            proposal_id=proposal_id,
            policy_row=policy_row,
            criteria_row=criteria_row,
            decision_row=decision_row,
            preflight_row=preflight_row,
            intent_row=intent_row,
            auth_row=auth_row,
        )

        proposal_ids_covered.append(proposal_id)

        for entry in blocker_entries:
            global_blocker_seq += 1
            blocker_state = "active_blocker"

            blocker_state_counts[blocker_state] = (
                blocker_state_counts.get(blocker_state, 0) + 1
            )
            blocker_category = entry["blocker_category"]
            blocker_category_counts[blocker_category] = (
                blocker_category_counts.get(blocker_category, 0) + 1
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

            registry_records.append(
                {
                    "blocker_id": f"blocker-{global_blocker_seq:04d}",
                    "proposal_id": proposal_id,
                    "decision_id": decision_id,
                    "policy_id": policy_id,
                    "criteria_id": criteria_id,
                    "blocker_state": blocker_state,
                    "blocker_category": blocker_category,
                    "blocker_source": entry["blocker_source"],
                    "blocking_condition": entry["blocking_condition"],
                    "required_resolution": entry["required_resolution"],
                    "required_operator_role": required_operator_role,
                    "rollback_reference": rollback_reference,
                    "blocker_notes": (
                        "governance_blocker_registry_assessment_only_no_execution_in_v3_2"
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
        "total_blocker_records": len(registry_records),
        "proposals_covered": len(set(proposal_ids_covered)),
        "all_proposals_covered": set(proposal_ids_in_source) == set(proposal_ids_covered),
        "blocker_state_counts": blocker_state_counts,
        "blocker_category_counts": blocker_category_counts,
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_execution_blocker_registry_version": "v3.2-slice-1",
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
        },
        "execution_blocker_registry_summary": summary,
        "execution_blocker_registry": registry_records,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = (
        payload.get("execution_blocker_registry_summary")
        if isinstance(payload.get("execution_blocker_registry_summary"), dict)
        else {}
    )
    source_versions = (
        payload.get("source_versions")
        if isinstance(payload.get("source_versions"), dict)
        else {}
    )
    rows = (
        payload.get("execution_blocker_registry")
        if isinstance(payload.get("execution_blocker_registry"), list)
        else []
    )

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Execution Blocker Registry (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(
        f"Registry Version: {payload.get('model_adjustment_execution_blocker_registry_version')}"
    )
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Blocker Registry Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Total Blocker Records: {summary.get('total_blocker_records')}")
    lines.append(f"- Proposals Covered: {summary.get('proposals_covered')}")
    lines.append(f"- All Proposals Covered: {summary.get('all_proposals_covered')}")
    lines.append(f"- Blocker State Counts: {summary.get('blocker_state_counts')}")
    lines.append(f"- Blocker Category Counts: {summary.get('blocker_category_counts')}")
    lines.append("")
    lines.append("## Execution Blocker Registry Records")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- {row.get('blocker_id')}: {row.get('proposal_id')} | "
                f"decision={row.get('decision_id')} | policy={row.get('policy_id')} | "
                f"criteria={row.get('criteria_id')}"
            )
            lines.append(
                f"  Blocker State: {row.get('blocker_state')} | "
                f"Category: {row.get('blocker_category')} | "
                f"Source: {row.get('blocker_source')}"
            )
            lines.append(f"  Blocking Condition: {row.get('blocking_condition')}")
            lines.append(f"  Required Resolution: {row.get('required_resolution')}")
            lines.append(f"  Required Operator Role: {row.get('required_operator_role')}")
            lines.append(f"  Rollback Reference: {row.get('rollback_reference')}")
            lines.append(f"  Blocker Notes: {row.get('blocker_notes')}")
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
    }

    payload = build_blocker_registry(
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
    s = payload.get("execution_blocker_registry_summary") or {}
    print(
        "[STATUS] blockers={total} proposals_covered={covered} all_covered={all_covered} "
        "blocker_state={state}".format(
            total=s.get("total_blocker_records"),
            covered=s.get("proposals_covered"),
            all_covered=s.get("all_proposals_covered"),
            state=s.get("blocker_state_counts"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
