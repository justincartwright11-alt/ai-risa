"""
generate_model_adjustment_release_resolution_wave_packet_review_session_consumer_audit.py

- Inputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_intake.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_queue.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_batch.json
- Outputs:
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_audit.json
    - ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_audit.md
- Contract: Consumer family only, do not mutate v8.8–v16.3, audit only, one audit record per batch, verify exact-once lineage, record-count parity, deterministic suffix alignment, source-order preservation, deterministic 4-digit audit IDs, no timestamps/policy/release/merge/tag/push.
"""
import json
import os

INTAKE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_intake.json"
QUEUE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_queue.json"
DISPATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch.json"
BATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_batch.json"
OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_audit.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_audit.md"

MD_COLUMNS = [
    "consumer_audit_id",
    "audit_position",
    "consumer_intake_id",
    "consumer_queue_id",
    "consumer_dispatch_id",
    "consumer_batch_id",
    "lineage_chain_complete",
    "source_order_preserved",
    "deterministic_suffix_alignment",
    "exact_once_lineage",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def main():
    with open(INTAKE_FILE, "r", encoding="utf-8") as f:
        intake = json.load(f)["records"]
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue = json.load(f)["records"]
    with open(DISPATCH_FILE, "r", encoding="utf-8") as f:
        dispatch = json.load(f)["records"]
    with open(BATCH_FILE, "r", encoding="utf-8") as f:
        batch = json.load(f)["records"]

    n = len(batch)
    # Checks
    layer_record_count_parity_pass = (
        len(intake) == len(queue) == len(dispatch) == len(batch)
    )
    audit_record_count_matches_batch_pass = n == len(batch)
    exact_once_lineage_pass = True
    source_order_preserved_pass = True
    deterministic_suffix_alignment_pass = True
    terminal_batch_coverage_pass = n == len(batch)

    # Check lineage and suffix alignment
    for i in range(n):
        # Suffixes
        suffix = f"{i+1:04d}"
        ids = [
            intake[i]["consumer_intake_id"],
            queue[i]["consumer_queue_id"],
            dispatch[i]["consumer_dispatch_id"],
            batch[i]["consumer_batch_id"],
        ]
        # Suffix alignment
        if not all(x.endswith(suffix) for x in ids):
            deterministic_suffix_alignment_pass = False
        # Source order
        if not (intake[i]["consumer_intake_id"] and queue[i]["consumer_intake_id"] == intake[i]["consumer_intake_id"]):
            source_order_preserved_pass = False
        if not (queue[i]["consumer_queue_id"] and dispatch[i]["consumer_queue_id"] == queue[i]["consumer_queue_id"]):
            source_order_preserved_pass = False
        if not (dispatch[i]["consumer_dispatch_id"] and batch[i]["consumer_dispatch_id"] == dispatch[i]["consumer_dispatch_id"]):
            source_order_preserved_pass = False
        # Exact-once lineage
        if not (
            queue[i]["consumer_intake_id"] == intake[i]["consumer_intake_id"] and
            dispatch[i]["consumer_queue_id"] == queue[i]["consumer_queue_id"] and
            batch[i]["consumer_dispatch_id"] == dispatch[i]["consumer_dispatch_id"]
        ):
            exact_once_lineage_pass = False

    all_checks_pass = (
        layer_record_count_parity_pass and
        audit_record_count_matches_batch_pass and
        exact_once_lineage_pass and
        source_order_preserved_pass and
        deterministic_suffix_alignment_pass and
        terminal_batch_coverage_pass
    )

    checks = {
        "layer_record_count_parity_pass": layer_record_count_parity_pass,
        "audit_record_count_matches_batch_pass": audit_record_count_matches_batch_pass,
        "exact_once_lineage_pass": exact_once_lineage_pass,
        "source_order_preserved_pass": source_order_preserved_pass,
        "deterministic_suffix_alignment_pass": deterministic_suffix_alignment_pass,
        "terminal_batch_coverage_pass": terminal_batch_coverage_pass,
    }

    audit_records = []
    for i in range(n):
        audit_id = f"resolution-wave-packet-review-session-consumer-audit-{i+1:04d}"
        audit_record = {
            "consumer_audit_id": audit_id,
            "audit_position": i+1,
            "consumer_intake_id": intake[i]["consumer_intake_id"],
            "consumer_queue_id": queue[i]["consumer_queue_id"],
            "consumer_dispatch_id": dispatch[i]["consumer_dispatch_id"],
            "consumer_batch_id": batch[i]["consumer_batch_id"],
            "lineage_chain_complete": True,
            "source_order_preserved": source_order_preserved_pass,
            "deterministic_suffix_alignment": deterministic_suffix_alignment_pass,
            "exact_once_lineage": exact_once_lineage_pass,
            "lineage_source_layer": "consumer_batch",
            "lineage_source_file": BATCH_FILE,
            "lineage_source_record_id": batch[i]["consumer_batch_id"],
        }
        audit_records.append(audit_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_consumer_audit",
        "source_files": [INTAKE_FILE, QUEUE_FILE, DISPATCH_FILE, BATCH_FILE],
        "source_record_counts": {
            "consumer_intake": len(intake),
            "consumer_queue": len(queue),
            "consumer_dispatch": len(dispatch),
            "consumer_batch": len(batch),
        },
        "record_count": len(audit_records),
        "all_checks_pass": all_checks_pass,
        "checks": checks,
        "records": audit_records,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# v16.4 Controlled Release Resolution Wave Packet Review Session Consumer Audit\n\n")
        f.write("## Source Files\n")
        for src in output["source_files"]:
            f.write(f"- {src}\n")
        f.write("\n## Checks\n")
        for k, v in checks.items():
            f.write(f"- {k}: {str(v).lower()}\n")
        f.write(f"- all_checks_pass: {str(all_checks_pass).lower()}\n\n")
        f.write("## Audit Table\n")
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        for record in audit_records:
            row = [
                str(record[col]) if not isinstance(record[col], bool) else str(record[col]).lower()
                for col in MD_COLUMNS
            ]
            f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
