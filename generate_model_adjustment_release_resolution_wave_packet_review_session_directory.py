#!/usr/bin/env python3
"""
v6.8: Model Adjustment Release Resolution Wave Packet Review Session Directory Generator

Pure downstream projection of review-session-index into operator-directory retrieval layer.
Consumes: model_adjustment_release_resolution_wave_packet_review_session_index.json (v6.7)
Produces: model_adjustment_release_resolution_wave_packet_review_session_directory.json (v6.8)
          model_adjustment_release_resolution_wave_packet_review_session_directory.md (v6.8)

Behavior:
- One directory entry per upstream index entry
- Preserves upstream priority, lane, and posture fields exactly
- Adds directory projection fields only (directory_id, directory_priority, directory_position)
- Deterministic ordering with lexical tie-break on source index id then source catalog id
- No re-classification, no release logic, no policy logic
- Fail-closed validation for malformed upstream payloads
- Markdown is a pure projection of JSON
"""

import datetime
import json
import os
import sys

SOURCE_PATHS = {
    "index": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_index.json",
}

OUTPUT_PATHS = {
    "json": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_directory.json",
    "md": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_directory.md",
}

LANE_ORDER = {
    "lane_prohibition_terminal": 0,
    "lane_blocker_terminal": 1,
    "lane_remaining_terminal": 2,
}


def normalize_string(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid {name}: expected non-empty string, got {repr(value)}")
    return value


def get_required_field(record, field_name, record_index):
    if field_name not in record:
        raise ValueError(f"Missing required field '{field_name}' in index record {record_index}")
    return record[field_name]


def normalize_list(value, name):
    if not isinstance(value, list):
        raise ValueError(f"Invalid {name}: expected list, got {type(value).__name__}")
    normalized = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"Invalid {name}[{idx}]: expected non-empty string, got {repr(item)}"
            )
        normalized.append(item)
    return sorted(set(normalized))


def normalize_int(value, name):
    if not isinstance(value, int):
        raise ValueError(f"Invalid {name}: expected int, got {type(value).__name__}")
    return value


def normalize_bool(value, name):
    if not isinstance(value, bool):
        raise ValueError(f"Invalid {name}: expected bool, got {type(value).__name__}")
    return value


def normalize_review_lane(value, name):
    lane = normalize_string(value, name)
    if lane not in LANE_ORDER:
        raise ValueError(
            f"Invalid {name}: expected one of {sorted(LANE_ORDER.keys())}, got {repr(lane)}"
        )
    return lane


def validate_upstream_payload(payload, path):
    if not isinstance(payload, dict):
        raise ValueError(f"Upstream payload {path} is not a dict: {type(payload).__name__}")

    version = payload.get("model_adjustment_release_resolution_wave_packet_review_session_index_version")
    if version != "v6.7-slice-1":
        raise ValueError(f"Expected index version 'v6.7-slice-1', got {repr(version)}")

    if "release_resolution_wave_packet_review_session_index" not in payload:
        raise ValueError("Missing upstream field: release_resolution_wave_packet_review_session_index")

    records = payload["release_resolution_wave_packet_review_session_index"]
    if not isinstance(records, list):
        raise ValueError(
            "release_resolution_wave_packet_review_session_index is not a list: "
            f"{type(records).__name__}"
        )
    if len(records) == 0:
        raise ValueError("No index records found in upstream payload")
    return records


def build_directory_records(index_records):
    directory_records = []

    for idx, index_record in enumerate(index_records):
        if not isinstance(index_record, dict):
            raise ValueError(
                f"Validation error in index record {idx}: expected object, got {type(index_record).__name__}"
            )

        try:
            index_id = normalize_string(
                get_required_field(index_record, "resolution_wave_packet_review_session_index_id", idx),
                "index_id",
            )
            catalog_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_session_catalog_id", idx),
                "catalog_id",
            )
            archive_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_session_archive_id", idx),
                "archive_id",
            )
            journal_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_session_journal_id", idx),
                "journal_id",
            )
            ledger_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_session_ledger_id", idx),
                "ledger_id",
            )
            register_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_session_register_id", idx),
                "register_id",
            )
            receipt_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_session_receipt_id", idx),
                "receipt_id",
            )
            intake_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_session_intake_id", idx),
                "intake_id",
            )
            handoff_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_session_handoff_id", idx),
                "handoff_id",
            )
            brief_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_session_brief_id", idx),
                "brief_id",
            )
            pack_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_session_pack_id", idx),
                "pack_id",
            )
            agenda_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_agenda_id", idx),
                "agenda_id",
            )
            docket_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_docket_id", idx),
                "docket_id",
            )
            board_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_review_board_id", idx),
                "board_id",
            )
            checklist_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_checklist_id", idx),
                "checklist_id",
            )
            packet_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_packet_id", idx),
                "packet_id",
            )
            wave_id = normalize_string(
                get_required_field(index_record, "source_resolution_wave_id", idx),
                "wave_id",
            )

            wave_rank = normalize_int(get_required_field(index_record, "wave_rank", idx), "wave_rank")
            wave_type = normalize_string(get_required_field(index_record, "wave_type", idx), "wave_type")
            packet_priority = normalize_string(
                get_required_field(index_record, "packet_priority", idx),
                "packet_priority",
            )
            checklist_priority = normalize_string(
                get_required_field(index_record, "checklist_priority", idx),
                "checklist_priority",
            )
            review_board_priority = normalize_string(
                get_required_field(index_record, "review_board_priority", idx),
                "review_board_priority",
            )
            review_docket_priority = normalize_string(
                get_required_field(index_record, "review_docket_priority", idx),
                "review_docket_priority",
            )
            review_agenda_priority = normalize_string(
                get_required_field(index_record, "review_agenda_priority", idx),
                "review_agenda_priority",
            )
            review_session_pack_priority = normalize_string(
                get_required_field(index_record, "review_session_pack_priority", idx),
                "review_session_pack_priority",
            )
            review_session_brief_priority = normalize_string(
                get_required_field(index_record, "review_session_brief_priority", idx),
                "review_session_brief_priority",
            )
            review_session_handoff_priority = normalize_string(
                get_required_field(index_record, "review_session_handoff_priority", idx),
                "review_session_handoff_priority",
            )
            review_session_intake_priority = normalize_string(
                get_required_field(index_record, "review_session_intake_priority", idx),
                "review_session_intake_priority",
            )
            review_session_receipt_priority = normalize_string(
                get_required_field(index_record, "review_session_receipt_priority", idx),
                "review_session_receipt_priority",
            )
            review_session_register_priority = normalize_string(
                get_required_field(index_record, "review_session_register_priority", idx),
                "review_session_register_priority",
            )
            review_session_ledger_priority = normalize_string(
                get_required_field(index_record, "review_session_ledger_priority", idx),
                "review_session_ledger_priority",
            )
            review_session_journal_priority = normalize_string(
                get_required_field(index_record, "review_session_journal_priority", idx),
                "review_session_journal_priority",
            )
            review_session_archive_priority = normalize_string(
                get_required_field(index_record, "review_session_archive_priority", idx),
                "review_session_archive_priority",
            )
            review_session_catalog_priority = normalize_string(
                get_required_field(index_record, "review_session_catalog_priority", idx),
                "review_session_catalog_priority",
            )
            review_session_index_priority = normalize_string(
                get_required_field(index_record, "review_session_index_priority", idx),
                "review_session_index_priority",
            )
            review_lane = normalize_review_lane(
                get_required_field(index_record, "review_lane", idx),
                "review_lane",
            )

            member_cluster_ids = normalize_list(
                get_required_field(index_record, "member_cluster_ids", idx),
                "member_cluster_ids",
            )
            member_dependency_ids = normalize_list(
                get_required_field(index_record, "member_dependency_ids", idx),
                "member_dependency_ids",
            )
            member_source_refs = normalize_list(
                get_required_field(index_record, "member_source_refs", idx),
                "member_source_refs",
            )
            affected_proposal_ids = normalize_list(
                get_required_field(index_record, "affected_proposal_ids", idx),
                "affected_proposal_ids",
            )
            affected_queue_ids = normalize_list(
                get_required_field(index_record, "affected_queue_ids", idx),
                "affected_queue_ids",
            )

            affected_record_count = normalize_int(
                get_required_field(index_record, "affected_record_count", idx),
                "affected_record_count",
            )
            cluster_count = normalize_int(
                get_required_field(index_record, "cluster_count", idx),
                "cluster_count",
            )
            dependency_count = normalize_int(
                get_required_field(index_record, "dependency_count", idx),
                "dependency_count",
            )
            has_prohibition_path = normalize_bool(
                get_required_field(index_record, "has_prohibition_path", idx),
                "has_prohibition_path",
            )
            has_blocker_path = normalize_bool(
                get_required_field(index_record, "has_blocker_path", idx),
                "has_blocker_path",
            )
            terminal_posture = normalize_string(
                get_required_field(index_record, "terminal_posture", idx),
                "terminal_posture",
            )
        except ValueError as e:
            raise ValueError(f"Validation error in index record {idx}: {e}")

        directory_records.append(
            {
                "resolution_wave_packet_review_session_directory_id": (
                    f"resolution-wave-packet-review-session-directory-{idx + 1:04d}"
                ),
                "source_resolution_wave_packet_review_session_index_id": index_id,
                "source_resolution_wave_packet_review_session_catalog_id": catalog_id,
                "source_resolution_wave_packet_review_session_archive_id": archive_id,
                "source_resolution_wave_packet_review_session_journal_id": journal_id,
                "source_resolution_wave_packet_review_session_ledger_id": ledger_id,
                "source_resolution_wave_packet_review_session_register_id": register_id,
                "source_resolution_wave_packet_review_session_receipt_id": receipt_id,
                "source_resolution_wave_packet_review_session_intake_id": intake_id,
                "source_resolution_wave_packet_review_session_handoff_id": handoff_id,
                "source_resolution_wave_packet_review_session_brief_id": brief_id,
                "source_resolution_wave_packet_review_session_pack_id": pack_id,
                "source_resolution_wave_packet_review_agenda_id": agenda_id,
                "source_resolution_wave_packet_review_docket_id": docket_id,
                "source_resolution_wave_packet_review_board_id": board_id,
                "source_resolution_wave_packet_checklist_id": checklist_id,
                "source_resolution_wave_packet_id": packet_id,
                "source_resolution_wave_id": wave_id,
                "wave_rank": wave_rank,
                "wave_type": wave_type,
                "packet_priority": packet_priority,
                "checklist_priority": checklist_priority,
                "review_board_priority": review_board_priority,
                "review_docket_priority": review_docket_priority,
                "review_agenda_priority": review_agenda_priority,
                "review_session_pack_priority": review_session_pack_priority,
                "review_session_brief_priority": review_session_brief_priority,
                "review_session_handoff_priority": review_session_handoff_priority,
                "review_session_intake_priority": review_session_intake_priority,
                "review_session_receipt_priority": review_session_receipt_priority,
                "review_session_register_priority": review_session_register_priority,
                "review_session_ledger_priority": review_session_ledger_priority,
                "review_session_journal_priority": review_session_journal_priority,
                "review_session_archive_priority": review_session_archive_priority,
                "review_session_catalog_priority": review_session_catalog_priority,
                "review_session_index_priority": review_session_index_priority,
                "review_lane": review_lane,
                "review_session_directory_priority": review_session_index_priority,
                "directory_position": idx + 1,
                "member_cluster_ids": member_cluster_ids,
                "member_dependency_ids": member_dependency_ids,
                "member_source_refs": member_source_refs,
                "affected_proposal_ids": affected_proposal_ids,
                "affected_queue_ids": affected_queue_ids,
                "affected_record_count": affected_record_count,
                "cluster_count": cluster_count,
                "dependency_count": dependency_count,
                "has_prohibition_path": has_prohibition_path,
                "has_blocker_path": has_blocker_path,
                "terminal_posture": terminal_posture,
            }
        )

    directory_records.sort(
        key=lambda rec: (
            LANE_ORDER[rec["review_lane"]],
            rec["wave_rank"],
            rec["source_resolution_wave_packet_review_session_index_id"],
            rec["source_resolution_wave_packet_review_session_catalog_id"],
        )
    )

    for idx, rec in enumerate(directory_records):
        rec["directory_position"] = idx + 1

    return directory_records


def generate_markdown(payload, records):
    md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Directory

**Version**: v6.8-slice-1
**Generated At (UTC)**: {payload['generated_at_utc']}

## Summary

| Field | Value |
|---|---|
| upstream_session_index_count | {payload['upstream_session_index_count']} |
| total_review_session_directory_records | {len(records)} |
| review_lane_counts | {payload['review_lane_counts']} |
| coverage_reconciled | {payload['coverage_reconciled']} |
| deterministic_ordering | {payload['deterministic_ordering']} |

## Source Versions

| Source | Version |
|---|---|
| model_adjustment_release_resolution_wave_packet_review_session_index_version | {payload['upstream_session_index_version']} |

"""

    for rec in records:
        md += f"""## {rec['resolution_wave_packet_review_session_directory_id']}

- source_resolution_wave_packet_review_session_index_id: {rec['source_resolution_wave_packet_review_session_index_id']}
- source_resolution_wave_packet_review_session_catalog_id: {rec['source_resolution_wave_packet_review_session_catalog_id']}
- source_resolution_wave_packet_review_session_archive_id: {rec['source_resolution_wave_packet_review_session_archive_id']}
- source_resolution_wave_packet_review_session_journal_id: {rec['source_resolution_wave_packet_review_session_journal_id']}
- source_resolution_wave_packet_review_session_ledger_id: {rec['source_resolution_wave_packet_review_session_ledger_id']}
- source_resolution_wave_packet_review_session_register_id: {rec['source_resolution_wave_packet_review_session_register_id']}
- source_resolution_wave_packet_review_session_receipt_id: {rec['source_resolution_wave_packet_review_session_receipt_id']}
- source_resolution_wave_packet_review_session_intake_id: {rec['source_resolution_wave_packet_review_session_intake_id']}
- source_resolution_wave_packet_review_session_handoff_id: {rec['source_resolution_wave_packet_review_session_handoff_id']}
- source_resolution_wave_packet_review_session_brief_id: {rec['source_resolution_wave_packet_review_session_brief_id']}
- source_resolution_wave_packet_review_session_pack_id: {rec['source_resolution_wave_packet_review_session_pack_id']}
- source_resolution_wave_packet_review_agenda_id: {rec['source_resolution_wave_packet_review_agenda_id']}
- source_resolution_wave_packet_review_docket_id: {rec['source_resolution_wave_packet_review_docket_id']}
- source_resolution_wave_packet_review_board_id: {rec['source_resolution_wave_packet_review_board_id']}
- source_resolution_wave_packet_checklist_id: {rec['source_resolution_wave_packet_checklist_id']}
- source_resolution_wave_packet_id: {rec['source_resolution_wave_packet_id']}
- source_resolution_wave_id: {rec['source_resolution_wave_id']}
- wave_rank: {rec['wave_rank']}
- wave_type: {rec['wave_type']}
- packet_priority: {rec['packet_priority']}
- checklist_priority: {rec['checklist_priority']}
- review_board_priority: {rec['review_board_priority']}
- review_docket_priority: {rec['review_docket_priority']}
- review_agenda_priority: {rec['review_agenda_priority']}
- review_session_pack_priority: {rec['review_session_pack_priority']}
- review_session_brief_priority: {rec['review_session_brief_priority']}
- review_session_handoff_priority: {rec['review_session_handoff_priority']}
- review_session_intake_priority: {rec['review_session_intake_priority']}
- review_session_receipt_priority: {rec['review_session_receipt_priority']}
- review_session_register_priority: {rec['review_session_register_priority']}
- review_session_ledger_priority: {rec['review_session_ledger_priority']}
- review_session_journal_priority: {rec['review_session_journal_priority']}
- review_session_archive_priority: {rec['review_session_archive_priority']}
- review_session_catalog_priority: {rec['review_session_catalog_priority']}
- review_session_index_priority: {rec['review_session_index_priority']}
- review_lane: {rec['review_lane']}
- review_session_directory_priority: {rec['review_session_directory_priority']}
- directory_position: {rec['directory_position']}
- terminal_posture: {rec['terminal_posture']}

### member_cluster_ids

{json.dumps(rec['member_cluster_ids'], indent=2)}

### member_dependency_ids

{json.dumps(rec['member_dependency_ids'], indent=2)}

### member_source_refs

{json.dumps(rec['member_source_refs'], indent=2)}

### affected_proposal_ids

{json.dumps(rec['affected_proposal_ids'], indent=2)}

### affected_queue_ids

{json.dumps(rec['affected_queue_ids'], indent=2)}

- affected_record_count: {rec['affected_record_count']}
- cluster_count: {rec['cluster_count']}
- dependency_count: {rec['dependency_count']}
- has_prohibition_path: {rec['has_prohibition_path']}
- has_blocker_path: {rec['has_blocker_path']}

"""

    return md


def main():
    try:
        index_path = SOURCE_PATHS["index"]
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Upstream index JSON not found: {index_path}")

        with open(index_path, "r", encoding="utf-8") as f:
            index_payload = json.load(f)

        index_records = validate_upstream_payload(index_payload, index_path)
        directory_records = build_directory_records(index_records)

        coverage_reconciled = len(index_records) == len(directory_records)

        ordering_keys = [
            (
                LANE_ORDER[rec["review_lane"]],
                rec["wave_rank"],
                rec["source_resolution_wave_packet_review_session_index_id"],
                rec["source_resolution_wave_packet_review_session_catalog_id"],
            )
            for rec in directory_records
        ]
        is_sorted = ordering_keys == sorted(ordering_keys)

        lane_counts = {}
        for rec in directory_records:
            lane = rec["review_lane"]
            lane_counts[lane] = lane_counts.get(lane, 0) + 1

        output_payload = {
            "model_adjustment_release_resolution_wave_packet_review_session_directory_version": "v6.8-slice-1",
            "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "upstream_session_index_count": len(index_records),
            "upstream_session_index_version": index_payload.get(
                "model_adjustment_release_resolution_wave_packet_review_session_index_version"
            ),
            "release_resolution_wave_packet_review_session_directory": directory_records,
            "coverage_reconciled": coverage_reconciled,
            "deterministic_ordering": is_sorted,
            "review_lane_counts": lane_counts,
        }

        markdown_output = generate_markdown(output_payload, directory_records)

        os.makedirs(os.path.dirname(OUTPUT_PATHS["json"]), exist_ok=True)

        with open(OUTPUT_PATHS["json"], "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['json'])}")

        with open(OUTPUT_PATHS["md"], "w", encoding="utf-8") as f:
            f.write(markdown_output)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['md'])}")

        print(
            f"[STATUS] review_session_directory_records={len(directory_records)} "
            f"upstream_session_index_count={len(index_records)} "
            f"coverage_reconciled={coverage_reconciled} deterministic_ordering={is_sorted} "
            f"review_lane_counts={lane_counts}"
        )
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
