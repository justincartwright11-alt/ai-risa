

# ...existing code...

# Place main block at the very end so all functions are defined

import os
import json
import hashlib

BASELINE_TAG = "ai-risa-v78.0-terminal-lifecycle-release-baseline"
BASELINE_SHA = "732a97c64e162d55e6cd0f9194b1f46d42b6ec7b"

REQUIRED_ARTIFACTS = [
    ("ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_lineage_manifest.json", "json"),
    ("ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_lineage_manifest.md", "hash"),
    ("ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_release_summary.md", "hash"),
    ("ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_convergence_registry.json", "json"),
    ("ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_convergence_registry.md", "hash"),
]

BASELINE_HASHES = {
    # "ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_lineage_manifest.json": "...",  # hash for JSON
    # "ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_lineage_manifest.md": "...",
    # "ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_release_summary.md": "...",
    # "ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_convergence_registry.json": "...",  # hash for JSON
    # "ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_convergence_registry.md": "...",
}

def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def compare_baseline():
    result = {
        "baseline_tag": BASELINE_TAG,
        "baseline_sha": BASELINE_SHA,
        "checked": 0,
        "passed": 0,
        "failed": 0,
        "missing": [],
        "hash_mismatches": [],
        "structural_mismatches": [],
        "first_failure": None,
        "status": "pass"
    }
    for path, mode in REQUIRED_ARTIFACTS:
        result["checked"] += 1
        if not os.path.exists(path):
            result["missing"].append(path)
            result["failed"] += 1
            result["first_failure"] = f"missing: {path}"
            result["status"] = "fail"
            break
        h = file_hash(path)
        baseline = BASELINE_HASHES.get(path)
        if baseline and h != baseline:
            result["hash_mismatches"].append({"file": path, "expected": baseline, "actual": h})
            result["failed"] += 1
            result["first_failure"] = f"hash: {path}"
            result["status"] = "fail"
            break
        if mode == "json":
            # JSON parse check
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                result["structural_mismatches"].append({"file": path, "error": f"json parse: {e}"})
                result["failed"] += 1
                result["first_failure"] = f"json parse: {path}"
                result["status"] = "fail"
                break
            # v78.0 baseline: both JSON artifacts are lists of dicts, check for list and unique terminal_registry_item_id
            if not isinstance(data, list):
                result["structural_mismatches"].append({"file": path, "error": "not a list at top level"})
                result["failed"] += 1
                result["first_failure"] = f"structure: {path}"
                result["status"] = "fail"
                break
            seen = set()
            for entry in data:
                tid = entry.get("terminal_registry_item_id")
                if not tid:
                    result["structural_mismatches"].append({"file": path, "error": "missing terminal_registry_item_id in entry"})
                    result["failed"] += 1
                    result["first_failure"] = f"structure: {path}"
                    result["status"] = "fail"
                    break
                if tid in seen:
                    result["structural_mismatches"].append({"file": path, "error": f"duplicate terminal_registry_item_id: {tid}"})
                    result["failed"] += 1
                    result["first_failure"] = f"structure: {path}"
                    result["status"] = "fail"
                    break
                seen.add(tid)
        result["passed"] += 1
    return result

if __name__ == "__main__":
    import json
    import sys
    result = compare_baseline()
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0 if result.get("status") == "pass" else 1)

import os
import json
import hashlib

# Canonical baseline references
BASELINE_TAG = "ai-risa-v78.0-terminal-lifecycle-release-baseline"
BASELINE_SHA = "732a97c64e162d55e6cd0f9194b1f46d42b6ec7b"

# Required artifacts (locked for v79.0)
REQUIRED_ARTIFACTS = [
    ("ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_lineage_manifest.json", "json"),
    ("ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_lineage_manifest.md", "hash"),
    ("ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_release_summary.md", "hash"),
    ("ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_convergence_registry.json", "json"),
    ("ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_convergence_registry.md", "hash"),
]

# Baseline hashes (to be filled in after first run)
BASELINE_HASHES = {
    # "ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_lineage_manifest.json": "...",  # hash for JSON
    # "ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_lineage_manifest.md": "...",
    # "ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_release_summary.md": "...",
    # "ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_convergence_registry.json": "...",  # hash for JSON
    # "ops/events/upcoming_schedule_manual_intervention_terminal_lifecycle_convergence_registry.md": "...",
}

def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def compare_baseline():
    result = {
        "baseline_tag": BASELINE_TAG,
        "baseline_sha": BASELINE_SHA,
        "checked": 0,
        "passed": 0,
        "failed": 0,
        "missing": [],
        "hash_mismatches": [],
        "structural_mismatches": [],
        "first_failure": None,
        "status": "pass"
    }
    for path, mode in REQUIRED_ARTIFACTS:
        result["checked"] += 1
        if not os.path.exists(path):
            result["missing"].append(path)
            result["failed"] += 1
            result["first_failure"] = f"missing: {path}"
            result["status"] = "fail"
            break
        h = file_hash(path)
        baseline = BASELINE_HASHES.get(path)
        if baseline and h != baseline:
            result["hash_mismatches"].append({"file": path, "expected": baseline, "actual": h})
            result["failed"] += 1
            result["first_failure"] = f"hash: {path}"
            result["status"] = "fail"
            break
        if mode == "json":
            # JSON parse check
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                result["structural_mismatches"].append({"file": path, "error": f"json parse: {e}"})
                result["failed"] += 1
                result["first_failure"] = f"json parse: {path}"
                result["status"] = "fail"
                break
            # Minimal structure check for registry/manifest
            if path.endswith("convergence_registry.json"):
                # Expect top-level 'registry' key and unique root-case/terminal IDs
                if "registry" not in data or not isinstance(data["registry"], list):
                    result["structural_mismatches"].append({"file": path, "error": "missing or invalid 'registry' key"})
                    result["failed"] += 1
                    result["first_failure"] = f"structure: {path}"
                    result["status"] = "fail"
                    break
                seen = set()
                for entry in data["registry"]:
                    tid = entry.get("terminal_id") or entry.get("id")
                    if not tid:
                        result["structural_mismatches"].append({"file": path, "error": "missing terminal_id in entry"})
                        result["failed"] += 1
                        result["first_failure"] = f"structure: {path}" 
                        result["status"] = "fail"
                        break
                    if tid in seen:
                        result["structural_mismatches"].append({"file": path, "error": f"duplicate terminal_id: {tid}"})
                        result["failed"] += 1
                        result["first_failure"] = f"structure: {path}"
                        result["status"] = "fail"
                        break
                    seen.add(tid)
            elif path.endswith("lineage_manifest.json"):
                # Expect top-level keys (e.g., 'lineage', 'artifacts')
                required_keys = ["lineage", "artifacts"]
                for k in required_keys:
                    if k not in data:
                        result["structural_mismatches"].append({"file": path, "error": f"missing key: {k}"})
                        result["failed"] += 1
                        result["first_failure"] = f"structure: {path}"
                        result["status"] = "fail"
                        break
        result["passed"] += 1
    return result
