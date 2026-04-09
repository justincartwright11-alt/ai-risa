# check_prediction_contract.py
"""
Script to assert required contract fields are present and non-null in prediction outputs.
Usage:
    py -3.10 check_prediction_contract.py <file1.json> <file2.json> ...
"""
import sys
import json

REQUIRED_FIELDS = [
    "predicted_winner_id",
    "confidence",
    "method",
    "round",
    "debug_metrics",
]

failures = []
for path in sys.argv[1:]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        missing = [k for k in REQUIRED_FIELDS if d.get(k) is None]
        if missing:
            failures.append((path, missing))
    except Exception as e:
        failures.append((path, [f"error: {e}"]))

if failures:
    print("CONTRACT FAILURE:")
    for path, missing in failures:
        print(f"  {path}: missing or null fields: {missing}")
    sys.exit(1)
else:
    print("All files pass contract check.")
    sys.exit(0)
