from __future__ import annotations
def _normalize_confidence(value):
    if value is None:
        return 0.5
    value = float(value)
    if value > 1.0:
        value = value / 100.0
    return max(0.0, min(1.0, value))

def engine_adapter(fight, requested_total_sims=1, confidence_scale=1.0):
    # --- Fatigue/Catastrophic Failure Tracing ---
    trace_fatigue_raw_fields = {}
    trace_fatigue_inverted_fields = {}
    trace_fatigue_weighted_components = {}
    trace_fatigue_pre_clamp = 0.0
    trace_fatigue_final = 0.0
    trace_collapse_raw_fields = {}
    trace_collapse_inverted_fields = {}
    trace_collapse_weighted_components = {}
    trace_collapse_pre_clamp = 0.0
    trace_collapse_final = 0.0

    matchup_id = fight.get("matchup_id", "fighter_israel_adesanya_vs_fighter_joe_pyfer")
    fighter_a_id = fight.get("fighter_a_id", "fighter_israel_adesanya")
    fighter_b_id = fight.get("fighter_b_id", "fighter_joe_pyfer")
    predicted_winner_id = fighter_a_id  # stub: always A for validation
    method = fight.get("method", "Decision")
    round_val = fight.get("round", "full")
    # --- Winner confidence: separate from method/finish noise ---
    # Use only winner-separation evidence (not method/finish signals)
    # For this stub, treat as a function of a clean signal_gap, not method
    base_confidence = float(fight.get("confidence", 0.6))
    # If method/finish evidence is weak, do not inflate winner confidence
    method_lower = str(method).lower()
    method_noise = 0.0
    if any(x in method_lower for x in ["ko", "tko", "stoppage", "finish"]):
        method_noise = 0.05
    elif "submission" in method_lower:
        method_noise = 0.03
    # Winner confidence is base minus any method/finish noise
    raw_confidence = base_confidence - method_noise
    winner_confidence = raw_confidence  # Do not clamp/normalize here
    # --- Stoppage evidence: require damage/collapse/fatigue/pace convergence ---
    # Simulate upstream signals (replace with real ones in production)
    # --- Conservative evidence derivation ---
    fighter_a_profile = fight.get("fighter_a_profile", {})
    fighter_b_profile = fight.get("fighter_b_profile", {})
    # Use only style and stance for proxies
    style = None
    stance = None
    if isinstance(fighter_a_profile, dict):
        style = fighter_a_profile.get("style", "")
        stance = fighter_a_profile.get("stance", "")
    # Damage: modest nonzero for striker/pressure, lower for boxer/control, stance minor mod
    style_lower = (style or "").lower()
    if "striker" in style_lower or "pressure" in style_lower:
        damage = 0.4
    elif "boxer" in style_lower or "control" in style_lower:
        damage = 0.2
    elif style_lower:
        damage = 0.1
    else:
        damage = 0.0
    # Stance: minor adjustment
    if stance and "southpaw" in stance.lower():
        damage += 0.05
    damage = min(max(damage, 0.0), 1.0)
    # Pace: similar mapping
    if "pressure" in style_lower or "volume" in style_lower:
        pace_degradation = 0.4
    elif "striker" in style_lower:
        pace_degradation = 0.3
    elif "boxer" in style_lower or "control" in style_lower:
        pace_degradation = 0.15
    elif style_lower:
        pace_degradation = 0.1
    else:
        pace_degradation = 0.0
    pace_degradation = min(max(pace_degradation, 0.0), 1.0)
    # --- Fatigue Failure Evidence (new schema) ---
    fatigue = 0.0
    fatigue_inputs = {}
    fatigue_provenance = {}
    # Cardio endurance (invert: higher = better)
    ce = fighter_a_profile.get("cardio_endurance")
    ce_val = None
    ce_inv = None
    if ce is not None:
        try:
            ce_val = float(ce)
            ce_inv = 1.0 - ce_val
            fatigue_inputs["cardio_endurance"] = ce_val
            fatigue_provenance["cardio_endurance"] = fighter_a_profile.get("trace_field_origins", {}).get("cardio_endurance", "unknown")
            trace_fatigue_raw_fields["cardio_endurance"] = ce_val
            trace_fatigue_inverted_fields["cardio_endurance"] = ce_inv
            trace_fatigue_weighted_components["cardio_endurance"] = ce_inv
            fatigue = max(fatigue, min(1.0, ce_inv))
        except Exception:
            fatigue_inputs["cardio_endurance"] = "invalid"
    # Recovery quality (invert: higher = better)
    rq = fighter_a_profile.get("recovery_quality")
    rq_val = None
    rq_inv = None
    if rq is not None:
        try:
            rq_val = float(rq)
            rq_inv = 1.0 - rq_val
            fatigue_inputs["recovery_quality"] = rq_val
            fatigue_provenance["recovery_quality"] = fighter_a_profile.get("trace_field_origins", {}).get("recovery_quality", "unknown")
            trace_fatigue_raw_fields["recovery_quality"] = rq_val
            trace_fatigue_inverted_fields["recovery_quality"] = rq_inv
            trace_fatigue_weighted_components["recovery_quality"] = rq_inv
            fatigue = max(fatigue, min(1.0, rq_inv))
        except Exception:
            fatigue_inputs["recovery_quality"] = "invalid"
    # Output decay (risk-positive)
    od = fighter_a_profile.get("output_decay")
    od_val = None
    if od is not None:
        try:
            od_val = float(od)
            fatigue_inputs["output_decay"] = od_val
            fatigue_provenance["output_decay"] = fighter_a_profile.get("trace_field_origins", {}).get("output_decay", "unknown")
            trace_fatigue_raw_fields["output_decay"] = od_val
            trace_fatigue_weighted_components["output_decay"] = od_val
            fatigue = max(fatigue, min(1.0, od_val))
        except Exception:
            fatigue_inputs["output_decay"] = "invalid"
    # Late-fight fade (risk-positive)
    lff = fighter_a_profile.get("late_fight_fade")
    lff_val = None
    if lff is not None:
        try:
            lff_val = float(lff)
            fatigue_inputs["late_fight_fade"] = lff_val
            fatigue_provenance["late_fight_fade"] = fighter_a_profile.get("trace_field_origins", {}).get("late_fight_fade", "unknown")
            trace_fatigue_raw_fields["late_fight_fade"] = lff_val
            trace_fatigue_weighted_components["late_fight_fade"] = lff_val
            fatigue = max(fatigue, min(1.0, lff_val))
        except Exception:
            fatigue_inputs["late_fight_fade"] = "invalid"
    # Attrition sensitivity (risk-positive)
    ats = fighter_a_profile.get("attrition_sensitivity")
    ats_val = None
    if ats is not None:
        try:
            ats_val = float(ats)
            fatigue_inputs["attrition_sensitivity"] = ats_val
            fatigue_provenance["attrition_sensitivity"] = fighter_a_profile.get("trace_field_origins", {}).get("attrition_sensitivity", "unknown")
            trace_fatigue_raw_fields["attrition_sensitivity"] = ats_val
            trace_fatigue_weighted_components["attrition_sensitivity"] = ats_val
            fatigue = max(fatigue, min(1.0, ats_val))
        except Exception:
            fatigue_inputs["attrition_sensitivity"] = "invalid"
        # Pre-clamp and final for fatigue
        trace_fatigue_pre_clamp = fatigue
        trace_fatigue_final = min(max(fatigue, 0.0), 1.0)
        fatigue = trace_fatigue_final
    # Style fallback (unchanged)
    if fatigue == 0.0 and style_lower:
        if any(x in style_lower for x in ["volume", "pressure", "attrition"]):
            fatigue = 0.15
            fatigue_inputs["style_fallback"] = style_lower
    # --- Collapse Trigger Evidence (new schema) ---
    collapse = 0.0
    collapse_inputs = {}
    collapse_provenance = {}
    # Durability (invert: higher = better)
    dur = fighter_a_profile.get("durability")
    dur_val = None
    dur_inv = None
    if dur is not None:
        try:
            dur_val = float(dur)
            dur_inv = 1.0 - dur_val
            collapse_inputs["durability"] = dur_val
            collapse_provenance["durability"] = fighter_a_profile.get("trace_field_origins", {}).get("durability", "unknown")
            trace_collapse_raw_fields["durability"] = dur_val
            trace_collapse_inverted_fields["durability"] = dur_inv
            trace_collapse_weighted_components["durability"] = dur_inv
            collapse = max(collapse, min(1.0, dur_inv))
        except Exception:
            collapse_inputs["durability"] = "invalid"
    # Knockdown susceptibility (risk-positive)
    kds = fighter_a_profile.get("knockdown_susceptibility")
    kds_val = None
    if kds is not None:
        try:
            kds_val = float(kds)
            collapse_inputs["knockdown_susceptibility"] = kds_val
            collapse_provenance["knockdown_susceptibility"] = fighter_a_profile.get("trace_field_origins", {}).get("knockdown_susceptibility", "unknown")
            trace_collapse_raw_fields["knockdown_susceptibility"] = kds_val
            trace_collapse_weighted_components["knockdown_susceptibility"] = kds_val
            collapse = max(collapse, min(1.0, kds_val))
        except Exception:
            collapse_inputs["knockdown_susceptibility"] = "invalid"
    # Defensive breakdown tendency (risk-positive)
    dbt = fighter_a_profile.get("defensive_breakdown_tendency")
    dbt_val = None
    if dbt is not None:
        try:
            dbt_val = float(dbt)
            collapse_inputs["defensive_breakdown_tendency"] = dbt_val
            collapse_provenance["defensive_breakdown_tendency"] = fighter_a_profile.get("trace_field_origins", {}).get("defensive_breakdown_tendency", "unknown")
            trace_collapse_raw_fields["defensive_breakdown_tendency"] = dbt_val
            trace_collapse_weighted_components["defensive_breakdown_tendency"] = dbt_val
            collapse = max(collapse, min(1.0, dbt_val))
        except Exception:
            collapse_inputs["defensive_breakdown_tendency"] = "invalid"
    # Panic/collapse sensitivity (risk-positive)
    pcs = fighter_a_profile.get("panic_collapse_sensitivity")
    pcs_val = None
    if pcs is not None:
        try:
            pcs_val = float(pcs)
            collapse_inputs["panic_collapse_sensitivity"] = pcs_val
            collapse_provenance["panic_collapse_sensitivity"] = fighter_a_profile.get("trace_field_origins", {}).get("panic_collapse_sensitivity", "unknown")
            trace_collapse_raw_fields["panic_collapse_sensitivity"] = pcs_val
            trace_collapse_weighted_components["panic_collapse_sensitivity"] = pcs_val
            collapse = max(collapse, min(1.0, pcs_val))
        except Exception:
            collapse_inputs["panic_collapse_sensitivity"] = "invalid"
    # Attrition sensitivity (risk-positive, also used in fatigue)
    if ats is not None:
        try:
            ats_val = float(ats)
            collapse_inputs["attrition_sensitivity"] = ats_val
            collapse_provenance["attrition_sensitivity"] = fighter_a_profile.get("trace_field_origins", {}).get("attrition_sensitivity", "unknown")
            trace_collapse_raw_fields["attrition_sensitivity"] = ats_val
            trace_collapse_weighted_components["attrition_sensitivity"] = ats_val * 0.5
            collapse = max(collapse, min(1.0, ats_val * 0.5))
        except Exception:
            collapse_inputs["attrition_sensitivity"] = "invalid"
        # Pre-clamp and final for collapse
        trace_collapse_pre_clamp = collapse
        trace_collapse_final = min(max(collapse, 0.0), 1.0)
        collapse = trace_collapse_final
    # Style fallback (unchanged)
    if collapse == 0.0 and style_lower:
        if any(x in style_lower for x in ["fragile", "panic", "attrition"]):
            collapse = 0.15
            collapse_inputs["style_fallback"] = style_lower
    # Bound scores
    fatigue = min(max(fatigue, 0.0), 1.0)
    collapse = min(max(collapse, 0.0), 1.0)
    # Trace fields for new evidence
    trace_fatigue_source_fields = dict(fatigue_inputs)
    for k, v in fatigue_provenance.items():
        trace_fatigue_source_fields[f"{k}_provenance"] = v
    trace_collapse_source_fields = dict(collapse_inputs)
    for k, v in collapse_provenance.items():
        trace_collapse_source_fields[f"{k}_provenance"] = v
    if not fatigue_inputs:
        trace_fatigue_source_fields["missing"] = True
    if not collapse_inputs:
        trace_collapse_source_fields["missing"] = True
    # Dominance: only if style signals control/range/pressure
    if "control" in style_lower or "range" in style_lower or "pressure" in style_lower:
        dominance = 0.3
    else:
        dominance = 0.0
    # Trace fields
    trace_damage_source_fields = {"style": style, "stance": stance}
    trace_pace_source_fields = {"style": style}
    trace_fatigue_source_fields = {}
    trace_collapse_source_fields = {}
    trace_dominance_source_fields = {"style": style}
    trace_missing_source_fields = []
    if not style:
        trace_missing_source_fields.append("style")
    if not stance:
        trace_missing_source_fields.append("stance")
    trace_fatigue_source_fields["missing"] = True
    trace_collapse_source_fields["missing"] = True
    if dominance == 0.0:
        trace_dominance_source_fields["missing"] = True
    # --- New: Fatigue/Collapse/Damage convergence modeling ---
    # At least two of the three must be meaningfully present (>0.5)
    # Strongest boost only if all three are high
    # No global boost, no single-signal flips
    # Trace all components and bonus
    
    # Thresholds
    threshold = 0.5
    high = 0.5
    # Count how many are above threshold
    present = sum([damage > high, fatigue > high, collapse > high])
    # Weighted base: equal weights for now
    base_stoppage = (damage + fatigue + collapse) / 3.0
    convergence_bonus = 0.0
    if present == 3:
        convergence_bonus = 0.15  # All three strong: extra boost
    elif present == 2:
        convergence_bonus = 0.05  # Two strong: small boost
    # Pre-threshold score
    pre_threshold_stoppage = base_stoppage + convergence_bonus
    # Only allow stoppage if at least two are present and pre-threshold > 0.5
    if present >= 2 and pre_threshold_stoppage > threshold:
        stoppage_propensity = min(1.0, pre_threshold_stoppage)
    else:
        stoppage_propensity = max(0.0, 0.1 + 0.2 * winner_confidence)
    # Trace for audit
    trace_damage_inputs = {"raw": style, "final": damage, "weight": 1/3}
    trace_fatigue_inputs = {"raw": None, "final": fatigue, "weight": 1/3}
    trace_collapse_inputs = {"raw": None, "final": collapse, "weight": 1/3}
    trace_pace_inputs = {"raw": style, "final": pace_degradation}
    trace_dominance_inputs = {"raw": style, "final": dominance}
    trace_stoppage_formula_path = "base_stoppage = (damage + fatigue + collapse)/3; bonus if >=2 high; require >=2 high for stoppage; no global boost"
    trace_convergence_bonus = convergence_bonus
    trace_pre_threshold_stoppage = pre_threshold_stoppage
    trace_threshold_crossed = present >= 2 and pre_threshold_stoppage > threshold
    trace_fallback_used = False
    trace_default_zero_reason = None
    if damage == 0.0 and collapse == 0.0 and fatigue == 0.0 and pace_degradation == 0.0 and dominance == 0.0:
        trace_fallback_used = True
        trace_default_zero_reason = "All evidence proxies are zero or missing; fallback/default logic used."

    # --- Early-finish noise: push marginal evidence later ---
    try:
        round_num = int(round_val)
        if stoppage_propensity > 0.7 and winner_confidence > 0.7:
            round_finish_tendency = max(0.0, 1.0 - 0.1 * (round_num - 1))
        elif stoppage_propensity > 0.5:
            round_finish_tendency = 0.5  # generic mid/late finish
        else:
            round_finish_tendency = 0.2  # only strong evidence gets early finish
    except Exception:
        if stoppage_propensity > 0.7 and winner_confidence > 0.7:
            round_finish_tendency = 0.7
        elif stoppage_propensity > 0.5:
            round_finish_tendency = 0.5
        else:
            round_finish_tendency = 0.2
    # --- Decision vs stoppage crossing: cleaner separation ---
    # If stoppage_propensity < 0.5, force method to Decision
    # --- Reporting consistency: predicted method must match threshold_crossed ---
    if trace_threshold_crossed:
        final_method = "Stoppage"
    else:
        final_method = "Decision"
    # --- signal_gap for debug: winner confidence separation ---
    signal_gap = abs(winner_confidence - 0.5) * 2
    # --- Stoppage-evidence diagnostics instrumentation ---
    diag_damage_score = damage
    diag_fatigue_failure_score = fatigue
    diag_collapse_trigger_score = collapse
    diag_pace_degradation_score = pace_degradation
    diag_dominance_control_score = dominance
    diag_stoppage_evidence_composite = base_stoppage
    # Path logic: what evidence is present?
    if base_stoppage > 0.4:
        if dominance > 0.4:
            diag_stoppage_path = "damage+collapse+dominance"
        else:
            diag_stoppage_path = "damage+collapse"
    elif dominance > 0.5 and base_stoppage <= 0.4:
        diag_stoppage_path = "control_only"
    elif pace_degradation > 0.5 and base_stoppage <= 0.4:
        diag_stoppage_path = "pace_only"
    else:
        diag_stoppage_path = "mixed_weak"
    diag_stoppage_decision_margin = abs(stoppage_propensity - (1.0 - stoppage_propensity))
    diag_early_finish_signal = 1.0 if (stoppage_propensity > 0.7 and winner_confidence > 0.7 and round_val in ["1", 1]) else 0.0
    diag_late_finish_signal = 1.0 if (stoppage_propensity > 0.7 and winner_confidence > 0.7 and str(round_val) in ["3", "4", "5"]) else 0.0
    # --- TEMPORARY: Trace enrichment field delivery ---
    profile_keys = sorted(list((fighter_a_profile or {}).keys()))
    fatigue_lookup_keys = [
        "cardio_endurance",
        "recovery_quality",
        "output_decay",
        "late_fight_fade",
        "attrition_sensitivity",
    ]
    collapse_lookup_keys = [
        "durability",
        "knockdown_susceptibility",
        "defensive_breakdown_tendency",
        "panic_collapse_sensitivity",
        "attrition_sensitivity",
    ]
    fatigue_lookup_misses = [k for k in fatigue_lookup_keys if k not in (fighter_a_profile or {})]
    collapse_lookup_misses = [k for k in collapse_lookup_keys if k not in (fighter_a_profile or {})]
    debug_metrics = {
        "signal_gap": signal_gap,
        "winner_confidence": winner_confidence,
        "stoppage_propensity": stoppage_propensity,
        "round_finish_tendency": round_finish_tendency,
        # --- Diagnostics fields ---
        "diag_damage_score": damage,
        "diag_fatigue_failure_score": fatigue,
        "diag_collapse_trigger_score": collapse,
        "diag_pace_degradation_score": pace_degradation,
        "diag_dominance_control_score": dominance,
        "diag_stoppage_evidence_composite": base_stoppage,
        "diag_stoppage_convergence_bonus": convergence_bonus,
        "diag_stoppage_pre_threshold": pre_threshold_stoppage,
        "diag_stoppage_threshold_crossed": trace_threshold_crossed,
        # --- Path logic ---
        "diag_stoppage_path": diag_stoppage_path if 'diag_stoppage_path' in locals() else "n/a",
        "diag_stoppage_decision_margin": diag_stoppage_decision_margin if 'diag_stoppage_decision_margin' in locals() else 0.0,
        "diag_early_finish_signal": diag_early_finish_signal if 'diag_early_finish_signal' in locals() else 0.0,
        "diag_late_finish_signal": diag_late_finish_signal if 'diag_late_finish_signal' in locals() else 0.0,
        # --- Trace fields ---
        "trace_damage_inputs": trace_damage_inputs,
        "trace_fatigue_inputs": trace_fatigue_inputs,
        "trace_collapse_inputs": trace_collapse_inputs,
        "trace_pace_inputs": trace_pace_inputs,
        "trace_dominance_inputs": trace_dominance_inputs,
        "trace_damage_source_fields": trace_damage_source_fields,
        "trace_fatigue_source_fields": trace_fatigue_source_fields,
        "trace_collapse_source_fields": trace_collapse_source_fields,
        "trace_pace_source_fields": trace_pace_source_fields,
        "trace_dominance_source_fields": trace_dominance_source_fields,
        "trace_missing_source_fields": trace_missing_source_fields,
        "trace_stoppage_formula_path": trace_stoppage_formula_path,
        "trace_convergence_bonus": trace_convergence_bonus,
        "trace_pre_threshold_stoppage": trace_pre_threshold_stoppage,
        "trace_threshold_crossed": trace_threshold_crossed,
        "trace_fallback_used": trace_fallback_used,
        "trace_default_zero_reason": trace_default_zero_reason,
        # --- Fatigue/Collapse score tracing ---
        "trace_fatigue_raw_fields": trace_fatigue_raw_fields,
        "trace_fatigue_inverted_fields": trace_fatigue_inverted_fields,
        "trace_fatigue_weighted_components": trace_fatigue_weighted_components,
        "trace_fatigue_pre_clamp": trace_fatigue_pre_clamp,
        "trace_fatigue_final": trace_fatigue_final,
        "trace_collapse_raw_fields": trace_collapse_raw_fields,
        "trace_collapse_inverted_fields": trace_collapse_inverted_fields,
        "trace_collapse_weighted_components": trace_collapse_weighted_components,
        "trace_collapse_pre_clamp": trace_collapse_pre_clamp,
        "trace_collapse_final": trace_collapse_final,
        # --- TEMPORARY: Enrichment field delivery tracing ---
        "trace_profile_keys_available": profile_keys,
        "trace_fatigue_lookup_keys": fatigue_lookup_keys,
        "trace_collapse_lookup_keys": collapse_lookup_keys,
        "trace_fatigue_lookup_misses": fatigue_lookup_misses,
        "trace_collapse_lookup_misses": collapse_lookup_misses,
    }
    predicted_winner = ID_TO_NAME.get(predicted_winner_id, predicted_winner_id)
    return {
        "matchup_id": matchup_id,
        "fighter_a_id": fighter_a_id,
        "fighter_b_id": fighter_b_id,
        "predicted_winner_id": predicted_winner_id,
        "predicted_winner": predicted_winner,
        "confidence": _normalize_confidence(winner_confidence),
        "method": final_method,
        "round": round_val,
        "signal_gap": signal_gap,
        "stoppage_propensity": stoppage_propensity,
        "round_finish_tendency": round_finish_tendency,
        "debug_metrics": debug_metrics,
    }

import json
import os
def resolve_fighter_profile_path(fighter_name: str):
    # Accepts either canonical id or display name, tries slug and prefixed forms
        from pathlib import Path
        slug = str(fighter_name).lower().strip()
        if slug.startswith("fighter_"):
            slug = slug[len("fighter_"):]
        slug = slug.replace("'", "").replace(".", "").replace("-", "_").replace(" ", "_")
        repo_root = Path(__file__).resolve().parent
        candidate_roots = [
            repo_root / "fighters",
            Path(r"C:\ai_risa_data\fighters"),
            Path(r"C:\Users\jusin\ai_risa_data\fighters"),
        ]
        candidates = [
            f"{slug}.json",
            f"fighter_{slug}.json",
            f"fighter_fighter_{slug}.json",
        ]
        for root in candidate_roots:
            for candidate in candidates:
                path = root / candidate
                if path.exists():
                    return path
        raise FileNotFoundError(
            f"Could not resolve fighter profile for {fighter_name!r}. "
            f"Tried: {candidates} in {candidate_roots}"
        )

def load_fighter_profile(fighter_name: str):
    profile_path = resolve_fighter_profile_path(fighter_name)
    with open(profile_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid fighter profile format: {profile_path}")
    data.setdefault("profile_path", str(profile_path))

    # Manual enrichment logic
    enrichment_path = os.path.join(os.path.dirname(profile_path), "manual_profile_enrichment.json")
    # Try repo-root and C:\ai_risa_data\fighters
    if not os.path.exists(enrichment_path):
        enrichment_path = os.path.join(r"C:\ai_risa_data\fighters", "manual_profile_enrichment.json")
    enrichment = {}
    if os.path.exists(enrichment_path):
        try:
            with open(enrichment_path, "r", encoding="utf-8") as enf:
                enrichment = json.load(enf)
        except Exception:
            enrichment = {}
    slug = str(fighter_name).lower().strip()
    if slug.startswith("fighter_"):
        slug = slug[len("fighter_"):]
    slug = slug.replace("'", "").replace(".", "").replace("-", "_").replace(" ", "_")
    manual = enrichment.get(slug) or enrichment.get(f"fighter_{slug}")

    # Trace origins
    style_origin = "source_json"
    stance_origin = "source_json"
    # --- Fatigue/Collapse enrichment fields ---
    enrichment_fields = [
        "cardio_endurance",
        "recovery_quality",
        "output_decay",
        "late_fight_fade",
        "attrition_sensitivity",
        "durability",
        "knockdown_susceptibility",
        "defensive_breakdown_tendency",
        "panic_collapse_sensitivity",
    ]
    trace_field_origins = {}
    if manual:
        if not data.get("style") and manual.get("style"):
            data["style"] = manual["style"]
            style_origin = "manual_enrichment"
        if not data.get("stance") and manual.get("stance"):
            data["stance"] = manual["stance"]
            stance_origin = "manual_enrichment"
        # Merge enrichment fields if missing
        for field in enrichment_fields:
            if field not in data or data[field] is None:
                if field in manual:
                    data[field] = manual[field]
                    trace_field_origins[field] = "manual_enrichment"
            else:
                trace_field_origins[field] = "source_json"
    else:
        for field in enrichment_fields:
            if field in data:
                trace_field_origins[field] = "source_json"
    data["trace_style_origin"] = style_origin
    data["trace_stance_origin"] = stance_origin
    data["trace_field_origins"] = trace_field_origins
    # --- TEMPORARY: Trace enrichment merge and profile keys ---
    data["trace_profile_keys_available"] = list(data.keys())
    data["trace_enrichment_merge_applied"] = {k: data.get(k, None) for k in [
        "cardio_endurance",
        "recovery_quality",
        "output_decay",
        "late_fight_fade",
        "attrition_sensitivity",
        "durability",
        "knockdown_susceptibility",
        "defensive_breakdown_tendency",
        "panic_collapse_sensitivity",
    ]}
    return data

ID_TO_NAME = {
    "fighter_israel_adesanya": "Israel Adesanya",
    "fighter_joe_pyfer": "Joe Pyfer",
}
