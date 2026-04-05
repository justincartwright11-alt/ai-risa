# v64.154-controlled-release-resolution-wave-packet-review-session-governed-operations-closure-release-final-prep-prep-prep-prep-verification
# Generator for controlled verification projection from attestation

import json
import hashlib
from pathlib import Path

PARENT_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_attestation.json"
CHILD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_verification.json"
CHILD_MD_PATH = "ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_governed_operations_closure_release_final_prep_prep_prep_prep_verification.md"

PASS_THROUGH_FIELDS = [
    "attestation_id", "receipt_id", "source_handoff_id", "handoff_id", "source_register_id", "register_id", "map_id", "record_type", "status", "name", "title", "slug"
]

REQUIRED_FIELDS = [
    "verification_id", "verification_position", "source_attestation_id", "source_attestation_position", "source_attestation_artifact", "verification_locator_key"
]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    parent = json.load(open(PARENT_PATH, "r", encoding="utf-8"))
    parent_records = parent["records"]
    out = {
        "parent_artifact": PARENT_PATH,
        "record_count": len(parent_records),
        "records": []
    }
    seen_attestation_ids = set()
    for i, rec in enumerate(parent_records):
        if "attestation_id" not in rec:
            raise Exception(f"No usable source_attestation_id in parent record {i+1}")
        if rec["attestation_id"] in seen_attestation_ids:
            raise Exception(f"Duplicate source_attestation_id: {rec['attestation_id']}")
        seen_attestation_ids.add(rec["attestation_id"])
        verification = {
            "verification_id": f"closure-release-final-prep-prep-prep-prep-verification-{i+1:04d}",
            "verification_position": i+1,
            "source_attestation_id": rec["attestation_id"],
            "source_attestation_position": rec["attestation_position"],
            "source_attestation_artifact": PARENT_PATH,
            "verification_locator_key": rec.get("attestation_locator_key", f"closure-release-final-prep-prep-prep-prep-verification-{i+1:04d}")
        }
        # Pass through allowed fields if present
        for field in PASS_THROUGH_FIELDS:
            if field in rec:
                verification[field] = rec[field]
        out["records"].append(verification)
    out["record_count"] = len(out["records"])
    with open(CHILD_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    # Write Markdown summary
    with open(CHILD_MD_PATH, "w", encoding="utf-8") as f:
        f.write("# closure-release-final-prep-prep-prep-prep-verification\n\n")
        f.write(f"* parent_artifact: {PARENT_PATH}\n")
        f.write(f"* record_count: {out['record_count']}\n\n")
        f.write("| verification_id | verification_position | source_attestation_id | verification_locator_key |\n")
        f.write("| --------------- | --------------------: | --------------------- | ------------------------ |\n")
        for r in out["records"]:
            f.write(f"| {r['verification_id']} | {r['verification_position']} | {r['source_attestation_id']} | {r['verification_locator_key']} |\n")
    print("Generation complete.")

if __name__ == "__main__":
    main()
