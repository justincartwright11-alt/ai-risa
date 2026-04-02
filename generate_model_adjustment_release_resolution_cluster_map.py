"""
generate_model_adjustment_release_resolution_cluster_map.py

v5.0-slice-1 — Read-only controlled release resolution-cluster-map generator.

Consumes the frozen v4.9 release resolution dependency index output and emits a
deterministic shared remediation cluster map.

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
    "model_adjustment_release_resolution_dependency_index_json": (
        "ops/model_adjustments/model_adjustment_release_resolution_dependency_index.json"
    ),
}

OUTPUT_JSON = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_cluster_map.json",
)
OUTPUT_MD = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_cluster_map.md",
)

VERSION = "v5.0-slice-1"
EXPECTED_DEPENDENCY_ENTRY_COUNT = 193

DEPENDENCY_TYPE_ORDER = {
    "prohibition_dependency": 0,
    "blocker_dependency": 1,
    "remaining_resolution_dependency": 2,
}

CLUSTER_TYPE_BY_DEPENDENCY_TYPE = {
    "prohibition_dependency": "prohibition_cluster",
    "blocker_dependency": "blocker_cluster",
    "remaining_resolution_dependency": "remaining_resolution_cluster",
}

CLUSTER_PRIORITY_BY_TYPE = {
    "prohibition_cluster": "P0_prohibition_cluster",
    "blocker_cluster": "P1_blocker_cluster",
    "remaining_resolution_cluster": "P2_remaining_resolution_cluster",
}

REQUIRED_DEPENDENCY_FIELDS = (
    "resolution_dependency_id",
    "dependency_type",
    "source_ref",
    "affected_proposal_ids",
    "affected_queue_ids",
    "affected_record_count",
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


def validate_dependency_entry(entry: dict, index: int) -> None:
    for field in REQUIRED_DEPENDENCY_FIELDS:
        if field not in entry:
            raise ValueError(
                f"dependency entry[{index}] missing required field {field!r}; "
                "fail-closed — manual review required"
            )

    dep_id = entry.get("resolution_dependency_id", "")
    if not dep_id:
        raise ValueError(
            f"dependency entry[{index}] has empty resolution_dependency_id; "
            "fail-closed — manual review required"
        )

    dep_type = entry.get("dependency_type", "")
    if dep_type not in DEPENDENCY_TYPE_ORDER:
        raise ValueError(
            f"dependency entry[{index}] has unknown dependency_type={dep_type!r}; "
            "fail-closed — manual review required"
        )


def cluster_sort_key(record: dict):
    return (
        DEPENDENCY_TYPE_ORDER[record["dependency_type"]],
        -record["affected_record_count"],
        -record["member_count"],
        record["resolution_cluster_id"],
    )


def build_cluster_key(entry: dict) -> tuple:
    dep_type = entry["dependency_type"]
    affected_proposals = tuple(dedup_sorted(entry.get("affected_proposal_ids", [])))
    affected_queues = tuple(dedup_sorted(entry.get("affected_queue_ids", [])))
    terminal_posture = entry.get("terminal_posture", "")

    if dep_type == "prohibition_dependency":
        return (dep_type, affected_proposals, affected_queues, terminal_posture)
    if dep_type == "blocker_dependency":
        return (
            dep_type,
            bool(entry.get("has_prohibition_path", False)),
            affected_proposals,
            affected_queues,
            terminal_posture,
        )
    return (
        dep_type,
        bool(entry.get("has_blocker_path", False)),
        bool(entry.get("has_prohibition_path", False)),
        affected_proposals,
        affected_queues,
        terminal_posture,
    )


def build_clusters(dependency_entries: list) -> list:
    grouped = {}

    for index, entry in enumerate(dependency_entries, start=1):
        validate_dependency_entry(entry, index)
        key = build_cluster_key(entry)
        if key not in grouped:
            grouped[key] = {
                "dependency_type": entry["dependency_type"],
                "member_dependency_ids": [],
                "member_source_refs": [],
                "affected_proposal_ids": set(),
                "affected_queue_ids": set(),
                "has_prohibition_path": False,
                "has_blocker_path": False,
                "terminal_postures": set(),
            }

        grouped[key]["member_dependency_ids"].append(entry["resolution_dependency_id"])
        grouped[key]["member_source_refs"].append(entry["source_ref"])
        grouped[key]["affected_proposal_ids"].update(entry.get("affected_proposal_ids", []))
        grouped[key]["affected_queue_ids"].update(entry.get("affected_queue_ids", []))
        grouped[key]["has_prohibition_path"] = (
            grouped[key]["has_prohibition_path"]
            or bool(entry.get("has_prohibition_path", False))
        )
        grouped[key]["has_blocker_path"] = (
            grouped[key]["has_blocker_path"]
            or bool(entry.get("has_blocker_path", False))
        )
        grouped[key]["terminal_postures"].add(entry.get("terminal_posture", ""))

    unsorted_records = []
    for cluster in grouped.values():
        dep_type = cluster["dependency_type"]
        cluster_type = CLUSTER_TYPE_BY_DEPENDENCY_TYPE[dep_type]
        terminal_posture = "|".join(dedup_sorted(cluster["terminal_postures"]))

        unsorted_records.append(
            {
                "dependency_type": dep_type,
                "cluster_type": cluster_type,
                "member_dependency_ids": dedup_sorted(cluster["member_dependency_ids"]),
                "member_source_refs": dedup_sorted(cluster["member_source_refs"]),
                "affected_proposal_ids": dedup_sorted(cluster["affected_proposal_ids"]),
                "affected_queue_ids": dedup_sorted(cluster["affected_queue_ids"]),
                "affected_record_count": len(cluster["affected_queue_ids"]),
                "member_count": len(set(cluster["member_dependency_ids"])),
                "has_prohibition_path": cluster["has_prohibition_path"],
                "has_blocker_path": cluster["has_blocker_path"],
                "cluster_priority": CLUSTER_PRIORITY_BY_TYPE[cluster_type],
                "terminal_posture": terminal_posture,
                "cluster_notes": (
                    "v5_0_read_only_resolution_cluster_projection_of_v4_9_index"
                    "_no_reclassification_no_release_recommendation_no_upstream_mutation"
                ),
                "upstream_source": SOURCE_PATHS[
                    "model_adjustment_release_resolution_dependency_index_json"
                ],
            }
        )

    pre_sorted = sorted(
        unsorted_records,
        key=lambda record: (
            DEPENDENCY_TYPE_ORDER[record["dependency_type"]],
            -record["affected_record_count"],
            -record["member_count"],
            record["member_source_refs"][0] if record["member_source_refs"] else "",
        ),
    )

    output = []
    for index, record in enumerate(pre_sorted, start=1):
        record = dict(record)
        record["resolution_cluster_id"] = f"resolution-cluster-{index:04d}"
        output.append(record)

    return sorted(output, key=cluster_sort_key)


def validate_clusters(clusters: list, dependency_entries: list) -> None:
    cluster_ids = [record["resolution_cluster_id"] for record in clusters]
    if len(cluster_ids) != len(set(cluster_ids)):
        raise ValueError("duplicate resolution_cluster_id in output; fail-closed")

    all_upstream_ids = [entry.get("resolution_dependency_id", "") for entry in dependency_entries]
    if len(all_upstream_ids) != EXPECTED_DEPENDENCY_ENTRY_COUNT:
        raise ValueError(
            f"upstream dependency entry count {len(all_upstream_ids)} does not match "
            f"EXPECTED_DEPENDENCY_ENTRY_COUNT={EXPECTED_DEPENDENCY_ENTRY_COUNT}; fail-closed"
        )

    covered_ids = []
    for cluster in clusters:
        member_ids = cluster.get("member_dependency_ids", [])
        if len(member_ids) != len(set(member_ids)):
            raise ValueError(
                f"duplicate member_dependency_ids in {cluster['resolution_cluster_id']}; "
                "fail-closed"
            )
        affected_proposals = cluster.get("affected_proposal_ids", [])
        if len(affected_proposals) != len(set(affected_proposals)):
            raise ValueError(
                f"duplicate affected_proposal_ids in {cluster['resolution_cluster_id']}; "
                "fail-closed"
            )
        affected_queues = cluster.get("affected_queue_ids", [])
        if len(affected_queues) != len(set(affected_queues)):
            raise ValueError(
                f"duplicate affected_queue_ids in {cluster['resolution_cluster_id']}; "
                "fail-closed"
            )
        covered_ids.extend(member_ids)

    if len(covered_ids) != len(set(covered_ids)):
        raise ValueError("a dependency entry is covered by more than one cluster; fail-closed")

    if set(covered_ids) != set(all_upstream_ids):
        raise ValueError("cluster coverage does not match upstream dependency entries; fail-closed")


def build_summary(clusters: list, dependency_entries: list) -> dict:
    cluster_type_counts = {
        cluster_type: sum(1 for c in clusters if c.get("cluster_type") == cluster_type)
        for cluster_type in (
            "prohibition_cluster",
            "blocker_cluster",
            "remaining_resolution_cluster",
        )
    }

    return {
        "upstream_dependency_entry_count": len(dependency_entries),
        "total_resolution_clusters": len(clusters),
        "cluster_type_counts": cluster_type_counts,
        "coverage_reconciled": True,
        "deterministic_ordering": True,
    }


def build_source_versions(data: dict) -> dict:
    return {
        "model_adjustment_release_resolution_dependency_index_version": data.get(
            "model_adjustment_release_resolution_dependency_index_version",
            "",
        )
    }


def write_markdown(clusters: list, summary: dict, source_versions: dict, generated_at: str):
    lines = [
        "# Model Adjustment Release Resolution Cluster Map",
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
    for cluster in clusters:
        lines.append(f"## {cluster['resolution_cluster_id']}")
        lines.append("")
        lines.append(f"- cluster_type: {cluster['cluster_type']}")
        lines.append(f"- dependency_type: {cluster['dependency_type']}")
        lines.append(f"- affected_record_count: {cluster['affected_record_count']}")
        lines.append(f"- member_count: {cluster['member_count']}")
        lines.append(f"- has_prohibition_path: {cluster['has_prohibition_path']}")
        lines.append(f"- has_blocker_path: {cluster['has_blocker_path']}")
        lines.append(f"- cluster_priority: {cluster['cluster_priority']}")
        lines.append(f"- terminal_posture: {cluster['terminal_posture']}")
        lines.append("")

        for section in (
            "member_dependency_ids",
            "member_source_refs",
            "affected_proposal_ids",
            "affected_queue_ids",
        ):
            lines.append(f"### {section}")
            lines.append("")
            values = cluster.get(section, [])
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

    source_data, errors["model_adjustment_release_resolution_dependency_index_json"] = load_source(
        "model_adjustment_release_resolution_dependency_index_json"
    )

    failures = [key for key, value in errors.items() if value is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    dependency_entries = source_data.get("release_resolution_dependency_index", [])
    clusters = build_clusters(dependency_entries)
    validate_clusters(clusters, dependency_entries)
    summary = build_summary(clusters, dependency_entries)
    source_versions = build_source_versions(source_data)
    source_status = {f"{key}_error": errors[key] for key in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_resolution_cluster_map_version": VERSION,
        "release_resolution_cluster_map_summary": summary,
        "release_resolution_cluster_map": clusters,
        "source_paths": SOURCE_PATHS,
        "source_status": source_status,
        "source_versions": source_versions,
    }

    os.makedirs(OPS_DIR, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, indent=2)
    print(f"[WRITE] {OUTPUT_JSON}")

    write_markdown(clusters, summary, source_versions, generated_at)
    print(f"[WRITE] {OUTPUT_MD}")

    print(
        "[STATUS] "
        f"clusters={summary['total_resolution_clusters']} "
        f"upstream_dependency_entries={summary['upstream_dependency_entry_count']} "
        f"coverage_reconciled={summary['coverage_reconciled']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"cluster_type_counts={summary['cluster_type_counts']}"
    )


if __name__ == "__main__":
    main()