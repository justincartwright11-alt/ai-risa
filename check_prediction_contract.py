# check_prediction_contract.py
"""
Script to assert required contract fields are present and non-null in prediction outputs.
Usage:
    py -3.10 check_prediction_contract.py <file1.json> <file2.json> ...
"""
import sys
import json
from typing import Any

REQUIRED_FIELDS = [
    "predicted_winner_id",
    "confidence",
    "method",
    "round",
    "debug_metrics",
    "signal_gap",
    "stoppage_propensity",
    "round_finish_tendency",
    "key_tactical_edges",
    "risk_factors",
    "confidence_explanation",
    "what_could_flip_the_fight",
]

def validate_prediction_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"missing field: {field}")
            continue
        if record[field] is None:
            errors.append(f"null field: {field}")

    # Minimal but strict shape checks for canonical narrative fields.
    if "key_tactical_edges" in record and record.get("key_tactical_edges") is not None:
        if not isinstance(record["key_tactical_edges"], list):
            errors.append("type mismatch: key_tactical_edges must be list")
    if "risk_factors" in record and record.get("risk_factors") is not None:
        if not isinstance(record["risk_factors"], list):
            errors.append("type mismatch: risk_factors must be list")
    if "confidence_explanation" in record and record.get("confidence_explanation") is not None:
        if not isinstance(record["confidence_explanation"], str):
            errors.append("type mismatch: confidence_explanation must be str")
    if "what_could_flip_the_fight" in record and record.get("what_could_flip_the_fight") is not None:
        if not isinstance(record["what_could_flip_the_fight"], list):
            errors.append("type mismatch: what_could_flip_the_fight must be list")

    return errors


def check_files(paths: list[str]) -> list[tuple[str, list[str]]]:
    failures: list[tuple[str, list[str]]] = []
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if not isinstance(payload, dict):
                failures.append((path, ["error: record must be a JSON object"]))
                continue
            record_errors = validate_prediction_record(payload)
            if record_errors:
                failures.append((path, record_errors))
        except Exception as exc:
            failures.append((path, [f"error: {exc}"]))
    return failures


def main(argv: list[str]) -> int:
    failures = check_files(argv[1:])
    if failures:
        print("CONTRACT FAILURE:")
        for path, errors in failures:
            print(f"  {path}: {errors}")
        return 1

    print("All files pass contract check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
