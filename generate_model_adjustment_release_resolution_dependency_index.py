"""
generate_model_adjustment_release_resolution_dependency_index.py

v4.9-slice-1 — Read-only controlled release resolution-dependency-index
generator.

Consumes the frozen v4.8 release resolution queue output and emits a
deterministic cross-record dependency index for shared blockers, prohibitions,
and remaining resolutions.

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
    "model_adjustment_release_resolution_queue_json": (
        "ops/model_adjustments/model_adjustment_release_resolution_queue.json"
    ),
}

OUTPUT_JSON = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_dependency_index.json",
)
OUTPUT_MD = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_dependency_index.md",
)

VERSION = "v4.9-slice-1"
EXPECTED_QUEUE_RECORD_COUNT = 4

KNOWN_FINALITY_STATES = frozenset({
    "governance_final_no_release",
    "structurally_closed",
    "temporarily_closed",
})

DEPENDENCY_TYPE_ORDER = {
    "prohibition_dependency": 0,
    "blocker_dependency": 1,
    "remaining_resolution_dependency": 2,
}

DEPENDENCY_PRIORITY_BY_TYPE = {
    "prohibition_dependency": "P0_shared_prohibition_dependency",
    "blocker_dependency": "P1_shared_blocker_dependency",
    "remaining_resolution_dependency": "P2_shared_remaining_resolution_dependency",
}

REQUIRED_QUEUE_FIELDS = (
    "release_resolution_queue_id",
    "release_finality_registry_id",
    "proposal_id",
    "release_finality_state",
    "release_finality_class",
    "has_prohibitions",
    "has_blockers",
    "registry_blocker_refs",
    "registry_prohibition_refs",
    "registry_remaining_resolutions",
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


def validate_queue_record(record: dict, index: int) -> None:
    for field in REQUIRED_QUEUE_FIELDS:
        if field not in record:
            raise ValueError(
                f"queue record[{index}] missing required field {field!r}; "
                "fail-closed — manual review required"
            )
    if not record.get("release_resolution_queue_id"):
        raise ValueError(
            f"queue record[{index}] has empty release_resolution_queue_id; "
            "fail-closed — manual review required"
        )
    if not record.get("proposal_id"):
        raise ValueError(
            f"queue record[{index}] has empty proposal_id; "
            "fail-closed — manual review required"
        )
    state = record.get("release_finality_state", "")
    if state not in KNOWN_FINALITY_STATES:
        raise ValueError(
            f"queue record[{index}] unrecognized release_finality_state={state!r}; "
            "fail-closed — manual review required"
        )


def build_dependency_sort_key(record: dict) -> tuple:
    return (
        DEPENDENCY_TYPE_ORDER[record["dependency_type"]],
        -record["affected_record_count"],
        record["source_ref"],
    )


def build_terminal_posture(postures: list) -> str:
    return "|".join(dedup_sorted(postures))


def aggregate_dependencies(queue_records: list) -> list:
    aggregates = {}

    dependency_sources = (
        ("prohibition_dependency", "registry_prohibition_refs"),
        ("blocker_dependency", "registry_blocker_refs"),
        ("remaining_resolution_dependency", "registry_remaining_resolutions"),
    )

    for index, queue_record in enumerate(queue_records, start=1):
        validate_queue_record(queue_record, index)
        for dependency_type, field_name in dependency_sources:
            for source_ref in dedup_sorted(queue_record.get(field_name, [])):
                key = (dependency_type, source_ref)
                if key not in aggregates:
                    aggregates[key] = {
                        "dependency_type": dependency_type,
                        "source_ref": source_ref,
                        "affected_proposal_ids": set(),
                        "affected_queue_ids": set(),
                        "terminal_postures": set(),
                        "has_prohibition_path": False,
                        "has_blocker_path": False,
                    }
                aggregates[key]["affected_proposal_ids"].add(queue_record["proposal_id"])
                aggregates[key]["affected_queue_ids"].add(
                    queue_record["release_resolution_queue_id"]
                )
                aggregates[key]["terminal_postures"].add(
                    queue_record.get("terminal_posture", "")
                )
                aggregates[key]["has_prohibition_path"] = (
                    aggregates[key]["has_prohibition_path"]
                    or bool(queue_record.get("has_prohibitions", False))
                )
                aggregates[key]["has_blocker_path"] = (
                    aggregates[key]["has_blocker_path"]
                    or bool(queue_record.get("has_blockers", False))
                )

    output = []
    sorted_aggregates = sorted(
        aggregates.values(),
        key=lambda aggregate: (
            DEPENDENCY_TYPE_ORDER[aggregate["dependency_type"]],
            -len(aggregate["affected_queue_ids"]),
            aggregate["source_ref"],
        ),
    )

    for index, aggregate in enumerate(sorted_aggregates, start=1):
        output.append(
            {
                "resolution_dependency_id": f"resolution-dependency-{index:04d}",
                "dependency_type": aggregate["dependency_type"],
                "source_ref": aggregate["source_ref"],
                "affected_proposal_ids": dedup_sorted(aggregate["affected_proposal_ids"]),
                "affected_queue_ids": dedup_sorted(aggregate["affected_queue_ids"]),
                "affected_record_count": len(aggregate["affected_queue_ids"]),
                "has_prohibition_path": aggregate["has_prohibition_path"],
                "has_blocker_path": aggregate["has_blocker_path"],
                "dependency_priority": DEPENDENCY_PRIORITY_BY_TYPE[
                    aggregate["dependency_type"]
                ],
                "terminal_posture": build_terminal_posture(
                    aggregate["terminal_postures"]
                ),
                "dependency_index_notes": (
                    "v4_9_read_only_shared_dependency_projection_of_v4_8_queue"
                    "_no_reclassification_no_release_recommendation_no_upstream_mutation"
                ),
                "upstream_source": SOURCE_PATHS[
                    "model_adjustment_release_resolution_queue_json"
                ],
            }
        )

    return sorted(output, key=build_dependency_sort_key)


def validate_dependency_index(records: list, queue_records: list) -> None:
    dependency_ids = [record["resolution_dependency_id"] for record in records]
    if len(dependency_ids) != len(set(dependency_ids)):
        raise ValueError("duplicate resolution_dependency_id in output; fail-closed")

    dependency_keys = [
        (record["dependency_type"], record["source_ref"])
        for record in records
    ]
    if len(dependency_keys) != len(set(dependency_keys)):
        raise ValueError("duplicate dependency_type/source_ref pair in output; fail-closed")

    queue_ids = [record["release_resolution_queue_id"] for record in queue_records]
    if len(queue_ids) != EXPECTED_QUEUE_RECORD_COUNT:
        raise ValueError(
            f"upstream queue count {len(queue_ids)} does not match "
            f"EXPECTED_QUEUE_RECORD_COUNT={EXPECTED_QUEUE_RECORD_COUNT}; fail-closed"
        )

    upstream_refs = {
        "prohibition_dependency": set(),
        "blocker_dependency": set(),
        "remaining_resolution_dependency": set(),
    }
    for queue_record in queue_records:
        upstream_refs["prohibition_dependency"].update(
            dedup_sorted(queue_record.get("registry_prohibition_refs", []))
        )
        upstream_refs["blocker_dependency"].update(
            dedup_sorted(queue_record.get("registry_blocker_refs", []))
        )
        upstream_refs["remaining_resolution_dependency"].update(
            dedup_sorted(queue_record.get("registry_remaining_resolutions", []))
        )

    indexed_refs = {
        "prohibition_dependency": set(),
        "blocker_dependency": set(),
        "remaining_resolution_dependency": set(),
    }
    for record in records:
        indexed_refs[record["dependency_type"]].add(record["source_ref"])
        if len(record.get("affected_proposal_ids", [])) != len(
            set(record.get("affected_proposal_ids", []))
        ):
            raise ValueError(
                f"duplicate affected_proposal_ids for dependency {record['source_ref']!r}; "
                "fail-closed"
            )
        if len(record.get("affected_queue_ids", [])) != len(
            set(record.get("affected_queue_ids", []))
        ):
            raise ValueError(
                f"duplicate affected_queue_ids for dependency {record['source_ref']!r}; "
                "fail-closed"
            )

    for dependency_type in upstream_refs:
        if upstream_refs[dependency_type] != indexed_refs[dependency_type]:
            raise ValueError(
                f"dependency coverage mismatch for {dependency_type}; fail-closed"
            )


def build_summary(records: list, queue_records: list) -> dict:
    type_counts = {}
    for dependency_type in DEPENDENCY_TYPE_ORDER:
        type_counts[dependency_type] = sum(
            1 for record in records if record.get("dependency_type") == dependency_type
        )

    upstream_unique_counts = {
        "prohibition_dependency": len(
            {
                value
                for queue_record in queue_records
                for value in dedup_sorted(queue_record.get("registry_prohibition_refs", []))
            }
        ),
        "blocker_dependency": len(
            {
                value
                for queue_record in queue_records
                for value in dedup_sorted(queue_record.get("registry_blocker_refs", []))
            }
        ),
        "remaining_resolution_dependency": len(
            {
                value
                for queue_record in queue_records
                for value in dedup_sorted(queue_record.get("registry_remaining_resolutions", []))
            }
        ),
    }

    return {
        "upstream_queue_count": len(queue_records),
        "total_dependency_entries": len(records),
        "dependency_type_counts": type_counts,
        "upstream_unique_dependency_counts": upstream_unique_counts,
        "coverage_reconciled": True,
        "deterministic_ordering": True,
    }


def build_source_versions(queue_data: dict) -> dict:
    return {
        "model_adjustment_release_resolution_queue_version": queue_data.get(
            "model_adjustment_release_resolution_queue_version",
            "",
        )
    }


def write_markdown(records: list, summary: dict, source_versions: dict, generated_at: str):
    lines = [
        "# Model Adjustment Release Resolution Dependency Index",
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
        lines.append(f"## {record['resolution_dependency_id']}")
        lines.append("")
        lines.append(f"- dependency_type: {record['dependency_type']}")
        lines.append(f"- source_ref: {record['source_ref']}")
        lines.append(f"- affected_record_count: {record['affected_record_count']}")
        lines.append(f"- has_prohibition_path: {record['has_prohibition_path']}")
        lines.append(f"- has_blocker_path: {record['has_blocker_path']}")
        lines.append(f"- dependency_priority: {record['dependency_priority']}")
        lines.append(f"- terminal_posture: {record['terminal_posture']}")
        lines.append("")

        for section in ["affected_proposal_ids", "affected_queue_ids"]:
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

    queue_data, errors["model_adjustment_release_resolution_queue_json"] = load_source(
        "model_adjustment_release_resolution_queue_json"
    )

    failures = [key for key, value in errors.items() if value is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    queue_records = queue_data.get("release_resolution_queue", [])
    records = aggregate_dependencies(queue_records)
    validate_dependency_index(records, queue_records)
    summary = build_summary(records, queue_records)
    source_versions = build_source_versions(queue_data)
    source_status = {f"{key}_error": errors[key] for key in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_resolution_dependency_index_version": VERSION,
        "release_resolution_dependency_index_summary": summary,
        "release_resolution_dependency_index": records,
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
        f"dependency_entries={summary['total_dependency_entries']} "
        f"upstream_queue_count={summary['upstream_queue_count']} "
        f"coverage_reconciled={summary['coverage_reconciled']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"dependency_type_counts={summary['dependency_type_counts']}"
    )


if __name__ == "__main__":
    main()