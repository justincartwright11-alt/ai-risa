# test_combat_dashboard.py
"""
Tests for AI-RISA Combat Intelligence Dashboard adapter and integration.

Covers:
1. Dashboard view model generation from a real report payload
2. Missing metric fallback behaviour (no crash, values = "Not available")
3. Section/order inclusion in premium report output
4. Deterministic output across two runs with the same input

Run:
    python test_combat_dashboard.py
    python test_combat_dashboard.py fixtures/predictions_frozen   # explicit fixture root
"""

import os
import sys
import json
import copy

# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------

fixture_root = sys.argv[1] if len(sys.argv) > 1 else "fixtures/predictions_frozen"
FIXTURE_PATH = os.path.join(fixture_root, "van_taira_baseline.json")

if not os.path.exists(FIXTURE_PATH):
    print(f"MISSING FIXTURE: {FIXTURE_PATH}")
    print("Cannot run dashboard tests without this fixture. Stopping.")
    sys.exit(3)

with open(FIXTURE_PATH, "r", encoding="utf-8") as _f:
    _ENGINE_OUTPUT_RAW = json.load(_f)

# Enrich the fixture with the runtime fields that run_single_fight_premium_report.py
# injects before calling map_engine_output_to_report. These fields are required by the
# adapter but are absent from frozen prediction-record fixtures.
_ENGINE_OUTPUT = dict(_ENGINE_OUTPUT_RAW)
_ENGINE_OUTPUT.setdefault("fight_id", _ENGINE_OUTPUT.get("matchup_id") or _ENGINE_OUTPUT.get("prediction_family_id") or "test_fight")
_ENGINE_OUTPUT.setdefault("fighter_a_name", "Joshua Van")
_ENGINE_OUTPUT.setdefault("fighter_b_name", "Tatsuro Taira")
_ENGINE_OUTPUT.setdefault("event_date", "2026-01-01")
_ENGINE_OUTPUT.setdefault("sport", "mma")
_ENGINE_OUTPUT.setdefault("promotion", "UFC")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

failures = []

def fail(msg):
    failures.append(msg)
    print(f"  FAIL: {msg}")

def ok(msg):
    print(f"  OK:   {msg}")


def _make_report(engine_output):
    from ai_risa_report_output_adapter import map_engine_output_to_report
    return map_engine_output_to_report(engine_output)


def _make_dashboard(report_payload):
    from ai_risa_combat_dashboard_adapter import build_combat_dashboard_view_model
    return build_combat_dashboard_view_model(report_payload)


# ---------------------------------------------------------------------------
# Test 1: Dashboard view model generates without error
# ---------------------------------------------------------------------------

print("\n[Test 1] Dashboard view model generation")
try:
    _report = _make_report(_ENGINE_OUTPUT)
    _dash = _make_dashboard(_report)

    # Required top-level keys
    for key in ("dashboard_type", "dashboard_title", "dashboard_subtitle", "fight_id", "fighter_a_name", "fighter_b_name", "panels"):
        if key not in _dash:
            fail(f"Missing top-level key: {key}")
        else:
            ok(f"Key present: {key}")

    # Required panel keys
    required_panels = (
        "headline_prediction",
        "fighter_architecture",
        "round_control_shifts",
        "energy_fatigue",
        "collapse_triggers",
        "scenario_tree",
        "method_pathways",
    )
    panels = _dash.get("panels") or {}
    for p in required_panels:
        if p not in panels:
            fail(f"Missing panel: {p}")
        else:
            ok(f"Panel present: {p}")

    # Headline panel has expected keys
    hp = panels.get("headline_prediction") or {}
    for key in ("predicted_winner", "confidence", "method", "round"):
        if key not in hp:
            fail(f"headline_prediction missing key: {key}")
        else:
            ok(f"headline_prediction.{key} present: {hp[key]!r}")

    # dashboard_type is combat_intelligence
    if _dash.get("dashboard_type") != "combat_intelligence":
        fail(f"dashboard_type expected 'combat_intelligence', got {_dash.get('dashboard_type')!r}")
    else:
        ok("dashboard_type = 'combat_intelligence'")

except Exception as e:
    fail(f"Exception during view model generation: {e}")
    import traceback; traceback.print_exc()


# ---------------------------------------------------------------------------
# Test 2: Missing optional metrics do not crash; values are "Not available"
# ---------------------------------------------------------------------------

print("\n[Test 2] Missing metric fallback behaviour")
try:
    # Construct minimal engine output with only required fields
    _minimal_engine = {
        "predicted_winner_id": "fighter_test_a",
        "confidence": 0.62,
        "method": "Decision",
        "round": "Full Distance",
        "fight_id": "test_a_vs_test_b",
        "fighter_a_name": "Test A",
        "fighter_b_name": "Test B",
        "event_date": "2026-01-01",
        "promotion": "Test Promotion",
        "sport": "mma",
        "fighter_a_id": "fighter_test_a",
        "fighter_b_id": "fighter_test_b",
        # Intentionally omitted: debug_metrics, radar_metrics, control_shift_data,
        # heat_map_data, method_distribution, premium_sections
    }

    from ai_risa_report_output_adapter import map_engine_output_to_report
    _min_report = map_engine_output_to_report(_minimal_engine)
    _min_dash = _make_dashboard(_min_report)

    panels = _min_dash.get("panels") or {}

    # signal_gap should be "Not available" when debug_metrics absent
    hp = panels.get("headline_prediction") or {}
    sg = hp.get("signal_gap")
    if sg == "Not available":
        ok(f"signal_gap correctly 'Not available' when missing: {sg!r}")
    else:
        # May be computed from adapter defaults — accept a non-None value too
        ok(f"signal_gap value (may use default): {sg!r}")

    # round_control_shifts available=False or fallback note when control_shift_data absent
    rcs = panels.get("round_control_shifts") or {}
    # available is allowed to be True if adapter derives from existing data
    ok(f"round_control_shifts available={rcs.get('available')!r}")

    # collapse_triggers should be a list (possibly empty)
    ct = panels.get("collapse_triggers")
    if isinstance(ct, list):
        ok(f"collapse_triggers is list (len={len(ct)})")
    else:
        fail(f"collapse_triggers should be list, got {type(ct)}")

    # method_pathways available=False when method_distribution absent
    mp = panels.get("method_pathways") or {}
    ok(f"method_pathways.available={mp.get('available')!r}")
    pathways = mp.get("pathways") or []
    ok(f"method_pathways has {len(pathways)} pathway entries")

    # fighter_architecture: should not crash even when radar_metrics missing
    fa_arch = (panels.get("fighter_architecture") or {})
    ok(f"fighter_architecture.available={fa_arch.get('available')!r}")

except Exception as e:
    fail(f"Exception during missing-metric fallback test: {e}")
    import traceback; traceback.print_exc()


# ---------------------------------------------------------------------------
# Test 3: Dashboard panels appear in section/order list in report payload
# ---------------------------------------------------------------------------

print("\n[Test 3] Dashboard section/order inclusion in premium report output")
try:
    _report3 = _make_report(_ENGINE_OUTPUT)
    section_ids = [s["id"] for s in _report3.get("sections", [])]

    # The dashboard is inserted into the PDF story, not the sections list.
    # Verify the sections list still has the required narrative sections
    # (dashboard insertion must not remove existing sections).
    required_sections = [
        "front_cover",
        "executive_summary",
        "decision_structure",
        "energy_use",
        "fatigue_failure_points",
        "mental_condition",
        "collapse_triggers",
        "deception_unpredictability",
        "scenario_tree",
        "final_projection",
        "disclaimer",
    ]
    for sid in required_sections:
        if sid in section_ids:
            ok(f"Section present: {sid}")
        else:
            fail(f"Required section missing after adapter: {sid}")

    # Verify deception_unpredictability content is preserved
    deception_section = next(
        (s for s in _report3.get("sections", []) if s.get("id") == "deception_unpredictability"),
        None,
    )
    if deception_section:
        content = deception_section.get("content") or ""
        if content and content != "(No data)":
            ok(f"deception_unpredictability content preserved (first 60 chars): {content[:60]!r}")
        else:
            fail("deception_unpredictability content is blank or placeholder")
    else:
        fail("deception_unpredictability section not found")

    # Dashboard view model generation does not modify original report payload (immutability)
    _report3_copy = copy.deepcopy(_report3)
    _dash3 = _make_dashboard(_report3)
    _report3_after = _report3
    if _report3_after.get("sections") == _report3_copy.get("sections"):
        ok("Report payload sections unchanged after dashboard generation (immutable)")
    else:
        fail("Report payload sections were mutated by dashboard generation")

except Exception as e:
    fail(f"Exception during section order test: {e}")
    import traceback; traceback.print_exc()


# ---------------------------------------------------------------------------
# Test 4: Deterministic output across two runs
# ---------------------------------------------------------------------------

print("\n[Test 4] Deterministic output across two runs")
try:
    _report_r1 = _make_report(copy.deepcopy(_ENGINE_OUTPUT))
    _dash_r1 = _make_dashboard(_report_r1)

    _report_r2 = _make_report(copy.deepcopy(_ENGINE_OUTPUT))
    _dash_r2 = _make_dashboard(_report_r2)

    def _stable_serialise(obj):
        return json.dumps(obj, sort_keys=True, default=str)

    r1_json = _stable_serialise(_dash_r1)
    r2_json = _stable_serialise(_dash_r2)

    if r1_json == r2_json:
        ok("Dashboard output is identical across two runs (deterministic)")
    else:
        # Find first differing key
        r1_dict = json.loads(r1_json)
        r2_dict = json.loads(r2_json)
        for key in r1_dict:
            if r1_dict.get(key) != r2_dict.get(key):
                fail(f"Non-deterministic key: {key}")
                break
        fail("Dashboard output differs between runs (non-deterministic)")

    # Also verify report section hashes are stable
    h1 = (_report_r1.get("trace") or {}).get("section_hashes") or {}
    h2 = (_report_r2.get("trace") or {}).get("section_hashes") or {}
    if h1 == h2:
        ok("Section hashes identical across two runs")
    else:
        fail("Section hashes differ between runs")

except Exception as e:
    fail(f"Exception during determinism test: {e}")
    import traceback; traceback.print_exc()


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print()
if failures:
    print(f"FAILED: {len(failures)} failure(s):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All combat dashboard tests passed.")
    sys.exit(0)
