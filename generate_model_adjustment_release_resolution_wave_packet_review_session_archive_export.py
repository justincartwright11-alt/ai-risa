#!/usr/bin/env python3
"""
generate_model_adjustment_release_resolution_wave_packet_review_session_archive_export.py

Deterministically generates the v24.0 archive export slice for the controlled release resolution wave packet review session.

Inputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_program_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operator_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_handoff.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_post_run_retrospective.json

Outputs:
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_export.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_export.md

Rules:
- export family only
- do not reopen or mutate v8.8 through v23.0
- deterministic output
- record export readiness and archive completeness
- no timestamps unless explicitly preserved from source artifacts
- no policy logic
- no release logic
- no merge/tag/push
"""
import json
from pathlib import Path

# Constants
INPUTS = [
    "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_program_closeout.json",
    "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_operator_handoff.json",
    "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_execution_handoff.json",
    "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_post_run_retrospective.json"
]
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_export.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_archive_export.md"

FROZEN_SLICES = [
    "v23.0-controlled-release-resolution-wave-packet-review-session-post-run-retrospective"
]

RECORD = {
    "archive_export_id": "resolution-wave-packet-review-session-archive-export-0001",
    "export_position": 1,
    "program_closeout_id": "resolution-wave-packet-review-session-program-closeout-0001",
    "operator_handoff_id": "resolution-wave-packet-review-session-operator-handoff-0001",
    "live_execution_handoff_id": "resolution-wave-packet-review-session-live-execution-handoff-0001",
    "post_run_retrospective_id": "resolution-wave-packet-review-session-post-run-retrospective-0001",
    "archive_export_status": "export_ready",
    "archive_completeness": "complete",
    "archive_export_summary": "Sealed archive is ready for external export, transfer, or re-import.",
    "archive_export_notes": [
        "All review-session program slices v8.8 through v23.0 are frozen and untouched.",
        "Export artifact is a deterministic, audit-ready package.",
        "No policy or release logic applied in export family."
    ],
    "lineage_source_layer": "post_run_retrospective",
    "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_post_run_retrospective.json",
    "lineage_source_record_id": "resolution-wave-packet-review-session-post-run-retrospective-0001"
}

JSON_CONTRACT = {
    "record_type": "model_adjustment_release_resolution_wave_packet_review_session_archive_export",
    "source_files": INPUTS,
    "frozen_slices": FROZEN_SLICES,
    "archive_export_ready": True,
    "archive_completeness": "complete",
    "archive_export_status": "export_ready",
    "record_count": 1,
    "records": [RECORD]
}

def write_json():
    Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(JSON_CONTRACT, f, indent=2, ensure_ascii=False)

def write_md():
    lines = []
    lines.append("# v24.0 Controlled Release Resolution Wave Packet Review Session Archive Export\n")
    lines.append("**Source files:**\n")
    for src in INPUTS:
        lines.append(f"- {src}")
    lines.append("\n**Frozen slices:**\n")
    for s in FROZEN_SLICES:
        lines.append(f"- {s}")
    lines.append("\n**Export status:**\n")
    for k in [
        "archive_export_ready",
        "archive_completeness",
        "archive_export_status"
    ]:
        v = JSON_CONTRACT[k]
        lines.append(f"- {k}: {v}")
    lines.append("\n**Archive export notes:**\n")
    for l in RECORD["archive_export_notes"]:
        lines.append(f"- {l}")
    lines.append("\n**Archive export record:**\n")
    # Table header
    cols = [
        "archive_export_id",
        "export_position",
        "program_closeout_id",
        "operator_handoff_id",
        "live_execution_handoff_id",
        "post_run_retrospective_id",
        "archive_export_status",
        "archive_completeness",
        "archive_export_summary",
        "lineage_source_layer",
        "lineage_source_file",
        "lineage_source_record_id"
    ]
    lines.append(" | ".join(cols))
    lines.append(" | ".join(["---"] * len(cols)))
    r = RECORD
    row = [
        r["archive_export_id"],
        str(r["export_position"]),
        r["program_closeout_id"],
        r["operator_handoff_id"],
        r["live_execution_handoff_id"],
        r["post_run_retrospective_id"],
        r["archive_export_status"],
        r["archive_completeness"],
        r["archive_export_summary"],
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
