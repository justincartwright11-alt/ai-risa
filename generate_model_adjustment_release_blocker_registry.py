#!/usr/bin/env python3
"""
AI-RISA v4.1 Controlled Release Blocker Registry (slice 1): read-only governance layer.

Builds a canonical release blocker registry by consolidating active blockers across
release conditions, release authority, release gate assessments, release decisions,
release ineligibility decisions, and release prohibition matrix.

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
OUTPUT_JSON = "model_adjustment_release_blocker_registry.json"
OUTPUT_MD = "model_adjustment_release_blocker_registry.md"

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
RELEASE_PROHIBITION_MATRIX_DEFAULT = Path(
    "ops/model_adjustments/model_adjustment_release_prohibition_matrix.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only controlled release blocker registry artifacts"
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
        "--release-prohibition-matrix-json",
        default=str(RELEASE_PROHIBITION_MATRIX_DEFAULT),
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
        proposal_id = str(row.get("proposal_id") or "").strip()
        if proposal_id:
            indexed[proposal_id] = row
    return indexed


def classify_blocker_category(
    authority_availability: str,
    release_gate_state: str,
    release_decision_state: str,
    release_ineligibility_class: str,
) -> str:
    if authority_availability in {"absent", "expired", "structurally_unavailable"}:
        return "release_authority_unavailable"
    if release_gate_state in {"blocked", "closed", "structurally_unavailable"}:
        return "release_gate_blocked"
    if release_decision_state in {"release_denied", "release_not_eligible", "structurally_unreleasable"}:
        return "release_decision_blocked"
    if release_ineligibility_class:
        return f"release_ineligibility_{release_ineligibility_class}"
    return "release_governance_blocked"


def build_release_blocker_registry(
    release_conditions_payload: dict[str, Any],
    release_authority_payload: dict[str, Any],
    release_gate_payload: dict[str, Any],
    release_decisions_payload: dict[str, Any],
    release_ineligibility_payload: dict[str, Any],
    release_prohibition_payload: dict[str, Any],
    source_paths: dict[str, str],
) -> dict[str, Any]:
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
    release_prohibition_rows = (
        release_prohibition_payload.get("release_prohibition_matrix")
        if isinstance(release_prohibition_payload.get("release_prohibition_matrix"), list)
        else []
    )

    release_conditions_by_pid = index_by_proposal_id(release_condition_rows)
    release_authority_by_pid = index_by_proposal_id(release_authority_rows)
    release_gate_by_pid = index_by_proposal_id(release_gate_rows)
    release_decision_by_pid = index_by_proposal_id(release_decision_rows)
    release_ineligibility_by_pid = index_by_proposal_id(release_ineligibility_rows)
    release_prohibition_by_pid = index_by_proposal_id(release_prohibition_rows)

    proposal_ids = sorted(
        {
            str(r.get("proposal_id") or "").strip()
            for r in release_ineligibility_rows
            if isinstance(r, dict) and str(r.get("proposal_id") or "").strip()
        }
    )

    records: list[dict[str, Any]] = []
    state_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}

    for seq, proposal_id in enumerate(proposal_ids, start=1):
        release_condition_row = release_conditions_by_pid.get(proposal_id, {})
        release_authority_row = release_authority_by_pid.get(proposal_id, {})
        release_gate_row = release_gate_by_pid.get(proposal_id, {})
        release_decision_row = release_decision_by_pid.get(proposal_id, {})
        release_ineligibility_row = release_ineligibility_by_pid.get(proposal_id, {})
        release_prohibition_row = release_prohibition_by_pid.get(proposal_id, {})

        release_blocker_state = "active"
        release_blocker_source = "|".join(
            [
                "execution_release_conditions",
                "execution_release_authority",
                "execution_release_gate_assessments",
                "execution_release_decisions",
                "release_ineligibility_decisions",
                "release_prohibition_matrix",
            ]
        )

        release_blocker_category = classify_blocker_category(
            authority_availability=str(
                release_authority_row.get("authority_availability") or "structurally_unavailable"
            ),
            release_gate_state=str(release_gate_row.get("release_gate_state") or "blocked"),
            release_decision_state=str(
                release_decision_row.get("release_decision_state") or "release_denied"
            ),
            release_ineligibility_class=str(
                release_ineligibility_row.get("release_ineligibility_class") or ""
            ),
        )

        blocking_parts: list[str] = []
        blocking_parts.extend(
            [str(x) for x in (release_condition_row.get("release_blockers") or []) if str(x).strip()]
        )
        blocking_parts.extend(
            [str(x) for x in (release_authority_row.get("authority_blockers") or []) if str(x).strip()]
        )
        blocking_parts.extend(
            [str(x) for x in (release_gate_row.get("gate_blockers") or []) if str(x).strip()]
        )
        blocking_parts.extend(
            [
                str(x)
                for x in (release_decision_row.get("release_decision_blockers") or [])
                if str(x).strip()
            ]
        )
        blocking_parts.extend(
            [
                str(x)
                for x in (release_ineligibility_row.get("release_ineligibility_blockers") or [])
                if str(x).strip()
            ]
        )
        blocking_parts.append(
            f"release_prohibition_state:{release_prohibition_row.get('release_prohibition_state') or 'prohibited'}"
        )

        deduped_blocking = sorted({x for x in blocking_parts if x})
        blocking_condition = " | ".join(deduped_blocking)

        required_resolution = str(
            release_ineligibility_row.get("required_resolution_path")
            or "resolve_release_condition_authority_gate_decision_and_prohibition_blockers"
        )

        required_operator_role = str(
            release_prohibition_row.get("required_operator_role")
            or release_ineligibility_row.get("required_operator_role")
            or release_decision_row.get("required_operator_role")
            or release_gate_row.get("required_operator_role")
            or release_authority_row.get("required_operator_role")
            or release_condition_row.get("required_operator_role")
            or "ops_reviewer"
        )

        rollback_reference = str(
            release_prohibition_row.get("rollback_reference")
            or release_ineligibility_row.get("rollback_reference")
            or release_decision_row.get("rollback_reference")
            or release_gate_row.get("rollback_reference")
            or release_authority_row.get("rollback_reference")
            or release_condition_row.get("rollback_reference")
            or f"rollback-from-{proposal_id}"
        )

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
            "model_adjustment_release_prohibition_matrix_json": source_paths[
                "model_adjustment_release_prohibition_matrix_json"
            ],
            "release_blocker_components": deduped_blocking,
        }

        records.append(
            {
                "release_blocker_id": f"release-blocker-{seq:04d}",
                "proposal_id": proposal_id,
                "release_condition_id": release_condition_row.get("release_condition_id"),
                "release_authority_id": release_authority_row.get("release_authority_id"),
                "release_gate_id": release_gate_row.get("release_gate_id"),
                "release_decision_id": release_decision_row.get("release_decision_id"),
                "release_ineligibility_decision_id": release_ineligibility_row.get(
                    "release_ineligibility_decision_id"
                ),
                "release_prohibition_id": release_prohibition_row.get("release_prohibition_id"),
                "release_blocker_state": release_blocker_state,
                "release_blocker_category": release_blocker_category,
                "release_blocker_source": release_blocker_source,
                "blocking_condition": blocking_condition,
                "required_resolution": required_resolution,
                "required_operator_role": required_operator_role,
                "rollback_reference": rollback_reference,
                "release_blocker_notes": (
                    "v4_1_governance_only_release_blockers_remain_active_no_execution_or_model_mutation"
                ),
                "source_paths": record_source_paths,
            }
        )

        state_counts[release_blocker_state] = state_counts.get(release_blocker_state, 0) + 1
        category_counts[release_blocker_category] = category_counts.get(
            release_blocker_category, 0
        ) + 1

    summary = {
        "total_proposals_in_source": len(proposal_ids),
        "total_release_blocker_records": len(records),
        "proposals_covered": len(
            {
                str(r.get("proposal_id") or "")
                for r in records
                if str(r.get("proposal_id") or "").strip()
            }
        ),
        "all_proposals_covered": len(records) == len(proposal_ids),
        "record_count_matches_expected": len(records) == len(proposal_ids),
        "release_blocker_state_counts": state_counts,
        "release_blocker_category_counts": category_counts,
        "deterministic_ordering": proposal_ids
        == sorted(
            [str(r.get("proposal_id") or "") for r in records if str(r.get("proposal_id") or "").strip()]
        ),
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_release_blocker_registry_version": "v4.1-slice-1",
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
            "model_adjustment_release_prohibition_matrix_version": release_prohibition_payload.get(
                "model_adjustment_release_prohibition_matrix_version"
            ),
        },
        "release_blocker_registry_summary": summary,
        "release_blocker_registry": records,
        "source_paths": source_paths,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("release_blocker_registry_summary") or {}
    rows = payload.get("release_blocker_registry") or []

    lines: list[str] = []
    lines.append("# AI-RISA Controlled Release Blocker Registry (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(
        "Release Blocker Registry Version: "
        f"{payload.get('model_adjustment_release_blocker_registry_version')}"
    )
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Total Blocker Records: {summary.get('total_release_blocker_records')}")
    lines.append(f"- Proposals Covered: {summary.get('proposals_covered')}")
    lines.append(f"- All Proposals Covered: {summary.get('all_proposals_covered')}")
    lines.append(f"- Record Count Matches Expected: {summary.get('record_count_matches_expected')}")
    lines.append(f"- Deterministic Ordering: {summary.get('deterministic_ordering')}")
    lines.append(f"- Release Blocker State Counts: {summary.get('release_blocker_state_counts')}")
    lines.append(
        f"- Release Blocker Category Counts: {summary.get('release_blocker_category_counts')}"
    )
    lines.append("")
    lines.append("## Release Blocker Records")

    if rows:
        for row in rows:
            lines.append(
                f"- {row.get('release_blocker_id')}: {row.get('proposal_id')} | "
                f"condition={row.get('release_condition_id')} | authority={row.get('release_authority_id')} | "
                f"gate={row.get('release_gate_id')} | decision={row.get('release_decision_id')} | "
                f"ineligibility={row.get('release_ineligibility_decision_id')} | "
                f"prohibition={row.get('release_prohibition_id')}"
            )
            lines.append(
                f"  state={row.get('release_blocker_state')} | "
                f"category={row.get('release_blocker_category')}"
            )
            lines.append(f"  source={row.get('release_blocker_source')}")
            lines.append(f"  blocking_condition={row.get('blocking_condition')}")
            lines.append(f"  required_resolution={row.get('required_resolution')}")
            lines.append(f"  required_operator_role={row.get('required_operator_role')}")
            lines.append(f"  rollback_reference={row.get('rollback_reference')}")
            lines.append(f"  notes={row.get('release_blocker_notes')}")
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
    release_prohibition_path = Path(args.release_prohibition_matrix_json)
    output_dir = Path(args.output_dir)

    release_conditions_payload, release_conditions_err = safe_read_json(repo_root / release_conditions_path)
    release_authority_payload, release_authority_err = safe_read_json(repo_root / release_authority_path)
    release_gate_payload, release_gate_err = safe_read_json(repo_root / release_gate_path)
    release_decisions_payload, release_decisions_err = safe_read_json(repo_root / release_decisions_path)
    release_ineligibility_payload, release_ineligibility_err = safe_read_json(
        repo_root / release_ineligibility_path
    )
    release_prohibition_payload, release_prohibition_err = safe_read_json(
        repo_root / release_prohibition_path
    )

    errors = [
        ("model-adjustment execution release conditions", release_conditions_err),
        ("model-adjustment execution release authority", release_authority_err),
        ("model-adjustment execution release gate assessments", release_gate_err),
        ("model-adjustment execution release decisions", release_decisions_err),
        ("model-adjustment release ineligibility decisions", release_ineligibility_err),
        ("model-adjustment release prohibition matrix", release_prohibition_err),
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
        release_prohibition_payload,
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
        "model_adjustment_release_prohibition_matrix_json": normalize_path(release_prohibition_path),
    }

    payload = build_release_blocker_registry(
        release_conditions_payload=release_conditions_payload,
        release_authority_payload=release_authority_payload,
        release_gate_payload=release_gate_payload,
        release_decisions_payload=release_decisions_payload,
        release_ineligibility_payload=release_ineligibility_payload,
        release_prohibition_payload=release_prohibition_payload,
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
            ("model_adjustment_release_prohibition_matrix_json", release_prohibition_err),
        ]
    }

    out_root = repo_root / output_dir
    out_root.mkdir(parents=True, exist_ok=True)

    out_json = out_root / OUTPUT_JSON
    out_md = out_root / OUTPUT_MD

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    out_md.write_text(render_markdown(payload), encoding="utf-8")

    summary = payload.get("release_blocker_registry_summary") or {}
    print(f"[WRITE] {out_json}")
    print(f"[WRITE] {out_md}")
    print(
        "[STATUS] release_blockers={total} proposals_covered={covered} all_covered={all_covered} "
        "record_count_matches_expected={match} deterministic_ordering={ordered} "
        "release_blocker_state={state}".format(
            total=summary.get("total_release_blocker_records"),
            covered=summary.get("proposals_covered"),
            all_covered=summary.get("all_proposals_covered"),
            match=summary.get("record_count_matches_expected"),
            ordered=summary.get("deterministic_ordering"),
            state=summary.get("release_blocker_state_counts"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())