"""
generate_model_adjustment_release_resolution_wave_packet_review_session_pack.py

v5.7-slice-1 — Read-only controlled release resolution-wave-packet-review-session-pack
generator.

Consumes the frozen v5.6 release resolution wave packet review agenda output and
emits one deterministic session-pack entry per agenda record.

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
    "model_adjustment_release_resolution_wave_packet_review_agenda_json": (
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_agenda.json"
    )
}

OUTPUT_JSON = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_wave_packet_review_session_pack.json",
)
OUTPUT_MD = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_wave_packet_review_session_pack.md",
)

VERSION = "v5.7-slice-1"
EXPECTED_REVIEW_AGENDA_COUNT = 3

REVIEW_LANE_ORDER = {
    "lane_prohibition_terminal": 0,
    "lane_blocker_terminal": 1,
    "lane_remaining_terminal": 2,
}

REQUIRED_AGENDA_FIELDS = (
    "resolution_wave_packet_review_agenda_id",
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
    "review_lane",
    "agenda_position",
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
    "resolution_wave_packet_review_agenda_id",
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
    "agenda_position",
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
            f"agenda record[{index}] field {field_name!r} must be str; "
            "fail-closed — manual review required"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(
            f"agenda record[{index}] field {field_name!r} must be non-empty; "
            "fail-closed — manual review required"
        )
    return normalized


def normalize_non_negative_int(value, field_name: str, index: int) -> int:
    if isinstance(value, bool):
        raise ValueError(
            f"agenda record[{index}] field {field_name!r} must be int, not bool; "
            "fail-closed — manual review required"
        )
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"agenda record[{index}] field {field_name!r} malformed int={value!r}; "
            "fail-closed — manual review required"
        ) from exc
    if normalized < 0:
        raise ValueError(
            f"agenda record[{index}] field {field_name!r} must be >= 0; "
            "fail-closed — manual review required"
        )
    return normalized


def normalize_bool(value, field_name: str, index: int) -> bool:
    if not isinstance(value, bool):
        raise ValueError(
            f"agenda record[{index}] field {field_name!r} must be bool; "
            "fail-closed — manual review required"
        )
    return value


def normalize_string_list(value, field_name: str, index: int) -> list:
    if not isinstance(value, list):
        raise ValueError(
            f"agenda record[{index}] field {field_name!r} must be list; "
            "fail-closed — manual review required"
        )

    normalized_values = []
    for item_index, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(
                f"agenda record[{index}] field {field_name!r} has non-str item at "
                f"index {item_index}; fail-closed — manual review required"
            )
        item_value = item.strip()
        if not item_value:
            raise ValueError(
                f"agenda record[{index}] field {field_name!r} has empty item at "
                f"index {item_index}; fail-closed — manual review required"
            )
        normalized_values.append(item_value)

    return normalized_values


def validate_upstream_payload(source_data: dict) -> None:
    if not isinstance(source_data, dict):
        raise ValueError("upstream agenda payload is not a dict; fail-closed")

    version = source_data.get(
        "model_adjustment_release_resolution_wave_packet_review_agenda_version"
    )
    if not isinstance(version, str) or not version.strip():
        raise ValueError(
            "upstream agenda version missing or malformed; fail-closed"
        )

    agenda_records = source_data.get("release_resolution_wave_packet_review_agenda")
    if not isinstance(agenda_records, list):
        raise ValueError(
            "upstream release_resolution_wave_packet_review_agenda missing or malformed; "
            "fail-closed"
        )


def validate_agenda_record(record: dict, index: int) -> None:
    if not isinstance(record, dict):
        raise ValueError(
            f"agenda record[{index}] malformed type={type(record).__name__}; "
            "fail-closed — manual review required"
        )

    for field in REQUIRED_AGENDA_FIELDS:
        if field not in record:
            raise ValueError(
                f"agenda record[{index}] missing required field {field!r}; "
                "fail-closed — manual review required"
            )

    for field in REQUIRED_NON_EMPTY_STRING_FIELDS:
        record[field] = normalize_non_empty_string(record.get(field), field, index)

    for field in REQUIRED_LIST_FIELDS:
        record[field] = normalize_string_list(record.get(field), field, index)

    for field in REQUIRED_NON_NEGATIVE_INT_FIELDS:
        record[field] = normalize_non_negative_int(record.get(field), field, index)

    for field in REQUIRED_BOOL_FIELDS:
        record[field] = normalize_bool(record.get(field), field, index)

    wave_type = record.get("wave_type", "")
    if wave_type not in ("prohibition_cluster", "blocker_cluster", "remaining_resolution_cluster"):
        raise ValueError(
            f"agenda record[{index}] has unknown wave_type={wave_type!r}; "
            "fail-closed — manual review required"
        )

    review_lane = record.get("review_lane", "")
    if review_lane not in REVIEW_LANE_ORDER:
        raise ValueError(
            f"agenda record[{index}] has unknown review_lane={review_lane!r}; "
            "fail-closed — manual review required"
        )


def sorted_agenda_records(records: list) -> list:
    return sorted(
        records,
        key=lambda record: (
            REVIEW_LANE_ORDER[record["review_lane"]],
            record["review_agenda_priority"],
            record["wave_rank"],
            record["packet_priority"],
            record["checklist_priority"],
            record["resolution_wave_packet_review_agenda_id"],
            record["source_resolution_wave_packet_review_docket_id"],
        ),
    )


def build_session_pack_records(records: list) -> list:
    for index, record in enumerate(records):
        validate_agenda_record(record, index)

    output = []

    for index, record in enumerate(sorted_agenda_records(records), start=1):
        output.append(
            {
                "resolution_wave_packet_review_session_pack_id": (
                    f"resolution-wave-packet-review-session-pack-{index:04d}"
                ),
                "source_resolution_wave_packet_review_agenda_id": record[
                    "resolution_wave_packet_review_agenda_id"
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
                "review_lane": record["review_lane"],
                "review_session_pack_priority": record["review_agenda_priority"],
                "session_pack_position": index,
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
                "review_session_pack_notes": (
                    "v5_7_read_only_review_session_pack_projection_of_v5_6_agenda"
                    "_no_reclassification_no_release_recommendation_no_upstream_mutation"
                ),
                "upstream_source": SOURCE_PATHS[
                    "model_adjustment_release_resolution_wave_packet_review_agenda_json"
                ],
            }
        )

    return output


def validate_session_pack(records: list, agenda_records: list) -> None:
    sorted_agendas = sorted_agenda_records(agenda_records)
    
    if len(records) != len(sorted_agendas):
        raise ValueError(
            f"session pack count {len(records)} does not match "
            f"sorted agenda count {len(sorted_agendas)}; fail-closed"
        )
    
    agenda_id_from_records = [
        record["source_resolution_wave_packet_review_agenda_id"] for record in records
    ]
    expected_agenda_id_order = [
        agenda.get("resolution_wave_packet_review_agenda_id", "")
        for agenda in sorted_agendas
    ]
    if agenda_id_from_records != expected_agenda_id_order:
        raise ValueError(
            "session pack records are not in deterministic agenda sort order; fail-closed"
        )

    pack_ids = [record["resolution_wave_packet_review_session_pack_id"] for record in records]
    if len(pack_ids) != len(set(pack_ids)):
        raise ValueError("duplicate resolution_wave_packet_review_session_pack_id in output; fail-closed")

    source_agenda_ids = [
        record["source_resolution_wave_packet_review_agenda_id"] for record in records
    ]
    if len(source_agenda_ids) != len(set(source_agenda_ids)):
        raise ValueError(
            "duplicate source_resolution_wave_packet_review_agenda_id in session pack; fail-closed"
        )

    upstream_agenda_ids = [
        record.get("resolution_wave_packet_review_agenda_id", "")
        for record in agenda_records
    ]
    if len(upstream_agenda_ids) != EXPECTED_REVIEW_AGENDA_COUNT:
        raise ValueError(
            f"upstream agenda count {len(upstream_agenda_ids)} does not match "
            f"EXPECTED_REVIEW_AGENDA_COUNT={EXPECTED_REVIEW_AGENDA_COUNT}; fail-closed"
        )

    if set(source_agenda_ids) != set(upstream_agenda_ids):
        raise ValueError(
            "session pack coverage does not match upstream agenda records; "
            "fail-closed"
        )

    for record in records:
        if record.get("review_session_pack_priority") != record.get("review_agenda_priority"):
            raise ValueError(
                f"review_session_pack_priority drift for {record['resolution_wave_packet_review_session_pack_id']}; "
                "fail-closed"
            )

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
                    f"{record['resolution_wave_packet_review_session_pack_id']}; fail-closed"
                )
            if values != dedup_sorted(values):
                raise ValueError(
                    f"non-canonical ordering in {field!r} for "
                    f"{record['resolution_wave_packet_review_session_pack_id']}; fail-closed"
                )


def build_summary(records: list, agenda_records: list) -> dict:
    lane_counts = {
        lane: sum(1 for record in records if record.get("review_lane") == lane)
        for lane in (
            "lane_prohibition_terminal",
            "lane_blocker_terminal",
            "lane_remaining_terminal",
        )
    }

    return {
        "upstream_agenda_count": len(agenda_records),
        "total_review_session_pack_records": len(records),
        "review_lane_counts": lane_counts,
        "coverage_reconciled": True,
        "deterministic_ordering": True,
    }


def build_source_versions(source_data: dict) -> dict:
    return {
        "model_adjustment_release_resolution_wave_packet_review_agenda_version": source_data.get(
            "model_adjustment_release_resolution_wave_packet_review_agenda_version", ""
        )
    }


def build_markdown_lines(
    records: list, summary: dict, source_versions: dict, generated_at: str
) -> list:
    lines = [
        "# Model Adjustment Release Resolution Wave Packet Review Session Pack",
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
        lines.append(f"## {record['resolution_wave_packet_review_session_pack_id']}")
        lines.append("")
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
        lines.append(
            f"- source_resolution_wave_packet_id: {record['source_resolution_wave_packet_id']}"
        )
        lines.append(f"- source_resolution_wave_id: {record['source_resolution_wave_id']}")
        lines.append(f"- wave_rank: {record['wave_rank']}")
        lines.append(f"- wave_type: {record['wave_type']}")
        lines.append(f"- packet_priority: {record['packet_priority']}")
        lines.append(f"- checklist_priority: {record['checklist_priority']}")
        lines.append(f"- review_board_priority: {record['review_board_priority']}")
        lines.append(f"- review_docket_priority: {record['review_docket_priority']}")
        lines.append(f"- review_agenda_priority: {record['review_agenda_priority']}")
        lines.append(f"- review_lane: {record['review_lane']}")
        lines.append(f"- review_session_pack_priority: {record['review_session_pack_priority']}")
        lines.append(f"- session_pack_position: {record['session_pack_position']}")
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
    lines = build_markdown_lines(records, summary, source_versions, generated_at)

    with open(OUTPUT_MD, "w", encoding="utf-8") as file_handle:
        file_handle.write("\n".join(lines))


def main():
    errors = {}

    source_data, errors["model_adjustment_release_resolution_wave_packet_review_agenda_json"] = load_source(
        "model_adjustment_release_resolution_wave_packet_review_agenda_json"
    )

    failures = [key for key, value in errors.items() if value is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    validate_upstream_payload(source_data)

    agenda_records = source_data.get("release_resolution_wave_packet_review_agenda", [])
    records = build_session_pack_records(agenda_records)
    validate_session_pack(records, agenda_records)
    summary = build_summary(records, agenda_records)
    source_versions = build_source_versions(source_data)
    source_status = {f"{key}_error": errors[key] for key in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_resolution_wave_packet_review_session_pack_version": VERSION,
        "release_resolution_wave_packet_review_session_pack_summary": summary,
        "release_resolution_wave_packet_review_session_pack": records,
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
        f"review_session_pack_records={summary['total_review_session_pack_records']} "
        f"upstream_agenda_count={summary['upstream_agenda_count']} "
        f"coverage_reconciled={summary['coverage_reconciled']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"review_lane_counts={summary['review_lane_counts']}"
    )


if __name__ == "__main__":
    main()
