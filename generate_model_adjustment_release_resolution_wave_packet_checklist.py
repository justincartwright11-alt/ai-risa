"""
generate_model_adjustment_release_resolution_wave_packet_checklist.py

v5.3-slice-1 — Read-only controlled release resolution-wave-packet-checklist
generator.

Consumes the frozen v5.2 release resolution wave packet manifest output and
emits one deterministic checklist record per upstream packet.

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
    "model_adjustment_release_resolution_wave_packet_manifest_json": (
        "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_manifest.json"
    )
}

OUTPUT_JSON = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_wave_packet_checklist.json",
)
OUTPUT_MD = os.path.join(
    OPS_DIR,
    "model_adjustment_release_resolution_wave_packet_checklist.md",
)

VERSION = "v5.3-slice-1"
EXPECTED_PACKET_COUNT = 3

WAVE_TYPE_ORDER = {
    "prohibition_cluster": 0,
    "blocker_cluster": 1,
    "remaining_resolution_cluster": 2,
}

REQUIRED_PACKET_FIELDS = (
    "resolution_wave_packet_id",
    "source_resolution_wave_id",
    "wave_rank",
    "wave_type",
    "packet_priority",
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


def validate_packet(packet: dict, index: int) -> None:
    for field in REQUIRED_PACKET_FIELDS:
        if field not in packet:
            raise ValueError(
                f"packet[{index}] missing required field {field!r}; "
                "fail-closed — manual review required"
            )

    packet_id = packet.get("resolution_wave_packet_id", "")
    if not packet_id:
        raise ValueError(
            f"packet[{index}] has empty resolution_wave_packet_id; "
            "fail-closed — manual review required"
        )

    wave_type = packet.get("wave_type", "")
    if wave_type not in WAVE_TYPE_ORDER:
        raise ValueError(
            f"packet[{index}] has unknown wave_type={wave_type!r}; "
            "fail-closed — manual review required"
        )


def sorted_packets(packets: list) -> list:
    return sorted(
        packets,
        key=lambda packet: (
            WAVE_TYPE_ORDER[packet.get("wave_type", "remaining_resolution_cluster")],
            packet.get("source_resolution_wave_id", ""),
            packet.get("resolution_wave_packet_id", ""),
        ),
    )


def build_checklist_records(packets: list) -> list:
    output = []

    for index, packet in enumerate(sorted_packets(packets), start=1):
        validate_packet(packet, index)

        output.append(
            {
                "resolution_wave_packet_checklist_id": (
                    f"resolution-wave-packet-checklist-{index:04d}"
                ),
                "source_resolution_wave_packet_id": packet["resolution_wave_packet_id"],
                "source_resolution_wave_id": packet["source_resolution_wave_id"],
                "wave_rank": int(packet.get("wave_rank", 0)),
                "wave_type": packet["wave_type"],
                "packet_priority": packet.get("packet_priority", ""),
                "checklist_priority": packet.get("packet_priority", ""),
                "member_cluster_ids": dedup_sorted(packet.get("member_cluster_ids", [])),
                "member_dependency_ids": dedup_sorted(packet.get("member_dependency_ids", [])),
                "member_source_refs": dedup_sorted(packet.get("member_source_refs", [])),
                "affected_proposal_ids": dedup_sorted(packet.get("affected_proposal_ids", [])),
                "affected_queue_ids": dedup_sorted(packet.get("affected_queue_ids", [])),
                "affected_record_count": int(packet.get("affected_record_count", 0)),
                "cluster_count": int(packet.get("cluster_count", 0)),
                "dependency_count": int(packet.get("dependency_count", 0)),
                "has_prohibition_path": bool(packet.get("has_prohibition_path", False)),
                "has_blocker_path": bool(packet.get("has_blocker_path", False)),
                "terminal_posture": packet.get("terminal_posture", ""),
                "checklist_notes": (
                    "v5_3_read_only_checklist_projection_of_v5_2_packet_manifest"
                    "_no_reclassification_no_release_recommendation_no_upstream_mutation"
                ),
                "upstream_source": SOURCE_PATHS[
                    "model_adjustment_release_resolution_wave_packet_manifest_json"
                ],
            }
        )

    return output


def validate_checklist(records: list, packets: list) -> None:
    checklist_ids = [r["resolution_wave_packet_checklist_id"] for r in records]
    if len(checklist_ids) != len(set(checklist_ids)):
        raise ValueError("duplicate resolution_wave_packet_checklist_id in output; fail-closed")

    src_packet_ids = [r["source_resolution_wave_packet_id"] for r in records]
    if len(src_packet_ids) != len(set(src_packet_ids)):
        raise ValueError("duplicate source_resolution_wave_packet_id in checklist; fail-closed")

    upstream_packet_ids = [p.get("resolution_wave_packet_id", "") for p in packets]
    if len(upstream_packet_ids) != EXPECTED_PACKET_COUNT:
        raise ValueError(
            f"upstream packet count {len(upstream_packet_ids)} does not match "
            f"EXPECTED_PACKET_COUNT={EXPECTED_PACKET_COUNT}; fail-closed"
        )

    if set(src_packet_ids) != set(upstream_packet_ids):
        raise ValueError("checklist coverage does not match upstream packets; fail-closed")

    for record in records:
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
                    f"{record['resolution_wave_packet_checklist_id']}; fail-closed"
                )


def build_summary(records: list, packets: list) -> dict:
    checklist_type_counts = {
        wave_type: sum(1 for r in records if r.get("wave_type") == wave_type)
        for wave_type in (
            "prohibition_cluster",
            "blocker_cluster",
            "remaining_resolution_cluster",
        )
    }

    return {
        "upstream_packet_count": len(packets),
        "total_checklist_records": len(records),
        "checklist_wave_type_counts": checklist_type_counts,
        "coverage_reconciled": True,
        "deterministic_ordering": True,
    }


def build_source_versions(source_data: dict) -> dict:
    return {
        "model_adjustment_release_resolution_wave_packet_manifest_version": source_data.get(
            "model_adjustment_release_resolution_wave_packet_manifest_version", ""
        )
    }


def write_markdown(records: list, summary: dict, source_versions: dict, generated_at: str):
    lines = [
        "# Model Adjustment Release Resolution Wave Packet Checklist",
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
        lines.append(f"## {record['resolution_wave_packet_checklist_id']}")
        lines.append("")
        lines.append(
            f"- source_resolution_wave_packet_id: {record['source_resolution_wave_packet_id']}"
        )
        lines.append(f"- source_resolution_wave_id: {record['source_resolution_wave_id']}")
        lines.append(f"- wave_rank: {record['wave_rank']}")
        lines.append(f"- wave_type: {record['wave_type']}")
        lines.append(f"- packet_priority: {record['packet_priority']}")
        lines.append(f"- checklist_priority: {record['checklist_priority']}")
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

    with open(OUTPUT_MD, "w", encoding="utf-8") as file_handle:
        file_handle.write("\n".join(lines))


def main():
    errors = {}

    source_data, errors["model_adjustment_release_resolution_wave_packet_manifest_json"] = load_source(
        "model_adjustment_release_resolution_wave_packet_manifest_json"
    )

    failures = [key for key, value in errors.items() if value is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    packets = source_data.get("release_resolution_wave_packet_manifest", [])
    records = build_checklist_records(packets)
    validate_checklist(records, packets)
    summary = build_summary(records, packets)
    source_versions = build_source_versions(source_data)
    source_status = {f"{key}_error": errors[key] for key in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_resolution_wave_packet_checklist_version": VERSION,
        "release_resolution_wave_packet_checklist_summary": summary,
        "release_resolution_wave_packet_checklist": records,
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
        f"checklist_records={summary['total_checklist_records']} "
        f"upstream_packet_count={summary['upstream_packet_count']} "
        f"coverage_reconciled={summary['coverage_reconciled']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"checklist_wave_type_counts={summary['checklist_wave_type_counts']}"
    )


if __name__ == "__main__":
    main()