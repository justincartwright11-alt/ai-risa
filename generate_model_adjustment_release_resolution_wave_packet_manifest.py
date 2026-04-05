"""
generate_model_adjustment_release_resolution_wave_packet_manifest.py

v5.2-slice-1 — Read-only controlled release resolution-wave-packet-manifest
generator.

Consumes the frozen v5.1 release resolution wave plan output and emits one
deterministic operator packet per wave.

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
    "model_adjustment_release_resolution_wave_plan_json": (
        "ops/model_adjustments/model_adjustment_release_resolution_wave_plan.json"
    )
}

OUTPUT_JSON = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_wave_packet_manifest.json",
)
OUTPUT_MD = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_wave_packet_manifest.md",
)

VERSION = "v5.2-slice-1"
EXPECTED_WAVE_COUNT = 3

WAVE_TYPE_ORDER = {
    "prohibition_cluster": 0,
    "blocker_cluster": 1,
    "remaining_resolution_cluster": 2,
}

REQUIRED_WAVE_FIELDS = (
    "resolution_wave_id",
    "wave_rank",
    "wave_type",
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
    "wave_priority",
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


def validate_wave(wave: dict, index: int) -> None:
    for field in REQUIRED_WAVE_FIELDS:
        if field not in wave:
            raise ValueError(
                f"wave[{index}] missing required field {field!r}; "
                "fail-closed — manual review required"
            )

    wave_id = wave.get("resolution_wave_id", "")
    if not wave_id:
        raise ValueError(
            f"wave[{index}] has empty resolution_wave_id; "
            "fail-closed — manual review required"
        )

    wave_type = wave.get("wave_type", "")
    if wave_type not in WAVE_TYPE_ORDER:
        raise ValueError(
            f"wave[{index}] has unknown wave_type={wave_type!r}; "
            "fail-closed — manual review required"
        )


def sorted_waves(waves: list) -> list:
    return sorted(
        waves,
        key=lambda wave: (
            WAVE_TYPE_ORDER[wave.get("wave_type", "remaining_resolution_cluster")],
            int(wave.get("wave_rank", 0)),
            wave.get("resolution_wave_id", ""),
        ),
    )


def build_packets(waves: list) -> list:
    packets = []

    for index, wave in enumerate(sorted_waves(waves), start=1):
        validate_wave(wave, index)

        packets.append(
            {
                "resolution_wave_packet_id": f"resolution-wave-packet-{index:04d}",
                "source_resolution_wave_id": wave["resolution_wave_id"],
                "wave_rank": int(wave.get("wave_rank", 0)),
                "wave_type": wave["wave_type"],
                "packet_priority": wave.get("wave_priority", ""),
                "member_cluster_ids": dedup_sorted(wave.get("member_cluster_ids", [])),
                "member_dependency_ids": dedup_sorted(wave.get("member_dependency_ids", [])),
                "member_source_refs": dedup_sorted(wave.get("member_source_refs", [])),
                "affected_proposal_ids": dedup_sorted(wave.get("affected_proposal_ids", [])),
                "affected_queue_ids": dedup_sorted(wave.get("affected_queue_ids", [])),
                "affected_record_count": int(wave.get("affected_record_count", 0)),
                "cluster_count": int(wave.get("cluster_count", 0)),
                "dependency_count": int(wave.get("dependency_count", 0)),
                "has_prohibition_path": bool(wave.get("has_prohibition_path", False)),
                "has_blocker_path": bool(wave.get("has_blocker_path", False)),
                "terminal_posture": wave.get("terminal_posture", ""),
                "packet_notes": (
                    "v5_2_read_only_wave_packet_manifest_projection_of_v5_1_wave_plan"
                    "_no_reclassification_no_release_recommendation_no_upstream_mutation"
                ),
                "upstream_source": SOURCE_PATHS[
                    "model_adjustment_release_resolution_wave_plan_json"
                ],
            }
        )

    return packets


def validate_packets(packets: list, waves: list) -> None:
    packet_ids = [packet["resolution_wave_packet_id"] for packet in packets]
    if len(packet_ids) != len(set(packet_ids)):
        raise ValueError("duplicate resolution_wave_packet_id in output; fail-closed")

    source_wave_ids = [packet["source_resolution_wave_id"] for packet in packets]
    if len(source_wave_ids) != len(set(source_wave_ids)):
        raise ValueError("duplicate source_resolution_wave_id in packets; fail-closed")

    upstream_wave_ids = [wave.get("resolution_wave_id", "") for wave in waves]
    if len(upstream_wave_ids) != EXPECTED_WAVE_COUNT:
        raise ValueError(
            f"upstream wave count {len(upstream_wave_ids)} does not match "
            f"EXPECTED_WAVE_COUNT={EXPECTED_WAVE_COUNT}; fail-closed"
        )

    if set(source_wave_ids) != set(upstream_wave_ids):
        raise ValueError("packet coverage does not match upstream waves; fail-closed")

    for packet in packets:
        for field in (
            "member_cluster_ids",
            "member_dependency_ids",
            "member_source_refs",
            "affected_proposal_ids",
            "affected_queue_ids",
        ):
            values = packet.get(field, [])
            if len(values) != len(set(values)):
                raise ValueError(
                    f"duplicate values in {field!r} for {packet['resolution_wave_packet_id']}; "
                    "fail-closed"
                )


def build_summary(packets: list, waves: list) -> dict:
    packet_type_counts = {
        wave_type: sum(1 for p in packets if p.get("wave_type") == wave_type)
        for wave_type in (
            "prohibition_cluster",
            "blocker_cluster",
            "remaining_resolution_cluster",
        )
    }

    return {
        "upstream_wave_count": len(waves),
        "total_wave_packets": len(packets),
        "wave_type_packet_counts": packet_type_counts,
        "coverage_reconciled": True,
        "deterministic_ordering": True,
    }


def build_source_versions(source_data: dict) -> dict:
    return {
        "model_adjustment_release_resolution_wave_plan_version": source_data.get(
            "model_adjustment_release_resolution_wave_plan_version", ""
        )
    }


def write_markdown(packets: list, summary: dict, source_versions: dict, generated_at: str):
    lines = [
        "# Model Adjustment Release Resolution Wave Packet Manifest",
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
    for packet in packets:
        lines.append(f"## {packet['resolution_wave_packet_id']}")
        lines.append("")
        lines.append(f"- source_resolution_wave_id: {packet['source_resolution_wave_id']}")
        lines.append(f"- wave_rank: {packet['wave_rank']}")
        lines.append(f"- wave_type: {packet['wave_type']}")
        lines.append(f"- packet_priority: {packet['packet_priority']}")
        lines.append(f"- affected_record_count: {packet['affected_record_count']}")
        lines.append(f"- cluster_count: {packet['cluster_count']}")
        lines.append(f"- dependency_count: {packet['dependency_count']}")
        lines.append(f"- has_prohibition_path: {packet['has_prohibition_path']}")
        lines.append(f"- has_blocker_path: {packet['has_blocker_path']}")
        lines.append(f"- terminal_posture: {packet['terminal_posture']}")
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
            values = packet.get(section, [])
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

    source_data, errors["model_adjustment_release_resolution_wave_plan_json"] = load_source(
        "model_adjustment_release_resolution_wave_plan_json"
    )

    failures = [key for key, value in errors.items() if value is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    waves = source_data.get("release_resolution_wave_plan", [])
    packets = build_packets(waves)
    validate_packets(packets, waves)
    summary = build_summary(packets, waves)
    source_versions = build_source_versions(source_data)
    source_status = {f"{key}_error": errors[key] for key in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_resolution_wave_packet_manifest_version": VERSION,
        "release_resolution_wave_packet_manifest_summary": summary,
        "release_resolution_wave_packet_manifest": packets,
        "source_paths": SOURCE_PATHS,
        "source_status": source_status,
        "source_versions": source_versions,
    }

    os.makedirs(OPS_DIR, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, indent=2)
    print(f"[WRITE] {OUTPUT_JSON}")

    write_markdown(packets, summary, source_versions, generated_at)
    print(f"[WRITE] {OUTPUT_MD}")

    print(
        "[STATUS] "
        f"wave_packets={summary['total_wave_packets']} "
        f"upstream_wave_count={summary['upstream_wave_count']} "
        f"coverage_reconciled={summary['coverage_reconciled']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"wave_type_packet_counts={summary['wave_type_packet_counts']}"
    )


if __name__ == "__main__":
    main()