"""
generate_model_adjustment_release_resolution_wave_packet_review_session_handoff.py

v5.9-slice-1 — Read-only controlled release resolution-wave-packet-review-session-handoff
generator.

Consumes the frozen v5.8 release resolution wave packet review session brief output
and emits one deterministic handoff entry per brief record.

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
    "model_adjustment_release_resolution_wave_packet_review_session_brief_json": (
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_brief.json"
    )
}

OUTPUT_JSON = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_wave_packet_review_session_handoff.json",
)
OUTPUT_MD = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_wave_packet_review_session_handoff.md",
)

VERSION = "v5.9-slice-1"
EXPECTED_REVIEW_SESSION_BRIEF_COUNT = 3

REVIEW_LANE_ORDER = {
    "lane_prohibition_terminal": 0,
    "lane_blocker_terminal": 1,
    "lane_remaining_terminal": 2,
}

REQUIRED_SESSION_BRIEF_FIELDS = (
    "resolution_wave_packet_review_session_brief_id",
    "source_resolution_wave_packet_review_session_pack_id",
    "source_resolution_wave_packet_review_agenda_id",
    "source_resolution_wave_packet_review_docket_id",
    "source_resolution_wave_packet_review_board_id",
    "source_resolution_wave_packet_checklist_id",
    "source_resolution_wave_packet_id",
    "source_resolution_wave_id",
    "wave_rank",
    "wave_type",
    "packet_priority",
    "checklist_priority",
    "review_board_priority",
    "review_docket_priority",
    "review_agenda_priority",
    "review_session_pack_priority",
    "review_session_brief_priority",
    "review_lane",
    "brief_position",
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

REQUIRED_NON_EMPTY_STRING_FIELDS = (
    "resolution_wave_packet_review_session_brief_id",
    "source_resolution_wave_packet_review_session_pack_id",
    "source_resolution_wave_packet_review_agenda_id",
    "source_resolution_wave_packet_review_docket_id",
    "source_resolution_wave_packet_review_board_id",
    "source_resolution_wave_packet_checklist_id",
    "source_resolution_wave_packet_id",
    "source_resolution_wave_id",
    "wave_type",
    "packet_priority",
    "checklist_priority",
    "review_board_priority",
    "review_docket_priority",
    "review_agenda_priority",
    "review_session_pack_priority",
    "review_session_brief_priority",
    "review_lane",
    "terminal_posture",
)

REQUIRED_LIST_FIELDS = (
    "member_cluster_ids",
    "member_dependency_ids",
    "member_source_refs",
    "affected_proposal_ids",
    "affected_queue_ids",
)

REQUIRED_NON_NEGATIVE_INT_FIELDS = (
    "wave_rank",
    "brief_position",
    "affected_record_count",
    "cluster_count",
    "dependency_count",
)

REQUIRED_BOOL_FIELDS = (
    "has_prohibition_path",
    "has_blocker_path",
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


def normalize_non_empty_string(value, field_name: str, index: int) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f"session-brief record[{index}] field {field_name!r} must be str; fail-closed"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(
            f"session-brief record[{index}] field {field_name!r} must be non-empty; fail-closed"
        )
    return normalized


def normalize_non_negative_int(value, field_name: str, index: int) -> int:
    if isinstance(value, bool):
        raise ValueError(
            f"session-brief record[{index}] field {field_name!r} must be int, not bool; fail-closed"
        )
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"session-brief record[{index}] field {field_name!r} malformed int={value!r}; fail-closed"
        ) from exc
    if normalized < 0:
        raise ValueError(
            f"session-brief record[{index}] field {field_name!r} must be >= 0; fail-closed"
        )
    return normalized


def normalize_bool(value, field_name: str, index: int) -> bool:
    if not isinstance(value, bool):
        raise ValueError(
            f"session-brief record[{index}] field {field_name!r} must be bool; fail-closed"
        )
    return value


def normalize_string_list(value, field_name: str, index: int) -> list:
    if not isinstance(value, list):
        raise ValueError(
            f"session-brief record[{index}] field {field_name!r} must be list; fail-closed"
        )
    normalized_values = []
    for item_index, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(
                f"session-brief record[{index}] field {field_name!r} non-str item at {item_index}; fail-closed"
            )
        item_value = item.strip()
        if not item_value:
            raise ValueError(
                f"session-brief record[{index}] field {field_name!r} empty item at {item_index}; fail-closed"
            )
        normalized_values.append(item_value)
    return normalized_values


def validate_upstream_payload(source_data: dict) -> None:
    if not isinstance(source_data, dict):
        raise ValueError("upstream session brief payload is not a dict; fail-closed")

    version = source_data.get(
        "model_adjustment_release_resolution_wave_packet_review_session_brief_version"
    )
    if not isinstance(version, str) or not version.strip():
        raise ValueError("upstream session brief version missing or malformed; fail-closed")

    records = source_data.get("release_resolution_wave_packet_review_session_brief")
    if not isinstance(records, list):
        raise ValueError("upstream release_resolution_wave_packet_review_session_brief missing or malformed; fail-closed")


def validate_session_brief_record(record: dict, index: int) -> None:
    if not isinstance(record, dict):
        raise ValueError(f"session-brief record[{index}] malformed type={type(record).__name__}; fail-closed")

    for field in REQUIRED_SESSION_BRIEF_FIELDS:
        if field not in record:
            raise ValueError(f"session-brief record[{index}] missing required field {field!r}; fail-closed")

    for field in REQUIRED_NON_EMPTY_STRING_FIELDS:
        record[field] = normalize_non_empty_string(record.get(field), field, index)

    for field in REQUIRED_LIST_FIELDS:
        record[field] = normalize_string_list(record.get(field), field, index)

    for field in REQUIRED_NON_NEGATIVE_INT_FIELDS:
        record[field] = normalize_non_negative_int(record.get(field), field, index)

    for field in REQUIRED_BOOL_FIELDS:
        record[field] = normalize_bool(record.get(field), field, index)

    if record["wave_type"] not in (
        "prohibition_cluster",
        "blocker_cluster",
        "remaining_resolution_cluster",
    ):
        raise ValueError(f"session-brief record[{index}] unknown wave_type={record['wave_type']!r}; fail-closed")

    if record["review_lane"] not in REVIEW_LANE_ORDER:
        raise ValueError(f"session-brief record[{index}] unknown review_lane={record['review_lane']!r}; fail-closed")


def sorted_session_brief_records(records: list) -> list:
    return sorted(
        records,
        key=lambda record: (
            REVIEW_LANE_ORDER[record["review_lane"]],
            record["review_session_brief_priority"],
            record["wave_rank"],
            record["packet_priority"],
            record["checklist_priority"],
            record["resolution_wave_packet_review_session_brief_id"],
            record["source_resolution_wave_packet_review_session_pack_id"],
        ),
    )


def build_handoff_records(records: list) -> list:
    for index, record in enumerate(records):
        validate_session_brief_record(record, index)

    output = []
    for index, record in enumerate(sorted_session_brief_records(records), start=1):
        output.append(
            {
                "resolution_wave_packet_review_session_handoff_id": (
                    f"resolution-wave-packet-review-session-handoff-{index:04d}"
                ),
                "source_resolution_wave_packet_review_session_brief_id": record[
                    "resolution_wave_packet_review_session_brief_id"
                ],
                "source_resolution_wave_packet_review_session_pack_id": record[
                    "source_resolution_wave_packet_review_session_pack_id"
                ],
                "source_resolution_wave_packet_review_agenda_id": record[
                    "source_resolution_wave_packet_review_agenda_id"
                ],
                "source_resolution_wave_packet_review_docket_id": record[
                    "source_resolution_wave_packet_review_docket_id"
                ],
                "source_resolution_wave_packet_review_board_id": record[
                    "source_resolution_wave_packet_review_board_id"
                ],
                "source_resolution_wave_packet_checklist_id": record[
                    "source_resolution_wave_packet_checklist_id"
                ],
                "source_resolution_wave_packet_id": record[
                    "source_resolution_wave_packet_id"
                ],
                "source_resolution_wave_id": record["source_resolution_wave_id"],
                "wave_rank": record["wave_rank"],
                "wave_type": record["wave_type"],
                "packet_priority": record["packet_priority"],
                "checklist_priority": record["checklist_priority"],
                "review_board_priority": record["review_board_priority"],
                "review_docket_priority": record["review_docket_priority"],
                "review_agenda_priority": record["review_agenda_priority"],
                "review_session_pack_priority": record["review_session_pack_priority"],
                "review_session_brief_priority": record["review_session_brief_priority"],
                "review_lane": record["review_lane"],
                "review_session_handoff_priority": record["review_session_brief_priority"],
                "handoff_position": index,
                "member_cluster_ids": dedup_sorted(record["member_cluster_ids"]),
                "member_dependency_ids": dedup_sorted(record["member_dependency_ids"]),
                "member_source_refs": dedup_sorted(record["member_source_refs"]),
                "affected_proposal_ids": dedup_sorted(record["affected_proposal_ids"]),
                "affected_queue_ids": dedup_sorted(record["affected_queue_ids"]),
                "affected_record_count": record["affected_record_count"],
                "cluster_count": record["cluster_count"],
                "dependency_count": record["dependency_count"],
                "has_prohibition_path": record["has_prohibition_path"],
                "has_blocker_path": record["has_blocker_path"],
                "terminal_posture": record["terminal_posture"],
                "review_session_handoff_notes": (
                    "v5_9_read_only_review_session_handoff_projection_of_v5_8_session_brief"
                    "_no_reclassification_no_release_recommendation_no_upstream_mutation"
                ),
                "upstream_source": SOURCE_PATHS[
                    "model_adjustment_release_resolution_wave_packet_review_session_brief_json"
                ],
            }
        )
    return output


def validate_handoff(records: list, session_brief_records: list) -> None:
    sorted_briefs = sorted_session_brief_records(session_brief_records)

    if len(records) != len(sorted_briefs):
        raise ValueError("session handoff count mismatch against sorted brief records; fail-closed")

    source_brief_ids = [
        record["source_resolution_wave_packet_review_session_brief_id"] for record in records
    ]
    expected_brief_order = [
        record.get("resolution_wave_packet_review_session_brief_id", "")
        for record in sorted_briefs
    ]
    if source_brief_ids != expected_brief_order:
        raise ValueError("session handoff records are not in deterministic brief sort order; fail-closed")

    handoff_ids = [record["resolution_wave_packet_review_session_handoff_id"] for record in records]
    if len(handoff_ids) != len(set(handoff_ids)):
        raise ValueError("duplicate resolution_wave_packet_review_session_handoff_id in output; fail-closed")

    if len(source_brief_ids) != len(set(source_brief_ids)):
        raise ValueError("duplicate source_resolution_wave_packet_review_session_brief_id in handoff; fail-closed")

    upstream_brief_ids = [
        record.get("resolution_wave_packet_review_session_brief_id", "")
        for record in session_brief_records
    ]
    if len(upstream_brief_ids) != EXPECTED_REVIEW_SESSION_BRIEF_COUNT:
        raise ValueError(
            "upstream session brief count does not match EXPECTED_REVIEW_SESSION_BRIEF_COUNT; fail-closed"
        )

    if set(source_brief_ids) != set(upstream_brief_ids):
        raise ValueError("session handoff coverage does not match upstream brief records; fail-closed")

    for record in records:
        if record["review_session_handoff_priority"] != record["review_session_brief_priority"]:
            raise ValueError("review_session_handoff_priority drift detected; fail-closed")

        for field in (
            "member_cluster_ids",
            "member_dependency_ids",
            "member_source_refs",
            "affected_proposal_ids",
            "affected_queue_ids",
        ):
            values = record.get(field, [])
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate values in {field!r}; fail-closed")
            if values != dedup_sorted(values):
                raise ValueError(f"non-canonical ordering in {field!r}; fail-closed")


def build_summary(records: list, session_brief_records: list) -> dict:
    lane_counts = {
        lane: sum(1 for record in records if record.get("review_lane") == lane)
        for lane in (
            "lane_prohibition_terminal",
            "lane_blocker_terminal",
            "lane_remaining_terminal",
        )
    }
    return {
        "upstream_session_brief_count": len(session_brief_records),
        "total_review_session_handoff_records": len(records),
        "review_lane_counts": lane_counts,
        "coverage_reconciled": True,
        "deterministic_ordering": True,
    }


def build_source_versions(source_data: dict) -> dict:
    return {
        "model_adjustment_release_resolution_wave_packet_review_session_brief_version": source_data.get(
            "model_adjustment_release_resolution_wave_packet_review_session_brief_version", ""
        )
    }


def build_markdown_lines(records: list, summary: dict, source_versions: dict, generated_at: str) -> list:
    lines = [
        "# Model Adjustment Release Resolution Wave Packet Review Session Handoff",
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
        lines.append(f"## {record['resolution_wave_packet_review_session_handoff_id']}")
        lines.append("")
        lines.append(
            f"- source_resolution_wave_packet_review_session_brief_id: {record['source_resolution_wave_packet_review_session_brief_id']}"
        )
        lines.append(
            f"- source_resolution_wave_packet_review_session_pack_id: {record['source_resolution_wave_packet_review_session_pack_id']}"
        )
        lines.append(
            f"- source_resolution_wave_packet_review_agenda_id: {record['source_resolution_wave_packet_review_agenda_id']}"
        )
        lines.append(
            f"- source_resolution_wave_packet_review_docket_id: {record['source_resolution_wave_packet_review_docket_id']}"
        )
        lines.append(
            f"- source_resolution_wave_packet_review_board_id: {record['source_resolution_wave_packet_review_board_id']}"
        )
        lines.append(
            f"- source_resolution_wave_packet_checklist_id: {record['source_resolution_wave_packet_checklist_id']}"
        )
        lines.append(f"- source_resolution_wave_packet_id: {record['source_resolution_wave_packet_id']}")
        lines.append(f"- source_resolution_wave_id: {record['source_resolution_wave_id']}")
        lines.append(f"- wave_rank: {record['wave_rank']}")
        lines.append(f"- wave_type: {record['wave_type']}")
        lines.append(f"- packet_priority: {record['packet_priority']}")
        lines.append(f"- checklist_priority: {record['checklist_priority']}")
        lines.append(f"- review_board_priority: {record['review_board_priority']}")
        lines.append(f"- review_docket_priority: {record['review_docket_priority']}")
        lines.append(f"- review_agenda_priority: {record['review_agenda_priority']}")
        lines.append(f"- review_session_pack_priority: {record['review_session_pack_priority']}")
        lines.append(f"- review_session_brief_priority: {record['review_session_brief_priority']}")
        lines.append(f"- review_lane: {record['review_lane']}")
        lines.append(f"- review_session_handoff_priority: {record['review_session_handoff_priority']}")
        lines.append(f"- handoff_position: {record['handoff_position']}")
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

    return lines


def write_markdown(records: list, summary: dict, source_versions: dict, generated_at: str):
    with open(OUTPUT_MD, "w", encoding="utf-8") as file_handle:
        file_handle.write("\n".join(build_markdown_lines(records, summary, source_versions, generated_at)))


def main():
    errors = {}
    source_data, errors[
        "model_adjustment_release_resolution_wave_packet_review_session_brief_json"
    ] = load_source("model_adjustment_release_resolution_wave_packet_review_session_brief_json")

    failures = [key for key, value in errors.items() if value is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    validate_upstream_payload(source_data)

    session_brief_records = source_data.get(
        "release_resolution_wave_packet_review_session_brief", []
    )
    records = build_handoff_records(session_brief_records)
    validate_handoff(records, session_brief_records)
    summary = build_summary(records, session_brief_records)
    source_versions = build_source_versions(source_data)
    source_status = {f"{key}_error": errors[key] for key in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_resolution_wave_packet_review_session_handoff_version": VERSION,
        "release_resolution_wave_packet_review_session_handoff_summary": summary,
        "release_resolution_wave_packet_review_session_handoff": records,
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
        f"review_session_handoff_records={summary['total_review_session_handoff_records']} "
        f"upstream_session_brief_count={summary['upstream_session_brief_count']} "
        f"coverage_reconciled={summary['coverage_reconciled']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"review_lane_counts={summary['review_lane_counts']}"
    )


if __name__ == "__main__":
    main()
