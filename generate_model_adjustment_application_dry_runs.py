#!/usr/bin/env python3
"""
AI-RISA v2.5 Controlled Application Dry Runs (slice 1): read-only rehearsal layer.

Builds dry-run planning artifacts from proposals, approval-ledger state,
validation manifests, application gates, and application packets. This script does
not apply adjustments or mutate model behavior, source artifacts, scheduler logic,
or pipeline outputs.
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
OUTPUT_JSON = "model_adjustment_application_dry_runs.json"
OUTPUT_MD = "model_adjustment_application_dry_runs.md"

PROPOSALS_DEFAULT = Path("ops/model_adjustments/controlled_model_adjustment_proposals.json")
APPROVAL_LEDGER_DEFAULT = Path("ops/model_adjustments/model_adjustment_approval_ledger.json")
VALIDATION_MANIFESTS_DEFAULT = Path("ops/model_adjustments/model_adjustment_validation_manifests.json")
APPLICATION_GATES_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_gates.json")
APPLICATION_PACKETS_DEFAULT = Path("ops/model_adjustments/model_adjustment_application_packets.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled application dry-run artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument("--proposals-json", default=str(PROPOSALS_DEFAULT))
    parser.add_argument("--approval-ledger-json", default=str(APPROVAL_LEDGER_DEFAULT))
    parser.add_argument("--validation-manifests-json", default=str(VALIDATION_MANIFESTS_DEFAULT))
    parser.add_argument("--application-gates-json", default=str(APPLICATION_GATES_DEFAULT))
    parser.add_argument("--application-packets-json", default=str(APPLICATION_PACKETS_DEFAULT))
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
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = str(row.get("proposal_id") or "").strip()
        if pid:
            out[pid] = row
    return out


def ordered_dry_run_steps(gate_status: str) -> list[str]:
    steps = [
        "Load packet and linked source artifacts in read-only mode",
        "Verify gate, validation, and approval coherence",
        "Simulate planned change scope with no write operations",
        "Evaluate abort conditions and checkpoint outcomes",
        "Record expected observations and final dry-run decision",
    ]
    if gate_status == "blocked":
        steps.insert(2, "Stop rehearsal at blocked-gate checkpoint")
    return steps


def checkpoint_sequence(gate_status: str) -> list[str]:
    base = [
        "checkpoint-source-consistency",
        "checkpoint-approval-validation-gate-alignment",
    ]
    if gate_status == "blocked":
        return base + ["checkpoint-blocked-stop"]
    return base + ["checkpoint-simulation-replay", "checkpoint-reviewable-outcome"]


def required_preconditions(gate_status: str) -> list[str]:
    conditions = [
        "All linked artifacts available and readable",
        "Read-only rehearsal mode confirmed",
    ]
    if gate_status != "blocked":
        conditions.append("Operator review context prepared")
    return conditions


def abort_conditions(gate_status: str) -> list[str]:
    conditions = [
        "Source artifact mismatch or stale linkage detected",
        "Any write/mutation path detected in rehearsal flow",
    ]
    if gate_status == "blocked":
        conditions.append("Gate status blocked")
    return conditions


def expected_observations(gate_status: str) -> list[str]:
    observations = [
        "No model or config mutation performed",
        "Dry-run output remains simulation-only",
    ]
    if gate_status == "blocked":
        observations.append("Dry run halts at blocked-gate checkpoint")
    elif gate_status == "conditionally_eligible":
        observations.append("Dry run completes with additional pre-application requirements noted")
    else:
        observations.append("Dry run completes as eligible simulation record only")
    return observations


def dry_run_readiness_and_blocking(gate_status: str) -> tuple[str, str]:
    if gate_status == "blocked":
        return "blocked", "gate_status_blocked"
    if gate_status == "conditionally_eligible":
        return "blocked", "conditionally_eligible_requires_manual_review"
    return "blocked", "eligible_record_still_simulation_only"


def required_operator_role(packet_row: dict[str, Any], gate_row: dict[str, Any]) -> str:
    if isinstance(packet_row, dict) and packet_row.get("operator_role_required"):
        return str(packet_row.get("operator_role_required"))
    if isinstance(gate_row, dict) and gate_row.get("required_operator_role"):
        return str(gate_row.get("required_operator_role"))
    return "ops_reviewer"


def build_dry_runs(
    proposals_payload: dict[str, Any],
    approval_ledger_payload: dict[str, Any],
    validation_manifests_payload: dict[str, Any],
    application_gates_payload: dict[str, Any],
    application_packets_payload: dict[str, Any],
    source_paths: dict[str, str],
) -> dict[str, Any]:
    proposals = proposals_payload.get("proposals") if isinstance(proposals_payload.get("proposals"), list) else []
    approval_rows = approval_ledger_payload.get("approval_ledger") if isinstance(approval_ledger_payload.get("approval_ledger"), list) else []
    manifest_rows = validation_manifests_payload.get("validation_manifests") if isinstance(validation_manifests_payload.get("validation_manifests"), list) else []
    gate_rows = application_gates_payload.get("application_gates") if isinstance(application_gates_payload.get("application_gates"), list) else []
    packet_rows = application_packets_payload.get("application_packets") if isinstance(application_packets_payload.get("application_packets"), list) else []

    approval_by_pid = index_by_proposal_id(approval_rows)
    manifest_by_pid = index_by_proposal_id(manifest_rows)
    gates_by_pid = index_by_proposal_id(gate_rows)
    packets_by_pid = index_by_proposal_id(packet_rows)

    dry_runs: list[dict[str, Any]] = []

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

        gate_status = str(gate_row.get("application_gate_status") or "blocked")
        packet_status = str(packet_row.get("packet_status") or "draft")
        packet_id = packet_row.get("packet_id")

        readiness, blocking = dry_run_readiness_and_blocking(gate_status)

        dry_runs.append(
            {
                "dry_run_id": f"dry-run-{idx:03d}",
                "proposal_id": proposal_id,
                "packet_id": packet_id,
                "proposal_family": proposal_family,
                "adjustment_target": adjustment_target,
                "application_gate_status": gate_status,
                "packet_status": packet_status,
                "dry_run_status": "planned",
                "execution_mode": "simulation_only",
                "ordered_dry_run_steps": ordered_dry_run_steps(gate_status),
                "checkpoint_sequence": checkpoint_sequence(gate_status),
                "required_preconditions": required_preconditions(gate_status),
                "abort_conditions": abort_conditions(gate_status),
                "expected_observations": expected_observations(gate_status),
                "required_operator_role": required_operator_role(packet_row, gate_row),
                "dry_run_readiness": readiness,
                "blocking_reason": blocking,
                "source_paths": {
                    "controlled_model_adjustment_proposals_json": source_paths["controlled_model_adjustment_proposals_json"],
                    "model_adjustment_approval_ledger_json": source_paths["model_adjustment_approval_ledger_json"],
                    "model_adjustment_validation_manifests_json": source_paths["model_adjustment_validation_manifests_json"],
                    "model_adjustment_application_gates_json": source_paths["model_adjustment_application_gates_json"],
                    "model_adjustment_application_packets_json": source_paths["model_adjustment_application_packets_json"],
                    "approval_ledger_entry_id": approval_row.get("ledger_item_id"),
                    "validation_manifest_id": manifest_row.get("manifest_id"),
                    "application_gate_id": gate_row.get("gate_id"),
                },
            }
        )

    proposal_ids = [str(x.get("proposal_id") or "") for x in proposals if isinstance(x, dict)]
    dry_run_ids = [str(x.get("proposal_id") or "") for x in dry_runs if isinstance(x, dict)]

    summary = {
        "total_proposals_in_source": len(proposal_ids),
        "total_dry_runs": len(dry_runs),
        "all_proposals_represented_exactly_once": (
            len(proposal_ids) == len(dry_run_ids) == len(set(dry_run_ids))
            and set(proposal_ids) == set(dry_run_ids)
        ),
        "dry_run_status_counts": {"planned": len(dry_runs)},
        "execution_mode_counts": {"simulation_only": len(dry_runs)},
        "dry_run_readiness_counts": {"blocked": len(dry_runs)},
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_application_dry_runs_version": "v2.5-slice-1",
        "source_versions": {
            "controlled_model_adjustment_proposals_version": proposals_payload.get("controlled_model_adjustment_proposals_version"),
            "model_adjustment_approval_ledger_version": approval_ledger_payload.get("model_adjustment_approval_ledger_version"),
            "model_adjustment_validation_manifests_version": validation_manifests_payload.get("model_adjustment_validation_manifests_version"),
            "model_adjustment_application_gates_version": application_gates_payload.get("model_adjustment_application_gates_version"),
            "model_adjustment_application_packets_version": application_packets_payload.get("model_adjustment_application_packets_version"),
        },
        "application_dry_run_summary": summary,
        "application_dry_runs": dry_runs,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("application_dry_run_summary") if isinstance(payload.get("application_dry_run_summary"), dict) else {}
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    rows = payload.get("application_dry_runs") if isinstance(payload.get("application_dry_runs"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Application Dry Runs (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Dry-Run Version: {payload.get('model_adjustment_application_dry_runs_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Dry-Run Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Dry Runs: {summary.get('total_dry_runs')}")
    lines.append(f"- Exact Once Representation: {summary.get('all_proposals_represented_exactly_once')}")
    lines.append(f"- Dry-Run Status Counts: {summary.get('dry_run_status_counts')}")
    lines.append(f"- Execution Mode Counts: {summary.get('execution_mode_counts')}")
    lines.append(f"- Dry-Run Readiness Counts: {summary.get('dry_run_readiness_counts')}")
    lines.append("")
    lines.append("## Dry-Run Records")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(f"- {row.get('dry_run_id')}: {row.get('proposal_id')} -> {row.get('adjustment_target')}")
            lines.append(f"  Packet ID: {row.get('packet_id')}")
            lines.append(f"  Gate Status: {row.get('application_gate_status')}")
            lines.append(f"  Packet Status: {row.get('packet_status')}")
            lines.append(f"  Dry-Run Status: {row.get('dry_run_status')}")
            lines.append(f"  Execution Mode: {row.get('execution_mode')}")
            lines.append(f"  Ordered Steps: {row.get('ordered_dry_run_steps')}")
            lines.append(f"  Checkpoints: {row.get('checkpoint_sequence')}")
            lines.append(f"  Required Preconditions: {row.get('required_preconditions')}")
            lines.append(f"  Abort Conditions: {row.get('abort_conditions')}")
            lines.append(f"  Expected Observations: {row.get('expected_observations')}")
            lines.append(f"  Required Operator Role: {row.get('required_operator_role')}")
            lines.append(f"  Dry-Run Readiness: {row.get('dry_run_readiness')}")
            lines.append(f"  Blocking Reason: {row.get('blocking_reason')}")
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
    output_dir = Path(args.output_dir)

    proposals_payload, proposals_err = safe_read_json(repo_root / proposals_path)
    approval_payload, approval_err = safe_read_json(repo_root / approval_path)
    manifests_payload, manifests_err = safe_read_json(repo_root / manifests_path)
    gates_payload, gates_err = safe_read_json(repo_root / gates_path)
    packets_payload, packets_err = safe_read_json(repo_root / packets_path)

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

    if not all(isinstance(x, dict) for x in [proposals_payload, approval_payload, manifests_payload, gates_payload, packets_payload]):
        print("ERROR: one or more source artifacts are not valid JSON objects", file=sys.stderr)
        return 1

    source_paths = {
        "controlled_model_adjustment_proposals_json": normalize_path(proposals_path),
        "model_adjustment_approval_ledger_json": normalize_path(approval_path),
        "model_adjustment_validation_manifests_json": normalize_path(manifests_path),
        "model_adjustment_application_gates_json": normalize_path(gates_path),
        "model_adjustment_application_packets_json": normalize_path(packets_path),
    }

    payload = build_dry_runs(
        proposals_payload=proposals_payload,
        approval_ledger_payload=approval_payload,
        validation_manifests_payload=manifests_payload,
        application_gates_payload=gates_payload,
        application_packets_payload=packets_payload,
        source_paths=source_paths,
    )

    payload["source_status"] = {
        "controlled_model_adjustment_proposals_json_error": proposals_err,
        "model_adjustment_approval_ledger_json_error": approval_err,
        "model_adjustment_validation_manifests_json_error": manifests_err,
        "model_adjustment_application_gates_json_error": gates_err,
        "model_adjustment_application_packets_json_error": packets_err,
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
        "[STATUS] dry_runs={total} exact_once={exact_once}".format(
            total=((payload.get("application_dry_run_summary") or {}).get("total_dry_runs")),
            exact_once=((payload.get("application_dry_run_summary") or {}).get("all_proposals_represented_exactly_once")),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())