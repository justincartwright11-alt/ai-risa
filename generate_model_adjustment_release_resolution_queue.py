"""
generate_model_adjustment_release_resolution_queue.py

v4.8-slice-1 — Read-only controlled release resolution-queue generator.

Consumes the frozen v4.7 release finality registry output and emits a
deterministic, read-only operator work queue of terminal release outcomes.

No re-classification logic. No release recommendation logic. No upstream
mutation.

Hard rules:
- no execution
- no auto-promotion
- no config writes
- no model mutation
- no upstream governance artifact mutation
- no re-classification of finality states
- no release recommendation path
"""

import json
import os
import sys
from datetime import datetime, timezone


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OPS_DIR = os.path.join(SCRIPT_DIR, "ops", "model_adjustments")

SOURCE_PATHS = {
    "model_adjustment_release_finality_registry_json": (
        "ops/model_adjustments/model_adjustment_release_finality_registry.json"
    ),
}

OUTPUT_JSON = os.path.join(OPS_DIR, "model_adjustment_release_resolution_queue.json")
OUTPUT_MD = os.path.join(OPS_DIR, "model_adjustment_release_resolution_queue.md")

VERSION = "v4.8-slice-1"
EXPECTED_RECORD_COUNT = 4

KNOWN_FINALITY_STATES = frozenset({
    "governance_final_no_release",
    "structurally_closed",
    "temporarily_closed",
})

REQUIRED_REGISTRY_FIELDS = (
    "release_finality_registry_id",
    "release_finality_decision_id",
    "proposal_id",
    "release_finality_state",
    "release_finality_class",
    "release_finality_reason",
    "registry_blocker_refs",
    "registry_prohibition_refs",
    "registry_remaining_resolutions",
    "blocker_ref_count",
    "prohibition_ref_count",
    "remaining_resolution_count",
    "required_release_authority",
    "required_operator_role",
    "rollback_reference",
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


def validate_registry_record(record: dict, index: int) -> None:
    for field in REQUIRED_REGISTRY_FIELDS:
        if field not in record:
            raise ValueError(
                f"registry record[{index}] missing required field {field!r}; "
                "fail-closed — manual review required"
            )

    if not record.get("release_finality_registry_id"):
        raise ValueError(
            f"registry record[{index}] has empty release_finality_registry_id; "
            "fail-closed — manual review required"
        )
    if not record.get("proposal_id"):
        raise ValueError(
            f"registry record[{index}] has empty proposal_id; "
            "fail-closed — manual review required"
        )

    state = record.get("release_finality_state", "")
    if state not in KNOWN_FINALITY_STATES:
        raise ValueError(
            f"registry record[{index}] unrecognized release_finality_state={state!r}; "
            "fail-closed — manual review required"
        )


def queue_priority(has_prohibitions: bool, has_blockers: bool, remaining_count: int) -> str:
    if has_prohibitions:
        return "P0_terminal_with_prohibitions"
    if has_blockers:
        return "P1_terminal_with_blockers"
    if remaining_count > 0:
        return "P2_terminal_resolution_backlog"
    return "P3_terminal_review_only"


def resolution_burden_score(
    prohibition_count: int,
    blocker_count: int,
    remaining_count: int,
) -> int:
    return (prohibition_count * 100) + (blocker_count * 10) + remaining_count


def build_sort_key(record: dict) -> str:
    has_prohibitions = bool(record.get("prohibition_ref_count", 0))
    has_blockers = bool(record.get("blocker_ref_count", 0))
    remaining_count = int(record.get("remaining_resolution_count", 0))
    burden_score = resolution_burden_score(
        int(record.get("prohibition_ref_count", 0)),
        int(record.get("blocker_ref_count", 0)),
        remaining_count,
    )

    return "|".join(
        [
            f"severity-{1 if has_prohibitions else 0}",
            f"blockers-{1 if has_blockers else 0}",
            f"burden-{burden_score:06d}",
            f"remaining-{remaining_count:06d}",
            record.get("release_finality_registry_id", ""),
        ]
    )


def sort_records_for_queue(records: list) -> list:
    return sorted(
        records,
        key=lambda record: (
            -int(bool(record.get("prohibition_ref_count", 0))),
            -int(bool(record.get("blocker_ref_count", 0))),
            -resolution_burden_score(
                int(record.get("prohibition_ref_count", 0)),
                int(record.get("blocker_ref_count", 0)),
                int(record.get("remaining_resolution_count", 0)),
            ),
            -int(record.get("remaining_resolution_count", 0)),
            record.get("release_finality_registry_id", ""),
        ),
    )


def build_queue_records(registry_records: list) -> list:
    sorted_registry_records = sort_records_for_queue(registry_records)

    output = []
    for index, registry_record in enumerate(sorted_registry_records, start=1):
        validate_registry_record(registry_record, index)

        prohibition_count = int(registry_record.get("prohibition_ref_count", 0))
        blocker_count = int(registry_record.get("blocker_ref_count", 0))
        remaining_count = int(registry_record.get("remaining_resolution_count", 0))
        has_prohibitions = prohibition_count > 0
        has_blockers = blocker_count > 0
        burden_score = resolution_burden_score(
            prohibition_count,
            blocker_count,
            remaining_count,
        )

        output.append(
            {
                "release_resolution_queue_id": f"release-resolution-queue-{index:04d}",
                "release_finality_registry_id": registry_record["release_finality_registry_id"],
                "release_finality_decision_id": registry_record["release_finality_decision_id"],
                "proposal_id": registry_record["proposal_id"],
                "release_condition_id": registry_record.get("release_condition_id", ""),
                "release_authority_id": registry_record.get("release_authority_id", ""),
                "release_gate_id": registry_record.get("release_gate_id", ""),
                "release_decision_id": registry_record.get("release_decision_id", ""),
                "release_ineligibility_id": registry_record.get("release_ineligibility_id", ""),
                "release_closure_assessment_id": registry_record.get(
                    "release_closure_assessment_id", ""
                ),
                "release_finality_state": registry_record["release_finality_state"],
                "release_finality_class": registry_record["release_finality_class"],
                "release_finality_reason": registry_record["release_finality_reason"],
                "queue_priority": queue_priority(
                    has_prohibitions,
                    has_blockers,
                    remaining_count,
                ),
                "queue_sort_key": build_sort_key(registry_record),
                "resolution_burden_score": burden_score,
                "has_prohibitions": has_prohibitions,
                "has_blockers": has_blockers,
                "remaining_resolution_count": remaining_count,
                "registry_blocker_refs": dedup_sorted(
                    registry_record.get("registry_blocker_refs", [])
                ),
                "registry_prohibition_refs": dedup_sorted(
                    registry_record.get("registry_prohibition_refs", [])
                ),
                "registry_remaining_resolutions": dedup_sorted(
                    registry_record.get("registry_remaining_resolutions", [])
                ),
                "terminal_posture": (
                    f"{registry_record['release_finality_state']}"
                    f"::{registry_record['release_finality_class']}"
                ),
                "required_release_authority": registry_record.get(
                    "required_release_authority", ""
                ),
                "required_operator_role": registry_record.get("required_operator_role", ""),
                "rollback_reference": registry_record.get("rollback_reference", ""),
                "queue_notes": (
                    "v4_8_read_only_resolution_queue_projection_of_v4_7_registry"
                    "_no_reclassification_no_release_recommendation_no_upstream_mutation"
                ),
                "upstream_source": SOURCE_PATHS[
                    "model_adjustment_release_finality_registry_json"
                ],
            }
        )

    return output


def validate_queue(records: list, upstream_registry_count: int) -> None:
    queue_ids = [record["release_resolution_queue_id"] for record in records]
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("duplicate release_resolution_queue_id in output; fail-closed")

    registry_ids = [record["release_finality_registry_id"] for record in records]
    if len(registry_ids) != len(set(registry_ids)):
        raise ValueError("duplicate release_finality_registry_id in queue; fail-closed")

    proposal_ids = [record["proposal_id"] for record in records]
    if len(proposal_ids) != len(set(proposal_ids)):
        raise ValueError("duplicate proposal_id in queue records; fail-closed")

    if len(records) != upstream_registry_count:
        raise ValueError(
            f"queue record count {len(records)} does not match upstream registry count "
            f"{upstream_registry_count}; fail-closed"
        )
    if len(records) != EXPECTED_RECORD_COUNT:
        raise ValueError(
            f"queue record count {len(records)} does not match "
            f"EXPECTED_RECORD_COUNT={EXPECTED_RECORD_COUNT}; fail-closed"
        )

    for record in records:
        state = record.get("release_finality_state", "")
        if state not in KNOWN_FINALITY_STATES:
            raise ValueError(
                f"unrecognized release_finality_state={state!r} for proposal "
                f"{record.get('proposal_id')!r}; fail-closed"
            )
        for field in (
            "registry_blocker_refs",
            "registry_prohibition_refs",
            "registry_remaining_resolutions",
        ):
            values = record.get(field, [])
            if len(values) != len(set(values)):
                raise ValueError(
                    f"duplicate entries in {field!r} for proposal "
                    f"{record.get('proposal_id')!r}; fail-closed"
                )


def build_summary(records: list, upstream_registry_count: int) -> dict:
    proposals_covered = len({record.get("proposal_id") for record in records})
    states = sorted({record.get("release_finality_state", "") for record in records})
    state_counts = {
        state: sum(1 for record in records if record.get("release_finality_state") == state)
        for state in states
    }
    priorities = sorted({record.get("queue_priority", "") for record in records})
    priority_counts = {
        priority: sum(1 for record in records if record.get("queue_priority") == priority)
        for priority in priorities
    }

    return {
        "upstream_registry_count": upstream_registry_count,
        "total_queue_records": len(records),
        "proposals_covered": proposals_covered,
        "all_proposals_covered": proposals_covered == upstream_registry_count,
        "record_count_matches_expected": len(records) == EXPECTED_RECORD_COUNT,
        "release_finality_state_counts": state_counts,
        "queue_priority_counts": priority_counts,
        "deterministic_ordering": True,
    }


def build_source_versions(registry_data: dict) -> dict:
    return {
        "model_adjustment_release_finality_registry_version": registry_data.get(
            "model_adjustment_release_finality_registry_version", ""
        )
    }


def write_markdown(records: list, summary: dict, source_versions: dict, generated_at: str):
    lines = [
        "# Model Adjustment Release Resolution Queue",
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
        lines.append(f"## {record['release_resolution_queue_id']}")
        lines.append("")
        lines.append(f"- release_finality_registry_id: {record['release_finality_registry_id']}")
        lines.append(f"- release_finality_decision_id: {record['release_finality_decision_id']}")
        lines.append(f"- proposal_id: {record['proposal_id']}")
        lines.append(f"- release_finality_state: {record['release_finality_state']}")
        lines.append(f"- release_finality_class: {record['release_finality_class']}")
        lines.append(f"- release_finality_reason: {record['release_finality_reason']}")
        lines.append(f"- queue_priority: {record['queue_priority']}")
        lines.append(f"- queue_sort_key: {record['queue_sort_key']}")
        lines.append(f"- resolution_burden_score: {record['resolution_burden_score']}")
        lines.append(f"- has_prohibitions: {record['has_prohibitions']}")
        lines.append(f"- has_blockers: {record['has_blockers']}")
        lines.append(f"- remaining_resolution_count: {record['remaining_resolution_count']}")
        lines.append(f"- terminal_posture: {record['terminal_posture']}")
        lines.append(f"- required_release_authority: {record['required_release_authority']}")
        lines.append(f"- required_operator_role: {record['required_operator_role']}")
        lines.append(f"- rollback_reference: {record['rollback_reference']}")
        lines.append("")

        for section in [
            "registry_remaining_resolutions",
            "registry_blocker_refs",
            "registry_prohibition_refs",
        ]:
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

    registry_data, errors["model_adjustment_release_finality_registry_json"] = load_source(
        "model_adjustment_release_finality_registry_json"
    )

    failures = [key for key, value in errors.items() if value is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    upstream_registry_records = registry_data.get("release_finality_registry", [])
    upstream_registry_count = len(upstream_registry_records)

    records = build_queue_records(upstream_registry_records)
    validate_queue(records, upstream_registry_count)

    summary = build_summary(records, upstream_registry_count)
    source_versions = build_source_versions(registry_data)
    source_status = {f"{key}_error": errors[key] for key in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_resolution_queue_version": VERSION,
        "release_resolution_queue_summary": summary,
        "release_resolution_queue": records,
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
        f"queue_records={summary['total_queue_records']} "
        f"proposals_covered={summary['proposals_covered']} "
        f"all_covered={summary['all_proposals_covered']} "
        f"record_count_matches_expected={summary['record_count_matches_expected']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"release_finality_state={summary['release_finality_state_counts']} "
        f"queue_priority={summary['queue_priority_counts']}"
    )


if __name__ == "__main__":
    main()