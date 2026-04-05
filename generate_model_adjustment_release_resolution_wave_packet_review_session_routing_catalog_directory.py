import json
from pathlib import Path

def main():
    input_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_index.json")
    output_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_directory.json")
    output_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_directory.md")

    # Read input index JSON
    with input_path.open("r", encoding="utf-8") as f:
        index_data = json.load(f)
    index_records = index_data["release_resolution_wave_packet_review_session_routing_catalog_index"]

    # Build directory records
    directory_records = []
    for i, index_record in enumerate(index_records, 1):
        directory_record = {
            "routing_catalog_directory_id": f"resolution-wave-packet-review-session-routing-catalog-directory-{i:04d}",
            "routing_catalog_index_id": index_record["resolution_wave_packet_review_session_routing_catalog_index_id"],
            "directory_position": i,
            "lineage_source_layer": "routing_catalog_index",
            "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_index.json",
            "lineage_source_record_id": index_record["resolution_wave_packet_review_session_routing_catalog_index_id"],
        }
        directory_records.append(directory_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_directory",
        "source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_index.json",
        "source_record_count": len(directory_records),
        "record_count": len(directory_records),
        "records": directory_records,
    }

    # Write JSON output
    with output_json_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Write Markdown output
    with output_md_path.open("w", encoding="utf-8") as f:
        f.write("# model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_directory\n")
        f.write(f"Source file: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_index.json\n")
        f.write(f"Record count: {len(directory_records)}\n\n")
        f.write("| routing_catalog_directory_id | routing_catalog_index_id | directory_position | lineage_source_layer | lineage_source_file | lineage_source_record_id |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        for rec in directory_records:
            f.write(f"| {rec['routing_catalog_directory_id']} | {rec['routing_catalog_index_id']} | {rec['directory_position']} | {rec['lineage_source_layer']} | {rec['lineage_source_file']} | {rec['lineage_source_record_id']} |\n")

if __name__ == "__main__":
    main()
