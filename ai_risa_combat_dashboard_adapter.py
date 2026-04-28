# ai_risa_combat_dashboard_adapter.py
"""
AI-RISA Combat Intelligence Dashboard Adapter.

Converts an existing report payload (as produced by map_engine_output_to_report)
into a structured dashboard view model for the Page 2-style Combat Intelligence
Dashboard page inserted into premium PDF reports.

Design contract:
- All values are sourced from existing report/prediction fields.
- Missing optional metrics are marked as the string "Not available" — never invented.
- Deterministic: same input produces same output.
- Does not mutate the incoming payload.
- Protected sections (deception_unpredictability) are read-only here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_UNAVAILABLE = "Not available"


def _safe_str(value: Any, fallback: str = _UNAVAILABLE) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _safe_float(value: Any, fallback: float = 0.0) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _pct(value: Any, fallback: str = _UNAVAILABLE) -> str:
    """Format a 0–1 float as a percentage string."""
    try:
        f = float(value)
        return f"{f * 100:.0f}%"
    except (TypeError, ValueError):
        return fallback


def _section_content(report_payload: dict, section_id: str) -> str:
    """Extract text content from a named section in the report payload."""
    for section in report_payload.get("sections", []):
        if section.get("id") == section_id:
            content = section.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
            if isinstance(content, dict):
                return " | ".join(
                    f"{k.replace('_', ' ').title()}: {v}"
                    for k, v in content.items()
                )
            return _UNAVAILABLE
    return _UNAVAILABLE


def _extract_bullets(text: str, max_items: int = 5) -> List[str]:
    """
    Attempt to extract bullet-like lines from a text block.
    Falls back to returning the first paragraph sentence if no bullets found.
    """
    if not text or text == _UNAVAILABLE:
        return []
    lines = [ln.strip().lstrip("•-*").strip() for ln in text.splitlines()]
    bullets = [ln for ln in lines if ln and len(ln) > 4][:max_items]
    if not bullets and text.strip():
        # Take first sentence as a single bullet
        first = text.strip().split(".")[0].strip()
        if first:
            bullets = [first + "."]
    return bullets


def _round_control_from_visual_data(visual_data: dict, fighter_a_name: str, fighter_b_name: str) -> dict:
    """
    Pull round-by-round control shifts from existing visual_data (control_shift_data).
    Returns structured dict for dashboard panel.
    """
    control_shift = visual_data.get("control_shift_data") or {}
    rounds = control_shift.get("rounds") or []
    series = control_shift.get("series") or []

    if not rounds or not series:
        return {
            "available": False,
            "note": _UNAVAILABLE,
        }

    series_a = next((s for s in series if s.get("label") == fighter_a_name), None)
    series_b = next((s for s in series if s.get("label") == fighter_b_name), None)

    def _pct_values(s):
        if not s:
            return []
        return [f"{v * 100:.0f}%" for v in (s.get("values") or [])]

    # Derive early / mid / late labels from round indices
    num_rounds = len(rounds)
    early_idx = 0
    mid_idx = num_rounds // 2
    late_idx = max(0, num_rounds - 1)

    def _phase_label(series_obj, idx):
        if not series_obj:
            return _UNAVAILABLE
        values = series_obj.get("values") or []
        if idx >= len(values):
            return _UNAVAILABLE
        return f"{values[idx] * 100:.0f}%"

    return {
        "available": True,
        "rounds": rounds,
        "fighter_a": {
            "name": fighter_a_name,
            "values": _pct_values(series_a),
            "early_control": _phase_label(series_a, early_idx),
            "mid_control": _phase_label(series_a, mid_idx),
            "late_control": _phase_label(series_a, late_idx),
        },
        "fighter_b": {
            "name": fighter_b_name,
            "values": _pct_values(series_b),
            "early_control": _phase_label(series_b, early_idx),
            "mid_control": _phase_label(series_b, mid_idx),
            "late_control": _phase_label(series_b, late_idx),
        },
    }


def _build_radar_metrics(report_payload: dict, fighter_a_name: str, fighter_b_name: str) -> dict:
    """
    Build fighter architecture / radar metrics from existing radar_metrics in payload.
    Adds dashboard-specific labels: decision structure, energy use, fatigue resistance,
    mental condition, collapse risk, deception and unpredictability.
    All sourced from existing fields — missing values marked unavailable.
    """
    radar = report_payload.get("radar_metrics") or {}
    labels = radar.get("labels") or []
    series = radar.get("series") or []

    series_a = next((s for s in series if s.get("label") == fighter_a_name), None)
    series_b = next((s for s in series if s.get("label") == fighter_b_name), None)

    def _get(series_obj, label):
        if not series_obj or not labels:
            return _UNAVAILABLE
        try:
            idx = labels.index(label)
            val = (series_obj.get("values") or [])[idx]
            return f"{float(val) * 100:.0f}%"
        except (ValueError, IndexError, TypeError):
            return _UNAVAILABLE

    # Map existing radar labels to dashboard labels
    # Cardio → Energy Use proxy / Fatigue Resistance
    # Durability → Collapse Risk (inverted: low durability = higher risk)
    # Recovery → Mental Condition proxy
    # Control → Decision Structure proxy
    # KD Resistance → kept as-is
    # Pace Retention → Deception proxy (not ideal — mark unavailable if missing)

    def _invert_pct(series_obj, label):
        """Invert a 0-1 metric for risk display (high val = low risk)."""
        if not series_obj or not labels:
            return _UNAVAILABLE
        try:
            idx = labels.index(label)
            val = (series_obj.get("values") or [])[idx]
            risk = max(0.0, min(1.0, 1.0 - float(val)))
            return f"{risk * 100:.0f}%"
        except (ValueError, IndexError, TypeError):
            return _UNAVAILABLE

    return {
        "available": bool(series_a or series_b),
        "fighter_a": {
            "name": fighter_a_name,
            "decision_structure": _get(series_a, "Control"),
            "energy_use": _get(series_a, "Cardio"),
            "fatigue_resistance": _get(series_a, "Cardio"),  # Best available proxy
            "mental_condition": _get(series_a, "Recovery"),
            "collapse_risk": _invert_pct(series_a, "Durability"),
            "deception_unpredictability": _get(series_a, "Pace Retention"),
        },
        "fighter_b": {
            "name": fighter_b_name,
            "decision_structure": _get(series_b, "Control"),
            "energy_use": _get(series_b, "Cardio"),
            "fatigue_resistance": _get(series_b, "Cardio"),
            "mental_condition": _get(series_b, "Recovery"),
            "collapse_risk": _invert_pct(series_b, "Durability"),
            "deception_unpredictability": _get(series_b, "Pace Retention"),
        },
    }


def _build_energy_fatigue_panel(report_payload: dict, fighter_a_name: str, fighter_b_name: str) -> dict:
    """
    Energy Use + Fatigue Failure Window panel.
    Sourced from energy_use and fatigue_failure_points sections and heat_map_data.
    """
    energy_text = _section_content(report_payload, "energy_use")
    fatigue_text = _section_content(report_payload, "fatigue_failure_points")

    # Derive danger window from heat_map_data (lowest combined control = highest fatigue risk)
    heat_map = report_payload.get("heat_map_data") or {}
    hm_values = heat_map.get("values") or []
    hm_ylabels = heat_map.get("y_labels") or []

    danger_window = _UNAVAILABLE
    if hm_values and hm_ylabels:
        try:
            # Find round with lowest average control (highest exhaustion pressure)
            round_averages = [
                (label, sum(row) / len(row) if row else 0)
                for label, row in zip(hm_ylabels, hm_values)
            ]
            min_round = min(round_averages, key=lambda x: x[1])
            danger_window = f"{min_round[0]} (lowest combined control)"
        except Exception:
            danger_window = _UNAVAILABLE

    return {
        "energy_use_summary": energy_text if energy_text != _UNAVAILABLE else _UNAVAILABLE,
        "fatigue_failure_summary": fatigue_text if fatigue_text != _UNAVAILABLE else _UNAVAILABLE,
        "danger_window": danger_window,
    }


def _build_collapse_triggers(report_payload: dict) -> List[str]:
    """
    Extract 3–5 collapse triggers from existing collapse_triggers section.
    """
    text = _section_content(report_payload, "collapse_triggers")
    if text == _UNAVAILABLE:
        return []
    bullets = _extract_bullets(text, max_items=5)
    # Minimum 3 from section; if text present but bullets too sparse, use full text as one item
    if not bullets and text and text != _UNAVAILABLE:
        bullets = [text[:180].strip()]
    return bullets[:5]


def _build_scenario_tree(report_payload: dict, fighter_a_name: str, fighter_b_name: str, headline: dict) -> dict:
    """
    Scenario Tree panel: Path A / B / C.
    Sourced from scenario_tree section content.
    """
    text = _section_content(report_payload, "scenario_tree")

    # Try to parse scenario A/B/C from existing generated text
    path_a = _UNAVAILABLE
    path_b = _UNAVAILABLE
    path_c = _UNAVAILABLE

    if text and text != _UNAVAILABLE:
        for line in text.splitlines():
            stripped = line.strip()
            sl = stripped.lower()
            if sl.startswith("scenario a:") or sl.startswith("path a:"):
                path_a = stripped.split(":", 1)[-1].strip()
            elif sl.startswith("scenario b:") or sl.startswith("path b:"):
                path_b = stripped.split(":", 1)[-1].strip()
            elif sl.startswith("scenario c:") or sl.startswith("path c:"):
                path_c = stripped.split(":", 1)[-1].strip()

    # Fallback: construct from headline data
    winner = headline.get("winner") or fighter_a_name
    method = headline.get("method") or _UNAVAILABLE
    loser = fighter_b_name if winner == fighter_a_name else fighter_a_name

    if path_a == _UNAVAILABLE:
        path_a = f"{winner} controls pace and wins by {method}" if method != _UNAVAILABLE else _UNAVAILABLE
    if path_b == _UNAVAILABLE:
        path_b = f"Competitive exchanges — split control, judge-dependent result"
    if path_c == _UNAVAILABLE:
        path_c = f"{loser} disrupts sequencing and wins via alternate method"

    return {
        "path_a": {"label": "Path A — Favored Control", "description": path_a},
        "path_b": {"label": "Path B — Competitive / Neutral", "description": path_b},
        "path_c": {"label": "Path C — Opponent Upset / Alternate", "description": path_c},
    }


def _build_method_pathways(report_payload: dict, headline: dict) -> dict:
    """
    Method Pathways panel.
    Sourced from method_distribution in report_payload.
    """
    method_dist = report_payload.get("method_distribution") or {}
    sport = _safe_str(
        next(
            (s.get("content", {}).get("sport") for s in report_payload.get("sections", []) if s.get("id") == "front_cover" and isinstance(s.get("content"), dict)),
            None,
        ),
        fallback="mma",
    ).lower()

    decision_prob = method_dist.get("Decision")
    ko_prob = method_dist.get("KO/TKO")
    sub_prob = method_dist.get("Submission")
    attrition_prob = method_dist.get("Accumulation/Corner")

    pathways = []
    if decision_prob is not None:
        pathways.append({"method": "Decision", "probability": _pct(decision_prob)})
    if ko_prob is not None:
        pathways.append({"method": "KO / TKO", "probability": _pct(ko_prob)})
    if "mma" in sport and sub_prob is not None:
        pathways.append({"method": "Submission", "probability": _pct(sub_prob)})
    if attrition_prob is not None:
        pathways.append({"method": "Late-Round Attrition / Upset", "probability": _pct(attrition_prob)})

    if not pathways:
        # Fall back to marking all as unavailable
        pathways = [
            {"method": "Decision", "probability": _UNAVAILABLE},
            {"method": "KO / TKO", "probability": _UNAVAILABLE},
        ]
        if "mma" in sport:
            pathways.append({"method": "Submission", "probability": _UNAVAILABLE})

    return {
        "available": bool(method_dist),
        "pathways": pathways,
        "predicted_method": _safe_str(headline.get("method")),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_combat_dashboard_view_model(report_payload: dict) -> dict:
    """
    Convert a report payload into a Combat Intelligence Dashboard view model.

    Args:
        report_payload: dict produced by map_engine_output_to_report()

    Returns:
        dashboard_view: dict with all 7 dashboard panels + metadata.
        All missing optional metrics are marked _UNAVAILABLE ("Not available").
        Never raises on missing data — always returns a populated (possibly
        partially-unavailable) view model.
    """
    # --- Core identity ---
    headline = report_payload.get("headline") or {}
    fight_id = _safe_str(report_payload.get("fight_id"))

    front_cover_content = next(
        (s.get("content") for s in report_payload.get("sections", [])
         if s.get("id") == "front_cover" and isinstance(s.get("content"), dict)),
        {},
    )
    fighter_a_name = _safe_str(
        front_cover_content.get("fighters", "").split(" vs ")[0].strip()
        if " vs " in (front_cover_content.get("fighters") or "")
        else front_cover_content.get("fighters"),
        fallback="Fighter A",
    )
    fighter_b_name = _safe_str(
        front_cover_content.get("fighters", "").split(" vs ")[-1].strip()
        if " vs " in (front_cover_content.get("fighters") or "")
        else "Fighter B",
        fallback="Fighter B",
    )

    # 1. Headline Prediction
    signal_gap_raw = report_payload.get("trace", {})
    # Try to get signal_gap from debug_metrics if present
    debug_metrics = report_payload.get("debug_metrics") or {}
    signal_gap_val = debug_metrics.get("signal_gap")
    headline_panel = {
        "predicted_winner": _safe_str(headline.get("winner")),
        "confidence": _safe_str(headline.get("confidence_label")),
        "method": _safe_str(headline.get("method")),
        "round": _safe_str(headline.get("round")),
        "signal_gap": _pct(signal_gap_val) if signal_gap_val is not None else _UNAVAILABLE,
    }

    # 2. Fighter Architecture / Radar Metrics
    radar_panel = _build_radar_metrics(report_payload, fighter_a_name, fighter_b_name)

    # 3. Round-by-Round Control Shifts
    round_control_panel = _round_control_from_visual_data(report_payload, fighter_a_name, fighter_b_name)

    # 4. Energy Use + Fatigue Failure Window
    energy_panel = _build_energy_fatigue_panel(report_payload, fighter_a_name, fighter_b_name)

    # 5. Collapse Triggers
    collapse_triggers = _build_collapse_triggers(report_payload)

    # 6. Scenario Tree
    scenario_tree_panel = _build_scenario_tree(report_payload, fighter_a_name, fighter_b_name, headline)

    # 7. Method Pathways
    method_pathways_panel = _build_method_pathways(report_payload, headline)

    return {
        "dashboard_type": "combat_intelligence",
        "dashboard_title": "AI-RISA Combat Intelligence Dashboard",
        "dashboard_subtitle": "Advanced Intelligence — Ring Intelligence Systems Architecture",
        "fight_id": fight_id,
        "fighter_a_name": fighter_a_name,
        "fighter_b_name": fighter_b_name,
        "panels": {
            "headline_prediction": headline_panel,
            "fighter_architecture": radar_panel,
            "round_control_shifts": round_control_panel,
            "energy_fatigue": energy_panel,
            "collapse_triggers": collapse_triggers,
            "scenario_tree": scenario_tree_panel,
            "method_pathways": method_pathways_panel,
        },
    }
