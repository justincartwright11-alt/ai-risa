#!/usr/bin/env python3
"""
AI-RISA v2.1 Adjustment Approval Ledger (slice 1): read-only control-state layer.

Builds an approval ledger from controlled model-adjustment proposals. This script
does not mutate model behavior, proposal files, scheduler logic, or pipeline outputs.
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
OUTPUT_JSON = "model_adjustment_approval_ledger.json"
OUTPUT_MD = "model_adjustment_approval_ledger.md"

PROPOSALS_DEFAULT = Path("ops/model_adjustments/controlled_model_adjustment_proposals.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only approval ledger artifacts for controlled adjustment proposals"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument(
        "--proposals-json",
        default=str(PROPOSALS_DEFAULT),
        help="Controlled model-adjustment proposals JSON path relative to repo root",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Approval ledger output directory relative to repo root",
    )
    return parser.parse_args()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_path(path: Path) -> str:
    return path.as_posix()


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


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


def required_reviewer_role_for_risk(risk_level: str) -> str:
    risk = str(risk_level or "").lower()
    if risk == "high":
        return "ml_lead_and_ops_approver"
    if risk == "medium":
        return "ml_reviewer"
    return "ops_reviewer"


def blocking_reason_default() -> str:
    return "awaiting_explicit_approval_and_validation_completion"


def build_ledger(
    proposals_payload: dict[str, Any],
    proposals_source_path: str,
) -> dict[str, Any]:
    rows = proposals_payload.get("proposals") if isinstance(proposals_payload.get("proposals"), list) else []

    ledger_items: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue

        proposal_id = str(row.get("proposal_id") or "").strip()
        risk_level = str(row.get("risk_level") or "low")
        source_paths = row.get("source_paths") if isinstance(row.get("source_paths"), list) else []
        validation_requirements = (
            row.get("validation_requirements")
            if isinstance(row.get("validation_requirements"), list)
            else []
        )

        ledger_items.append(
            {
                "ledger_item_id": f"ledger-{index:03d}",
                "proposal_id": proposal_id,
                "proposal_family": proposal_family_from_id(proposal_id),
                "adjustment_target": row.get("adjustment_target"),
                "risk_level": risk_level,
                "approval_status": "pending_review",
                "review_outcome": "undecided",
                "required_reviewer_role": required_reviewer_role_for_risk(risk_level),
                "decision_notes": None,
                "decision_timestamp": None,
                "validation_requirements": validation_requirements,
                "application_readiness": "blocked",
                "blocking_reason": blocking_reason_default(),
                "source_paths": {
                    "controlled_model_adjustment_proposals_json": proposals_source_path,
                    "proposal_source_paths": source_paths,
                },
            }
        )

    summary = {
        "total_proposals_in_source": len(rows),
        "total_ledger_items": len(ledger_items),
        "all_proposals_represented_exactly_once": len(rows) == len(ledger_items),
        "approval_status_counts": {
            "pending_review": len(ledger_items),
        },
        "application_readiness_counts": {
            "blocked": len(ledger_items),
        },
    }

    return {
        "generated_at_utc": now_utc_iso(),
        "model_adjustment_approval_ledger_version": "v2.1-slice-1",
        "source_versions": {
            "controlled_model_adjustment_proposals_version": proposals_payload.get(
                "controlled_model_adjustment_proposals_version"
            ),
        },
        "ledger_summary": summary,
        "approval_ledger": ledger_items,
        "source_paths": {
            "controlled_model_adjustment_proposals_json": proposals_source_path,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("ledger_summary") if isinstance(payload.get("ledger_summary"), dict) else {}
    source_versions = payload.get("source_versions") if isinstance(payload.get("source_versions"), dict) else {}
    rows = payload.get("approval_ledger") if isinstance(payload.get("approval_ledger"), list) else []

    lines: list[str] = []
    lines.append("# AI-RISA Model Adjustment Approval Ledger (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append(f"Ledger Version: {payload.get('model_adjustment_approval_ledger_version')}")
    lines.append(f"Source Versions: {source_versions}")
    lines.append("")
    lines.append("## Ledger Summary")
    lines.append(f"- Source Proposals: {summary.get('total_proposals_in_source')}")
    lines.append(f"- Ledger Items: {summary.get('total_ledger_items')}")
    lines.append(
        f"- Exact Once Representation: {summary.get('all_proposals_represented_exactly_once')}"
    )
    lines.append(f"- Approval Status Counts: {summary.get('approval_status_counts')}")
    lines.append(f"- Application Readiness Counts: {summary.get('application_readiness_counts')}")
    lines.append("")
    lines.append("## Approval Ledger Items")

    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- {row.get('ledger_item_id')}: {row.get('proposal_id')} -> {row.get('adjustment_target')}"
            )
            lines.append(f"  Proposal Family: {row.get('proposal_family')}")
            lines.append(f"  Risk Level: {row.get('risk_level')}")
            lines.append(f"  Approval Status: {row.get('approval_status')}")
            lines.append(f"  Review Outcome: {row.get('review_outcome')}")
            lines.append(f"  Required Reviewer Role: {row.get('required_reviewer_role')}")
            lines.append(f"  Decision Notes: {row.get('decision_notes')}")
            lines.append(f"  Decision Timestamp: {row.get('decision_timestamp')}")
            lines.append(f"  Validation Requirements: {row.get('validation_requirements')}")
            lines.append(f"  Application Readiness: {row.get('application_readiness')}")
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
    output_dir = Path(args.output_dir)

    proposals_payload, proposals_err = safe_read_json(repo_root / proposals_path)

    if proposals_err is not None:
        print(f"ERROR: controlled model-adjustment proposals unavailable: {proposals_err}", file=sys.stderr)
        return 1

    if not isinstance(proposals_payload, dict):
        print("ERROR: source proposals artifact is not a valid JSON object", file=sys.stderr)
        return 1

    proposals_source_path = normalize_path(proposals_path)
    payload = build_ledger(
        proposals_payload=proposals_payload,
        proposals_source_path=proposals_source_path,
    )

    payload["source_status"] = {
        "controlled_model_adjustment_proposals_json_error": proposals_err,
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
        "[STATUS] ledger_items={total} exact_once={exact_once}".format(
            total=((payload.get("ledger_summary") or {}).get("total_ledger_items")),
            exact_once=((payload.get("ledger_summary") or {}).get("all_proposals_represented_exactly_once")),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())