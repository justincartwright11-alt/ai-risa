import json
from pathlib import Path

def main():
    input_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_directory.json")
    output_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_locator.json")
    output_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_locator.md")

    # Read input directory JSON
    with input_path.open("r", encoding="utf-8") as f:
        directory_data = json.load(f)
    directory_records = directory_data["records"] if "records" in directory_data else directory_data.get("release_resolution_wave_packet_review_session_routing_catalog_directory", [])

    # Build locator records
    locator_records = []
    for i, directory_record in enumerate(directory_records, 1):
        locator_record = {
            "routing_catalog_locator_id": f"resolution-wave-packet-review-session-routing-catalog-locator-{i:04d}",
            "routing_catalog_directory_id": directory_record["routing_catalog_directory_id"],
            "locator_position": i,
            "lineage_source_layer": "routing_catalog_directory",
            "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_directory.json",
            "lineage_source_record_id": directory_record["routing_catalog_directory_id"],
        }
        locator_records.append(locator_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_locator",
        "source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_directory.json",
        "source_record_count": len(locator_records),
        "record_count": len(locator_records),
        "records": locator_records,
    }

    # Write JSON output
    with output_json_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Write Markdown output
    with output_md_path.open("w", encoding="utf-8") as f:
        f.write("# model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_locator\n")
        f.write(f"Source file: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_directory.json\n")
        f.write(f"Record count: {len(locator_records)}\n\n")
        f.write("| routing_catalog_locator_id | routing_catalog_directory_id | locator_position | lineage_source_layer | lineage_source_file | lineage_source_record_id |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        for rec in locator_records:
            f.write(f"| {rec['routing_catalog_locator_id']} | {rec['routing_catalog_directory_id']} | {rec['locator_position']} | {rec['lineage_source_layer']} | {rec['lineage_source_file']} | {rec['lineage_source_record_id']} |\n")

if __name__ == "__main__":
    main()
