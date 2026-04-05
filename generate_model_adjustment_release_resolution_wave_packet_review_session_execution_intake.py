# v10.0 execution intake generator for AI-RISA review-session chain
# Contract: new workstream, do not mutate v8.8–v9.6, deterministic, one intake record per manifest, stable lineage, sealed-chain status, no timestamps, no policy/release logic

import json
import os
from pathlib import Path

INPUT_PATH = os.path.join("ops", "model_adjustments")
MANIFEST = os.path.join(INPUT_PATH, "model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_manifest.json")
CHAIN_AUDIT = os.path.join(INPUT_PATH, "model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_chain_audit.json")
HANDOFF = os.path.join(INPUT_PATH, "model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_audit_handoff.json")
CLOSEOUT = os.path.join(INPUT_PATH, "model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_closeout.json")
OUTPUT_JSON = os.path.join(INPUT_PATH, "model_adjustment_release_resolution_wave_packet_review_session_execution_intake.json")
OUTPUT_MD = os.path.join(INPUT_PATH, "model_adjustment_release_resolution_wave_packet_review_session_execution_intake.md")

def main():
    # Load manifest records
    with open(MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)["release_resolution_wave_packet_review_session_routing_catalog_manifest"]
    # Load closeout for sealed-chain status
    with open(CLOSEOUT, "r", encoding="utf-8") as f:
        closeout = json.load(f)
    # Build intake records
    intake_records = []
    for i, m in enumerate(manifest):
        intake_id = f"resolution-wave-packet-review-session-execution-intake-{i+1:04d}"
        intake_records.append({
            "execution_intake_id": intake_id,
            "intake_position": i+1,
            "routing_catalog_manifest_id": m["resolution_wave_packet_review_session_routing_catalog_manifest_id"],
            "lineage_source_layer": "routing_catalog_manifest",
            "lineage_source_file": MANIFEST,
            "lineage_source_record_id": m["resolution_wave_packet_review_session_routing_catalog_manifest_id"],
            "sealed_chain_status": {
                "chain_complete": closeout["chain_complete"],
                "audit_complete": closeout["audit_complete"],
                "handoff_complete": closeout["handoff_complete"],
                "closeout_complete": True,
                "merge_performed": closeout["merge_performed"],
                "tag_performed": closeout["tag_performed"],
                "push_performed": closeout["push_performed"]
            }
        })
    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_execution_intake",
        "source_files": [MANIFEST, CHAIN_AUDIT, HANDOFF, CLOSEOUT],
        "record_count": len(intake_records),
        "records": intake_records
    }
    # Write JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    # Write Markdown summary
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# Execution Intake (v10.0)\n\n")
        f.write(f"## Source files\n\n")
        for sf in output['source_files']:
            f.write(f"- {sf}\n")
        f.write(f"\n## Intake Records\n\n")
        for r in intake_records:
            f.write(f"- {r['execution_intake_id']}: manifest_id={r['routing_catalog_manifest_id']}\n")
        f.write(f"\n## Sealed Chain Status\n\n")
        for k, v in intake_records[0]['sealed_chain_status'].items():
            f.write(f"- {k}: {v}\n")
        f.write(f"\n## Final Record Count\n\n")
        f.write(f"{output['record_count']}\n")

if __name__ == "__main__":
    main()
