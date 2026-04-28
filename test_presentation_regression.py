import os
import json
import sys
from ai_risa_report_output_adapter import map_engine_output_to_report
from ai_risa_report_renderer import _resolve_visual_slot, render_markdown
from report_render_assets import VISUAL_SLOT_CONFIG
from report_visual_asset_producer import build_visual_manifest


def _derive_fighter_name(fighter_id, fallback):
    text = str(fighter_id or "").strip()
    if not text:
        return fallback
    return text.replace("fighter_", "").replace("_", " ").strip().title() or fallback


def _enrich_for_report_contract(engine_output, fixture_path):
    """Mirror runtime metadata injection used before report mapping in CLI flow."""
    enriched = dict(engine_output or {})

    fallback_fight_id = os.path.splitext(os.path.basename(fixture_path))[0]
    enriched.setdefault(
        "fight_id",
        enriched.get("matchup_id")
        or enriched.get("prediction_family_id")
        or fallback_fight_id,
    )

    fighter_a_id = enriched.get("fighter_a_id")
    fighter_b_id = enriched.get("fighter_b_id")
    enriched.setdefault("fighter_a_name", _derive_fighter_name(fighter_a_id, "Fighter A"))
    enriched.setdefault("fighter_b_name", _derive_fighter_name(fighter_b_id, "Fighter B"))

    enriched.setdefault("event_date", "Date TBD")
    enriched.setdefault("sport", "mma")
    enriched.setdefault("promotion", "Independent Promotion")
    return enriched

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
        engine_output = _enrich_for_report_contract(json.load(f), fixture)
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
    # Current adapter may leave visual_slots empty and rely on manifest + renderer slot config.
    slot_ids = list((report.get("visual_slots") or {}).keys())
    if slot_ids and slot_ids != VISUAL_SLOT_IDS:
        failures.append(f"{fixture}: visual slot order mismatch {slot_ids} != {VISUAL_SLOT_IDS}")

    # Build visual manifest the same way export pipeline does before rendering checks.
    build_visual_manifest(report)
    # Slot behavior
    manifest = {k: None for k in VISUAL_SLOT_IDS}
    # Simulate slot resolution
    for slot_id in VISUAL_SLOT_IDS:
        slot = _resolve_visual_slot(slot_id, report)
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
    # heat_map
    if "heat_map_data" in report:
        if manifest["heat_map"] != "asset":
            failures.append(f"{fixture}: heat_map should be asset when heat_map_data exists")
    else:
        if manifest["heat_map"] != "placeholder":
            failures.append(f"{fixture}: heat_map should be placeholder when heat_map_data is missing")
    # control_shift
    if "control_shift_data" in report:
        if manifest["control_shift"] != "asset":
            failures.append(f"{fixture}: control_shift should be asset when control_shift_data exists")
    else:
        if manifest["control_shift"] != "placeholder":
            failures.append(f"{fixture}: control_shift should be placeholder when control_shift_data is missing")
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
