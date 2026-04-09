import os
import json
import sys
from ai_risa_report_output_adapter import map_engine_output_to_report
from ai_risa_report_renderer import _resolve_visual_slot, render_markdown
from report_render_assets import VISUAL_SLOT_CONFIG

# Fixture root (default to frozen fixtures for CI)
fixture_root = sys.argv[1] if len(sys.argv) > 1 else "fixtures/predictions_frozen"
FIXTURES = [
    os.path.join(fixture_root, "van_taira_baseline.json"),
    os.path.join(fixture_root, "volkov_cortes_baseline.json"),
    os.path.join(fixture_root, "volkov_cortes_sens2.json"),
    os.path.join(fixture_root, "muhammad_bonfim_baseline.json"),
    os.path.join(fixture_root, "muhammad_bonfim_sens2.json"),
]

# Engine contract fields
CONTRACT_FIELDS = [
    "predicted_winner_id",
    "confidence",
    "method",
    "round",
    "debug_metrics",
]

# Section and slot invariants
SECTION_IDS = None
VISUAL_SLOT_IDS = list(VISUAL_SLOT_CONFIG.keys())

failures = []

for fixture in FIXTURES:
    with open(fixture, "r", encoding="utf-8") as f:
        engine_output = json.load(f)
    # Contract fields
    for field in CONTRACT_FIELDS:
        if field not in engine_output:
            failures.append(f"{fixture}: missing contract field {field}")
    # Adapter output
    report = map_engine_output_to_report(engine_output)
    # Section order
    section_ids = [s["id"] for s in report["sections"]]
    if SECTION_IDS is None:
        SECTION_IDS = section_ids
    elif section_ids != SECTION_IDS:
        failures.append(f"{fixture}: section order mismatch {section_ids} != {SECTION_IDS}")
    # Visual slot order
    slot_ids = list(report["visual_slots"].keys())
    if slot_ids != VISUAL_SLOT_IDS:
        failures.append(f"{fixture}: visual slot order mismatch {slot_ids} != {VISUAL_SLOT_IDS}")
    # Slot behavior
    manifest = {k: None for k in VISUAL_SLOT_IDS}
    # Simulate slot resolution
    for slot_id in VISUAL_SLOT_IDS:
        slot = _resolve_visual_slot(slot_id, report["visual_slots"].get(slot_id))
        manifest[slot_id] = slot["status"]
    # method_chart
    if "method_distribution" in report:
        if manifest["method_chart"] != "asset":
            failures.append(f"{fixture}: method_chart should be asset when method_distribution exists")
    else:
        if manifest["method_chart"] != "placeholder":
            failures.append(f"{fixture}: method_chart should be placeholder when method_distribution is missing")
    # radar
    if "radar_metrics" in report:
        if manifest["radar"] != "asset":
            failures.append(f"{fixture}: radar should be asset when radar_metrics exists")
    else:
        if manifest["radar"] != "placeholder":
            failures.append(f"{fixture}: radar should be placeholder when radar_metrics is missing")
    # heat_map and control_shift always placeholder
    for slot_id in ["heat_map", "control_shift"]:
        if manifest[slot_id] != "placeholder":
            failures.append(f"{fixture}: {slot_id} should always be placeholder in baseline")
    # Optional: render markdown and check slot order
    md = render_markdown(report)
    # Check slot order in markdown output
    visual_section = md.split("## Visual Dashboard")[-1]
    lines = [l for l in visual_section.splitlines() if l.strip().startswith("**")]
    md_slot_titles = [l.split(':')[0].strip('* ') for l in lines if ':' in l]
    expected_titles = [VISUAL_SLOT_CONFIG[k]["title"] for k in VISUAL_SLOT_IDS]
    if md_slot_titles != expected_titles:
        failures.append(f"{fixture}: Markdown visual slot order {md_slot_titles} != {expected_titles}")

if failures:
    print("\n".join(failures))
    sys.exit(1)
else:
    print("All presentation regression checks passed.")
