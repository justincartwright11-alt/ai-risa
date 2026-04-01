#!/usr/bin/env python3
"""
AI-RISA v3.1 Controlled Execution Enablement Criteria (slice 1): read-only governance layer.

Builds per-proposal criteria records that define what enablement conditions would be
required before execution could ever be permitted, and which criteria are currently
unmet. This script does not execute adjustments, create an execution path,
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
OUTPUT_JSON = "model_adjustment_execution_enablement_criteria.json"
OUTPUT_MD = "model_adjustment_execution_enablement_criteria.md"

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled execution enablement criteria artifacts"
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
    parser.add_argument("--execution-policy-json", default=str(EXECUTION_POLICY_DEFAULT))
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


def canonical_required_criteria() -> list[str]:
    return [
        "Approval status is approved with accepted review outcome",
        "Validation manifests completed with required criteria met",
        "Application gate is eligible_for_controlled_application",
        "Authorization status is authorized with required signoffs",
        "Execution intent is authorization_ready_intent",
        "Preflight confirms go_no_go_state resolved for execution pathway",
        "Readiness decision is governance_ready_but_execution_disabled",
        "Execution policy explicitly permits execution mode",
        "Dedicated execution enablement slice approved and published",
    ]


def derive_unmet_criteria(
    approval_status: str,
    review_outcome: str,
    gate_status: str,
    authorization_status: str,
    intent_status: str,
    preflight_status: str,
    go_no_go_state: str,
    readiness_decision: str,
    execution_permission: str,
) -> list[str]:
    unmet: list[str] = []

    if approval_status != "approved" or review_outcome not in ("approved", "conditionally_approved"):
        unmet.append("Approval and review outcome are not in execution-eligible state")
    unmet.append("Validation manifests are not marked as execution-complete in governance layer")
    if gate_status != "eligible_for_controlled_application":
        unmet.append("Application gate is not eligible_for_controlled_application")
    if authorization_status != "authorized":
        unmet.append("Authorization status is not authorized")
    if intent_status != "authorization_ready_intent":
        unmet.append("Execution intent is not authorization_ready_intent")
    if preflight_status != "ready_for_execution" or go_no_go_state != "go":
        unmet.append("Preflight state remains no-go in governance defaults")
    if readiness_decision != "governance_ready_but_execution_disabled":
        unmet.append("Readiness decision is not governance_ready_but_execution_disabled")
    if execution_permission != "allowed":
        unmet.append("Execution policy permission is not allowed")
    unmet.append("No approved execution-enablement release exists")
    return unmet


def build_enablement_criteria(
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
    policy_rows = policy_payload.get("execution_policy_records") if isinstance(policy_payload.get("execution_policy_records"), list) else []

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

    criteria_records: list[dict[str, Any]] = []
    enablement_state_counts: dict[str, int] = {}
    criteria_status_counts: dict[str, int] = {}

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
        policy_row = policy_by_pid.get(proposal_id, {})

        approval_status = str(approval_row.get("approval_status") or "pending_review")
        review_outcome = str(approval_row.get("review_outcome") or "undecided")
        gate_status = str(gate_row.get("application_gate_status") or "blocked")
        authorization_status = str(auth_row.get("authorization_status") or "not_authorized")
        intent_status = str(intent_row.get("execution_intent_status") or "blocked_intent")
        preflight_status = str(preflight_row.get("preflight_status") or "blocked")
        go_no_go_state = str(preflight_row.get("go_no_go_state") or "no_go")
        readiness_decision = str(decision_row.get("readiness_decision") or "not_ready")
        execution_permission = str(policy_row.get("execution_permission") or "denied")

        unmet = derive_unmet_criteria(
            approval_status=approval_status,
            review_outcome=review_outcome,
            gate_status=gate_status,
            authorization_status=authorization_status,
            intent_status=intent_status,
            preflight_status=preflight_status,
            go_no_go_state=go_no_go_state,
            readiness_decision=readiness_decision,
            execution_permission=execution_permission,
        )

        enablement_state = "enablement_not_met" if unmet else "enablement_met"
        criteria_status = "blocked" if unmet else "satisfied"

        enablement_state_counts[enablement_state] = enablement_state_counts.get(enablement_state, 0) + 1
        criteria_status_counts[criteria_status] = criteria_status_counts.get(criteria_status, 0) + 1

        required_operator_role = str(
            policy_row.get("required_operator_role")
            or decision_row.get("required_operator_role")
            or auth_row.get("required_operator_role")
            or packet_row.get("operator_role_required")
            or dry_row.get("required_operator_role")
            or "ops_reviewer"
        )

        policy_id = policy_row.get("policy_id")
        decision_id = decision_row.get("decision_id")
        packet_id = packet_row.get("packet_id")

        criteria_records.append(
            {
                "criteria_id": f"criteria-{idx:03d}",
                "proposal_id": proposal_id,
                "decision_id": decision_id,
                "policy_id": policy_id,
                "enablement_state": enablement_state,
                "criteria_status": criteria_status,
                "required_enablement_criteria": canonical_required_criteria(),
                "currently_unmet_criteria": unmet,
                "required_operator_role": required_operator_role,
                "enablement_blockers": [
                    "execution_path_not_enabled_in_v3_1",
                    "governance_only_mode_active",
                    "execution_permission_denied",
                ] + ([] if not unmet else ["criteria_unmet"]),
                "rollback_reference": f"rollback-from-{packet_id or proposal_id}",
                "criteria_notes": "governance_enablement_assessment_only_no_execution_in_v3_1",
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
                    "model_adjustment_execution_policy_json": source_paths["model_adjustment_execution_policy_json"],
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
                },
            }
        )

    proposal_ids = [str(x.get("proposal_id") or "") for x in proposals if isinstance(x, dict)]
    criteria_pids = [str(x.get("proposal_id") or "") for x in criteria_records if isinstance(x, dict)]

    summary = {
        "total_proposals_in_source": len(proposal_ids),
        "total_enablement_criteria_records": len(criteria_records),
        "all_proposals_represented_exactly_once": (
            len(proposal_ids) == len(criteria_pids) == len(set(criteria_pids))
            and set(proposal_ids) == set(criteria_pids)
        ),
        "enablement_state_counts": enablement_state_counts,
        "criteria_status_counts": criteria_status_counts,
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_execution_enablement_criteria_version": "v3.1-slice-1",
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
            "model_adjustment_execution_policy_version": policy_payload.get("model_adjustment_execution_policy_version"),
        },
        "execution_enablement_summary": summary,
        "execution_enablement_criteria": criteria_records,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("execution_enablement_summary") if isinstance(payload.get("execution_enablement_summary"), dict) else {}
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    rows = payload.get("execution_enablement_criteria") if isinstance(payload.get("execution_enablement_criteria"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Execution Enablement Criteria (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Criteria Version: {payload.get('model_adjustment_execution_enablement_criteria_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Criteria Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Criteria Records: {summary.get('total_enablement_criteria_records')}")
    lines.append(f"- Exact Once Representation: {summary.get('all_proposals_represented_exactly_once')}")
    lines.append(f"- Enablement State Counts: {summary.get('enablement_state_counts')}")
    lines.append(f"- Criteria Status Counts: {summary.get('criteria_status_counts')}")
    lines.append("")
    lines.append("## Execution Enablement Criteria Records")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(f"- {row.get('criteria_id')}: {row.get('proposal_id')} | decision={row.get('decision_id')} | policy={row.get('policy_id')}")
            lines.append(f"  Enablement State: {row.get('enablement_state')} | Criteria Status: {row.get('criteria_status')}")
            lines.append(f"  Required Enablement Criteria: {row.get('required_enablement_criteria')}")
            lines.append(f"  Currently Unmet Criteria: {row.get('currently_unmet_criteria')}")
            lines.append(f"  Required Operator Role: {row.get('required_operator_role')}")
            lines.append(f"  Enablement Blockers: {row.get('enablement_blockers')}")
            lines.append(f"  Rollback Reference: {row.get('rollback_reference')}")
            lines.append(f"  Criteria Notes: {row.get('criteria_notes')}")
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
    }

    payload = build_enablement_criteria(
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
    s = payload.get("execution_enablement_summary") or {}
    print(
        "[STATUS] criteria={total} exact_once={exact_once} enablement={state}".format(
            total=s.get("total_enablement_criteria_records"),
            exact_once=s.get("all_proposals_represented_exactly_once"),
            state=s.get("enablement_state_counts"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
