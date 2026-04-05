"""
generate_model_adjustment_release_resolution_wave_packet_review_agenda.py

v5.6-slice-1 — Read-only controlled release resolution-wave-packet-review-agenda
generator.

Consumes the frozen v5.5 release resolution wave packet review docket output and
emits one deterministic review-agenda entry per docket record.

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
    "model_adjustment_release_resolution_wave_packet_review_docket_json": (
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_docket.json"
    )
}

OUTPUT_JSON = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_wave_packet_review_agenda.json",
)
OUTPUT_MD = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_wave_packet_review_agenda.md",
)

VERSION = "v5.6-slice-1"
EXPECTED_REVIEW_DOCKET_COUNT = 3

REVIEW_LANE_ORDER = {
    "lane_prohibition_terminal": 0,
    "lane_blocker_terminal": 1,
    "lane_remaining_terminal": 2,
}

REQUIRED_DOCKET_FIELDS = (
    "resolution_wave_packet_review_docket_id",
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
    "review_lane",
    "docket_position",
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
    "resolution_wave_packet_review_docket_id",
    "source_resolution_wave_packet_review_board_id",
    "source_resolution_wave_packet_checklist_id",
    "source_resolution_wave_packet_id",
    "source_resolution_wave_id",
    "wave_type",
    "packet_priority",
    "checklist_priority",
    "review_board_priority",
    "review_docket_priority",
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
    "docket_position",
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
            f"docket record[{index}] field {field_name!r} must be str; "
            "fail-closed — manual review required"
        )
    normalized = value.strip()
    if not normalized:
        raise ValueError(
            f"docket record[{index}] field {field_name!r} must be non-empty; "
            "fail-closed — manual review required"
        )
    return normalized


def normalize_non_negative_int(value, field_name: str, index: int) -> int:
    if isinstance(value, bool):
        raise ValueError(
            f"docket record[{index}] field {field_name!r} must be int, not bool; "
            "fail-closed — manual review required"
        )
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"docket record[{index}] field {field_name!r} malformed int={value!r}; "
            "fail-closed — manual review required"
        ) from exc
    if normalized < 0:
        raise ValueError(
            f"docket record[{index}] field {field_name!r} must be >= 0; "
            "fail-closed — manual review required"
        )
    return normalized


def normalize_bool(value, field_name: str, index: int) -> bool:
    if not isinstance(value, bool):
        raise ValueError(
            f"docket record[{index}] field {field_name!r} must be bool; "
            "fail-closed — manual review required"
        )
    return value


def normalize_string_list(value, field_name: str, index: int) -> list:
    if not isinstance(value, list):
        raise ValueError(
            f"docket record[{index}] field {field_name!r} must be list; "
            "fail-closed — manual review required"
        )

    normalized_values = []
    for item_index, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(
                f"docket record[{index}] field {field_name!r} has non-str item at "
                f"index {item_index}; fail-closed — manual review required"
            )
        item_value = item.strip()
        if not item_value:
            raise ValueError(
                f"docket record[{index}] field {field_name!r} has empty item at "
                f"index {item_index}; fail-closed — manual review required"
            )
        normalized_values.append(item_value)

    return normalized_values


def validate_upstream_payload(source_data: dict) -> None:
    if not isinstance(source_data, dict):
        raise ValueError("upstream docket payload is not a dict; fail-closed")

    version = source_data.get(
        "model_adjustment_release_resolution_wave_packet_review_docket_version"
    )
    if not isinstance(version, str) or not version.strip():
        raise ValueError(
            "upstream docket version missing or malformed; fail-closed"
        )

    docket_records = source_data.get("release_resolution_wave_packet_review_docket")
    if not isinstance(docket_records, list):
        raise ValueError(
            "upstream release_resolution_wave_packet_review_docket missing or malformed; "
            "fail-closed"
        )


def validate_docket_record(record: dict, index: int) -> None:
    if not isinstance(record, dict):
        raise ValueError(
            f"docket record[{index}] malformed type={type(record).__name__}; "
            "fail-closed — manual review required"
        )

    for field in REQUIRED_DOCKET_FIELDS:
        if field not in record:
            raise ValueError(
                f"docket record[{index}] missing required field {field!r}; "
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
            f"docket record[{index}] has unknown wave_type={wave_type!r}; "
            "fail-closed — manual review required"
        )

    review_lane = record.get("review_lane", "")
    if review_lane not in REVIEW_LANE_ORDER:
        raise ValueError(
            f"docket record[{index}] has unknown review_lane={review_lane!r}; "
            "fail-closed — manual review required"
        )


def sorted_docket_records(records: list) -> list:
    return sorted(
        records,
        key=lambda record: (
            REVIEW_LANE_ORDER[record["review_lane"]],
            record["review_docket_priority"],
            record["wave_rank"],
            record["packet_priority"],
            record["checklist_priority"],
            record["resolution_wave_packet_review_docket_id"],
            record["source_resolution_wave_packet_review_board_id"],
        ),
    )


def build_review_agenda_records(records: list) -> list:
    for index, record in enumerate(records):
        validate_docket_record(record, index)

    output = []

    for index, record in enumerate(sorted_docket_records(records), start=1):
        output.append(
            {
                "resolution_wave_packet_review_agenda_id": (
                    f"resolution-wave-packet-review-agenda-{index:04d}"
                ),
                "source_resolution_wave_packet_review_docket_id": record[
                    "resolution_wave_packet_review_docket_id"
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
                "review_lane": record["review_lane"],
                "review_agenda_priority": record["review_docket_priority"],
                "agenda_position": index,
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
                "review_agenda_notes": (
                    "v5_6_read_only_review_agenda_projection_of_v5_5_docket"
                    "_no_reclassification_no_release_recommendation_no_upstream_mutation"
                ),
                "upstream_source": SOURCE_PATHS[
                    "model_adjustment_release_resolution_wave_packet_review_docket_json"
                ],
            }
        )

    return output


def validate_review_agenda(records: list, docket_records: list) -> None:
    sorted_dockets = sorted_docket_records(docket_records)
    
    # Verify output records match the number of sorted docket records
    if len(records) != len(sorted_dockets):
        raise ValueError(
            f"review agenda count {len(records)} does not match "
            f"sorted docket count {len(sorted_dockets)}; fail-closed"
        )
    
    # Verify the mapping from docket IDs to agenda records is canonical
    docket_id_from_records = [
        record["source_resolution_wave_packet_review_docket_id"] for record in records
    ]
    expected_docket_id_order = [
        docket.get("resolution_wave_packet_review_docket_id", "")
        for docket in sorted_dockets
    ]
    if docket_id_from_records != expected_docket_id_order:
        raise ValueError(
            "review agenda records are not in deterministic docket sort order; fail-closed"
        )

    agenda_ids = [record["resolution_wave_packet_review_agenda_id"] for record in records]
    if len(agenda_ids) != len(set(agenda_ids)):
        raise ValueError("duplicate resolution_wave_packet_review_agenda_id in output; fail-closed")

    source_docket_ids = [
        record["source_resolution_wave_packet_review_docket_id"] for record in records
    ]
    if len(source_docket_ids) != len(set(source_docket_ids)):
        raise ValueError(
            "duplicate source_resolution_wave_packet_review_docket_id in agenda; fail-closed"
        )

    upstream_docket_ids = [
        record.get("resolution_wave_packet_review_docket_id", "")
        for record in docket_records
    ]
    if len(upstream_docket_ids) != EXPECTED_REVIEW_DOCKET_COUNT:
        raise ValueError(
            f"upstream docket count {len(upstream_docket_ids)} does not match "
            f"EXPECTED_REVIEW_DOCKET_COUNT={EXPECTED_REVIEW_DOCKET_COUNT}; fail-closed"
        )

    if set(source_docket_ids) != set(upstream_docket_ids):
        raise ValueError(
            "review agenda coverage does not match upstream docket records; "
            "fail-closed"
        )

    for record in records:
        if record.get("review_agenda_priority") != record.get("review_docket_priority"):
            raise ValueError(
                f"review_agenda_priority drift for {record['resolution_wave_packet_review_agenda_id']}; "
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
                    f"{record['resolution_wave_packet_review_agenda_id']}; fail-closed"
                )
            if values != dedup_sorted(values):
                raise ValueError(
                    f"non-canonical ordering in {field!r} for "
                    f"{record['resolution_wave_packet_review_agenda_id']}; fail-closed"
                )


def build_summary(records: list, docket_records: list) -> dict:
    lane_counts = {
        lane: sum(1 for record in records if record.get("review_lane") == lane)
        for lane in (
            "lane_prohibition_terminal",
            "lane_blocker_terminal",
            "lane_remaining_terminal",
        )
    }

    return {
        "upstream_docket_count": len(docket_records),
        "total_review_agenda_records": len(records),
        "review_lane_counts": lane_counts,
        "coverage_reconciled": True,
        "deterministic_ordering": True,
    }


def build_source_versions(source_data: dict) -> dict:
    return {
        "model_adjustment_release_resolution_wave_packet_review_docket_version": source_data.get(
            "model_adjustment_release_resolution_wave_packet_review_docket_version", ""
        )
    }


def build_markdown_lines(
    records: list, summary: dict, source_versions: dict, generated_at: str
) -> list:
    lines = [
        "# Model Adjustment Release Resolution Wave Packet Review Agenda",
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
        lines.append(f"## {record['resolution_wave_packet_review_agenda_id']}")
        lines.append("")
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
        lines.append(f"- review_lane: {record['review_lane']}")
        lines.append(f"- review_agenda_priority: {record['review_agenda_priority']}")
        lines.append(f"- agenda_position: {record['agenda_position']}")
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

    source_data, errors["model_adjustment_release_resolution_wave_packet_review_docket_json"] = load_source(
        "model_adjustment_release_resolution_wave_packet_review_docket_json"
    )

    failures = [key for key, value in errors.items() if value is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    validate_upstream_payload(source_data)

    docket_records = source_data.get("release_resolution_wave_packet_review_docket", [])
    records = build_review_agenda_records(docket_records)
    validate_review_agenda(records, docket_records)
    summary = build_summary(records, docket_records)
    source_versions = build_source_versions(source_data)
    source_status = {f"{key}_error": errors[key] for key in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_resolution_wave_packet_review_agenda_version": VERSION,
        "release_resolution_wave_packet_review_agenda_summary": summary,
        "release_resolution_wave_packet_review_agenda": records,
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
        f"review_agenda_records={summary['total_review_agenda_records']} "
        f"upstream_docket_count={summary['upstream_docket_count']} "
        f"coverage_reconciled={summary['coverage_reconciled']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"review_lane_counts={summary['review_lane_counts']}"
    )


if __name__ == "__main__":
    main()
