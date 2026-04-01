#!/usr/bin/env python3
"""
AI-RISA v2.9 Controlled Application Readiness Decisions (slice 1): read-only governance layer.

Builds per-proposal readiness decisions by consolidating proposals, approval-ledger,
validation manifests, application gates, application packets, dry-run plans,
authorization records, execution-intent records, and preflight records.
This script does not execute adjustments, create an execution path, auto-promote
any record to runnable, write configuration, or mutate model behavior.
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
OUTPUT_JSON = "model_adjustment_readiness_decisions.json"
OUTPUT_MD = "model_adjustment_readiness_decisions.md"

PROPOSALS_DEFAULT = Path("ops/model_adjustments/controlled_model_adjustment_proposals.json")
APPROVAL_LEDGER_DEFAULT = Path("ops/model_adjustments/model_adjustment_approval_ledger.json")
VALIDATION_MANIFESTS_DEFAULT = Path("ops/model_adjustments/model_adjustment_validation_manifests.json")
APPLICATION_GATES_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_gates.json")
APPLICATION_PACKETS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_packets.json")
APPLICATION_DRY_RUNS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_dry_runs.json")
APPLICATION_AUTH_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_authorizations.json")
EXECUTION_INTENTS_DEFAULT = Path("ops/model_adjustments/model_adjustment_execution_intents.json")
PREFLIGHT_RECORDS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_preflight_records.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled application readiness decision artifacts"
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


def decide_readiness(
    gate_status: str,
    authorization_status: str,
    intent_status: str,
    preflight_status: str,
    go_no_go_state: str,
    approval_status: str,
    review_outcome: str,
) -> tuple[str, str, list[str], list[str]]:
    """
    Returns (readiness_decision, decision_state, required_remaining_conditions, blockers).
    Decision taxonomy for v2.9:
      - not_ready
      - conditionally_ready
      - governance_ready_but_execution_disabled
    """
    blockers: list[str] = []
    conditions: list[str] = []

    if approval_status != "approved":
        blockers.append("approval_not_granted")
        conditions.append("Complete approval and record approved outcome")
    if review_outcome not in ("approved", "conditionally_approved"):
        blockers.append("review_outcome_not_approved")
        conditions.append("Record approved or conditionally_approved review outcome")
    if gate_status == "blocked":
        blockers.append("application_gate_blocked")
        conditions.append("Resolve blocked gate conditions")
    elif gate_status == "conditionally_eligible":
        blockers.append("application_gate_conditionally_eligible")
        conditions.append("Resolve conditional gate requirements to eligible")
    if authorization_status != "authorized":
        blockers.append("authorization_not_active")
        conditions.append("Obtain active authorization with required signoffs")
    if intent_status == "blocked_intent":
        blockers.append("execution_intent_blocked")
        conditions.append("Resolve all execution-intent blockers")
    if preflight_status != "blocked" or go_no_go_state != "no_go":
        # Keep conservative semantics if upstream values deviate from expected v2.8 defaults.
        blockers.append("preflight_state_unexpected")
        conditions.append("Reconcile preflight state to conservative governance defaults")

    if blockers:
        if gate_status == "conditionally_eligible" and len(blockers) <= 3:
            return "conditionally_ready", "blocked", conditions, blockers
        return "not_ready", "blocked", conditions, blockers

    # Even when all governance requirements are met, execution remains disabled.
    conditions.append("Execution path remains disabled in governance-only mode")
    blockers.append("execution_path_not_enabled_in_v2_9")
    return "governance_ready_but_execution_disabled", "blocked", conditions, blockers


def build_decisions(
    proposals_payload: dict[str, Any],
    approval_payload: dict[str, Any],
    manifests_payload: dict[str, Any],
    gates_payload: dict[str, Any],
    packets_payload: dict[str, Any],
    dry_runs_payload: dict[str, Any],
    auth_payload: dict[str, Any],
    intents_payload: dict[str, Any],
    preflight_payload: dict[str, Any],
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

    approval_by_pid = index_by_proposal_id(approval_rows)
    manifest_by_pid = index_by_proposal_id(manifest_rows)
    gates_by_pid = index_by_proposal_id(gate_rows)
    packets_by_pid = index_by_proposal_id(packet_rows)
    dry_by_pid = index_by_proposal_id(dry_rows)
    auth_by_pid = index_by_proposal_id(auth_rows)
    intents_by_pid = index_by_proposal_id(intent_rows)
    preflight_by_pid = index_by_proposal_id(preflight_rows)

    decisions: list[dict[str, Any]] = []
    readiness_counts: dict[str, int] = {}
    state_counts: dict[str, int] = {}

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

        gate_status = str(gate_row.get("application_gate_status") or "blocked")
        authorization_status = str(auth_row.get("authorization_status") or "not_authorized")
        intent_status = str(intent_row.get("execution_intent_status") or "blocked_intent")
        preflight_status = str(preflight_row.get("preflight_status") or "blocked")
        go_no_go_state = str(preflight_row.get("go_no_go_state") or "no_go")
        approval_status = str(approval_row.get("approval_status") or "pending_review")
        review_outcome = str(approval_row.get("review_outcome") or "undecided")

        readiness_decision, decision_state, remaining_conditions, blockers = decide_readiness(
            gate_status=gate_status,
            authorization_status=authorization_status,
            intent_status=intent_status,
            preflight_status=preflight_status,
            go_no_go_state=go_no_go_state,
            approval_status=approval_status,
            review_outcome=review_outcome,
        )

        readiness_counts[readiness_decision] = readiness_counts.get(readiness_decision, 0) + 1
        state_counts[decision_state] = state_counts.get(decision_state, 0) + 1

        authorization_id = auth_row.get("authorization_id")
        intent_id = intent_row.get("intent_id")
        preflight_id = preflight_row.get("preflight_id")
        packet_id = packet_row.get("packet_id")

        required_operator_role = str(
            auth_row.get("required_operator_role")
            or preflight_row.get("required_operator_role")
            or packet_row.get("operator_role_required")
            or dry_row.get("required_operator_role")
            or "ops_reviewer"
        )

        decisions.append(
            {
                "decision_id": f"decision-{idx:03d}",
                "proposal_id": proposal_id,
                "authorization_id": authorization_id,
                "intent_id": intent_id,
                "preflight_id": preflight_id,
                "readiness_decision": readiness_decision,
                "decision_state": decision_state,
                "required_remaining_conditions": remaining_conditions,
                "required_operator_role": required_operator_role,
                "decision_blockers": blockers,
                "rollback_reference": f"rollback-from-{packet_id or proposal_id}",
                "decision_notes": "governance_decision_only_execution_disabled_in_v2_9",
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
                    "approval_ledger_entry_id": approval_row.get("ledger_item_id"),
                    "validation_manifest_id": manifest_row.get("manifest_id"),
                    "application_gate_id": gate_row.get("gate_id"),
                    "application_packet_id": packet_id,
                    "application_dry_run_id": dry_row.get("dry_run_id"),
                    "application_authorization_id": authorization_id,
                    "execution_intent_id": intent_id,
                    "application_preflight_id": preflight_id,
                },
            }
        )

    proposal_ids = [str(x.get("proposal_id") or "") for x in proposals if isinstance(x, dict)]
    decision_pids = [str(x.get("proposal_id") or "") for x in decisions if isinstance(x, dict)]

    summary = {
        "total_proposals_in_source": len(proposal_ids),
        "total_readiness_decisions": len(decisions),
        "all_proposals_represented_exactly_once": (
            len(proposal_ids) == len(decision_pids) == len(set(decision_pids))
            and set(proposal_ids) == set(decision_pids)
        ),
        "readiness_decision_counts": readiness_counts,
        "decision_state_counts": state_counts,
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_readiness_decisions_version": "v2.9-slice-1",
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
        },
        "readiness_summary": summary,
        "readiness_decisions": decisions,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("readiness_summary") if isinstance(payload.get("readiness_summary"), dict) else {}
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    rows = payload.get("readiness_decisions") if isinstance(payload.get("readiness_decisions"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Application Readiness Decisions (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Decision Version: {payload.get('model_adjustment_readiness_decisions_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Decision Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Readiness Decisions: {summary.get('total_readiness_decisions')}")
    lines.append(f"- Exact Once Representation: {summary.get('all_proposals_represented_exactly_once')}")
    lines.append(f"- Readiness Decision Counts: {summary.get('readiness_decision_counts')}")
    lines.append(f"- Decision State Counts: {summary.get('decision_state_counts')}")
    lines.append("")
    lines.append("## Readiness Decisions")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(f"- {row.get('decision_id')}: {row.get('proposal_id')}")
            lines.append(f"  Authorization ID: {row.get('authorization_id')} | Intent ID: {row.get('intent_id')} | Preflight ID: {row.get('preflight_id')}")
            lines.append(f"  Readiness Decision: {row.get('readiness_decision')} | Decision State: {row.get('decision_state')}")
            lines.append(f"  Required Remaining Conditions: {row.get('required_remaining_conditions')}")
            lines.append(f"  Required Operator Role: {row.get('required_operator_role')}")
            lines.append(f"  Decision Blockers: {row.get('decision_blockers')}")
            lines.append(f"  Rollback Reference: {row.get('rollback_reference')}")
            lines.append(f"  Decision Notes: {row.get('decision_notes')}")
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
    }

    payload = build_decisions(
        proposals_payload=proposals_payload,
        approval_payload=approval_payload,
        manifests_payload=manifests_payload,
        gates_payload=gates_payload,
        packets_payload=packets_payload,
        dry_runs_payload=dry_runs_payload,
        auth_payload=auth_payload,
        intents_payload=intents_payload,
        preflight_payload=preflight_payload,
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
    s = payload.get("readiness_summary") or {}
    print(
        "[STATUS] decisions={total} exact_once={exact_once} readiness={counts}".format(
            total=s.get("total_readiness_decisions"),
            exact_once=s.get("all_proposals_represented_exactly_once"),
            counts=s.get("readiness_decision_counts"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
