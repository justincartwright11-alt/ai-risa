import json
from pathlib import Path

def main():
    input_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_locator.json")
    output_json_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_register.json")
    output_md_path = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_register.md")

    # Read input locator JSON
    with input_path.open("r", encoding="utf-8") as f:
        locator_data = json.load(f)
    locator_records = locator_data["records"] if "records" in locator_data else locator_data.get("release_resolution_wave_packet_review_session_routing_catalog_locator", [])

    # Build register records
    register_records = []
    for i, locator_record in enumerate(locator_records, 1):
        register_record = {
            "routing_catalog_register_id": f"resolution-wave-packet-review-session-routing-catalog-register-{i:04d}",
            "routing_catalog_locator_id": locator_record["routing_catalog_locator_id"],
            "register_position": i,
            "lineage_source_layer": "routing_catalog_locator",
            "lineage_source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_locator.json",
            "lineage_source_record_id": locator_record["routing_catalog_locator_id"],
        }
        register_records.append(register_record)

    output = {
        "record_type": "model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_register",
        "source_file": "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_locator.json",
        "source_record_count": len(register_records),
        "record_count": len(register_records),
        "records": register_records,
    }

    # Write JSON output
    with output_json_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Write Markdown output
    with output_md_path.open("w", encoding="utf-8") as f:
        f.write("# model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_register\n")
        f.write(f"Source file: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_locator.json\n")
        f.write(f"Record count: {len(register_records)}\n\n")
        f.write("| routing_catalog_register_id | routing_catalog_locator_id | register_position | lineage_source_layer | lineage_source_file | lineage_source_record_id |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        for rec in register_records:
            f.write(f"| {rec['routing_catalog_register_id']} | {rec['routing_catalog_locator_id']} | {rec['register_position']} | {rec['lineage_source_layer']} | {rec['lineage_source_file']} | {rec['lineage_source_record_id']} |\n")

if __name__ == "__main__":
    main()
