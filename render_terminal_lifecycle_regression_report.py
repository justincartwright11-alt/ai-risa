"""
Renders the operator-facing regression harness report.
- Outputs JSON and Markdown reports to ops/events/
"""
import json
import os

def render_report(result):
    os.makedirs("ops/events", exist_ok=True)
    # Write JSON report
    with open("ops/events/terminal_lifecycle_regression_harness_report.json", "w") as f:
        json.dump(result, f, indent=2)
    # Write Markdown report
    with open("ops/events/terminal_lifecycle_regression_harness_report.md", "w") as f:
        f.write(f"""
# Terminal Lifecycle Regression Harness Report

**Baseline tag:** {result['baseline_tag']}
**Baseline SHA:** {result['baseline_sha']}
**Run status:** {result['status']}
**Checked artifacts:** {result['checked']}
**Passed:** {result['passed']}
**Failed:** {result['failed']}

## Missing artifacts
{result['missing']}

## Hash mismatches
{result['hash_mismatches']}

## Structural mismatches
{result['structural_mismatches']}

**First failure:** {result['first_failure']}
""")
