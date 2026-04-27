import json
import os
import unicodedata
from report_template_config import REPORT_SECTIONS, VISUAL_SLOTS

def _load_enrichment_store():
    fighters_dir = os.path.join(os.path.dirname(__file__), 'fighters')
    canonical_path = os.path.join(fighters_dir, 'canonical_fighter_enrichment.json')
    legacy_path = os.path.join(fighters_dir, 'manual_profile_enrichment.json')

    canonical = {}
    if os.path.exists(canonical_path):
        try:
            with open(canonical_path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            if isinstance(payload, dict) and isinstance(payload.get('fighters'), dict):
                canonical = payload.get('fighters') or {}
        except Exception:
            canonical = {}

    legacy = {}
    if os.path.exists(legacy_path):
        try:
            with open(legacy_path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            if isinstance(payload, dict):
                legacy = payload
        except Exception:
            legacy = {}

    # Canonical-first, legacy-second fallback.
    merged = dict(legacy)
    merged.update(canonical)
    return merged


MANUAL_ENRICHMENT = _load_enrichment_store()

def _normalize_method(method):
    if not method:
           return "(method missing)"
    return str(method).title()

def _normalize_round(round_val):
    if not round_val:
           return "(round missing)"
    if str(round_val).lower() == "full":
        return "Full Distance"
    return str(round_val)

def _confidence_label(conf):
    try:
        return f"{float(conf)*100:.1f}%"
    except Exception:
            return "(confidence missing)"

def _get_manual_enrichment(fighter_name_or_id):
    if not fighter_name_or_id:
        return {}
    key = unicodedata.normalize('NFKD', str(fighter_name_or_id)).encode('ascii', 'ignore').decode('ascii')
    key = key.lower().replace(' ', '_')
    if key.startswith('fighter_'):
        key = key[8:]
    return MANUAL_ENRICHMENT.get(key, {})

def _get_fighter_profile(engine_output, which):
    profile = engine_output.get(f'{which}_profile')
    if isinstance(profile, dict):
        return profile
    return {}

def _safe_metric(source, key, default=0.0):
    try:
        value = source.get(key, default) if isinstance(source, dict) else default
        return float(value)
    except Exception:
        return float(default)


def _clean_short_scalar(value, fallback="", max_len=32):
    """Allow only short scalar text values for table cells; reject prose/narrative payloads."""
    if value is None:
        return fallback
    if isinstance(value, bool):
        return fallback
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, dict, tuple, set)):
        return fallback

    text = str(value).strip()
    if not text:
        return fallback

    # Block sentence-like or scraped narrative content from scalar cells.
    if "\n" in text or any(mark in text for mark in [".", "!", "?", ":", ";"]):
        return fallback
    if len(text) > max_len:
        return fallback
    if len(text.split()) > 4:
        return fallback
    return text


def _canonical_style(enrich, profile, fallback="Generalist"):
    style = _clean_short_scalar((enrich or {}).get("style"), fallback="", max_len=32)
    if not style:
        style = _clean_short_scalar((profile or {}).get("style"), fallback="", max_len=32)
    if not style:
        return fallback
    return style


def _canonical_stance(enrich, profile, fallback="unlisted stance"):
    allowed = {"orthodox", "southpaw", "switch"}
    raw = _clean_short_scalar((enrich or {}).get("stance"), fallback="", max_len=16).lower()
    if not raw:
        raw = _clean_short_scalar((profile or {}).get("stance"), fallback="", max_len=16).lower()
    if raw in allowed:
        return raw
    return fallback

def _style_profile(style_text):
    style = (style_text or "").lower()
    aggression = 0.50
    technique = 0.50
    if "aggressive" in style or "pressure" in style:
        aggression += 0.22
    if "power" in style:
        aggression += 0.12
    if "technical" in style or "technician" in style:
        technique += 0.22
    if "boxer" in style or "kickboxer" in style:
        technique += 0.10
    if "counter" in style:
        technique += 0.08
    return {
        "aggression": min(0.95, aggression),
        "technique": min(0.95, technique),
    }

def _build_visual_data(engine_output, fighter_a_name, fighter_b_name, enrich_a, enrich_b, headline):
    debug_metrics = engine_output.get("debug_metrics") or {}
    confidence = _safe_metric(engine_output, "confidence", 0.50)
    signal_gap = _safe_metric(engine_output, "signal_gap", debug_metrics.get("signal_gap", 0.10))
    stoppage_propensity = _safe_metric(engine_output, "stoppage_propensity", debug_metrics.get("stoppage_propensity", 0.20))
    round_finish_tendency = _safe_metric(engine_output, "round_finish_tendency", debug_metrics.get("round_finish_tendency", 0.20))

    fighter_a_profile = _get_fighter_profile(engine_output, 'fighter_a')
    fighter_b_profile = _get_fighter_profile(engine_output, 'fighter_b')

    style_a = _canonical_style(enrich_a, fighter_a_profile, fallback="Aggressive Striker")
    style_b = _canonical_style(enrich_b, fighter_b_profile, fallback="Technical Striker")
    stance_a = _canonical_stance(enrich_a, fighter_a_profile, fallback="unlisted stance")
    stance_b = _canonical_stance(enrich_b, fighter_b_profile, fallback="unlisted stance")
    profile_a = _style_profile(style_a)
    profile_b = _style_profile(style_b)

    cardio_a = _safe_metric(enrich_a, "cardio_endurance", 0.70)
    cardio_b = _safe_metric(enrich_b, "cardio_endurance", 0.70)
    durability_a = _safe_metric(enrich_a, "durability", 0.70)
    durability_b = _safe_metric(enrich_b, "durability", 0.70)
    recovery_a = _safe_metric(enrich_a, "recovery_quality", 0.70)
    recovery_b = _safe_metric(enrich_b, "recovery_quality", 0.70)
    output_decay_a = _safe_metric(enrich_a, "output_decay", 0.55)
    output_decay_b = _safe_metric(enrich_b, "output_decay", 0.55)
    knockdown_a = _safe_metric(enrich_a, "knockdown_susceptibility", 0.50)
    knockdown_b = _safe_metric(enrich_b, "knockdown_susceptibility", 0.50)

    pace_retention_a = max(0.0, min(1.0, 1.0 - output_decay_a))
    pace_retention_b = max(0.0, min(1.0, 1.0 - output_decay_b))
    knockdown_resistance_a = max(0.0, min(1.0, 1.0 - knockdown_a))
    knockdown_resistance_b = max(0.0, min(1.0, 1.0 - knockdown_b))

    control_profile_a = max(0.0, min(1.0, 0.45 * profile_a["aggression"] + 0.30 * cardio_a + 0.25 * pace_retention_a))
    control_profile_b = max(0.0, min(1.0, 0.45 * profile_b["technique"] + 0.30 * cardio_b + 0.25 * pace_retention_b))

    favored_a = headline.get("winner") == fighter_a_name
    favored_bias = min(0.12, signal_gap * 0.30)
    score_bonus_a = favored_bias if favored_a else -favored_bias
    score_bonus_b = -score_bonus_a

    round_scores_a = [
        max(0.0, min(1.0, 0.42 * profile_a["aggression"] + 0.20 * durability_a + 0.18 * stoppage_propensity + 0.20 * cardio_a + score_bonus_a)),
        max(0.0, min(1.0, 0.28 * profile_a["aggression"] + 0.22 * profile_a["technique"] + 0.18 * cardio_a + 0.14 * pace_retention_a + 0.18 * confidence + score_bonus_a)),
        max(0.0, min(1.0, 0.22 * profile_a["aggression"] + 0.18 * cardio_a + 0.22 * recovery_a + 0.18 * durability_a + 0.20 * (1.0 - round_finish_tendency) + score_bonus_a)),
    ]
    round_scores_b = [
        max(0.0, min(1.0, 0.26 * profile_b["aggression"] + 0.28 * profile_b["technique"] + 0.20 * durability_b + 0.26 * cardio_b + score_bonus_b)),
        max(0.0, min(1.0, 0.20 * profile_b["aggression"] + 0.34 * profile_b["technique"] + 0.20 * cardio_b + 0.16 * pace_retention_b + 0.10 * (1.0 - confidence) + score_bonus_b)),
        max(0.0, min(1.0, 0.18 * profile_b["aggression"] + 0.22 * profile_b["technique"] + 0.24 * recovery_b + 0.18 * durability_b + 0.18 * (1.0 - round_finish_tendency) + score_bonus_b)),
    ]

    control_share_a = []
    control_share_b = []
    for value_a, value_b in zip(round_scores_a, round_scores_b):
        total = max(0.01, value_a + value_b)
        control_share_a.append(round(value_a / total, 3))
        control_share_b.append(round(value_b / total, 3))

    predicted_method = (engine_output.get("method") or "Decision").lower()
    decision_prob = max(0.20, min(0.75, confidence if "decision" in predicted_method else 0.36 + (1.0 - stoppage_propensity) * 0.24))
    ko_prob = max(0.10, min(0.60, stoppage_propensity + (0.10 if "ko" in predicted_method or "tko" in predicted_method else 0.06)))
    attritional_prob = max(0.05, min(0.30, round_finish_tendency * 0.45 + 0.05))
    total = decision_prob + ko_prob + attritional_prob
    method_distribution = {
        "Decision": round(decision_prob / total, 3),
        "KO/TKO": round(ko_prob / total, 3),
        "Accumulation/Corner": round(attritional_prob / total, 3),
    }

    comparison_table = {
        "title": "Premium Metric Comparison",
        "headers": ["Metric", fighter_a_name, fighter_b_name],
        "rows": [
            ["Style", style_a, style_b],
            ["Stance", stance_a, stance_b],
            ["Cardio", f"{cardio_a:.2f}", f"{cardio_b:.2f}"],
            ["Durability", f"{durability_a:.2f}", f"{durability_b:.2f}"],
            ["Recovery", f"{recovery_a:.2f}", f"{recovery_b:.2f}"],
            ["Output Decay", f"{output_decay_a:.2f}", f"{output_decay_b:.2f}"],
            ["Knockdown Susc.", f"{knockdown_a:.2f}", f"{knockdown_b:.2f}"],
        ],
    }

    return {
        "radar_metrics": {
            "labels": ["Cardio", "Durability", "Recovery", "Pace Retention", "KD Resistance", "Control"],
            "series": [
                {"label": fighter_a_name, "values": [cardio_a, durability_a, recovery_a, pace_retention_a, knockdown_resistance_a, control_profile_a]},
                {"label": fighter_b_name, "values": [cardio_b, durability_b, recovery_b, pace_retention_b, knockdown_resistance_b, control_profile_b]},
            ],
            "scale_min": 0.0,
            "scale_max": 1.0,
        },
        "heat_map_data": {
            "title": "Round Leverage Heat Map",
            "x_labels": [fighter_a_name, fighter_b_name],
            "y_labels": ["Round 1", "Round 2", "Round 3"],
            "values": [
                [round_scores_a[0], round_scores_b[0]],
                [round_scores_a[1], round_scores_b[1]],
                [round_scores_a[2], round_scores_b[2]],
            ],
        },
        "control_shift_data": {
            "title": "Projected Control Share by Round",
            "rounds": ["R1", "R2", "R3"],
            "series": [
                {"label": fighter_a_name, "values": control_share_a},
                {"label": fighter_b_name, "values": control_share_b},
            ],
        },
        "method_distribution": method_distribution,
        "comparison_table": comparison_table,
    }

def _get_merged_content(section_id, engine_output, fighter_a, fighter_b, enrich_a, enrich_b):
    eo = engine_output.get(section_id)
    if eo and isinstance(eo, str) and eo.strip() and 'not available' not in eo.lower():
        return eo
    fp_a = fighter_a.get(section_id)
    fp_b = fighter_b.get(section_id)
    if fp_a and isinstance(fp_a, str) and fp_a.strip():
        return fp_a
    if fp_b and isinstance(fp_b, str) and fp_b.strip():
        return fp_b
    en_a = enrich_a.get(section_id)
    en_b = enrich_b.get(section_id)
    if en_a and en_b and en_a != en_b:
        return f"A: {en_a}\nB: {en_b}"
    if en_a: return en_a
    if en_b: return en_b
    return None

def _slugify_key(text):
    normalized = unicodedata.normalize('NFKD', str(text or '')).encode('ascii', 'ignore').decode('ascii')
    return normalized.lower().replace(' ', '_')


def _sidecar_matches_fight(premium_sections, fight_id):
    if not isinstance(premium_sections, dict):
        return False
    meta = premium_sections.get("_meta") if isinstance(premium_sections.get("_meta"), dict) else {}
    sidecar_slug = str(meta.get("matchup_slug") or "").strip()
    if not sidecar_slug:
        # Legacy sidecars may not have metadata; allow but treat as unverified.
        return True
    return sidecar_slug == str(fight_id or "").strip()


def _pair_metric_line(fighter_a_name, fighter_b_name, label, value_a, value_b):
    return f"{label}: {fighter_a_name} {value_a} vs {fighter_b_name} {value_b}."


def _normalize_text_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        out = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                out.append(text)
        return out
    text = str(value).strip()
    return [text] if text else []


def _append_list_block(content, heading, items):
    if not items:
        return content
    lines = [f"- {item}" for item in items]
    block = f"{heading}:\n" + "\n".join(lines)
    if content and isinstance(content, str) and content.strip():
        return f"{content}\n\n{block}"
    return block


def _generate_matchup_section(sid, context):
    a = context["fighter_a_name"]
    b = context["fighter_b_name"]
    style_a = context["style_a"]
    style_b = context["style_b"]
    stance_a = context["stance_a"]
    stance_b = context["stance_b"]
    confidence_label = context["confidence_label"]
    winner = context["winner_name"]
    loser = context["loser_name"]
    method = context["method"]
    round_text = context["round"]
    sport = context["sport"]
    promotion = context["promotion"]
    signal_gap = context["signal_gap"]
    stoppage = context["stoppage_propensity"]
    control_a = context["control_profile_a"]
    control_b = context["control_profile_b"]
    cardio_a = context["cardio_a"]
    cardio_b = context["cardio_b"]
    durability_a = context["durability_a"]
    durability_b = context["durability_b"]
    recovery_a = context["recovery_a"]
    recovery_b = context["recovery_b"]
    output_decay_a = context["output_decay_a"]
    output_decay_b = context["output_decay_b"]
    attrition_a = context["attrition_a"]
    attrition_b = context["attrition_b"]

    control_lead = a if control_a >= control_b else b
    pace_fragile = a if output_decay_a >= output_decay_b else b
    sturdier = a if durability_a >= durability_b else b

    if sid == "executive_summary":
        return (
            f"{promotion} {sport} matchup {a} vs {b} projects {winner} by {method} in {round_text} at {confidence_label} confidence. "
            f"The model edge is phase control, with signal gap {signal_gap:.2f} and stoppage pressure {stoppage:.2f}.\n\n"
            f"{a} ({style_a}, {stance_a}) and {b} ({style_b}, {stance_b}) force different decision loops. "
            f"The projection leans toward {winner} because their control pathway is more repeatable under fatigue while {loser} carries more reset pressure late."
        )
    if sid == "matchup_snapshot":
        return (
            f"{a}: {style_a} ({stance_a}) | Cardio {cardio_a:.2f} | Durability {durability_a:.2f} | Recovery {recovery_a:.2f} | Control {control_a:.2f}.\n"
            f"{b}: {style_b} ({stance_b}) | Cardio {cardio_b:.2f} | Durability {durability_b:.2f} | Recovery {recovery_b:.2f} | Control {control_b:.2f}.\n\n"
            f"Control advantage currently tracks to {control_lead}, while pace fragility risk is higher for {pace_fragile}."
        )
    if sid == "decision_structure":
        return (
            f"{a} should build decisions around {style_a.lower()} sequencing and preserve entry quality to avoid high-cost resets. "
            f"{b} should force phase breaks and punish continuation windows before exchange chains develop.\n\n"
            f"The highest leverage decision node is transition ownership: when {a} wins second-phase exchanges, control compounds; "
            f"when {b} forces first-phase resets, scoring variance narrows."
        )
    if sid == "tactical_edges":
        return (
            f"{a} edge: {style_a.lower()} pressure with {stance_a} entries can stack exchanges when timing is hidden.\n"
            f"{b} edge: {style_b.lower()} timing from {stance_b} can interrupt entry rhythm and force low-value restarts.\n\n"
            f"Primary tactical edge in this pairing is control-transfer timing, where {control_lead} currently grades ahead."
        )
    if sid == "energy_use":
        return (
            f"{a} energy profile: output decay {output_decay_a:.2f} with cardio {cardio_a:.2f}; efficiency rises when exchanges extend.\n"
            f"{b} energy profile: output decay {output_decay_b:.2f} with cardio {cardio_b:.2f}; efficiency rises when exchanges reset quickly.\n\n"
            f"Sustained pace risk is currently higher for {pace_fragile}, which can shift late-round scoring if transition fights stay frequent."
        )
    if sid == "fatigue_failure_points":
        return (
            f"{a} fatigue failure point: decision precision declines if entries are denied repeatedly and attrition pressure reaches {attrition_a:.2f}.\n"
            f"{b} fatigue failure point: recovery quality {recovery_b:.2f} can be taxed when layered defense repeats under attrition {attrition_b:.2f}.\n\n"
            f"The fighter who protects recovery windows better through round two and round three should carry the closing minutes."
        )
    if sid == "mental_condition":
        return (
            f"Mental resilience for {a} is tied to maintaining proactive decisions after defended entries; for {b}, it depends on preserving structure after hard exchanges.\n\n"
            f"Adversity handling is asymmetric: {a} usually adapts by increasing decision density, while {b} adapts by tightening selection and minimizing variance."
        )
    if sid == "collapse_triggers":
        return (
            f"{a} collapse trigger: predictable entry lanes combined with rising output decay {output_decay_a:.2f}.\n"
            f"{b} collapse trigger: defensive maintenance loops when durability margin compresses toward {durability_b:.2f}.\n\n"
            f"Once either trigger repeats across consecutive rounds, momentum can flip quickly regardless of early optics."
        )
    if sid == "deception_unpredictability":
        return (
            f"{a} deception path is feint-to-phase extension from {stance_a}; {b} deception path is rhythm disruption and counter release from {stance_b}.\n\n"
            f"Unpredictability advantage goes to the fighter who wins transition reads first and forces the opponent to commit early in mixed phases."
        )
    if sid == "fight_control":
        return (
            f"Fight control depends on who dictates where exchanges restart. {a} benefits from continued contact chains, while {b} benefits from clean resets.\n\n"
            f"Current control profile {a} {control_a:.2f} vs {b} {control_b:.2f} points to {control_lead} as the likely geography owner unless early denial trends reverse."
        )
    if sid == "fight_turns":
        return (
            f"The bout turns when one side repeatedly solves the same transition problem. {a} turns the fight by chaining contacts; {b} turns it by interrupting those chains before continuation develops.\n\n"
            f"Middle rounds are the highest-probability swing window because attrition, reads, and control incentives converge there."
        )
    if sid == "scenario_tree":
        return (
            f"Scenario A: {a} compounds control and wins minute volume through extended sequences.\n"
            f"Scenario B: {b} repeatedly denies continuation and banks cleaner first-phase scoring.\n"
            f"Scenario C: split control with judge-sensitive late exchanges and high volatility.\n\n"
            f"Most likely branch remains {winner} by {method}, but branch probability shifts if {loser} wins early transition denial."
        )
    if sid == "round_by_round_outlook":
        return (
            f"Round 1: read capture and distance calibration; watch whether {a} can convert first contact into second-phase control.\n"
            f"Round 2: attritional separation; output decay pressure starts shaping pace and reset quality.\n"
            f"Round 3+: recovery and durability decide optics, especially if signal gap {signal_gap:.2f} narrows under resistance."
        )
    if sid == "risk_factors":
        return (
            f"{a} risk: overcommitting entries into timed counters, especially when output decay rises toward {output_decay_a:.2f}.\n"
            f"{b} risk: conceding repeat exchanges that erode decision quality under sustained pressure.\n\n"
            f"Shared risk is scoring ambiguity in split-control rounds where neither fighter closes exchanges clearly."
        )
    if sid == "what_could_flip":
        return (
            f"The fight flips if {loser} wins early transition denial and forces {winner} off preferred sequencing.\n"
            f"Secondary flip condition is a hidden pace collapse: one fighter's recovery loop fails despite stable visible output.\n\n"
            f"The model is most sensitive to early adaptation speed and whether attrition gradients steepen after the midpoint."
        )
    if sid == "corner_notes":
        return (
            f"{a} corner: protect entry quality, chain only after clean touch, and keep durability exchanges selective.\n"
            f"{b} corner: deny continuation quickly, preserve reset geometry, and avoid trading in opponent-favored phases.\n\n"
            f"Both corners should track transition-win ratio and late-minute control share as round-to-round KPI signals."
        )
    if sid == "final_projection":
        return (
            f"Final projection: {winner} by {method} in {round_text} at {confidence_label}. "
            f"This projection is anchored to control repeatability, durability margin ({sturdier} currently ahead), and lower collapse exposure.\n\n"
            f"If transition ownership reverses early, the path can move from structured control to volatility-heavy scoring." 
        )
    if sid == "confidence_explanation":
        return (
            f"Confidence derives from signal gap {signal_gap:.2f}, control profile split ({a} {control_a:.2f} vs {b} {control_b:.2f}), "
            f"and stoppage propensity {stoppage:.2f}.\n\n"
            f"Confidence is capped by adaptation uncertainty: if {loser} disrupts preferred sequencing in the first half, projection certainty decreases materially."
        )
    if sid == "disclaimer":
        return "This report is for informational purposes only. All predictions are probabilistic and not financial advice."
    return ""


def map_engine_output_to_report(engine_output):
    import hashlib
    winner = engine_output.get("predicted_winner_id")
    confidence = engine_output.get("confidence")
    method = engine_output.get("method")
    round_val = engine_output.get("round")

    event_date = engine_output.get("event_date") or engine_output.get("event")
    promotion = engine_output.get("promotion")
    sport = engine_output.get("sport")

    # Use canonical fighter profile display names if available
    fighter_a_profile = _get_fighter_profile(engine_output, 'fighter_a')
    fighter_b_profile = _get_fighter_profile(engine_output, 'fighter_b')
    fighter_a_name = fighter_a_profile.get("name") or engine_output.get("fighter_a_name")
    fighter_b_name = fighter_b_profile.get("name") or engine_output.get("fighter_b_name")
    fight_id = engine_output.get("fight_id")
    matchup_details = engine_output.get("matchup_details")

    # Block if any required field is missing
    if not (event_date and promotion and sport and fighter_a_name and fighter_b_name and fight_id):
        raise ValueError("Missing required core fields for report: fight_id, fighter names, event date, sport, promotion")

    fighter_a_profile = _get_fighter_profile(engine_output, 'fighter_a')
    fighter_b_profile = _get_fighter_profile(engine_output, 'fighter_b')
    # Patch: Try both fighter_name and fighter_id for enrichment
    enrich_a = _get_manual_enrichment(fighter_a_name)
    if not enrich_a:
        enrich_a = _get_manual_enrichment(engine_output.get('fighter_a_id', ''))
    enrich_b = _get_manual_enrichment(fighter_b_name)
    if not enrich_b:
        enrich_b = _get_manual_enrichment(engine_output.get('fighter_b_id', ''))

    is_target_fight = bool(enrich_a or enrich_b)

    # Guard confidence formatting
    conf_label = _confidence_label(confidence)
    if confidence is None or conf_label in ["(confidence missing)", "N/A", "None", ""]:
        raise ValueError("Missing or invalid confidence value for report headline")
    headline = {
        "winner": fighter_a_name if winner == engine_output.get('fighter_a_id') else (fighter_b_name if winner == engine_output.get('fighter_b_id') else winner),
        "confidence": confidence,
        "confidence_label": conf_label,
        "method": _normalize_method(method),
        "round": _normalize_round(round_val),
    }
    winner_str = headline["winner"]
    loser_name = fighter_b_name if winner_str == fighter_a_name else fighter_a_name

    # Step 2 compatibility layer: dual-read canonical + legacy aliases,
    # while preserving legacy report section IDs.
    key_tactical_edges = _normalize_text_list(
        engine_output.get("key_tactical_edges")
        or engine_output.get("tactical_edges")
        or []
    )
    what_could_flip_the_fight = _normalize_text_list(
        engine_output.get("what_could_flip_the_fight")
        or engine_output.get("what_could_flip")
        or []
    )
    risk_factors = _normalize_text_list(engine_output.get("risk_factors") or [])
    confidence_explanation = str(engine_output.get("confidence_explanation") or "").strip()

    premium_sections = engine_output.get("premium_sections") or {}
    if not _sidecar_matches_fight(premium_sections, fight_id):
        premium_sections = {}

    style_a = _canonical_style(enrich_a, fighter_a_profile, fallback="Generalist")
    style_b = _canonical_style(enrich_b, fighter_b_profile, fallback="Generalist")
    stance_a = _canonical_stance(enrich_a, fighter_a_profile, fallback="unlisted stance")
    stance_b = _canonical_stance(enrich_b, fighter_b_profile, fallback="unlisted stance")

    control_profile_a = max(0.0, min(1.0,
        0.45 * _style_profile(style_a)["aggression"]
        + 0.30 * _safe_metric(enrich_a, "cardio_endurance", 0.70)
        + 0.25 * (1.0 - _safe_metric(enrich_a, "output_decay", 0.55))
    ))
    control_profile_b = max(0.0, min(1.0,
        0.45 * _style_profile(style_b)["technique"]
        + 0.30 * _safe_metric(enrich_b, "cardio_endurance", 0.70)
        + 0.25 * (1.0 - _safe_metric(enrich_b, "output_decay", 0.55))
    ))

    debug_metrics = engine_output.get("debug_metrics") or {}
    section_context = {
        "fighter_a_name": fighter_a_name,
        "fighter_b_name": fighter_b_name,
        "style_a": style_a,
        "style_b": style_b,
        "stance_a": stance_a,
        "stance_b": stance_b,
        "winner_name": winner_str,
        "loser_name": loser_name,
        "method": headline["method"],
        "round": headline["round"],
        "confidence_label": conf_label,
        "sport": sport,
        "promotion": promotion,
        "signal_gap": _safe_metric(engine_output, "signal_gap", debug_metrics.get("signal_gap", 0.10)),
        "stoppage_propensity": _safe_metric(engine_output, "stoppage_propensity", debug_metrics.get("stoppage_propensity", 0.30)),
        "control_profile_a": control_profile_a,
        "control_profile_b": control_profile_b,
        "cardio_a": _safe_metric(enrich_a, "cardio_endurance", 0.70),
        "cardio_b": _safe_metric(enrich_b, "cardio_endurance", 0.70),
        "durability_a": _safe_metric(enrich_a, "durability", 0.70),
        "durability_b": _safe_metric(enrich_b, "durability", 0.70),
        "recovery_a": _safe_metric(enrich_a, "recovery_quality", 0.70),
        "recovery_b": _safe_metric(enrich_b, "recovery_quality", 0.70),
        "output_decay_a": _safe_metric(enrich_a, "output_decay", 0.55),
        "output_decay_b": _safe_metric(enrich_b, "output_decay", 0.55),
        "attrition_a": _safe_metric(enrich_a, "attrition_sensitivity", 0.55),
        "attrition_b": _safe_metric(enrich_b, "attrition_sensitivity", 0.55),
    }

    sections = []
    boilerplate_ids = {"front_cover", "disclaimer"}
    narrative_ids = {
        "executive_summary",
        "matchup_snapshot",
        "decision_structure",
        "tactical_edges",
        "energy_use",
        "fatigue_failure_points",
        "mental_condition",
        "collapse_triggers",
        "deception_unpredictability",
        "fight_control",
        "fight_turns",
        "scenario_tree",
        "round_by_round_outlook",
        "risk_factors",
        "what_could_flip",
        "corner_notes",
        "final_projection",
        "confidence_explanation",
    }
    for section in REPORT_SECTIONS:
        sid = section["id"]
        content = None

        if sid == "front_cover":
            content = {
                "fight_id": fight_id,
                "fighters": f"{fighter_a_name} vs {fighter_b_name}",
                "event_date": event_date,
                "sport": sport,
                "promotion": promotion,
            }
        else:
            sidecar_text = premium_sections.get(sid)
            generated_text = _generate_matchup_section(sid, section_context)
            if isinstance(sidecar_text, str) and sidecar_text.strip():
                if sid in narrative_ids:
                    content = f"{generated_text}\n\nSupplemental matchup notes:\n{sidecar_text.strip()}"
                else:
                    content = sidecar_text.strip()
            else:
                content = generated_text

            if sid == "tactical_edges":
                content = _append_list_block(content, "Model tactical edges", key_tactical_edges)
            elif sid == "what_could_flip":
                content = _append_list_block(content, "Model flip factors", what_could_flip_the_fight)
            elif sid == "risk_factors":
                content = _append_list_block(content, "Model risk factors", risk_factors)
            elif sid == "confidence_explanation" and confidence_explanation:
                content = f"{content}\n\nModel confidence note:\n{confidence_explanation}" if content else confidence_explanation

        sections.append({"id": sid, "title": section["title"], "content": content})

    visual_data = _build_visual_data(engine_output, fighter_a_name, fighter_b_name, enrich_a, enrich_b, headline)
    section_hashes = {
        s.get("id"): hashlib.sha1(str(s.get("content")).encode("utf-8")).hexdigest()
        for s in sections
    }

    return {
        "headline": headline,
        "sections": sections,
        "visuals": [],
        "fight_id": fight_id,
        "trace": {
            "premium_sidecar_path": engine_output.get("trace_premium_sidecar_path"),
            "premium_sidecar_slug_validated": bool(premium_sections),
            "section_hashes": section_hashes,
        },
        "packaging": {
            "report_type": "Fight Intelligence Report",
            "brand_name": "AI-RISA",
            "theme": "black_gold_analyst",
            "version": "RC1",
            "fixture_id": fight_id,
            "report_id": fight_id,
        },
        "visual_slots": {},
        **visual_data,
    }

