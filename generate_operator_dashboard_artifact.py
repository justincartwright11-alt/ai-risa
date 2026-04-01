#!/usr/bin/env python3
"""
AI-RISA v1.4 Operator Dashboard (slice 1): read-only dashboard artifact generator.

Generates a minimal operator-facing dashboard from existing summary outputs only.
This script does not execute pipeline stages or mutate canonical pipeline schemas.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")

OUTPUT_DIR = Path("ops/dashboard")
OUTPUT_JSON = "operator_dashboard.json"
OUTPUT_MD = "operator_dashboard.md"

FULL_SUMMARY = Path("output/full_pipeline_run_summary.json")
BATCH_SUMMARY = Path("output/event_batch_run_summary.json")
BATCH_DRY_RUN_SUMMARY = Path("output/dry_run/event_batch_run_summary.json")
QUEUE_SUMMARY = Path("output/prediction_queue_run_summary.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only operator dashboard artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Output directory relative to repo root",
    )
    return parser.parse_args()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_path(path: Path) -> str:
    return path.as_posix()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def safe_read_json(path: Path) -> tuple[Any, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return load_json(path), None
    except Exception as exc:
        return None, f"unreadable: {exc}"


def file_meta(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": normalize_path(path),
            "exists": False,
            "last_modified_utc": None,
        }
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    return {
        "path": normalize_path(path),
        "exists": True,
        "last_modified_utc": mtime,
    }


def extract_recommended_action(markdown: str | None) -> str | None:
    if not markdown:
        return None

    lines = markdown.splitlines()
    in_section = False
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            in_section = line.lower().startswith("# recommended operator action")
            continue
        if in_section and line.startswith("-"):
            return line[1:].strip()
    return None


def collect_source_summaries(repo_root: Path) -> list[dict[str, Any]]:
    candidates = [
        ("full_pipeline", FULL_SUMMARY),
        ("event_batch", BATCH_SUMMARY),
        ("event_batch_dry_run", BATCH_DRY_RUN_SUMMARY),
        ("prediction_queue_run", QUEUE_SUMMARY),
    ]

    out: list[dict[str, Any]] = []
    for label, rel_path in candidates:
        abs_path = repo_root / rel_path
        summary, error = safe_read_json(abs_path)
        entry = {
            "label": label,
            **file_meta(rel_path),
            "read_error": error,
            "stage": summary.get("stage") if isinstance(summary, dict) else None,
            "status": summary.get("status") if isinstance(summary, dict) else None,
            "started_at": summary.get("started_at") if isinstance(summary, dict) else None,
            "finished_at": summary.get("finished_at") if isinstance(summary, dict) else None,
        }
        out.append(entry)

    return out


def pick_primary(full_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(full_summary, dict):
        return {
            "status": "unknown",
            "summary_available": False,
            "message": "Full pipeline summary is missing or unreadable.",
        }

    counts = full_summary.get("counts") if isinstance(full_summary.get("counts"), dict) else {}
    warnings = full_summary.get("warnings") if isinstance(full_summary.get("warnings"), list) else []
    errors = full_summary.get("errors") if isinstance(full_summary.get("errors"), list) else []

    return {
        "summary_available": True,
        "stage": full_summary.get("stage"),
        "status": full_summary.get("status"),
        "started_at": full_summary.get("started_at"),
        "finished_at": full_summary.get("finished_at"),
        "counts": counts,
        "warnings_count": len(warnings),
        "errors_count": len(errors),
    }


def pick_reporting_block(
    full_summary: dict[str, Any] | None,
    batch_dry_run_summary: dict[str, Any] | None,
) -> tuple[dict[str, Any], str]:
    def details_of(summary: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(summary, dict):
            return {}
        details = summary.get("details")
        return details if isinstance(details, dict) else {}

    full_details = details_of(full_summary)
    batch_details = details_of(batch_dry_run_summary)

    if full_details.get("analysis_coverage"):
        return full_details, normalize_path(FULL_SUMMARY)
    if batch_details.get("analysis_coverage"):
        return batch_details, normalize_path(BATCH_DRY_RUN_SUMMARY)

    return {}, "none"


def build_dashboard_payload(repo_root: Path) -> dict[str, Any]:
    full_summary, _ = safe_read_json(repo_root / FULL_SUMMARY)
    batch_dry_run_summary, _ = safe_read_json(repo_root / BATCH_DRY_RUN_SUMMARY)

    source_summaries = collect_source_summaries(repo_root)
    latest_pipeline_snapshot = pick_primary(full_summary if isinstance(full_summary, dict) else None)

    details, details_source = pick_reporting_block(
        full_summary if isinstance(full_summary, dict) else None,
        batch_dry_run_summary if isinstance(batch_dry_run_summary, dict) else None,
    )

    coverage = details.get("analysis_coverage") if isinstance(details.get("analysis_coverage"), dict) else {}
    skipped = (
        details.get("skipped_items_exclusions")
        if isinstance(details.get("skipped_items_exclusions"), dict)
        else {}
    )
    interpretation = (
        details.get("operator_interpretation")
        if isinstance(details.get("operator_interpretation"), dict)
        else {}
    )
    warning_readability = (
        details.get("warning_readability")
        if isinstance(details.get("warning_readability"), dict)
        else {}
    )

    recommended_action = extract_recommended_action(
        details.get("human_readable_summary_markdown")
        if isinstance(details.get("human_readable_summary_markdown"), str)
        else None
    )

    if not recommended_action:
        if latest_pipeline_snapshot.get("status") == "success":
            recommended_action = (
                "Proceed with outputs while monitoring warning trends and documented exclusions."
            )
        else:
            recommended_action = (
                "Inspect failed stages and latest summary details before proceeding."
            )

    payload: dict[str, Any] = {
        "generated_at_utc": now_utc_iso(),
        "dashboard_version": "v1.4-slice-1",
        "latest_pipeline_snapshot": {
            **latest_pipeline_snapshot,
            "source_summary_path": normalize_path(FULL_SUMMARY),
        },
        "coverage_snapshot": {
            "source": details_source,
            "analysis_coverage": coverage,
        },
        "skipped_exclusions_snapshot": {
            "source": details_source,
            "skipped_items_exclusions": skipped,
        },
        "warning_interpretation_snapshot": {
            "source": details_source,
            "operator_interpretation": interpretation,
            "warning_readability": warning_readability,
        },
        "recommended_operator_action": {
            "action": recommended_action,
            "source": details_source,
        },
        "source_summaries": source_summaries,
    }

    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    latest = payload.get("latest_pipeline_snapshot", {})
    coverage = payload.get("coverage_snapshot", {})
    skipped = payload.get("skipped_exclusions_snapshot", {})
    warn = payload.get("warning_interpretation_snapshot", {})
    action = payload.get("recommended_operator_action", {})
    sources = payload.get("source_summaries", [])

    analysis_coverage = coverage.get("analysis_coverage", {})
    skipped_items = skipped.get("skipped_items_exclusions", {})
    operator_interp = warn.get("operator_interpretation", {})
    warning_readability = warn.get("warning_readability", {})

    lines = [
        "# AI-RISA Operator Dashboard (Slice 1)",
        "",
        f"Generated (UTC): {payload.get('generated_at_utc')}",
        "",
        "## Latest Pipeline Snapshot",
        f"- Status: {latest.get('status')}",
        f"- Stage: {latest.get('stage')}",
        f"- Started At: {latest.get('started_at')}",
        f"- Finished At: {latest.get('finished_at')}",
        f"- Warnings: {latest.get('warnings_count')}",
        f"- Errors: {latest.get('errors_count')}",
        f"- Summary Path: {latest.get('source_summary_path')}",
        "",
        "## Coverage Snapshot",
        f"- Source: {coverage.get('source')}",
        f"- Analysis Coverage: {analysis_coverage}",
        "",
        "## Skipped/Exclusions Snapshot",
        f"- Source: {skipped.get('source')}",
        f"- Skipped/Exclusions: {skipped_items}",
        "",
        "## Warning Interpretation Snapshot",
        f"- Source: {warn.get('source')}",
        f"- Operator Interpretation: {operator_interp}",
        f"- Warning Readability: {warning_readability}",
        "",
        "## Recommended Operator Action",
        f"- {action.get('action')}",
        "",
        "## Source Summaries",
    ]

    if isinstance(sources, list) and sources:
        for row in sources:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- {label}: path={path} exists={exists} status={status} stage={stage} finished_at={finished_at}".format(
                    label=row.get("label"),
                    path=row.get("path"),
                    exists=row.get("exists"),
                    status=row.get("status"),
                    stage=row.get("stage"),
                    finished_at=row.get("finished_at"),
                )
            )
    else:
        lines.append("- None")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)

    if not repo_root.exists():
        print(f"ERROR: repo root not found: {repo_root}", file=sys.stderr)
        return 1

    payload = build_dashboard_payload(repo_root)

    out_dir = repo_root / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    out_json = out_dir / OUTPUT_JSON
    out_md = out_dir / OUTPUT_MD

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    out_md.write_text(render_markdown(payload), encoding="utf-8")

    print(f"[WRITE] {out_json}")
    print(f"[WRITE] {out_md}")
    print(
        "[STATUS] pipeline_status={status} coverage_source={source}".format(
            status=payload.get("latest_pipeline_snapshot", {}).get("status"),
            source=payload.get("coverage_snapshot", {}).get("source"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
