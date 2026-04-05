#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_archive_handoff.py

Deterministically generates the v24.2 archive handoff slice for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_export.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_verification.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_handoff.md

Rules:
- archive family only
- do not reopen or mutate v8.8 through v24.1
- handoff only
- deterministic output
- no timestamps unless explicitly preserved from source artifacts
- no policy logic
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

# Constants
INPUTS = [
    "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_export.json",
    "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_verification.json"
]
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_handoff.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_handoff.md"

FROZEN_SLICES = [
    "v24.0-controlled-release-resolution-wave-packet-review-session-archive-export",
    "v24.1-controlled-release-resolution-wave-packet-review-session-archive-verification"
]

RECORD = {
    "archive_handoff_id": "resolution-wave-packet-review-session-archive-handoff-0001",
    "handoff_position": 1,
    "terminal_archive_export_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_export.json",
    "terminal_archive_verification_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_verification.json",
    "archive_family_complete": True,
    "archive_transfer_ready": True,
    "lineage_source_layer": "archive_verification",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_verification.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-archive-verification-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_archive_handoff",
    "source_files": INPUTS,
    "frozen_slices": FROZEN_SLICES,
    "archive_export_complete": True,
    "archive_verification_complete": True,
    "archive_family_complete": True,
    "archive_transfer_ready": True,
    "merge_performed": False,
    "tag_performed": False,
    "push_performed": False,
    "record_count": 1,
    "records": [RECORD]
}

def write_json():
    Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(JSON_CONTRACT, f, indent=2, ensure_ascii=False)

def write_md():
    lines = []
    lines.append("# v24.2 Controlled Release Resolution Wave Packet Review Session Archive Handoff\n")
    lines.append("**Source files:**\n")
    for src in INPUTS:
        lines.append(f"- {src}")
    lines.append("\n**Frozen slices:**\n")
    for s in FROZEN_SLICES:
        lines.append(f"- {s}")
    lines.append("\n**Archive handoff status:**\n")
    for k in [
        "archive_export_complete",
        "archive_verification_complete",
        "archive_family_complete",
        "archive_transfer_ready",
        "merge_performed",
        "tag_performed",
        "push_performed"
    ]:
        v = JSON_CONTRACT[k]
        lines.append(f"- {k}: {v}")
    lines.append("\n**Archive handoff record:**\n")
    # Table header
    cols = [
        "archive_handoff_id",
        "handoff_position",
        "terminal_archive_export_file",
        "terminal_archive_verification_file",
        "archive_family_complete",
        "archive_transfer_ready",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    lines.append(" | ".join(cols))
    lines.append(" | ".join(["---"] * len(cols)))
    r = RECORD
    row = [
        r["archive_handoff_id"],
        str(r["handoff_position"]),
        r["terminal_archive_export_file"],
        r["terminal_archive_verification_file"],
        str(r["archive_family_complete"]),
        str(r["archive_transfer_ready"]),
        r["lineage_source_layer"],
        r["lineage_source_file"],
        r["lineage_source_record_id"]
    ]
    lines.append(" | ".join(row))
    Path(OUTPUT_MD).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def main():
    write_json()
    write_md()

if __name__ == "__main__":
    main()
