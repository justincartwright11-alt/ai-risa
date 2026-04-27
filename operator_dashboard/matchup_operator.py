"""
Matchup Operator Module

Core operator workflow for single-matchup analysis:
1. Parse matchup input
2. Resolve fighters
3. Build/export premium report
4. Compare with real result
5. Run calibration review
"""
import json
import re
import subprocess
import sys
import os
import unicodedata
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Set
from operator_dashboard.fighter_auto_intake import auto_intake_missing_fighters
from operator_dashboard.report_scoring import ReportScorer
from operator_dashboard.real_result_searcher import RealResultSearcher
from operator_dashboard.calibration_review import CalibrationReviewGenerator
from operator_dashboard.premium_sidecar_generator import generate_or_refresh_sidecar


class MatchupOperator:
    """Orchestrates the full matchup analysis workflow"""
    
    def __init__(self, ai_risa_data_path: str = "c:/ai_risa_data"):
        self.ai_risa_data_path = Path(ai_risa_data_path)
        self.matchups_dir = self.ai_risa_data_path / "matchups"
        self.reports_dir = self.ai_risa_data_path / "reports"
        self.fighters_dir = self.ai_risa_data_path / "fighters"
        
        self.scorer = ReportScorer(ai_risa_data_path)
        self.result_searcher = RealResultSearcher(ai_risa_data_path)
        self.calibration_generator = CalibrationReviewGenerator(ai_risa_data_path)
    
    def parse_matchup_input(self, user_input: str) -> Optional[Tuple[str, str]]:
        """
        Parse matchup from user input like 'Tim Tszyu vs Errol Spence Jr.'
        
        Returns: (fighter_a, fighter_b) or None if parsing fails
        """
        # Try "X vs Y" format
        vs_pattern = r"^(.+?)\s+vs\.?\s+(.+)$"
        match = re.match(vs_pattern, user_input, re.IGNORECASE)
        
        if match:
            fighter_a = match.group(1).strip()
            fighter_b = match.group(2).strip()
            return (fighter_a, fighter_b)
        
        return None
    
    def normalize_fighter_names(self, fighter_a: str, fighter_b: str) -> Tuple[str, str]:
        """
        Normalize fighter names:
        - Remove annotations like (#5), (Champion), (Interim)
        - Clean whitespace
        - Standardize capitalization
        """
        def clean_name(name: str) -> str:
            # Remove bracket annotations
            name = re.sub(r'\s*\([^)]*(?:champion|interim|title|ranked|#\d+)[^)]*\)', '', name, flags=re.IGNORECASE)
            name = re.sub(r'\s*\(#?\d+\)', '', name)
            return name.strip().title()
        
        return (clean_name(fighter_a), clean_name(fighter_b))
    
    def resolve_fighter_slugs(self, fighter_a: str, fighter_b: str, sport: str = "mma") -> Tuple[str, str]:
        """
        Resolve canonical fighter slugs from known fighter registry and aliases.
        Bare surname input is never treated as canonical slug by default.
        
        Returns: (slug_a, slug_b)
        """
        registry, alias_to_slugs = self._build_fighter_registry()
        if not registry:
            raise ValueError("Fighter registry is empty; cannot resolve matchup safely.")

        fighter_a_clean = self._normalize_human_text(fighter_a)
        slug_a, suggestions_a = self._resolve_known_fighter_slug(fighter_a, registry, alias_to_slugs)
        if not slug_a:
            if self._is_single_token_name(fighter_a_clean) and not suggestions_a:
                raise ValueError(f"Need full fighter name: {fighter_a}")
            suggestion_text = f". Suggested candidates: {', '.join(suggestions_a)}" if suggestions_a else ""
            raise ValueError(f"Ambiguous fighter name: {fighter_a}{suggestion_text}")

        fighter_b_clean = self._normalize_human_text(fighter_b)
        slug_b, suggestions_b = self._resolve_known_fighter_slug(fighter_b, registry, alias_to_slugs)
        if not slug_b:
            if self._is_single_token_name(fighter_b_clean) and not suggestions_b:
                raise ValueError(f"Need full fighter name: {fighter_b}")
            suggestion_text = f". Suggested candidates: {', '.join(suggestions_b)}" if suggestions_b else ""
            raise ValueError(f"Ambiguous fighter name: {fighter_b}{suggestion_text}")

        self._assert_canonical_slug(slug_a, fighter_a)
        self._assert_canonical_slug(slug_b, fighter_b)
        return (slug_a, slug_b)

    def _normalize_human_text(self, value: str) -> str:
        folded = unicodedata.normalize("NFKD", value or "")
        ascii_value = folded.encode("ascii", "ignore").decode("ascii")
        ascii_value = ascii_value.lower()
        ascii_value = re.sub(r"[^a-z0-9\s]", " ", ascii_value)
        ascii_value = re.sub(r"\s+", " ", ascii_value).strip()
        return ascii_value

    def _build_fighter_registry(self) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Set[str]]]:
        registry: Dict[str, Dict[str, Any]] = {}
        alias_to_slugs: Dict[str, Set[str]] = {}

        if not self.fighters_dir.exists():
            return registry, alias_to_slugs

        for profile_path in self.fighters_dir.glob("*.json"):
            if profile_path.name in {"manual_profile_enrichment.json", "tba.json"}:
                continue

            base = profile_path.stem.lower()
            canonical_slug = base[8:] if base.startswith("fighter_") else base
            canonical_slug = self._slugify(canonical_slug)
            if not canonical_slug:
                continue
            if self._is_weak_slug(canonical_slug):
                # Do not treat weak surname-only artifacts as canonical fighter IDs.
                continue

            display_name = canonical_slug.replace("_", " ").title()
            try:
                with open(profile_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if isinstance(payload, dict) and payload.get("name"):
                    display_name = str(payload.get("name")).strip()
            except Exception:
                pass

            existing = registry.get(canonical_slug)
            prefer_current = existing is None or not base.startswith("fighter_")
            if prefer_current:
                registry[canonical_slug] = {
                    "slug": canonical_slug,
                    "display_name": display_name,
                    "profile_path": str(profile_path),
                }

        def _add_alias(alias_value: str, slug_value: str) -> None:
            key = self._normalize_human_text(alias_value)
            if not key:
                return
            alias_to_slugs.setdefault(key, set()).add(slug_value)

        for slug, item in registry.items():
            display_name = item["display_name"]
            tokens = [t for t in self._normalize_human_text(display_name).split(" ") if t]
            _add_alias(slug.replace("_", " "), slug)
            _add_alias(display_name, slug)
            if tokens:
                _add_alias(tokens[0], slug)
                _add_alias(tokens[-1], slug)
                if len(tokens) >= 2:
                    _add_alias(" ".join(tokens[-2:]), slug)

        # Include names used in recent successful matchup records as additional aliases.
        if self.matchups_dir.exists():
            for matchup_path in self.matchups_dir.glob("*.json"):
                if matchup_path.name.endswith("_premium_sections.json"):
                    continue
                try:
                    with open(matchup_path, "r", encoding="utf-8") as handle:
                        matchup = json.load(handle)
                except Exception:
                    continue
                if not isinstance(matchup, dict):
                    continue

                fighter_ids = [
                    str(matchup.get("fighter_a_id") or "").lower(),
                    str(matchup.get("fighter_b_id") or "").lower(),
                ]
                fighter_names = matchup.get("fighters") or []
                if len(fighter_names) != 2:
                    continue

                for idx in range(2):
                    fighter_id = fighter_ids[idx]
                    fighter_name = str(fighter_names[idx] or "").strip()
                    if not fighter_id.startswith("fighter_"):
                        continue
                    slug = self._slugify(fighter_id[8:])
                    if slug in registry and fighter_name:
                        _add_alias(fighter_name, slug)

        return registry, alias_to_slugs

    def _resolve_known_fighter_slug(
        self,
        fighter_name: str,
        registry: Dict[str, Dict[str, Any]],
        alias_to_slugs: Dict[str, Set[str]],
    ) -> Tuple[Optional[str], List[str]]:
        cleaned = self._normalize_human_text(fighter_name)
        if not cleaned:
            return None, []

        direct = sorted(alias_to_slugs.get(cleaned, set()))
        if len(direct) == 1 and direct[0] in registry:
            return direct[0], []
        if len(direct) > 1:
            suggestions = []
            for slug in direct:
                if slug in registry:
                    name = registry[slug]["display_name"]
                    if name not in suggestions:
                        suggestions.append(name)
                if len(suggestions) >= 6:
                    break
            return None, suggestions

        query_tokens = [t for t in cleaned.split(" ") if t]
        partial_matches: List[str] = []
        for slug, item in registry.items():
            candidate_tokens = set(slug.split("_")) | set(self._normalize_human_text(item["display_name"]).split(" "))
            if query_tokens and all(token in candidate_tokens for token in query_tokens):
                partial_matches.append(slug)

        partial_matches = sorted(set(partial_matches))
        if len(partial_matches) == 1 and partial_matches[0] in registry:
            return partial_matches[0], []
        if partial_matches:
            suggestions = []
            for slug in partial_matches:
                if slug in registry:
                    name = registry[slug]["display_name"]
                    if name not in suggestions:
                        suggestions.append(name)
                if len(suggestions) >= 6:
                    break
            return None, suggestions

        # Explicitly block fallback to weak surname-only artifacts like fighter_sterling.
        return None, []

    def _is_weak_slug(self, slug: str) -> bool:
        tokens = [t for t in (slug or "").split("_") if t]
        if len(tokens) < 2:
            return True
        weak_artifacts = {"fighter", "unknown", "tba", "na", "none"}
        return any(t in weak_artifacts for t in tokens)

    def _is_single_token_name(self, normalized_name: str) -> bool:
        tokens = [t for t in (normalized_name or "").split(" ") if t]
        return len(tokens) == 1

    def _assert_canonical_slug(self, slug: str, raw_name: str) -> None:
        if self._is_weak_slug(slug):
            raise ValueError(f"Ambiguous fighter name: {raw_name}. Suggested candidates: use full fighter name.")
    
    def _slugify(self, name: str) -> str:
        """Convert name to slug"""
        folded = unicodedata.normalize("NFKD", name or "")
        ascii_name = folded.encode("ascii", "ignore").decode("ascii")
        slug = ascii_name.lower().replace(" ", "_").replace("-", "_")
        slug = re.sub(r"[^a-z0-9_]+", "_", slug)
        slug = re.sub(r"_+", "_", slug).strip("_")
        return slug
    
    def ensure_matchup_record(self, slug_a: str, slug_b: str, sport: str = "mma") -> str:
        """
        Ensure matchup record exists.
        
        Returns: matchup filename
        """
        matchup_slug = self._create_matchup_slug(slug_a, slug_b)
        matchup_file = self.matchups_dir / f"{matchup_slug}.json"
        
        if not matchup_file.exists():
            matchup_data = {
                "fight_id": matchup_slug,
                "event": matchup_slug,
                "event_date": "Date TBD",
                "fighters": [slug_a.replace("_", " ").title(), slug_b.replace("_", " ").title()],
                "fighter_a_id": f"fighter_{slug_a}",
                "fighter_b_id": f"fighter_{slug_b}",
                "sport": sport,
                "ruleset": "unified",
                "report_ready": True,
                "profile_gaps": [],
                "notes": "Created by operator matchup input.",
            }
            matchup_file.parent.mkdir(parents=True, exist_ok=True)
            with open(matchup_file, "w", encoding="utf-8") as f:
                json.dump(matchup_data, f, indent=2)
        
        return matchup_slug
    
    def _create_matchup_slug(self, slug_a: str, slug_b: str) -> str:
        """Create matchup slug from fighter slugs"""
        return f"{slug_a}_vs_{slug_b}"

    def _sidecar_is_deep_quality(self, sidecar_path: Path) -> bool:
        """Quality gate for premium sidecar depth to prevent generic fallback content."""
        if not sidecar_path.exists():
            return False

        try:
            with open(sidecar_path, "r", encoding="utf-8") as f:
                sidecar = json.load(f)
        except Exception:
            return False

        required_sections = [
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

        disallowed_tokens = [
            "[primary strength]",
            "{a}",
            "{b}",
            "{{a}}",
            "{{b}}",
        ]

        for section in required_sections:
            text = str(sidecar.get(section) or "")
            if len(text.strip()) < 320:
                return False
            lowered = text.lower()
            if any(token in text for token in disallowed_tokens):
                return False
            if "both fighters are skilled" in lowered:
                return False

        return True

    def _sidecar_is_reusable(self, sidecar_path: Path) -> bool:
        """
        Decide whether an existing sidecar should be reused as authoritative.

        Reuse policy is intentionally broader than deep-generation quality gate:
        if a sidecar exists and is not obviously broken/placeholder, prefer reuse
        over regeneration.
        """
        if not sidecar_path.exists():
            return False

        try:
            with open(sidecar_path, "r", encoding="utf-8") as f:
                sidecar = json.load(f)
        except Exception:
            return False

        if not isinstance(sidecar, dict):
            return False

        required_sections = [
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

        placeholder_tokens = [
            "[primary strength]",
            "{a}",
            "{b}",
            "{{a}}",
            "{{b}}",
            "analysis not available",
            "not available",
            "tba",
        ]

        present_sections = 0
        min_length_failures = 0
        for section in required_sections:
            text = str(sidecar.get(section) or "").strip()
            if not text:
                continue
            present_sections += 1

            lowered = text.lower()
            if any(token in lowered for token in placeholder_tokens):
                return False

            # "Obviously weak" threshold only; deep-quality threshold remains stricter.
            if len(text) < 80:
                min_length_failures += 1

        if present_sections < 14:
            return False
        if min_length_failures > 6:
            return False

        return True

    def _load_profile(self, profile_path: Path) -> Optional[Dict[str, Any]]:
        if not profile_path.exists():
            return None
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    def _profile_is_sufficient(self, profile: Dict[str, Any]) -> bool:
        def _clean(v: Any) -> str:
            return str(v or "").strip()

        def _is_bad(v: str) -> bool:
            lowered = v.lower()
            return lowered in {"", "unknown", "n/a", "na", "tbd", "none"}

        name = _clean(profile.get("name"))
        sport = _clean(profile.get("sport"))
        style = _clean(profile.get("style"))
        stance = _clean(profile.get("stance"))
        notes = _clean(profile.get("notes"))

        if _is_bad(name) or _is_bad(sport):
            return False
        if _is_bad(style) and _is_bad(stance) and len(notes) < 40:
            return False
        return True

    def _ensure_profiles_ready(
        self,
        fighter_a: str,
        fighter_b: str,
        slug_a: str,
        slug_b: str,
        sport: str,
    ) -> Tuple[bool, list]:
        """
        Ensure both fighter profiles exist and are strong enough for report analysis.
        Performs one retry auto-intake if missing/weak.
        """
        failures = []

        targets = [
            (fighter_a, slug_a),
            (fighter_b, slug_b),
        ]

        def _profile_path_for_slug(slug: str) -> Path:
            return self.fighters_dir / f"fighter_{slug}.json"

        # First pass assessment.
        missing_or_weak = []
        for fighter_name, slug in targets:
            profile_path = _profile_path_for_slug(slug)
            profile = self._load_profile(profile_path)
            if not profile:
                missing_or_weak.append({"name": fighter_name, "slug": slug, "sport": sport})
                continue
            if not self._profile_is_sufficient(profile):
                missing_or_weak.append({"name": fighter_name, "slug": slug, "sport": sport})

        # Retry auto-intake for missing/weak profiles.
        if missing_or_weak:
            try:
                auto_intake_missing_fighters(missing_or_weak, str(self.ai_risa_data_path))
            except Exception as intake_err:
                failures.append(f"Auto-intake retry failed: {intake_err}")

        # Final sufficiency pass.
        for fighter_name, slug in targets:
            profile_path = _profile_path_for_slug(slug)
            profile = self._load_profile(profile_path)
            if not profile:
                failures.append(f"Missing fighter profile after intake: fighter_{slug}.json ({fighter_name})")
                continue
            if not self._profile_is_sufficient(profile):
                failures.append(f"Fighter profile too weak for analysis: fighter_{slug}.json ({fighter_name})")

        return (len(failures) == 0, failures)

    def _build_usable_fallback_sidecar(
        self,
        matchup_slug: str,
        fighter_a: str,
        fighter_b: str,
        sport: str,
        reason: str,
    ) -> Path:
        """
        Build a readable, non-placeholder v4 fallback sidecar when deep generation is not viable.
        This path is intentionally non-fatal for new fights with sufficient fighter data.
        """
        sport_label = (sport or "mma").strip().lower()
        if sport_label not in {"mma", "boxing", "kickboxing", "muay thai", "muay_thai"}:
            sport_label = "mma"

        if sport_label == "boxing":
            control_axis = "jab lane ownership, pocket entries, and body-work pacing"
            phase_terms = "ring geography and reset timing"
        elif sport_label in {"kickboxing", "muay thai", "muay_thai"}:
            control_axis = "kick range command, rhythm disruption, and balance checks"
            phase_terms = "open-space geometry and visible scoring optics"
        else:
            control_axis = "entry safety, transition control, and reset denial"
            phase_terms = "cage geography and phase chaining"

        sections = {
            "executive_summary": (
                f"This v4 operator fallback report was built because deep sidecar generation did not pass the premium depth gate on first pass. "
                f"The fight between {fighter_a} and {fighter_b} is framed as a control battle over {control_axis}. "
                f"The expected winner is the fighter who can repeatedly win transition beats while preserving structure under fatigue. "
                f"This fallback keeps the report usable, readable, and sport-specific while preserving non-placeholder decision logic."
            ),
            "matchup_snapshot": (
                f"{fighter_a} vs {fighter_b} projects as a high-information tactical collision defined by {phase_terms}. "
                f"Early minutes should reveal who owns first-contact exchanges and who can convert those moments into repeatable control. "
                f"This snapshot is built for operator use, emphasizing interaction patterns rather than generic trait lists."
            ),
            "decision_structure": (
                f"Decision structure in this matchup is shaped by risk pricing after first contact. "
                f"{fighter_a} needs repeatable entries that preserve defensive integrity, while {fighter_b} needs denial timing that forces clean resets. "
                f"Whichever side keeps making decisions from preferred phase wins middle-round momentum."
            ),
            "tactical_edges": (
                f"The tactical edge for either side comes from controlling the same transition problem repeatedly. "
                f"If {fighter_a} can force continuation phases, pressure compounds. If {fighter_b} can interrupt those continuations, scoring stays cleaner. "
                f"The fight is decided less by single highlights and more by repeatable control outcomes."
            ),
            "energy_use": (
                f"Energy economics in this fight are tied to successful conversion versus wasted effort. "
                f"Failed access attempts increase cost quickly, while clean reset cycles preserve output quality. "
                f"Late-fight control usually belongs to the side spending less energy on maintenance work."
            ),
            "fatigue_failure_points": (
                f"Fatigue failure points are most likely to appear when one fighter cannot restore preferred geometry for multiple exchanges. "
                f"If {fighter_a} is repeatedly denied access, precision declines. If {fighter_b} is repeatedly forced into high-friction defense, reset quality drops. "
                f"The fighter who protects first failure point longer has a strong late-round advantage."
            ),
            "mental_condition": (
                f"Mental condition projects through adaptability under adversity. "
                f"Composure is tested when expected sequencing fails and tactical adjustments must happen in real time. "
                f"The side that adapts without abandoning structure will usually carry momentum through the decisive rounds."
            ),
            "collapse_triggers": (
                f"Collapse triggers in this matchup are state-based rather than single-event based. "
                f"Repeated failed entries can collapse initiative, while repeated positional concessions can collapse control. "
                f"The first side forced into reactive maintenance for two rounds is at elevated upset risk."
            ),
            "deception_unpredictability": (
                f"Deception quality should be judged by whether it changes opponent decision timing. "
                f"Both {fighter_a} and {fighter_b} can gain edge by disguising phase intention long enough to force premature defensive commits. "
                f"Unpredictability matters most in transitions, where one hidden beat can decide the exchange."
            ),
            "fight_control": (
                f"Fight control is ownership of restart conditions. "
                f"In this matchup, control means deciding where exchanges happen and whether they extend or reset. "
                f"The side winning more transition resets per round is most likely to win decision optics and late-fight command."
            ),
            "fight_turns": (
                f"The likely turn window is the middle segment of the fight, where reads and fatigue begin to interact. "
                f"If one side starts solving the same transition problem repeatedly, momentum can flip quickly and stay flipped. "
                f"Late rounds then reward structural consistency more than isolated highlights."
            ),
            "scenario_tree": (
                f"Scenario A: {fighter_a} wins transition ownership and compounds control into clear round margins. "
                f"Scenario B: {fighter_b} repeatedly interrupts continuation phases and keeps the fight in clean scoring structure. "
                f"Scenario C: split-phase rounds create a close scorecard decided by closing sequences and control optics."
            ),
            "round_by_round_outlook": (
                f"Early phase should be information-heavy with both fighters testing entries, denials, and reset timing. "
                f"Middle phase is the tactical core, where repetition patterns reveal true control ownership. "
                f"Late phase rewards whichever side preserved efficiency and protected collapse points."
            ),
            "risk_factors": (
                f"Primary risk for both sides is becoming predictable in transition. "
                f"Predictable access attempts get punished, and predictable exits get trapped. "
                f"A second risk is judging volatility in close split-phase rounds where final-minute control matters disproportionately."
            ),
            "what_could_flip": (
                f"The primary flip event is sustained control denial by the projected leader for two rounds, forcing strategic overcorrection. "
                f"Secondary flip event is subtle functional degradation, such as slower exits or delayed re-centering, that changes control flow. "
                f"Either event can move the fight from expected script to opportunistic momentum logic."
            ),
            "corner_notes": (
                f"{fighter_a} corner should prioritize repeatable entries, efficient continuation, and controlled risk escalation. "
                f"{fighter_b} corner should prioritize denial timing, clean resets, and immediate punishment of predictable re-entries. "
                f"Both corners should track transition wins per minute as the core tactical KPI."
            ),
            "final_projection": (
                f"Final projection in fallback mode remains a control-based outcome between {fighter_a} and {fighter_b}, "
                f"with the expected winner being the side that sustains preferred phase ownership longer. "
                f"This preserves a usable premium-v4 output path while waiting for optional deeper narrative regeneration."
            ),
            "confidence_explanation": (
                f"Confidence is moderate in fallback mode because deep narrative generation was not accepted on first pass ({reason}). "
                f"Even so, fighter data was sufficient to produce a valid, non-placeholder operator-safe report. "
                f"Confidence would increase with richer enrichment and a successful deep_v4 sidecar refresh."
            ),
            "disclaimer": (
                "This report is an AI-RISA tactical intelligence assessment based on available style, profile, and process signals. "
                "It is probabilistic rather than certain and should be used as a decision-support document, not as a guarantee of outcome."
            ),
            "_meta": {
                "generated_by": "premium_sidecar_generator_v4_usable_fallback",
                "fallback_mode": "usable_v4_fallback",
                "fallback_reason": str(reason),
                "matchup_slug": matchup_slug,
            },
        }

        sidecar_path = self.matchups_dir / f"{matchup_slug}_premium_sections.json"
        with open(sidecar_path, "w", encoding="utf-8") as f:
            json.dump(sections, f, indent=2, ensure_ascii=False)
        return sidecar_path
    
    def build_premium_report(
        self,
        fighter_a: str,
        fighter_b: str,
        sport: str = "mma"
    ) -> Dict[str, Any]:
        """
        Build and export premium report for matchup using the real report runner.
        
        Workflow:
        1. Normalize fighter names
        2. Resolve fighter slugs (auto-intake if needed)
        3. Create/ensure matchup record
        4. Generate or refresh v4-depth premium sidecar
        5. Call real premium report runner
        6. Verify PDF creation and QA
        
        Returns:
        {
            'ok': bool,
            'matchup_slug': str,
            'files_written': [str],
            'output_pdf_path': str,
            'qa_pass': bool,
            'errors': [str],
        }
        """
        try:
            # Normalize names
            fighter_a, fighter_b = self.normalize_fighter_names(fighter_a, fighter_b)
            
            # Resolve slugs
            slug_a, slug_b = self.resolve_fighter_slugs(fighter_a, fighter_b, sport)

            # Fail only when fighter data is truly too weak.
            profiles_ok, profile_errors = self._ensure_profiles_ready(fighter_a, fighter_b, slug_a, slug_b, sport)
            if not profiles_ok:
                return {
                    "ok": False,
                    "matchup_slug": self._create_matchup_slug(slug_a, slug_b),
                    "files_written": [],
                    "output_pdf_path": None,
                    "qa_pass": False,
                    "errors": profile_errors,
                }
            
            # Ensure matchup record
            matchup_slug = self.ensure_matchup_record(slug_a, slug_b, sport)
            sidecar_path = self.matchups_dir / f"{matchup_slug}_premium_sections.json"
            
            # Reuse an existing good sidecar first. Only generate when missing/obviously weak.
            if not self._sidecar_is_reusable(sidecar_path):
                sidecar_err_message = None
                try:
                    generate_or_refresh_sidecar(
                        matchup_slug,
                        fighter_a,
                        fighter_b,
                        str(self.ai_risa_data_path)
                    )

                    # Hard quality gate only applies in generation path.
                    if not self._sidecar_is_deep_quality(sidecar_path):
                        # Try one forced regeneration pass.
                        from operator_dashboard.premium_sidecar_generator import PremiumSidecarGenerator

                        generator = PremiumSidecarGenerator(str(self.ai_risa_data_path))
                        sections = generator.generate_sections(matchup_slug, fighter_a, fighter_b)
                        if not sections:
                            raise RuntimeError("Unable to generate deep premium sidecar sections")

                        sections["_meta"] = {
                            "generated_by": "premium_sidecar_generator_v4_quality",
                            "matchup_slug": matchup_slug,
                        }
                        with open(sidecar_path, "w", encoding="utf-8") as sidecar_file:
                            json.dump(sections, sidecar_file, indent=2, ensure_ascii=False)

                    if not self._sidecar_is_deep_quality(sidecar_path):
                        raise RuntimeError("Premium sidecar did not meet deep-quality threshold")

                except Exception as sidecar_err:
                    sidecar_err_message = f"Sidecar generation failed quality gate: {sidecar_err}"

                # Non-fatal fallback path for new fights with sufficient fighter data.
                if not self._sidecar_is_deep_quality(sidecar_path):
                    fallback_reason = sidecar_err_message or "Deep sidecar did not reach v4 quality threshold"
                    try:
                        self._build_usable_fallback_sidecar(matchup_slug, fighter_a, fighter_b, sport, fallback_reason)
                    except Exception as fallback_err:
                        return {
                            "ok": False,
                            "matchup_slug": matchup_slug,
                            "files_written": [],
                            "output_pdf_path": None,
                            "qa_pass": False,
                            "errors": [
                                fallback_reason,
                                f"Fallback sidecar generation failed: {fallback_err}",
                            ],
                        }

                    if not self._sidecar_is_reusable(sidecar_path):
                        return {
                            "ok": False,
                            "matchup_slug": matchup_slug,
                            "files_written": [],
                            "output_pdf_path": None,
                            "qa_pass": False,
                            "errors": [
                                fallback_reason,
                                "Fallback sidecar did not meet reusable threshold",
                            ],
                        }
            
            # Define paths
            matchup_json_path = str(self.matchups_dir / f"{matchup_slug}.json")
            report_pdf_path = f"reports/{matchup_slug}_premium_v4.pdf"
            
            # Call the real premium report runner
            cmd = [
                sys.executable,
                "run_single_fight_premium_report.py",
                "--matchup",
                matchup_json_path,
                "--output",
                report_pdf_path,
            ]
            
            proc = subprocess.run(
                cmd,
                cwd=str(self.ai_risa_data_path),
                capture_output=True,
                text=True,
                timeout=180
            )
            
            output = (proc.stdout or "") + (proc.stderr or "")
            qa_pass = "QA: PASS" in output
            file_exists = os.path.exists(os.path.join(str(self.ai_risa_data_path), report_pdf_path))
            success = proc.returncode == 0 and file_exists and (qa_pass or "[SUCCESS] Premium PDF report exported to:" in output)
            
            # Get the full path to the created file
            full_output_path = os.path.join(str(self.ai_risa_data_path), report_pdf_path)
            
            if success:
                return {
                    "ok": True,
                    "matchup_slug": matchup_slug,
                    "files_written": [full_output_path],
                    "output_pdf_path": full_output_path,
                    "qa_pass": True,
                    "errors": [],
                }
            else:
                # Collect error details
                errors = []
                if proc.returncode != 0:
                    errors.append(f"Report runner failed with code {proc.returncode}")
                if not file_exists:
                    errors.append(f"PDF file not created at {full_output_path}")
                if not qa_pass:
                    errors.append("QA check failed")
                if proc.stderr:
                    errors.append(f"Stderr: {proc.stderr[:200]}")
                
                return {
                    "ok": False,
                    "matchup_slug": matchup_slug,
                    "files_written": [],
                    "output_pdf_path": full_output_path,
                    "qa_pass": False,
                    "errors": errors or ["Report export failed"],
                }
        
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "matchup_slug": None,
                "files_written": [],
                "output_pdf_path": None,
                "qa_pass": False,
                "errors": ["Report export timed out (exceeded 180 seconds)"],
            }
        
        except Exception as e:
            return {
                "ok": False,
                "matchup_slug": None,
                "files_written": [],
                "output_pdf_path": None,
                "qa_pass": False,
                "errors": [str(e)],
            }
    
    def compare_with_real_result(
        self,
        fighter_a: str,
        fighter_b: str,
        sport: str = "mma"
    ) -> Dict[str, Any]:
        """
        Search for real fight result and compare.
        
        Returns:
        {
            'ok': bool,
            'result_found': bool,
            'result': {...} or None,
            'score': {...} or None,
            'confidence_blocker': str or None,
            'errors': [str],
        }
        """
        try:
            # Normalize names
            fighter_a, fighter_b = self.normalize_fighter_names(fighter_a, fighter_b)
            
            # Search for real result
            search_result = self.result_searcher.search_for_result(fighter_a, fighter_b, sport)
            
            if not search_result.get("found"):
                return {
                    "ok": True,
                    "result_found": False,
                    "result": None,
                    "score": None,
                    "confidence_blocker": search_result.get("confidence_blocker"),
                    "message": search_result.get("note"),
                    "errors": [],
                }
            
            # Load premium report for scoring
            slug_a = self._slugify(fighter_a)
            slug_b = self._slugify(fighter_b)
            matchup_slug = self._create_matchup_slug(slug_a, slug_b)
            sidecar_path = self.matchups_dir / f"{matchup_slug}_premium_sections.json"
            
            if not sidecar_path.exists():
                return {
                    "ok": False,
                    "result_found": True,
                    "result": search_result.get("result"),
                    "score": None,
                    "confidence_blocker": "Premium sidecar not found",
                    "errors": [f"Sidecar not found at {sidecar_path}"],
                }
            
            # Load report
            with open(sidecar_path, "r", encoding="utf-8") as f:
                report_dict = json.load(f)
            
            # Score report
            result = search_result.get("result", {})
            score = self.scorer.score_report(
                report_dict=report_dict,
                actual_winner=result.get("winner", ""),
                actual_method=result.get("method", ""),
                actual_round=result.get("round", 5),
                fighter_a=fighter_a,
                fighter_b=fighter_b,
                control_pattern="grappling",  # Would be detected from fighters
            )
            
            return {
                "ok": True,
                "result_found": True,
                "result": result,
                "score": score,
                "confidence_blocker": None,
                "errors": [],
            }
        
        except Exception as e:
            return {
                "ok": False,
                "result_found": False,
                "result": None,
                "score": None,
                "confidence_blocker": str(e),
                "errors": [str(e)],
            }
    
    def run_calibration_review(self) -> Dict[str, Any]:
        """
        Run calibration review on full ledger.
        
        Returns calibration review result (see calibration_review.py)
        """
        try:
            return self.calibration_generator.generate_calibration_review()
        except Exception as e:
            return {
                "timestamp": None,
                "fights_analyzed": 0,
                "miss_patterns": {},
                "proposed_calibrations": [],
                "backtest_summary": {},
                "confidence_in_calibration": 0,
                "approval_required": True,
                "recommendation": f"Error generating calibration review: {str(e)}",
            }
