"""
Button 2 betting-market analytical adapter.

Design constraints:
- Analytical-only output.
- No live odds fetching.
- No betting automation or execution.
- Additive fields only.
- Missing data degrades betting_market_status, never blocks core report generation.
"""

from __future__ import annotations

import re


BETTING_RISK_DISCLAIMER_TEXT = (
    "Analytical content only. No wagering advice, no guaranteed outcomes, and no "
    "automated betting execution."
)


def _to_float(value) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _extract_moneyline(record: dict, side: str) -> float | None:
    snapshot = record.get("odds_snapshot")
    if not isinstance(snapshot, dict):
        return None

    candidates = [
        f"{side}_moneyline",
        f"{side}_ml",
        side,
    ]
    for key in candidates:
        if key in snapshot:
            return _to_float(snapshot.get(key))
    return None


def _american_to_implied_prob(moneyline: float | None) -> float | None:
    if moneyline is None:
        return None
    if moneyline == 0:
        return None
    if moneyline > 0:
        return round(100.0 / (moneyline + 100.0), 4)
    # negative line
    return round(abs(moneyline) / (abs(moneyline) + 100.0), 4)


def _extract_confidence(record: dict, report_obj: dict) -> float | None:
    direct = _to_float(record.get("confidence"))
    if direct is not None:
        if direct > 1.0:
            direct = direct / 100.0
        return max(0.0, min(1.0, direct))

    preview = str((report_obj.get("content_preview") or {}).get("headline_prediction_preview") or "")
    m = re.search(r"(\d{1,2}(?:\.\d+)?)%", preview)
    if not m:
        return None

    pct = _to_float(m.group(1))
    if pct is None:
        return None
    return max(0.0, min(1.0, pct / 100.0))


def _compute_volatility_grade(max_edge: float | None, betting_missing_inputs: list[str]) -> str | None:
    if max_edge is None:
        return "unstable" if betting_missing_inputs else None
    if max_edge >= 0.10:
        return "high"
    if max_edge >= 0.05:
        return "medium"
    return "low"


def build_betting_market_enrichment(
    queue_record: dict,
    report_obj: dict,
    sections: dict,
) -> dict:
    """Return additive betting-market fields for Button 2 analyst mode."""
    queue_record = queue_record if isinstance(queue_record, dict) else {}
    report_obj = report_obj if isinstance(report_obj, dict) else {}
    sections = sections if isinstance(sections, dict) else {}

    missing_inputs: list[str] = []
    contributions: list[dict] = []

    odds_snapshot = queue_record.get("odds_snapshot")
    if not isinstance(odds_snapshot, dict):
        missing_inputs.append("odds_snapshot")

    a_line = _extract_moneyline(queue_record, "fighter_a")
    b_line = _extract_moneyline(queue_record, "fighter_b")
    if a_line is None or b_line is None:
        missing_inputs.append("moneyline_pair")

    implied_a = _american_to_implied_prob(a_line)
    implied_b = _american_to_implied_prob(b_line)

    model_conf = _extract_confidence(queue_record, report_obj)
    if model_conf is None:
        missing_inputs.append("model_confidence")

    fair_price_estimate = None
    if model_conf is not None:
        fair_price_estimate = {
            "fighter_a_fair_probability": round(model_conf, 4),
            "fighter_b_fair_probability": round(1.0 - model_conf, 4),
        }

    max_edge = None
    market_edge_summary = None
    if implied_a is not None and implied_b is not None and fair_price_estimate is not None:
        edge_a = round(fair_price_estimate["fighter_a_fair_probability"] - implied_a, 4)
        edge_b = round(fair_price_estimate["fighter_b_fair_probability"] - implied_b, 4)
        max_edge = max(abs(edge_a), abs(edge_b))
        market_edge_summary = {
            "fighter_a_edge": edge_a,
            "fighter_b_edge": edge_b,
            "note": "Analytical edge signal only; not a wagering instruction.",
        }

    round_path = str(sections.get("round_by_round_control_shifts") or "").strip()
    round_band_betting_path = round_path[:240] if round_path else None

    prop_market_notes = []
    if round_band_betting_path:
        prop_market_notes.append("Round-band path available for analyst review.")
    else:
        prop_market_notes.append("Insufficient round-band detail for prop pathway confidence.")

    odds_source_status = "absent"
    if isinstance(odds_snapshot, dict):
        odds_source_status = "verified_snapshot" if queue_record.get("odds_snapshot_verified") else "snapshot_attached"

    if "odds_snapshot" in missing_inputs:
        betting_market_status = "unavailable"
    elif missing_inputs:
        betting_market_status = "partial"
    else:
        betting_market_status = "ready"

    pass_no_bet_conditions = []
    if betting_market_status != "ready":
        pass_no_bet_conditions.append("Pass when verified market snapshot is unavailable or incomplete.")
    if model_conf is None:
        pass_no_bet_conditions.append("Pass when model confidence cannot be derived from approved analysis.")
    if market_edge_summary is not None and max_edge is not None and max_edge < 0.02:
        pass_no_bet_conditions.append("No-bet when estimated edge is below minimum analyst threshold.")
    if not pass_no_bet_conditions:
        pass_no_bet_conditions.append("No-bet unless operator confirms risk tolerance and market integrity.")

    volatility_grade = _compute_volatility_grade(max_edge, missing_inputs)

    engine_status = {
        "betting.odds_ingestion": odds_source_status != "absent",
        "betting.implied_probability": implied_a is not None and implied_b is not None,
        "betting.fair_price": fair_price_estimate is not None,
        "betting.market_edge": market_edge_summary is not None,
        "betting.prop_market": bool(prop_market_notes),
        "betting.volatility_grade": volatility_grade is not None,
        "betting.round_band_betting_path": round_band_betting_path is not None,
        "betting.pass_no_bet": bool(pass_no_bet_conditions),
        "betting.market_movement_watch": False,
        "betting.risk_disclaimer": True,
    }

    for engine_id, active in engine_status.items():
        contributions.append(
            {
                "engine_id": engine_id,
                "status": "contributed" if active else "insufficient_input",
            }
        )

    implied_probability = None
    if implied_a is not None and implied_b is not None:
        implied_probability = {
            "fighter_a": implied_a,
            "fighter_b": implied_b,
        }

    return {
        "betting_market_status": betting_market_status,
        "odds_source_status": odds_source_status,
        "implied_probability": implied_probability,
        "fair_price_estimate": fair_price_estimate,
        "market_edge_summary": market_edge_summary,
        "prop_market_notes": prop_market_notes,
        "volatility_grade": volatility_grade,
        "round_band_betting_path": round_band_betting_path,
        "pass_no_bet_conditions": pass_no_bet_conditions,
        "betting_risk_disclaimer": BETTING_RISK_DISCLAIMER_TEXT,
        "betting_engine_contributions": contributions,
        "betting_missing_inputs": sorted(set(missing_inputs)),
    }
