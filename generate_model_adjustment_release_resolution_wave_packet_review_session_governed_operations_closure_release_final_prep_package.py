
# v64.100 closure-release-final-prep-package generator
# Pure downstream projection from closure-release-final-prep-archive
# Reads: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_archive.json
# Writes: model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_package.json, .md

import json
import hashlib
from pathlib import Path

ARCHIVE_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_archive.json")
PACKAGE_JSON_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_package.json")
PACKAGE_MD_PATH = Path("ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_package.md")

FROZEN_GENERATED_AT_UTC = "2026-04-04T00:00:00Z"

def deterministic_id(record):
    # Deterministic ID: hash of upstream id + family marker
    upstream_id = record["id"]
    base = f"{upstream_id}|closure-release-final-prep-package"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def main():
    with ARCHIVE_PATH.open("r", encoding="utf-8") as f:
        archive_records = json.load(f)

    # Deterministic ordering by upstream id
    archive_records = sorted(archive_records, key=lambda r: r["id"])

    package_records = []
    for rec in archive_records:
        new_id = deterministic_id(rec)
        package_record = {
            "id": new_id,
            "upstream_id": rec["id"],
            "generated_at_utc": FROZEN_GENERATED_AT_UTC,
            "trace": rec.get("trace", {}),
            "data": rec.get("data", {}),
        }
        package_records.append(package_record)

    # Write JSON
    with PACKAGE_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(package_records, f, indent=2, ensure_ascii=False)

    # Write Markdown as pure projection of JSON
    with PACKAGE_MD_PATH.open("w", encoding="utf-8") as f:
        f.write(f"# closure-release-final-prep-package\n\n")
        for rec in package_records:
            f.write(f"- id: {rec['id']}\n")
            f.write(f"  upstream_id: {rec['upstream_id']}\n")
            f.write(f"  generated_at_utc: {rec['generated_at_utc']}\n")
            f.write(f"  trace: {json.dumps(rec['trace'], ensure_ascii=False)}\n")
            f.write(f"  data: {json.dumps(rec['data'], ensure_ascii=False)}\n\n")

if __name__ == "__main__":
    main()
