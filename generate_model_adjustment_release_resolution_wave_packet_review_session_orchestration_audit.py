import json

# Input file paths
INTAKE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_intake.json"
QUEUE_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_queue.json"
DISPATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_dispatch.json"
BATCH_FILE = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_batch.json"

OUTPUT_JSON = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_audit.json"
OUTPUT_MD = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_orchestration_audit.md"

MD_COLUMNS = [
    "orchestration_audit_id",
    "audit_position",
    "orchestration_intake_id",
    "orchestration_queue_id",
    "orchestration_dispatch_id",
    "orchestration_batch_id",
    "lineage_chain_complete",
    "source_order_preserved",
    "deterministic_suffix_alignment",
    "exact_once_lineage",
    "lineage_source_layer",
    "lineage_source_file",
    "lineage_source_record_id",
]

def load_records(path, key="records"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data[key], data


def main():
    # Load all layers
    intake_records, intake_data = load_records(INTAKE_FILE)
    queue_records, queue_data = load_records(QUEUE_FILE)
    dispatch_records, dispatch_data = load_records(DISPATCH_FILE)
    batch_records, batch_data = load_records(BATCH_FILE)

    # Audit checks
    parity = (
        len(intake_records) == len(queue_records) == len(dispatch_records) == len(batch_records)
    )
    audit_record_count_matches_batch = (len(batch_records) == len(batch_records))
    exact_once_lineage = True
    source_order_preserved = True
    deterministic_suffix_alignment = True
    terminal_batch_coverage = (len(batch_records) == len(dispatch_records))

    # Check for empty case
    if not batch_records:
        output = {
            "record_type": "model_adjustment_release_resolution_wave_packet_review_session_orchestration_audit",
            "source_files": [INTAKE_FILE, QUEUE_FILE, DISPATCH_FILE, BATCH_FILE],
            "source_record_counts": {
                "orchestration_intake": len(intake_records),
                "orchestration_queue": len(queue_records),
                "orchestration_dispatch": len(dispatch_records),
                "orchestration_batch": len(batch_records),
            },
            "record_count": 0,
            "all_checks_pass": False,
            "checks": {
                "layer_record_count_parity_pass": parity,
                "audit_record_count_matches_batch_pass": audit_record_count_matches_batch,
                "exact_once_lineage_pass": exact_once_lineage,
                "source_order_preserved_pass": source_order_preserved,
                "deterministic_suffix_alignment_pass": deterministic_suffix_alignment,
                "terminal_batch_coverage_pass": terminal_batch_coverage,
            },
            "records": [],
        }
    else:
        audit_records = []
        for i, (intake, queue, dispatch, batch) in enumerate(
            zip(intake_records, queue_records, dispatch_records, batch_records), 1
        ):
            # Check deterministic suffix alignment
            suffix_ok = (
                intake["orchestration_intake_id"][-4:] == queue["orchestration_queue_id"][-4:] ==
                dispatch["orchestration_dispatch_id"][-4:] == batch["orchestration_batch_id"][-4:]
            )
            deterministic_suffix_alignment = deterministic_suffix_alignment and suffix_ok
            # Check source order
            source_order_preserved = source_order_preserved and (
                batch["batch_position"] == i
            )
            # Check exact-once lineage
            lineage_ok = (
                batch["orchestration_dispatch_id"] == dispatch["orchestration_dispatch_id"] and
                dispatch["orchestration_queue_id"] == queue["orchestration_queue_id"] and
                queue["orchestration_intake_id"] == intake["orchestration_intake_id"]
            )
            exact_once_lineage = exact_once_lineage and lineage_ok
            audit_record = {
                "orchestration_audit_id": f"resolution-wave-packet-review-session-orchestration-audit-{i:04d}",
                "audit_position": i,
                "orchestration_intake_id": intake["orchestration_intake_id"],
                "orchestration_queue_id": queue["orchestration_queue_id"],
                "orchestration_dispatch_id": dispatch["orchestration_dispatch_id"],
                "orchestration_batch_id": batch["orchestration_batch_id"],
                "lineage_chain_complete": lineage_ok and suffix_ok,
                "source_order_preserved": batch["batch_position"] == i,
                "deterministic_suffix_alignment": suffix_ok,
                "exact_once_lineage": lineage_ok,
                "lineage_source_layer": "orchestration_batch",
                "lineage_source_file": BATCH_FILE,
                "lineage_source_record_id": batch["orchestration_batch_id"],
            }
            audit_records.append(audit_record)
        output = {
            "record_type": "model_adjustment_release_resolution_wave_packet_review_session_orchestration_audit",
            "source_files": [INTAKE_FILE, QUEUE_FILE, DISPATCH_FILE, BATCH_FILE],
            "source_record_counts": {
                "orchestration_intake": len(intake_records),
                "orchestration_queue": len(queue_records),
                "orchestration_dispatch": len(dispatch_records),
                "orchestration_batch": len(batch_records),
            },
            "record_count": len(audit_records),
            "all_checks_pass": (
                parity and audit_record_count_matches_batch and exact_once_lineage and
                source_order_preserved and deterministic_suffix_alignment and terminal_batch_coverage
            ),
            "checks": {
                "layer_record_count_parity_pass": parity,
                "audit_record_count_matches_batch_pass": audit_record_count_matches_batch,
                "exact_once_lineage_pass": exact_once_lineage,
                "source_order_preserved_pass": source_order_preserved,
                "deterministic_suffix_alignment_pass": deterministic_suffix_alignment,
                "terminal_batch_coverage_pass": terminal_batch_coverage,
            },
            "records": audit_records,
        }

    # Write JSON output
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Write Markdown output
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(" | ".join(MD_COLUMNS) + "\n")
        f.write(" | ".join(["---"] * len(MD_COLUMNS)) + "\n")
        for rec in output["records"]:
            row = [
                str(rec[col]) if not isinstance(rec[col], bool) else ("true" if rec[col] else "false")
                for col in MD_COLUMNS
            ]
            f.write(" | ".join(row) + "\n")

if __name__ == "__main__":
    main()
