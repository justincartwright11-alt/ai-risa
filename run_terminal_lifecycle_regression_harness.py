"""
Entry point for the terminal lifecycle regression harness.
- Executes the frozen baseline builders in the approved order
- Verifies required output files exist
- Stops immediately on the first failure
- Writes one deterministic pass/fail result object in memory
"""

from compare_terminal_lifecycle_baseline import compare_baseline
from render_terminal_lifecycle_regression_report import render_report

if __name__ == "__main__":
    try:
        result = compare_baseline()
    except Exception as e:
        # On error, emit a fail report with exception info
        result = {
            "baseline_tag": "ai-risa-v78.0-terminal-lifecycle-release-baseline",
            "baseline_sha": "732a97c64e162d55e6cd0f9194b1f46d42b6ec7b",
            "checked": 0,
            "passed": 0,
            "failed": 1,
            "missing": [],
            "hash_mismatches": [],
            "structural_mismatches": [
                {"file": "<comparator exception>", "error": str(e)}
            ],
            "first_failure": f"exception: {e}",
            "status": "fail"
        }
    try:
        render_report(result)
    except Exception as e2:
        # If report writing fails, print to stdout as last resort
        import json
        print(json.dumps({"report_write_error": str(e2), "result": result}, indent=2))
