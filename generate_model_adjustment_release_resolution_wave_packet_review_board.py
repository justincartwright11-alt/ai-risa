"""
generate_model_adjustment_release_resolution_wave_packet_review_board.py

v5.4-slice-1 — Read-only controlled release resolution-wave-packet-review-board
generator.

Consumes the frozen v5.3 release resolution wave packet checklist output and
emits one deterministic review-board entry per checklist record.

No re-classification logic. No release recommendation logic. No upstream
mutation.
"""

import json
import os
import sys
from datetime import datetime, timezone


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OPS_DIR = os.path.join(SCRIPT_DIR, "ops", "model_adjustments")

SOURCE_PATHS = {
    "model_adjustment_release_resolution_wave_packet_checklist_json": (
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_checklist.json"
    )
}

OUTPUT_JSON = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_wave_packet_review_board.json",
)
OUTPUT_MD = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_wave_packet_review_board.md",
)

VERSION = "v5.4-slice-1"
EXPECTED_CHECKLIST_COUNT = 3

WAVE_TYPE_ORDER = {
    "prohibition_cluster": 0,
    "blocker_cluster": 1,
    "remaining_resolution_cluster": 2,
}

REVIEW_LANE_BY_WAVE_TYPE = {
    "prohibition_cluster": "lane_prohibition_terminal",
    "blocker_cluster": "lane_blocker_terminal",
    "remaining_resolution_cluster": "lane_remaining_terminal",
}

REQUIRED_CHECKLIST_FIELDS = (
    "resolution_wave_packet_checklist_id",
    "source_resolution_wave_packet_id",
    "source_resolution_wave_id",
    "wave_rank",
    "wave_type",
    "packet_priority",
    "checklist_priority",
    "member_cluster_ids",
    "member_dependency_ids",
    "member_source_refs",
    "affected_proposal_ids",
    "affected_queue_ids",
    "affected_record_count",
    "cluster_count",
    "dependency_count",
    "has_prohibition_path",
    "has_blocker_path",
    "terminal_posture",
)


def abs_path(rel_path: str) -> str:
    return os.path.join(SCRIPT_DIR, rel_path.replace("/", os.sep))


def load_json(rel_path: str):
    with open(abs_path(rel_path), "r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def load_source(source_key: str):
    rel_path = SOURCE_PATHS[source_key]
    try:
        return load_json(rel_path), None
    except Exception as exc:
        return None, str(exc)


def dedup_sorted(values) -> list:
    return sorted(set(str(value) for value in (values or []) if value))


def validate_checklist_record(record: dict, index: int) -> None:
    for field in REQUIRED_CHECKLIST_FIELDS:
        if field not in record:
            raise ValueError(
                f"checklist record[{index}] missing required field {field!r}; "
                "fail-closed — manual review required"
            )

    checklist_id = record.get("resolution_wave_packet_checklist_id", "")
    if not checklist_id:
        raise ValueError(
            f"checklist record[{index}] has empty resolution_wave_packet_checklist_id; "
            "fail-closed — manual review required"
        )

    wave_type = record.get("wave_type", "")
    if wave_type not in WAVE_TYPE_ORDER:
        raise ValueError(
            f"checklist record[{index}] has unknown wave_type={wave_type!r}; "
            "fail-closed — manual review required"
        )


def sorted_checklist_records(records: list) -> list:
    return sorted(
        records,
        key=lambda record: (
            WAVE_TYPE_ORDER[record.get("wave_type", "remaining_resolution_cluster")],
            record.get("source_resolution_wave_packet_id", ""),
            record.get("resolution_wave_packet_checklist_id", ""),
        ),
    )


def build_review_board_records(records: list) -> list:
    output = []

    for index, record in enumerate(sorted_checklist_records(records), start=1):
        validate_checklist_record(record, index)

        output.append(
            {
                "resolution_wave_packet_review_board_id": (
                    f"resolution-wave-packet-review-board-{index:04d}"
                ),
                "source_resolution_wave_packet_checklist_id": record[
                    "resolution_wave_packet_checklist_id"
                ],
                "source_resolution_wave_packet_id": record[
                    "source_resolution_wave_packet_id"
                ],
                "source_resolution_wave_id": record["source_resolution_wave_id"],
                "wave_rank": int(record.get("wave_rank", 0)),
                "wave_type": record["wave_type"],
                "packet_priority": record.get("packet_priority", ""),
                "checklist_priority": record.get("checklist_priority", ""),
                "review_board_priority": record.get("checklist_priority", ""),
                "review_lane": REVIEW_LANE_BY_WAVE_TYPE[record["wave_type"]],
                "member_cluster_ids": dedup_sorted(record.get("member_cluster_ids", [])),
                "member_dependency_ids": dedup_sorted(
                    record.get("member_dependency_ids", [])
                ),
                "member_source_refs": dedup_sorted(record.get("member_source_refs", [])),
                "affected_proposal_ids": dedup_sorted(
                    record.get("affected_proposal_ids", [])
                ),
                "affected_queue_ids": dedup_sorted(record.get("affected_queue_ids", [])),
                "affected_record_count": int(record.get("affected_record_count", 0)),
                "cluster_count": int(record.get("cluster_count", 0)),
                "dependency_count": int(record.get("dependency_count", 0)),
                "has_prohibition_path": bool(record.get("has_prohibition_path", False)),
                "has_blocker_path": bool(record.get("has_blocker_path", False)),
                "terminal_posture": record.get("terminal_posture", ""),
                "review_board_notes": (
                    "v5_4_read_only_review_board_projection_of_v5_3_checklist"
                    "_no_reclassification_no_release_recommendation_no_upstream_mutation"
                ),
                "upstream_source": SOURCE_PATHS[
                    "model_adjustment_release_resolution_wave_packet_checklist_json"
                ],
            }
        )

    return output


def validate_review_board(records: list, checklist_records: list) -> None:
    board_ids = [record["resolution_wave_packet_review_board_id"] for record in records]
    if len(board_ids) != len(set(board_ids)):
        raise ValueError("duplicate resolution_wave_packet_review_board_id in output; fail-closed")

    source_checklist_ids = [
        record["source_resolution_wave_packet_checklist_id"] for record in records
    ]
    if len(source_checklist_ids) != len(set(source_checklist_ids)):
        raise ValueError(
            "duplicate source_resolution_wave_packet_checklist_id in review board; fail-closed"
        )

    upstream_checklist_ids = [
        record.get("resolution_wave_packet_checklist_id", "")
        for record in checklist_records
    ]
    if len(upstream_checklist_ids) != EXPECTED_CHECKLIST_COUNT:
        raise ValueError(
            f"upstream checklist count {len(upstream_checklist_ids)} does not match "
            f"EXPECTED_CHECKLIST_COUNT={EXPECTED_CHECKLIST_COUNT}; fail-closed"
        )

    if set(source_checklist_ids) != set(upstream_checklist_ids):
        raise ValueError(
            "review board coverage does not match upstream checklist records; fail-closed"
        )

    for record in records:
        for field in (
            "member_cluster_ids",
            "member_dependency_ids",
            "member_source_refs",
            "affected_proposal_ids",
            "affected_queue_ids",
        ):
            values = record.get(field, [])
            if len(values) != len(set(values)):
                raise ValueError(
                    f"duplicate values in {field!r} for "
                    f"{record['resolution_wave_packet_review_board_id']}; fail-closed"
                )


def build_summary(records: list, checklist_records: list) -> dict:
    review_type_counts = {
        wave_type: sum(1 for record in records if record.get("wave_type") == wave_type)
        for wave_type in (
            "prohibition_cluster",
            "blocker_cluster",
            "remaining_resolution_cluster",
        )
    }

    return {
        "upstream_checklist_count": len(checklist_records),
        "total_review_board_records": len(records),
        "review_wave_type_counts": review_type_counts,
        "coverage_reconciled": True,
        "deterministic_ordering": True,
    }


def build_source_versions(source_data: dict) -> dict:
    return {
        "model_adjustment_release_resolution_wave_packet_checklist_version": source_data.get(
            "model_adjustment_release_resolution_wave_packet_checklist_version", ""
        )
    }


def write_markdown(records: list, summary: dict, source_versions: dict, generated_at: str):
    lines = [
        "# Model Adjustment Release Resolution Wave Packet Review Board",
        "",
        f"**Version**: {VERSION}",
        f"**Generated At (UTC)**: {generated_at}",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "|---|---|",
    ]

    for key, value in summary.items():
        lines.append(f"| {key} | {value} |")

    lines.extend(["", "## Source Versions", "", "| Source | Version |", "|---|---|"])
    for key, value in source_versions.items():
        lines.append(f"| {key} | {value} |")

    lines.append("")
    for record in records:
        lines.append(f"## {record['resolution_wave_packet_review_board_id']}")
        lines.append("")
        lines.append(
            f"- source_resolution_wave_packet_checklist_id: {record['source_resolution_wave_packet_checklist_id']}"
        )
        lines.append(
            f"- source_resolution_wave_packet_id: {record['source_resolution_wave_packet_id']}"
        )
        lines.append(f"- source_resolution_wave_id: {record['source_resolution_wave_id']}")
        lines.append(f"- wave_rank: {record['wave_rank']}")
        lines.append(f"- wave_type: {record['wave_type']}")
        lines.append(f"- packet_priority: {record['packet_priority']}")
        lines.append(f"- checklist_priority: {record['checklist_priority']}")
        lines.append(f"- review_board_priority: {record['review_board_priority']}")
        lines.append(f"- review_lane: {record['review_lane']}")
        lines.append(f"- affected_record_count: {record['affected_record_count']}")
        lines.append(f"- cluster_count: {record['cluster_count']}")
        lines.append(f"- dependency_count: {record['dependency_count']}")
        lines.append(f"- has_prohibition_path: {record['has_prohibition_path']}")
        lines.append(f"- has_blocker_path: {record['has_blocker_path']}")
        lines.append(f"- terminal_posture: {record['terminal_posture']}")
        lines.append("")

        for section in (
            "member_cluster_ids",
            "member_dependency_ids",
            "member_source_refs",
            "affected_proposal_ids",
            "affected_queue_ids",
        ):
            lines.append(f"### {section}")
            lines.append("")
            values = record.get(section, [])
            if values:
                for value in values:
                    lines.append(f"- {value}")
            else:
                lines.append("- none")
            lines.append("")

        lines.append("---")
        lines.append("")

    with open(OUTPUT_MD, "w", encoding="utf-8") as file_handle:
        file_handle.write("\n".join(lines))


def main():
    errors = {}

    source_data, errors["model_adjustment_release_resolution_wave_packet_checklist_json"] = load_source(
        "model_adjustment_release_resolution_wave_packet_checklist_json"
    )

    failures = [key for key, value in errors.items() if value is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    checklist_records = source_data.get("release_resolution_wave_packet_checklist", [])
    records = build_review_board_records(checklist_records)
    validate_review_board(records, checklist_records)
    summary = build_summary(records, checklist_records)
    source_versions = build_source_versions(source_data)
    source_status = {f"{key}_error": errors[key] for key in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_resolution_wave_packet_review_board_version": VERSION,
        "release_resolution_wave_packet_review_board_summary": summary,
        "release_resolution_wave_packet_review_board": records,
        "source_paths": SOURCE_PATHS,
        "source_status": source_status,
        "source_versions": source_versions,
    }

    os.makedirs(OPS_DIR, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, indent=2)
    print(f"[WRITE] {OUTPUT_JSON}")

    write_markdown(records, summary, source_versions, generated_at)
    print(f"[WRITE] {OUTPUT_MD}")

    print(
        "[STATUS] "
        f"review_board_records={summary['total_review_board_records']} "
        f"upstream_checklist_count={summary['upstream_checklist_count']} "
        f"coverage_reconciled={summary['coverage_reconciled']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"review_wave_type_counts={summary['review_wave_type_counts']}"
    )


if __name__ == "__main__":
    main()