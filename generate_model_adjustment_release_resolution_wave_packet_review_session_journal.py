#!/usr/bin/env python3
"""
v6.4: Model Adjustment Release Resolution Wave Packet Review Session Journal Generator

Pure downstream projection of review-session-ledger into operator-journal bookkeeping layer.
Consumes: model_adjustment_release_resolution_wave_packet_review_session_ledger.json (v6.3)
Produces: model_adjustment_release_resolution_wave_packet_review_session_journal.json (v6.4)
          model_adjustment_release_resolution_wave_packet_review_session_journal.md (v6.4)

Behavior:
- One journal entry per upstream ledger entry
- Preserves all upstream priority, lane, posture fields exactly (pass-through)
- Adds journal-specific projection fields only (journal_position, journal_priority, journal_id)
- Deterministic ordering stable on ledger_id / register_id
- No re-classification, no release logic, no policy logic
- Fail-closed validation: raises explicit errors on malformed upstream data
- Markdown as pure projection of JSON
"""

import datetime
import json
import os
import sys

SOURCE_PATHS = {
    "ledger": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_ledger.json",
}

OUTPUT_PATHS = {
    "json": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_journal.json",
    "md": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_journal.md",
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


def normalize_list(value, name):
    if not isinstance(value, list):
        raise ValueError(f"Invalid {name}: expected list, got {type(value).__name__}")
    return sorted(set(value))


def normalize_int(value, name):
    if not isinstance(value, int):
        raise ValueError(f"Invalid {name}: expected int, got {type(value).__name__}")
    return value


def normalize_bool(value, name):
    if not isinstance(value, bool):
        raise ValueError(f"Invalid {name}: expected bool, got {type(value).__name__}")
    return value


def validate_upstream_payload(payload, path):
    if not isinstance(payload, dict):
        raise ValueError(f"Upstream payload {path} is not a dict: {type(payload).__name__}")

    version = payload.get("model_adjustment_release_resolution_wave_packet_review_session_ledger_version")
    if version != "v6.3-slice-1":
        raise ValueError(f"Expected ledger version 'v6.3-slice-1', got {repr(version)}")

    records = payload.get("release_resolution_wave_packet_review_session_ledger", [])
    if not isinstance(records, list):
        raise ValueError(
            "release_resolution_wave_packet_review_session_ledger is not a list: "
            f"{type(records).__name__}"
        )
    if len(records) == 0:
        raise ValueError("No ledger records found in upstream payload")
    return records


def build_journal_records(ledger_records):
    journal_records = []

    for idx, ledger_record in enumerate(ledger_records):
        try:
            ledger_id = normalize_string(
                ledger_record.get("resolution_wave_packet_review_session_ledger_id"),
                "ledger_id",
            )
            register_id = normalize_string(
                ledger_record.get("source_resolution_wave_packet_review_session_register_id"),
                "register_id",
            )
            receipt_id = normalize_string(
                ledger_record.get("source_resolution_wave_packet_review_session_receipt_id"),
                "receipt_id",
            )
            intake_id = normalize_string(
                ledger_record.get("source_resolution_wave_packet_review_session_intake_id"),
                "intake_id",
            )
            handoff_id = normalize_string(
                ledger_record.get("source_resolution_wave_packet_review_session_handoff_id"),
                "handoff_id",
            )
            brief_id = normalize_string(
                ledger_record.get("source_resolution_wave_packet_review_session_brief_id"),
                "brief_id",
            )
            pack_id = normalize_string(
                ledger_record.get("source_resolution_wave_packet_review_session_pack_id"),
                "pack_id",
            )
            agenda_id = normalize_string(
                ledger_record.get("source_resolution_wave_packet_review_agenda_id"),
                "agenda_id",
            )
            docket_id = normalize_string(
                ledger_record.get("source_resolution_wave_packet_review_docket_id"),
                "docket_id",
            )
            board_id = normalize_string(
                ledger_record.get("source_resolution_wave_packet_review_board_id"),
                "board_id",
            )
            checklist_id = normalize_string(
                ledger_record.get("source_resolution_wave_packet_checklist_id"),
                "checklist_id",
            )
            packet_id = normalize_string(
                ledger_record.get("source_resolution_wave_packet_id"),
                "packet_id",
            )
            wave_id = normalize_string(
                ledger_record.get("source_resolution_wave_id"),
                "wave_id",
            )

            wave_rank = normalize_int(ledger_record.get("wave_rank"), "wave_rank")
            wave_type = normalize_string(ledger_record.get("wave_type"), "wave_type")
            packet_priority = normalize_string(ledger_record.get("packet_priority"), "packet_priority")
            checklist_priority = normalize_string(ledger_record.get("checklist_priority"), "checklist_priority")
            review_board_priority = normalize_string(
                ledger_record.get("review_board_priority"), "review_board_priority"
            )
            review_docket_priority = normalize_string(
                ledger_record.get("review_docket_priority"), "review_docket_priority"
            )
            review_agenda_priority = normalize_string(
                ledger_record.get("review_agenda_priority"), "review_agenda_priority"
            )
            review_session_pack_priority = normalize_string(
                ledger_record.get("review_session_pack_priority"), "review_session_pack_priority"
            )
            review_session_brief_priority = normalize_string(
                ledger_record.get("review_session_brief_priority"), "review_session_brief_priority"
            )
            review_session_handoff_priority = normalize_string(
                ledger_record.get("review_session_handoff_priority"), "review_session_handoff_priority"
            )
            review_session_intake_priority = normalize_string(
                ledger_record.get("review_session_intake_priority"), "review_session_intake_priority"
            )
            review_session_receipt_priority = normalize_string(
                ledger_record.get("review_session_receipt_priority"), "review_session_receipt_priority"
            )
            review_session_register_priority = normalize_string(
                ledger_record.get("review_session_register_priority"), "review_session_register_priority"
            )
            review_session_ledger_priority = normalize_string(
                ledger_record.get("review_session_ledger_priority"), "review_session_ledger_priority"
            )
            review_lane = normalize_string(ledger_record.get("review_lane"), "review_lane")
            terminal_posture = normalize_string(ledger_record.get("terminal_posture"), "terminal_posture")

            member_cluster_ids = normalize_list(
                ledger_record.get("member_cluster_ids", []), "member_cluster_ids"
            )
            member_dependency_ids = normalize_list(
                ledger_record.get("member_dependency_ids", []), "member_dependency_ids"
            )
            member_source_refs = normalize_list(
                ledger_record.get("member_source_refs", []), "member_source_refs"
            )
            affected_proposal_ids = normalize_list(
                ledger_record.get("affected_proposal_ids", []), "affected_proposal_ids"
            )
            affected_queue_ids = normalize_list(
                ledger_record.get("affected_queue_ids", []), "affected_queue_ids"
            )

            affected_record_count = normalize_int(
                ledger_record.get("affected_record_count"), "affected_record_count"
            )
            cluster_count = normalize_int(ledger_record.get("cluster_count"), "cluster_count")
            dependency_count = normalize_int(ledger_record.get("dependency_count"), "dependency_count")
            has_prohibition_path = normalize_bool(
                ledger_record.get("has_prohibition_path"), "has_prohibition_path"
            )
            has_blocker_path = normalize_bool(
                ledger_record.get("has_blocker_path"), "has_blocker_path"
            )
        except ValueError as e:
            raise ValueError(f"Validation error in ledger record {idx}: {e}")

        journal_records.append(
            {
                "resolution_wave_packet_review_session_journal_id": (
                    f"resolution-wave-packet-review-session-journal-{idx + 1:04d}"
                ),
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
                "review_lane": review_lane,
                "review_session_journal_priority": review_session_ledger_priority,
                "journal_position": idx + 1,
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

    journal_records.sort(
        key=lambda rec: (
            LANE_ORDER.get(rec["review_lane"], 999),
            rec["wave_rank"],
            rec["source_resolution_wave_packet_review_session_ledger_id"],
            rec["source_resolution_wave_packet_review_session_register_id"],
        )
    )

    for idx, rec in enumerate(journal_records):
        rec["journal_position"] = idx + 1
    return journal_records


def generate_markdown(payload, records):
    md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Journal

**Version**: v6.4-slice-1
**Generated At (UTC)**: {payload['generated_at_utc']}

## Summary

| Field | Value |
|---|---|
| upstream_session_ledger_count | {payload['upstream_session_ledger_count']} |
| total_review_session_journal_records | {len(records)} |
| review_lane_counts | {payload['review_lane_counts']} |
| coverage_reconciled | {payload['coverage_reconciled']} |
| deterministic_ordering | {payload['deterministic_ordering']} |

## Source Versions

| Source | Version |
|---|---|
| model_adjustment_release_resolution_wave_packet_review_session_ledger_version | {payload['upstream_session_ledger_version']} |

"""

    for rec in records:
        md += f"""## {rec['resolution_wave_packet_review_session_journal_id']}

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
- review_lane: {rec['review_lane']}
- review_session_journal_priority: {rec['review_session_journal_priority']}
- journal_position: {rec['journal_position']}
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
        ledger_path = SOURCE_PATHS["ledger"]
        if not os.path.exists(ledger_path):
            raise FileNotFoundError(f"Upstream ledger JSON not found: {ledger_path}")

        with open(ledger_path, "r") as f:
            ledger_payload = json.load(f)

        ledger_records = validate_upstream_payload(ledger_payload, ledger_path)
        journal_records = build_journal_records(ledger_records)

        coverage_reconciled = len(ledger_records) == len(journal_records)
        is_sorted = all(
            journal_records[i]["journal_position"] <= journal_records[i + 1]["journal_position"]
            for i in range(len(journal_records) - 1)
        )

        lane_counts = {}
        for rec in journal_records:
            lane = rec["review_lane"]
            lane_counts[lane] = lane_counts.get(lane, 0) + 1

        output_payload = {
            "model_adjustment_release_resolution_wave_packet_review_session_journal_version": "v6.4-slice-1",
            "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "upstream_session_ledger_count": len(ledger_records),
            "upstream_session_ledger_version": ledger_payload.get(
                "model_adjustment_release_resolution_wave_packet_review_session_ledger_version"
            ),
            "release_resolution_wave_packet_review_session_journal": journal_records,
            "coverage_reconciled": coverage_reconciled,
            "deterministic_ordering": is_sorted,
            "review_lane_counts": lane_counts,
        }

        markdown_output = generate_markdown(output_payload, journal_records)

        os.makedirs(os.path.dirname(OUTPUT_PATHS["json"]), exist_ok=True)

        with open(OUTPUT_PATHS["json"], "w") as f:
            json.dump(output_payload, f, indent=2)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['json'])}")

        with open(OUTPUT_PATHS["md"], "w") as f:
            f.write(markdown_output)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['md'])}")

        print(
            f"[STATUS] review_session_journal_records={len(journal_records)} "
            f"upstream_session_ledger_count={len(ledger_records)} "
            f"coverage_reconciled={coverage_reconciled} deterministic_ordering={is_sorted} "
            f"review_lane_counts={lane_counts}"
        )
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
