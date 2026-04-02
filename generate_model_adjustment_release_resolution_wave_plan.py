"""
generate_model_adjustment_release_resolution_wave_plan.py

v5.1-slice-1 — Read-only controlled release resolution-wave-plan generator.

Consumes the frozen v5.0 release resolution cluster map output and emits a
deterministic remediation wave plan.

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
    "model_adjustment_release_resolution_cluster_map_json": (
        "ops/model_adjustments/model_adjustment_release_resolution_cluster_map.json"
    ),
}

OUTPUT_JSON = os.path.join(OPS_DIR, "model_adjustment_release_resolution_wave_plan.json")
OUTPUT_MD = os.path.join(OPS_DIR, "model_adjustment_release_resolution_wave_plan.md")

VERSION = "v5.1-slice-1"
EXPECTED_CLUSTER_COUNT = 13

CLUSTER_TYPE_ORDER = {
    "prohibition_cluster": 0,
    "blocker_cluster": 1,
    "remaining_resolution_cluster": 2,
}

WAVE_PRIORITY_BY_TYPE = {
    "prohibition_cluster": "WAVE_P0_PROHIBITION",
    "blocker_cluster": "WAVE_P1_BLOCKER",
    "remaining_resolution_cluster": "WAVE_P2_REMAINING",
}

REQUIRED_CLUSTER_FIELDS = (
    "resolution_cluster_id",
    "cluster_type",
    "member_dependency_ids",
    "member_source_refs",
    "affected_proposal_ids",
    "affected_queue_ids",
    "affected_record_count",
    "member_count",
    "has_prohibition_path",
    "has_blocker_path",
    "cluster_priority",
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


def validate_cluster(cluster: dict, index: int) -> None:
    for field in REQUIRED_CLUSTER_FIELDS:
        if field not in cluster:
            raise ValueError(
                f"cluster[{index}] missing required field {field!r}; "
                "fail-closed — manual review required"
            )

    cluster_id = cluster.get("resolution_cluster_id", "")
    if not cluster_id:
        raise ValueError(
            f"cluster[{index}] has empty resolution_cluster_id; "
            "fail-closed — manual review required"
        )

    cluster_type = cluster.get("cluster_type", "")
    if cluster_type not in CLUSTER_TYPE_ORDER:
        raise ValueError(
            f"cluster[{index}] has unknown cluster_type={cluster_type!r}; "
            "fail-closed — manual review required"
        )


def sorted_clusters(clusters: list) -> list:
    return sorted(
        clusters,
        key=lambda cluster: (
            CLUSTER_TYPE_ORDER[cluster.get("cluster_type", "remaining_resolution_cluster")],
            -int(cluster.get("affected_record_count", 0)),
            -int(cluster.get("member_count", 0)),
            cluster.get("resolution_cluster_id", ""),
        ),
    )


def build_waves(clusters: list) -> list:
    # group by ordered wave type while preserving deterministic cluster order
    grouped = {
        "prohibition_cluster": [],
        "blocker_cluster": [],
        "remaining_resolution_cluster": [],
    }

    for cluster in sorted_clusters(clusters):
        grouped[cluster["cluster_type"]].append(cluster)

    waves = []
    rank = 1
    for wave_type in ("prohibition_cluster", "blocker_cluster", "remaining_resolution_cluster"):
        members = grouped[wave_type]
        if not members:
            continue

        member_cluster_ids = dedup_sorted([m["resolution_cluster_id"] for m in members])
        member_dependency_ids = dedup_sorted(
            dep_id for m in members for dep_id in m.get("member_dependency_ids", [])
        )
        member_source_refs = dedup_sorted(
            ref for m in members for ref in m.get("member_source_refs", [])
        )
        affected_proposal_ids = dedup_sorted(
            pid for m in members for pid in m.get("affected_proposal_ids", [])
        )
        affected_queue_ids = dedup_sorted(
            qid for m in members for qid in m.get("affected_queue_ids", [])
        )
        terminal_posture = "|".join(
            dedup_sorted(m.get("terminal_posture", "") for m in members)
        )

        waves.append(
            {
                "resolution_wave_id": f"resolution-wave-{rank:04d}",
                "wave_rank": rank,
                "wave_type": wave_type,
                "member_cluster_ids": member_cluster_ids,
                "member_dependency_ids": member_dependency_ids,
                "member_source_refs": member_source_refs,
                "affected_proposal_ids": affected_proposal_ids,
                "affected_queue_ids": affected_queue_ids,
                "affected_record_count": len(affected_queue_ids),
                "cluster_count": len(member_cluster_ids),
                "dependency_count": len(member_dependency_ids),
                "has_prohibition_path": any(bool(m.get("has_prohibition_path", False)) for m in members),
                "has_blocker_path": any(bool(m.get("has_blocker_path", False)) for m in members),
                "wave_priority": WAVE_PRIORITY_BY_TYPE[wave_type],
                "terminal_posture": terminal_posture,
                "wave_notes": (
                    "v5_1_read_only_wave_sequencing_projection_of_v5_0_cluster_map"
                    "_no_reclassification_no_release_recommendation_no_upstream_mutation"
                ),
                "upstream_source": SOURCE_PATHS[
                    "model_adjustment_release_resolution_cluster_map_json"
                ],
            }
        )
        rank += 1

    return waves


def validate_waves(waves: list, clusters: list) -> None:
    wave_ids = [wave["resolution_wave_id"] for wave in waves]
    if len(wave_ids) != len(set(wave_ids)):
        raise ValueError("duplicate resolution_wave_id in output; fail-closed")

    if len(clusters) != EXPECTED_CLUSTER_COUNT:
        raise ValueError(
            f"upstream cluster count {len(clusters)} does not match "
            f"EXPECTED_CLUSTER_COUNT={EXPECTED_CLUSTER_COUNT}; fail-closed"
        )

    all_cluster_ids = [cluster.get("resolution_cluster_id", "") for cluster in clusters]
    covered_cluster_ids = []
    for wave in waves:
        for field in (
            "member_cluster_ids",
            "member_dependency_ids",
            "member_source_refs",
            "affected_proposal_ids",
            "affected_queue_ids",
        ):
            values = wave.get(field, [])
            if len(values) != len(set(values)):
                raise ValueError(
                    f"duplicate values in {field!r} for {wave['resolution_wave_id']}; fail-closed"
                )
        covered_cluster_ids.extend(wave.get("member_cluster_ids", []))

    if len(covered_cluster_ids) != len(set(covered_cluster_ids)):
        raise ValueError("a cluster is covered by more than one wave; fail-closed")

    if set(covered_cluster_ids) != set(all_cluster_ids):
        raise ValueError("wave coverage does not match upstream clusters; fail-closed")


def build_summary(waves: list, clusters: list) -> dict:
    wave_type_counts = {
        wave_type: sum(1 for wave in waves if wave.get("wave_type") == wave_type)
        for wave_type in ("prohibition_cluster", "blocker_cluster", "remaining_resolution_cluster")
    }
    return {
        "upstream_cluster_count": len(clusters),
        "total_resolution_waves": len(waves),
        "wave_type_counts": wave_type_counts,
        "coverage_reconciled": True,
        "deterministic_ordering": True,
    }


def build_source_versions(source_data: dict) -> dict:
    return {
        "model_adjustment_release_resolution_cluster_map_version": source_data.get(
            "model_adjustment_release_resolution_cluster_map_version", ""
        )
    }


def write_markdown(waves: list, summary: dict, source_versions: dict, generated_at: str):
    lines = [
        "# Model Adjustment Release Resolution Wave Plan",
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
    for wave in waves:
        lines.append(f"## {wave['resolution_wave_id']}")
        lines.append("")
        lines.append(f"- wave_rank: {wave['wave_rank']}")
        lines.append(f"- wave_type: {wave['wave_type']}")
        lines.append(f"- affected_record_count: {wave['affected_record_count']}")
        lines.append(f"- cluster_count: {wave['cluster_count']}")
        lines.append(f"- dependency_count: {wave['dependency_count']}")
        lines.append(f"- has_prohibition_path: {wave['has_prohibition_path']}")
        lines.append(f"- has_blocker_path: {wave['has_blocker_path']}")
        lines.append(f"- wave_priority: {wave['wave_priority']}")
        lines.append(f"- terminal_posture: {wave['terminal_posture']}")
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
            values = wave.get(section, [])
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

    source_data, errors["model_adjustment_release_resolution_cluster_map_json"] = load_source(
        "model_adjustment_release_resolution_cluster_map_json"
    )

    failures = [key for key, value in errors.items() if value is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    clusters = source_data.get("release_resolution_cluster_map", [])
    for idx, cluster in enumerate(clusters, start=1):
        validate_cluster(cluster, idx)

    waves = build_waves(clusters)
    validate_waves(waves, clusters)
    summary = build_summary(waves, clusters)
    source_versions = build_source_versions(source_data)
    source_status = {f"{key}_error": errors[key] for key in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_resolution_wave_plan_version": VERSION,
        "release_resolution_wave_plan_summary": summary,
        "release_resolution_wave_plan": waves,
        "source_paths": SOURCE_PATHS,
        "source_status": source_status,
        "source_versions": source_versions,
    }

    os.makedirs(OPS_DIR, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, indent=2)
    print(f"[WRITE] {OUTPUT_JSON}")

    write_markdown(waves, summary, source_versions, generated_at)
    print(f"[WRITE] {OUTPUT_MD}")

    print(
        "[STATUS] "
        f"waves={summary['total_resolution_waves']} "
        f"upstream_cluster_count={summary['upstream_cluster_count']} "
        f"coverage_reconciled={summary['coverage_reconciled']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"wave_type_counts={summary['wave_type_counts']}"
    )


if __name__ == "__main__":
    main()