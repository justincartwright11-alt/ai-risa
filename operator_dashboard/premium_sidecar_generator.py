"""
Premium Sidecar Generator (v4 Quality)

Builds deep, section-specific premium report narratives from matchup, profile,
and enrichment context. The generator prioritizes opponent-interactive reasoning,
sport-specific logic, and tactical collision analysis.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional


NARRATIVE_SECTIONS = [
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
]

GENERIC_PHRASES = [
    "both fighters are skilled",
    "either fighter can win",
    "it will be interesting",
    "high level matchup",
    "styles make fights",
    "competitive fight",
    "anything can happen",
    "close fight on paper",
]


class PremiumSidecarGenerator:
    """Generates deeper v4 premium sections for any matchup."""

    def __init__(self, ai_risa_data_path: str = "c:/ai_risa_data"):
        self.ai_risa_data_path = Path(ai_risa_data_path)
        self.fighters_dir = self.ai_risa_data_path / "fighters"
        self.matchups_dir = self.ai_risa_data_path / "matchups"
        self.enrichment_path = self.fighters_dir / "manual_profile_enrichment.json"
        self._enrichment_cache: Optional[Dict[str, Any]] = None

    def _load_json(self, path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
            return None
        except Exception:
            return None

    def _slugify(self, name: str) -> str:
        return re.sub(r"[^a-z0-9_]+", "", name.lower().replace(" ", "_").replace("-", "_"))

    def _title_or_unknown(self, value: Any, fallback: str = "Unknown") -> str:
        text = str(value or "").strip()
        return text if text else fallback

    def _normalize_style(self, profile: Dict[str, Any], enrichment: Dict[str, Any]) -> str:
        style = str(
            enrichment.get("style")
            or profile.get("style")
            or "generalist"
        ).strip().lower()
        return style if style else "generalist"

    def _normalize_stance(self, profile: Dict[str, Any], enrichment: Dict[str, Any]) -> str:
        stance = str(
            enrichment.get("stance")
            or profile.get("stance")
            or "orthodox"
        ).strip().lower()
        if stance in {"orthodox", "southpaw", "switch"}:
            return stance
        return "orthodox"

    def _load_enrichment(self) -> Dict[str, Any]:
        if self._enrichment_cache is None:
            self._enrichment_cache = self._load_json(self.enrichment_path) or {}
        return self._enrichment_cache

    def _load_enrichment_for_slug(self, slug: str) -> Dict[str, Any]:
        data = self._load_enrichment()
        raw = data.get(slug, {}) if isinstance(data, dict) else {}
        return raw if isinstance(raw, dict) else {}

    def _load_matchup_record(self, matchup_slug: str) -> Dict[str, Any]:
        path = self.matchups_dir / f"{matchup_slug}.json"
        return self._load_json(path) or {}

    def _find_profile(self, fighter_name: str, fighter_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        candidates = []
        if fighter_id:
            candidates.append(self.fighters_dir / f"{fighter_id}.json")
        slug = self._slugify(fighter_name)
        candidates.append(self.fighters_dir / f"fighter_{slug}.json")
        candidates.append(self.fighters_dir / f"{slug}.json")

        for candidate in candidates:
            loaded = self._load_json(candidate)
            if loaded:
                return loaded
        return None

    def _as_float(self, value: Any, default: float) -> float:
        try:
            return float(value)
        except Exception:
            return default

    def _get_metric(self, profile: Dict[str, Any], enrichment: Dict[str, Any], key: str, default: float) -> float:
        if key in enrichment:
            return self._as_float(enrichment.get(key), default)
        return self._as_float(profile.get(key), default)

    def _infer_sport(self, matchup_sport: str, profile_a: Dict[str, Any], profile_b: Dict[str, Any], style_a: str, style_b: str) -> str:
        explicit = str(matchup_sport or "").strip().lower()
        if explicit in {"mma", "boxing", "kickboxing", "muay thai", "muay_thai"}:
            return "muay_thai" if explicit == "muay thai" else explicit

        profile_sports = {
            str(profile_a.get("sport") or "").strip().lower(),
            str(profile_b.get("sport") or "").strip().lower(),
        }
        if "boxing" in profile_sports:
            return "boxing"
        if "kickboxing" in profile_sports:
            return "kickboxing"
        if "muay thai" in profile_sports or "muay_thai" in profile_sports:
            return "muay_thai"
        if "mma" in profile_sports:
            return "mma"

        style_text = f"{style_a} {style_b}".lower()
        if any(k in style_text for k in ["boxer", "boxing", "jab"]):
            return "boxing"
        if any(k in style_text for k in ["muay", "knee", "elbow"]):
            return "muay_thai"
        if any(k in style_text for k in ["kickbox", "kicker"]):
            return "kickboxing"
        return "mma"

    def _sport_vocab(self, sport: str) -> Dict[str, str]:
        if sport == "boxing":
            return {
                "arena": "ring position",
                "control_axis": "jab lane ownership and pocket entry timing",
                "entry": "jab-to-body entry",
                "defense": "high guard and shoulder roll layers",
                "transition": "outside-to-pocket conversion",
                "attrition": "body work and volume pacing",
                "finish": "late-round scoring separation",
            }
        if sport in {"kickboxing", "muay_thai"}:
            return {
                "arena": "open-space geometry and rope pressure",
                "control_axis": "kick range command and tempo ownership",
                "entry": "kick-to-boxing step-in",
                "defense": "frame control and balance recovery",
                "transition": "long-range to close-range clinch or knee lanes",
                "attrition": "leg-body attrition and balance taxation",
                "finish": "scoring optics through clean weapon selection",
            }
        return {
            "arena": "cage geography",
            "control_axis": "range-to-clinch-to-ground transition control",
            "entry": "striking-to-shot entry",
            "defense": "layered takedown and scramble defense",
            "transition": "kickboxing-to-grappling phase shift",
            "attrition": "clinch grinding and top-control energy drain",
            "finish": "control-based late-round separation",
        }

    def _archetype_flags(self, style: str) -> Dict[str, bool]:
        s = style.lower()
        return {
            "grappler": any(x in s for x in ["grappl", "wrestl", "jiu", "sambo"]),
            "striker": any(x in s for x in ["striker", "box", "kick", "muay", "punch"]),
            "pressure": any(x in s for x in ["pressure", "aggressive", "forward"]),
            "counter": any(x in s for x in ["counter", "reactive"]),
            "technical": any(x in s for x in ["technical", "technician", "outside"]),
            "power": any(x in s for x in ["power", "knockout", "finisher"]),
            "volume": any(x in s for x in ["volume", "high-volume", "pace"]),
        }

    def _primary_archetype(self, flags: Dict[str, bool]) -> str:
        if flags["grappler"] and flags["pressure"]:
            return "pressure grappler"
        if flags["counter"] and flags["technical"]:
            return "technical counter fighter"
        if flags["pressure"] and flags["striker"]:
            return "pressure striker"
        if flags["volume"] and flags["striker"]:
            return "volume striker"
        if flags["technical"] and flags["striker"]:
            return "technical striker"
        if flags["grappler"]:
            return "control grappler"
        if flags["power"]:
            return "power-oriented striker"
        return "balanced operator"

    def _extract_fighter_model(self, fighter_name: str, profile: Dict[str, Any], enrichment: Dict[str, Any], sport: str) -> Dict[str, Any]:
        name = self._title_or_unknown(profile.get("name"), fighter_name)
        style = self._normalize_style(profile, enrichment)
        stance = self._normalize_stance(profile, enrichment)
        flags = self._archetype_flags(style)

        model = {
            "name": name,
            "style": style,
            "stance": stance,
            "weight_class": str(profile.get("weight_class") or "").strip().lower() or "unknown",
            "notes": str(profile.get("notes") or "").strip(),
            "recent_activity": str(profile.get("recent_activity") or "").strip(),
            "primary_archetype": self._primary_archetype(flags),
            "flags": flags,
            "cardio_endurance": self._get_metric(profile, enrichment, "cardio_endurance", 0.64),
            "recovery_quality": self._get_metric(profile, enrichment, "recovery_quality", 0.63),
            "output_decay": self._get_metric(profile, enrichment, "output_decay", 0.56),
            "late_fight_fade": self._get_metric(profile, enrichment, "late_fight_fade", 0.58),
            "attrition_sensitivity": self._get_metric(profile, enrichment, "attrition_sensitivity", 0.57),
            "durability": self._get_metric(profile, enrichment, "durability", 0.72),
            "knockdown_susceptibility": self._get_metric(profile, enrichment, "knockdown_susceptibility", 0.53),
            "defensive_breakdown_tendency": self._get_metric(profile, enrichment, "defensive_breakdown_tendency", 0.57),
            "panic_collapse_sensitivity": self._get_metric(profile, enrichment, "panic_collapse_sensitivity", 0.55),
            "sport": sport,
        }
        return model

    def _build_gameplans(self, a: Dict[str, Any], b: Dict[str, Any], vocab: Dict[str, str], sport: str) -> Dict[str, str]:
        if sport == "boxing":
            a_wants = (
                f"{a['name']} wants to establish {vocab['control_axis']} through lead-hand discipline, body touches, "
                f"and repeated {vocab['transition']} so exchanges end on his terms."
            )
            b_wants = (
                f"{b['name']} wants to deny clean entries, win first contact with stance-aligned jab and straight lanes, "
                f"and keep rounds in a clean sequencing rhythm."
            )
        elif sport in {"kickboxing", "muay_thai"}:
            a_wants = (
                f"{a['name']} wants to own long-weapon rhythm, force reactions to kicks and frames, and convert that read "
                f"into {vocab['transition']} moments where balance breaks."
            )
            b_wants = (
                f"{b['name']} wants to blunt early kick tempo, answer with counters or clinch frame disruption, and score "
                f"through cleaner visible weapon selection."
            )
        else:
            a_wants = (
                f"{a['name']} wants to connect range pressure to {vocab['transition']} and keep {b['name']} in "
                f"defensive chains long enough to tax decision quality."
            )
            b_wants = (
                f"{b['name']} wants to break those chains early, force resets after first contact, and avoid extended "
                f"{vocab['arena']} phases where attrition accumulates."
            )

        collision = (
            f"Their systems collide at {vocab['control_axis']}: if {a['name']} can make second-phase exchanges frequent, "
            f"he compounds control; if {b['name']} keeps exchanges single-beat and reset-heavy, he keeps scoring cleaner."
        )

        momentum = (
            f"Momentum changes when one fighter controls the transition layer. {a['name']} gains momentum when {b['name']} is "
            f"forced into maintenance defense. {b['name']} gains momentum when {a['name']}'s entries are checked before "
            f"continuation offense appears."
        )

        risk = (
            f"Primary risk is asymmetric: {a['name']} risks overcommitting into prepared counters; {b['name']} risks conceding "
            f"position and repeated attritional exchanges that degrade his reset quality."
        )

        collapse = (
            f"Collapse begins when a fighter loses preferred decision space. {a['name']} collapses if he cannot enter safely enough to "
            f"sustain pressure; {b['name']} collapses if he cannot reset cleanly after body or positional taxation."
        )

        return {
            "a_wants": a_wants,
            "b_wants": b_wants,
            "collision": collision,
            "momentum": momentum,
            "risk": risk,
            "collapse": collapse,
        }

    def _project_outcome(self, a: Dict[str, Any], b: Dict[str, Any], sport: str) -> Dict[str, Any]:
        a_score = (
            (a["cardio_endurance"] + a["recovery_quality"] + a["durability"]) * 0.34
            - (a["output_decay"] + a["defensive_breakdown_tendency"]) * 0.18
        )
        b_score = (
            (b["cardio_endurance"] + b["recovery_quality"] + b["durability"]) * 0.34
            - (b["output_decay"] + b["defensive_breakdown_tendency"]) * 0.18
        )

        if a["flags"]["pressure"] and b["flags"]["counter"]:
            a_score += 0.03
            b_score += 0.02
        if a["flags"]["grappler"] and sport == "mma":
            a_score += 0.03
        if b["flags"]["technical"]:
            b_score += 0.02

        margin = a_score - b_score
        winner = a if margin >= 0 else b
        loser = b if winner is a else a
        abs_margin = abs(margin)

        if abs_margin < 0.03:
            confidence = "moderate"
            likely_method = "narrow decision"
        elif abs_margin < 0.07:
            confidence = "moderate-high"
            likely_method = "clear decision"
        else:
            confidence = "high"
            likely_method = "decision with late separation"

        return {
            "winner": winner,
            "loser": loser,
            "margin": abs_margin,
            "confidence": confidence,
            "likely_method": likely_method,
        }

    def _build_context(self, matchup_slug: str, fighter_a: str, fighter_b: str) -> Optional[Dict[str, Any]]:
        matchup = self._load_matchup_record(matchup_slug)

        fighter_a_id = str(matchup.get("fighter_a_id") or "").strip() or None
        fighter_b_id = str(matchup.get("fighter_b_id") or "").strip() or None

        profile_a = self._find_profile(fighter_a, fighter_a_id)
        profile_b = self._find_profile(fighter_b, fighter_b_id)
        if not profile_a or not profile_b:
            return None

        slug_a = self._slugify(fighter_a)
        slug_b = self._slugify(fighter_b)
        enrichment_a = self._load_enrichment_for_slug(slug_a)
        enrichment_b = self._load_enrichment_for_slug(slug_b)

        inferred_sport = self._infer_sport(
            str(matchup.get("sport") or ""),
            profile_a,
            profile_b,
            self._normalize_style(profile_a, enrichment_a),
            self._normalize_style(profile_b, enrichment_b),
        )

        a = self._extract_fighter_model(fighter_a, profile_a, enrichment_a, inferred_sport)
        b = self._extract_fighter_model(fighter_b, profile_b, enrichment_b, inferred_sport)
        vocab = self._sport_vocab(inferred_sport)
        gameplans = self._build_gameplans(a, b, vocab, inferred_sport)
        projection = self._project_outcome(a, b, inferred_sport)

        return {
            "matchup_slug": matchup_slug,
            "sport": inferred_sport,
            "vocab": vocab,
            "a": a,
            "b": b,
            "gameplans": gameplans,
            "projection": projection,
        }

    def _section_executive_summary(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        g = c["gameplans"]
        p = c["projection"]
        w = p["winner"]["name"]
        return (
            f"Central fight logic starts with opposed control agendas. {g['a_wants']} {g['b_wants']} "
            f"The likely shape is therefore an iterative control battle rather than a single-moment shootout.\n\n"
            f"The reason this shape is most probable is structural: both fighters depend on positional sequencing, but in different phases. "
            f"{a['name']} gains value when exchanges stay alive beyond first contact. {b['name']} gains value when he can score and reset "
            f"before continuation offense develops. {g['collision']}\n\n"
            f"Main variables that decide the fight are transition ownership, defensive layer durability, and late-round maintenance cost. "
            f"{g['momentum']} {g['risk']} {g['collapse']}\n\n"
            f"Projected outcome is {w} by {p['likely_method']} because his preferred phase is more repeatable over deep rounds and less "
            f"dependent on perfect sequencing for twelve or five rounds."
        )

    def _section_matchup_snapshot(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        g = c["gameplans"]
        return (
            f"{a['name']} enters as a {a['primary_archetype']} ({a['stance']} stance), while {b['name']} enters as a "
            f"{b['primary_archetype']} ({b['stance']} stance). This is comparative context, not a trait list: each style only matters "
            f"in how it stresses the opponent's decision loop.\n\n"
            f"What {a['name']} wants immediately is phase extension after first contact; what {b['name']} wants immediately is phase denial "
            f"through cleaner first-beat scoring. {g['collision']}\n\n"
            f"The immediate interaction pattern is a race over whether entries become sustained sequences or forced resets. Momentum shifts early "
            f"if one fighter owns the first two transition exchanges in each round. Risk appears when the loser of those exchanges has to "
            f"abandon preferred geometry, which is where collapse pathways begin."
        )

    def _section_decision_structure(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        return (
            f"{a['name']}'s decision structure under pressure is to choose repeatable, lower-risk access points that still force response. "
            f"When ahead, he should keep decision density high and avoid unnecessary variance. When behind, he has to increase entry frequency "
            f"without sacrificing layer-one defense.\n\n"
            f"{b['name']}'s decision structure under pressure is to prioritize denial choices: stop continuation early, then re-establish geometry. "
            f"When ahead, he should stay disciplined and avoid overtrading for optics. When behind, he must take selective initiative to prevent "
            f"being walked into pure reaction rounds.\n\n"
            f"Their systems collide in how they price risk. {a['name']} accepts short-term contact risk to create long-term control gain. "
            f"{b['name']} accepts lower output at times to preserve structural control. Momentum turns when either fighter is forced to make "
            f"decisions from the wrong phase of the exchange."
        )

    def _section_tactical_edges(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        sport = c["sport"]
        if sport == "boxing":
            axis = "jab lane ownership, body work conversion, and pocket exits"
        elif sport in {"kickboxing", "muay_thai"}:
            axis = "long-weapon rhythm, frame control, and balance recovery"
        else:
            axis = "entry safety, clinch transitions, and scramble denial"

        return (
            f"{a['name']}'s opponent-specific edge is his ability to force repeated decisions in the same tactical channel. Against {b['name']}, "
            f"that means making {axis} happen often enough that one defensive leak becomes cumulative damage.\n\n"
            f"{b['name']}'s opponent-specific edge is cleaner interruption timing. He can punish predictable entries and force {a['name']} into "
            f"higher-cost re-entry attempts, which directly attacks {a['name']}'s preferred tempo build.\n\n"
            f"The collision point is not generic pressure versus movement. It is whether {a['name']} can convert first touch into second touch "
            f"before {b['name']} resets. Momentum changes when one fighter repeatedly wins the last scoring beat in contested exchanges."
        )

    def _section_energy_use(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        return (
            f"{a['name']}'s energy profile is driven by entry volume, continuation attempts, and recovery between high-friction exchanges. "
            f"His efficiency improves when entry-to-control conversion is high and declines when he must restart from distance repeatedly.\n\n"
            f"{b['name']}'s energy profile is built around cleaner cycle management: score, deny continuation, reset. That is efficient early, "
            f"but recovery load spikes if he is forced to defend layered sequences and then immediately re-center.\n\n"
            f"The collision in energy economics is output versus wasted motion. If {a['name']} spends less on failed entries, he can carry late pace. "
            f"If {b['name']} spends less on emergency exits, he keeps technical clarity. Momentum and risk both hinge on which fighter turns energy "
            f"into scoring events rather than maintenance work."
        )

    def _section_fatigue_failure_points(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        return (
            f"What breaks first for {a['name']} is usually decision precision after repeated failed access attempts. As fatigue accumulates, entry "
            f"selection can become obvious, making counters and denials more available to {b['name']}.\n\n"
            f"What breaks first for {b['name']} is reset quality under sustained attrition. His technical structure can remain present, but the "
            f"small delay in exits creates the exact extra beat {a['name']} needs to extend exchanges.\n\n"
            f"Attrition changes the fight by shifting from clean sequence scoring to phase-control scoring. The fighter who protects his first failure "
            f"point longer usually wins the middle and late rounds. Collapse risk rises sharply once either side has to fight from reactive maintenance "
            f"for two consecutive rounds."
        )

    def _section_mental_condition(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        return (
            f"{a['name']}'s mental condition projects strongest when he can trust process over immediate optics. Composure here means accepting some "
            f"lost minutes while still building his preferred fight shape through disciplined repetition.\n\n"
            f"{b['name']}'s mental condition projects strongest when tactical order remains intact. His confidence climbs when exchanges are clean and "
            f"phase one decisions are rewarded; it is tested when he must defend long sequences and still produce scoring replies.\n\n"
            f"Adaptability under adversity is therefore asymmetric. {a['name']} adapts by increasing density. {b['name']} adapts by increasing selectivity. "
            f"Momentum swings mentally when one adaptation no longer restores control in the following round."
        )

    def _section_collapse_triggers(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        return (
            f"{a['name']}'s collapse trigger is state-based: repeated unsuccessful entries followed by visible defensive overreach. In that state, "
            f"he spends energy without building control, and his decision tree compresses into predictable approaches.\n\n"
            f"{b['name']}'s collapse trigger is positional drift: losing clean exits and conceding repeat exchanges in compromised geometry. In that "
            f"state, technical quality remains but structural control disappears.\n\n"
            f"These triggers are not theoretical. They appear when momentum shifts are ignored for too long. The fight collapses for either side once "
            f"the same unfavorable state repeats across two rounds without successful adjustment."
        )

    def _section_deception_unpredictability(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        sport = c["sport"]
        if sport == "boxing":
            toolkit = "feint-to-jab layering, tempo checks, and disguised pocket exits"
        elif sport in {"kickboxing", "muay_thai"}:
            toolkit = "kick feints, rhythm breaks, and hidden clinch or knee entries"
        else:
            toolkit = "level-change feints, strike-to-shot disguise, and scramble traps"

        return (
            f"Deception quality is defined by how well each fighter hides phase intention. {a['name']} should use {toolkit} to force {b['name']} "
            f"into premature defensive commits, then attack the opened lane.\n\n"
            f"{b['name']} should answer with rhythm disruption and baited counters, making {a['name']} uncertain about whether continuation offense "
            f"will be rewarded or punished.\n\n"
            f"Unpredictability matters most in transition beats, not in static range. Momentum turns when one fighter successfully disguises entry "
            f"or exit two or three times in the same round, because that rewrites the opponent's decision confidence for the next phase."
        )

    def _section_fight_control(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        v = c["vocab"]
        return (
            f"Fight control is owned through {v['arena']} and the right to choose where exchanges restart. {a['name']} controls when rounds spend "
            f"more time in his preferred continuation zone. {b['name']} controls when he can force clean separations after first contact.\n\n"
            f"Range and geography are not passive here. They are active scoring engines. If {a['name']} keeps compressing space, tempo ownership "
            f"tilts his way. If {b['name']} keeps restoring open-space timing, control stays with his structure.\n\n"
            f"The control axis is therefore measurable: who wins more transition resets per round. That metric is usually more predictive than raw "
            f"output totals in this specific collision."
        )

    def _section_fight_turns(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        return (
            f"This fight turns when one fighter starts forcing the other to solve the same transition problem repeatedly. For {a['name']}, the turn "
            f"comes from building chained exchanges that remove {b['name']}'s reset comfort.\n\n"
            f"For {b['name']}, the turn comes from punishing entries early enough that {a['name']} must reset strategy rather than merely adjust timing. "
            f"Those are different kinds of turns: cumulative control versus punctuated interruption.\n\n"
            f"Most likely swing window is the middle rounds, where accumulated reads and fatigue begin to interact. The side that wins that window "
            f"usually carries both momentum and judging optics into the final third."
        )

    def _section_scenario_tree(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        p = c["projection"]
        w = p["winner"]["name"]
        return (
            f"Scenario 1, control accumulation: {a['name']} secures repeated transition wins, keeps {b['name']} in layered defense, and turns later "
            f"rounds into maintenance stress for {b['name']}. In this branch, round margins widen over time.\n\n"
            f"Scenario 2, interruption control: {b['name']} repeatedly denies continuation, punishes predictable entries, and keeps most rounds in "
            f"single-phase scoring structure. In this branch, {a['name']}'s pressure reads as effort more than command.\n\n"
            f"Scenario 3, split-phase volatility: each fighter wins his preferred phase in different minutes, producing narrow rounds decided by "
            f"closing sequences and judges' weighting of control versus cleanliness.\n\n"
            f"Most likely branch is {w} by {p['likely_method']} because that path requires fewer fragile assumptions about perfect execution over "
            f"the full fight length."
        )

    def _section_round_by_round_outlook(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        sport = c["sport"]
        rounds_label = "Rounds 1-2" if sport == "boxing" else "Round 1"
        return (
            f"{rounds_label}: information and range mapping. {a['name']} tests entry reliability while {b['name']} tests denial timing. Early optics may "
            f"favor whoever wins first contact, but deeper value comes from who owns the transition after that touch.\n\n"
            f"Middle rounds: this is the decision core. {a['name']} should be increasing successful second-phase exchanges; {b['name']} should be "
            f"preserving clean exits and forcing resets. Momentum and risk become visible in this block.\n\n"
            f"Late rounds: fatigue and confidence combine. If {a['name']} has established attritional control, his projection improves. If {b['name']} "
            f"has protected geometry and pace, he can bank cleaner late scoring. Round progression is therefore a control-then-maintenance story, "
            f"not a sequence of disconnected fragments."
        )

    def _section_risk_factors(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        return (
            f"Opponent-specific liability for {a['name']}: forcing entries from too far out and giving {b['name']} predictable timing reads. That risk "
            f"raises both counter exposure and cumulative energy waste.\n\n"
            f"Opponent-specific liability for {b['name']}: overreliance on clean resets when {a['name']} is built to chase continuation phases. That risk "
            f"raises attrition and late-round positional debt.\n\n"
            f"Shared systemic risk is judging ambiguity in split-phase rounds. The fighter who fails to close exchanges with clear terms in the final "
            f"minute invites scoring volatility and strategic overcorrection next round."
        )

    def _section_what_could_flip(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        p = c["projection"]
        w = p["winner"]["name"]
        l = p["loser"]["name"]
        return (
            f"The primary upset pathway is {l} forcing early strategic doubt in {w}'s core game. That can happen if he wins repeated transition beats "
            f"and makes the favorite's best route look inefficient by the middle rounds.\n\n"
            f"A second flip point is injury-like functional loss without a knockdown event, such as footwork slowdown, exit delay, or guarded offense "
            f"after body or positional stress. Those subtle shifts can reverse expected control arcs quickly.\n\n"
            f"The model's unstable assumptions are pace sustainability and adaptation speed. If either assumption breaks, the fight can move from expected "
            f"control logic to opportunistic momentum logic within one or two rounds."
        )

    def _section_corner_notes(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        sport = c["sport"]
        if sport == "boxing":
            a_note = "keep lead-hand initiative, touch body before head commitments, and finish rounds with the last clean sequence"
            b_note = "win first contact with jab alignment, punish entries with straight lanes, and never concede pocket exits in straight lines"
        elif sport in {"kickboxing", "muay_thai"}:
            a_note = "layer kicks into hands, force balance checks, and exit on angle before counters reset"
            b_note = "interrupt rhythm with frames and teeps, answer kicks immediately, and control visible scoring optics"
        else:
            a_note = "chain strikes into shot threats, trap exits at the fence, and prioritize top-position stability over low-value scrambles"
            b_note = "defend first shot with layered hips and frames, re-center immediately, and punish re-entries before clinch settles"

        return (
            f"{a['name']} corner: {a_note}. The strategic goal is to keep decision pressure on {b['name']} every exchange and avoid empty-volume surges.\n\n"
            f"{b['name']} corner: {b_note}. The strategic goal is to deny continuation and force the fight back into clean, first-phase scoring.\n\n"
            f"Both corners should track one KPI between rounds: transition wins per minute. That single metric best predicts who is controlling momentum, "
            f"risk, and collapse trajectory in this matchup."
        )

    def _section_final_projection(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        p = c["projection"]
        w = p["winner"]["name"]
        l = p["loser"]["name"]
        return (
            f"Final projection is {w} by {p['likely_method']}. The reason is not abstract style preference; it is the expected repeatability of his "
            f"control pathway under fatigue and tactical adjustment.\n\n"
            f"{l} absolutely has a live route, but it demands cleaner sequencing for longer stretches and lower error tolerance in transition defense. "
            f"That route is real, just less robust across full fight length.\n\n"
            f"Most likely fight shape remains: early contested control, middle-round separation via transition ownership, then late-round scoring that "
            f"favors whichever side protected collapse points better."
        )

    def _section_confidence_explanation(self, c: Dict[str, Any]) -> str:
        a = c["a"]
        b = c["b"]
        p = c["projection"]
        w = p["winner"]["name"]
        l = p["loser"]["name"]
        return (
            f"Confidence is {p['confidence']} on {w} because his projected edge comes from multiple reinforcing mechanisms: control sustainability, "
            f"energy conversion, and lower collapse exposure in the expected fight shape.\n\n"
            f"Confidence is not extreme because {l} has credible denial tools that can disrupt the projection if he wins transition phases consistently "
            f"in the first half. The model is sensitive to early tactical sequencing quality.\n\n"
            f"What lowers confidence most is execution variance in close rounds and unplanned state changes, especially if the underdog forces the "
            f"favorite into non-preferred decision loops for two rounds in a row."
        )

    def _build_sections(self, context: Dict[str, Any]) -> Dict[str, str]:
        sections = {
            "executive_summary": self._section_executive_summary(context),
            "matchup_snapshot": self._section_matchup_snapshot(context),
            "decision_structure": self._section_decision_structure(context),
            "tactical_edges": self._section_tactical_edges(context),
            "energy_use": self._section_energy_use(context),
            "fatigue_failure_points": self._section_fatigue_failure_points(context),
            "mental_condition": self._section_mental_condition(context),
            "collapse_triggers": self._section_collapse_triggers(context),
            "deception_unpredictability": self._section_deception_unpredictability(context),
            "fight_control": self._section_fight_control(context),
            "fight_turns": self._section_fight_turns(context),
            "scenario_tree": self._section_scenario_tree(context),
            "round_by_round_outlook": self._section_round_by_round_outlook(context),
            "risk_factors": self._section_risk_factors(context),
            "what_could_flip": self._section_what_could_flip(context),
            "corner_notes": self._section_corner_notes(context),
            "final_projection": self._section_final_projection(context),
            "confidence_explanation": self._section_confidence_explanation(context),
            "disclaimer": (
                "This report is an AI-RISA tactical intelligence assessment based on available style, "
                "profile, and process signals. It is probabilistic rather than certain and should be used "
                "as a decision-support document, not as a guarantee of outcome."
            ),
        }
        return sections

    def generate_sections(self, matchup_slug: str, fighter_a: str, fighter_b: str) -> Optional[Dict[str, str]]:
        context = self._build_context(matchup_slug, fighter_a, fighter_b)
        if not context:
            return None
        return self._build_sections(context)


def _section_is_thin(text: str) -> bool:
    body = str(text or "").strip()
    if len(body) < 550:
        return True

    lowered = body.lower()
    if any(phrase in lowered for phrase in GENERIC_PHRASES):
        return True

    unique_tokens = set(re.findall(r"[a-z]{4,}", lowered))
    if len(unique_tokens) < 65:
        return True

    return False


def _is_strong_sidecar(sidecar: Dict[str, Any]) -> bool:
    if not isinstance(sidecar, dict):
        return False

    for key in NARRATIVE_SECTIONS:
        if key not in sidecar:
            return False
        if _section_is_thin(sidecar.get(key, "")):
            return False

    # Check repeated lead sentences across sections.
    starts = []
    for key in NARRATIVE_SECTIONS:
        text = str(sidecar.get(key, "")).strip().lower()
        starts.append(text[:120])
    if len(set(starts)) < len(starts) - 3:
        return False

    return True


def _existing_is_auto_generated(sidecar: Dict[str, Any]) -> bool:
    if not isinstance(sidecar, dict):
        return False
    meta = sidecar.get("_meta")
    if isinstance(meta, dict):
        source = str(meta.get("generated_by") or "").lower()
        if "premium_sidecar_generator" in source or "auto" in source:
            return True
    return False


def generate_or_refresh_sidecar(
    matchup_slug: str,
    fighter_a: str,
    fighter_b: str,
    ai_risa_data_path: str = "c:/ai_risa_data",
) -> Optional[str]:
    """
    Generate or refresh a v4 premium sidecar for a matchup.

    Preserve existing strong sidecars by default. Regenerate when existing sidecar
    is clearly thin or auto-generated and below quality threshold.

    Returns path to sidecar if created/refreshed, None if existing strong sidecar kept.
    """
    matchups_dir = Path(ai_risa_data_path) / "matchups"
    sidecar_path = matchups_dir / f"{matchup_slug}_premium_sections.json"

    existing_sidecar = None
    if sidecar_path.exists():
        try:
            with open(sidecar_path, "r", encoding="utf-8") as f:
                existing_sidecar = json.load(f)
        except Exception:
            existing_sidecar = None

        if isinstance(existing_sidecar, dict) and _is_strong_sidecar(existing_sidecar):
            return None

        # Non-strong sidecars are candidates for refresh.
        # We still preserve clearly manual high-effort documents if they pass quality checks.
        if isinstance(existing_sidecar, dict) and not _existing_is_auto_generated(existing_sidecar):
            # If it is manual but weak, refresh only when clearly thin.
            executive = str(existing_sidecar.get("executive_summary") or "")
            if len(executive) > 900 and not _section_is_thin(executive):
                return None

    generator = PremiumSidecarGenerator(ai_risa_data_path)
    sections = generator.generate_sections(matchup_slug, fighter_a, fighter_b)
    if not sections:
        return None

    sections["_meta"] = {
        "generated_by": "premium_sidecar_generator_v4_quality",
        "matchup_slug": matchup_slug,
    }

    matchups_dir.mkdir(parents=True, exist_ok=True)
    with open(sidecar_path, "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=2, ensure_ascii=False)

    return str(sidecar_path)
