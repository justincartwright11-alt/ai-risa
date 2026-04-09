
# ai_risa_report_output_adapter.py
"""
Adapter to map engine output (result_dict) to the master report template structure.
This module does not alter engine logic or scoring.
"""

from report_template_config import REPORT_SECTIONS, VISUAL_SLOTS

def _normalize_method(method):
    if not method:
        return "Unknown"
    return str(method).title()

def _normalize_round(round_val):
    if not round_val:
        return "Unknown"
    if str(round_val).lower() == "full":
        return "Full Distance"
    return str(round_val)

def _confidence_label(conf):
    try:
        return f"{float(conf)*100:.1f}%"
    except Exception:
        return "N/A"

def map_engine_output_to_report(engine_output):
    # Headline block
    winner = engine_output.get("predicted_winner_id")
    confidence = engine_output.get("confidence")
    method = engine_output.get("method")
    round_val = engine_output.get("round")
    debug_metrics = engine_output.get("debug_metrics")

    headline = {
        "winner": winner,
        "confidence": confidence,
        "confidence_label": _confidence_label(confidence),
        "method": _normalize_method(method),
        "round": _normalize_round(round_val),
    }

    # Section mapping (stubbed for now, can be expanded)
    sections = []
    for section in REPORT_SECTIONS:
        sid = section["id"]
        if sid == "executive_summary":
            summary = f"Prediction: {headline['winner']} by {headline['method']} ({headline['confidence_label']})"
            sections.append({"id": sid, "title": section["title"], "content": summary})
        elif sid == "prediction_core":
            core = {k: headline[k] for k in ["winner", "confidence", "confidence_label", "method", "round"]}
            sections.append({"id": sid, "title": section["title"], "content": core})
        elif sid == "tactical_overview":
            sections.append({"id": sid, "title": section["title"], "content": "Tactical overview not yet implemented."})
        elif sid == "risk_and_fallbacks":
            fallback = debug_metrics.get("fallback_reason") if debug_metrics else None
            content = f"Fallback reason: {fallback}" if fallback else "No fallback triggered."
            sections.append({"id": sid, "title": section["title"], "content": content})
        elif sid == "visual_dashboard":
            # Just list available slots for now
            slots = {k: VISUAL_SLOTS[k]["title"] for k in VISUAL_SLOTS}
            sections.append({"id": sid, "title": section["title"], "content": slots})
        elif sid == "debug_appendix":
            sections.append({"id": sid, "title": section["title"], "content": debug_metrics})
        else:
            sections.append({"id": sid, "title": section["title"], "content": None})

    # Visual slots (populate with None or fallback for now)
    visual_slots = {}
    for k, v in VISUAL_SLOTS.items():
        visual_slots[k] = {
            "title": v["title"],
            "data": None,
            "fallback": v["fallback"]
        }

    # Packaging block
    packaging = {
        "theme": "black_gold_analyst",
        "brand_name": "AI-RISA Combat Intelligence",
        "report_type": "Premium Fight Intelligence Brief",
        "version": "v100-template-standardized",
    }

    # Metadata (stub)
    metadata = {
        "source": "ai_risa_engine",
        "generated_utc": None,
    }

    # Add method_distribution to the top-level payload if present and valid
    report = {
        "metadata": metadata,
        "headline": headline,
        "sections": sections,
        "visual_slots": visual_slots,
        "packaging": packaging,
    }
    # Only promote method_distribution if it exists and is a dict
    method_dist = engine_output.get("method_distribution")
    if isinstance(method_dist, dict) and method_dist:
        report["method_distribution"] = method_dist

    # Radar metrics: fixed schema, only if all present and normalized
    radar_metric_keys = [
        ("control", "Control"),
        ("aggression", "Aggression"),
        ("defense", "Defense"),
        ("cardio", "Cardio"),
        ("durability", "Durability"),
        ("adaptability", "Adaptability"),
    ]
    # Try to get from engine_output (presentation-safe fields only)
    radar_values = []
    all_present = True
    for key, _ in radar_metric_keys:
        val = engine_output.get(key)
        if val is None or not isinstance(val, (int, float)):
            all_present = False
            break
        radar_values.append(float(val))
    if all_present and len(radar_values) == 6:
        report["radar_metrics"] = {
            "labels": [label for _, label in radar_metric_keys],
            "values": radar_values,
            "scale_min": 0.0,
            "scale_max": 1.0,
        }
    return report
