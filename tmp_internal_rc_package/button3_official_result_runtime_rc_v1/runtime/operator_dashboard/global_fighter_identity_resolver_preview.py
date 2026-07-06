"""
Global Fighter Identity Resolver — Preview Scaffold.

Preview-only deterministic fighter identity matching engine.
No permanent writes, merges, or profile updates.
All match recommendations are preview evidence only.

Status: Preview scaffold, fail-closed, no side effects.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Tuple
import json
from enum import Enum


class ConfidenceTier(Enum):
    """Identity match confidence tiers."""
    EXACT_MATCH = "exact_match"
    STRONG_ALIAS_MATCH = "strong_alias_match"
    LIKELY_SAME_FIGHTER = "likely_same_fighter"
    POSSIBLE_DUPLICATE = "possible_duplicate"
    CONFLICT_MANUAL_REVIEW = "conflict_manual_review"
    NO_MATCH = "no_match"


@dataclass
class SourceRef:
    """Source provenance for identity evidence."""
    source_name: str
    source_url: Optional[str] = None
    source_type: str = "unknown"  # official, secondary, user, operator
    source_date: Optional[str] = None


@dataclass
class IncomingFighterCandidate:
    """Incoming fighter identity candidate to resolve."""
    name: str
    aliases: List[str] = field(default_factory=list)
    nationality: Optional[str] = None
    promotion: Optional[str] = None
    sport_ruleset: Optional[str] = None
    division: Optional[str] = None
    date_of_birth: Optional[str] = None
    height: Optional[str] = None
    reach: Optional[str] = None
    stance: Optional[str] = None
    record: Optional[Dict] = None  # {wins, losses, draws}
    source_refs: List[SourceRef] = field(default_factory=list)


@dataclass
class KnownFighterRecord:
    """Known global fighter record (in-memory)."""
    fighter_global_id: str
    full_name: str
    known_aliases: List[str] = field(default_factory=list)
    nationality: Optional[str] = None
    promotion: Optional[str] = None
    sport_ruleset: Optional[str] = None
    division: Optional[str] = None
    date_of_birth: Optional[str] = None
    height: Optional[str] = None
    reach: Optional[str] = None
    stance: Optional[str] = None
    record: Optional[Dict] = None
    active_years: Optional[Tuple[int, int]] = None  # (start, end)
    confidence_grade: str = "C"  # A/B/C/D/F


@dataclass
class MatchEvidence:
    """Evidence for a candidate match."""
    matching_fields: List[str] = field(default_factory=list)
    conflicting_fields: List[str] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class CandidateMatch:
    """Candidate global fighter match result."""
    fighter_global_id: str
    full_name: str
    confidence_tier: ConfidenceTier
    confidence_score: float
    evidence: MatchEvidence = field(default_factory=MatchEvidence)
    rank: int = 0


@dataclass
class IdentityResolutionResult:
    """Preview-only identity resolution result."""
    # Input echo
    incoming_candidate: IncomingFighterCandidate

    # Match results
    candidate_matches: List[CandidateMatch] = field(default_factory=list)
    conflict_type: Optional[str] = None  # same_name, source_conflict, incomplete_evidence, new_fighter
    manual_review_required: bool = False
    recommendation: str = ""

    # Safety flags (all no-op)
    preview_only: bool = True
    profile_create_performed: bool = False
    profile_update_performed: bool = False
    merge_performed: bool = False
    database_write_performed: bool = False
    ranking_write_performed: bool = False
    learning_apply_performed: bool = False
    calibration_write_performed: bool = False

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        result = asdict(self)
        # Serialize enums
        result["candidate_matches"] = [
            {
                **asdict(m),
                "confidence_tier": m.confidence_tier.value,
            }
            for m in self.candidate_matches
        ]
        result["incoming_candidate"] = asdict(self.incoming_candidate)
        result["incoming_candidate"]["source_refs"] = [
            asdict(sr) for sr in self.incoming_candidate.source_refs
        ]
        return result

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)


def _levenshtein_distance(s1: str, s2: str) -> float:
    """Calculate Levenshtein similarity (0.0-1.0)."""
    if not s1 or not s2:
        return 0.0
    if s1.lower() == s2.lower():
        return 1.0

    len1, len2 = len(s1), len(s2)
    if len1 > len2:
        s1, s2 = s2, s1
        len1, len2 = len2, len1

    current = range(len1 + 1)
    for i in range(1, len2 + 1):
        prev = current
        current = [i] + [0] * len1
        for j in range(1, len1 + 1):
            add = prev[j] + 1
            delete = current[j - 1] + 1
            sub = prev[j - 1] + (s1[j - 1] != s2[j - 1])
            current[j] = min(add, delete, sub)

    distance = current[len1]
    max_len = max(len(s1), len(s2))
    similarity = 1.0 - (distance / max_len)
    return max(0.0, similarity)


def _check_name_match(incoming_name: str, known_name: str, aliases: List[str]) -> Tuple[bool, float]:
    """Check if names match exactly or via alias. Returns (is_match, similarity)."""
    # Exact match
    if incoming_name.lower() == known_name.lower():
        return True, 1.0

    # Alias match
    for alias in aliases:
        if incoming_name.lower() == alias.lower():
            return True, 1.0

    # Similarity
    sim = _levenshtein_distance(incoming_name, known_name)
    return sim > 0.85, sim


def _check_evidence_completeness(candidate: IncomingFighterCandidate) -> Tuple[bool, List[str]]:
    """Check if evidence is complete. Returns (is_complete, missing_fields)."""
    missing = []
    if not candidate.nationality:
        missing.append("nationality")
    if not candidate.date_of_birth:
        missing.append("date_of_birth")
    if not candidate.promotion:
        missing.append("promotion")
    if not candidate.division:
        missing.append("division")
    return len(missing) <= 1, missing


def resolve_fighter_identity_preview(
    candidate: IncomingFighterCandidate,
    known_fighters: List[KnownFighterRecord],
) -> IdentityResolutionResult:
    """
    Preview-only fighter identity resolution.

    Matches incoming candidate to known global fighters with confidence assessment.
    No permanent writes, merges, or profile updates.
    All results are preview evidence only.

    Args:
        candidate: Incoming fighter identity candidate
        known_fighters: Known global fighter records (in-memory)

    Returns:
        IdentityResolutionResult with match evidence and no-op write flags
    """
    result = IdentityResolutionResult(incoming_candidate=candidate)

    # Fail closed: require source provenance
    if not candidate.source_refs:
        result.manual_review_required = True
        result.conflict_type = "missing_source_provenance"
        result.recommendation = "Cannot resolve without source provenance. Escalate to manual review."
        return result

    # No known fighters: new fighter candidate
    if not known_fighters:
        result.manual_review_required = True
        result.conflict_type = "new_fighter"
        result.recommendation = (
            "No matching global fighters found. Queue for operator review and global database entry."
        )
        return result

    # Phase 1: Collect candidate matches
    candidate_matches: List[CandidateMatch] = []

    for known in known_fighters:
        # Name matching (exact or alias)
        name_match, name_sim = _check_name_match(candidate.name, known.full_name, known.known_aliases)

        if not name_match:
            continue  # Skip non-matching names

        # Evidence collection
        evidence = MatchEvidence()
        confidence_score = 0.0

        # Tier 1: Exact match on core fields
        if (
            candidate.name.lower() == known.full_name.lower()
            and candidate.nationality == known.nationality
            and candidate.date_of_birth == known.date_of_birth
        ):
            evidence.matching_fields = ["name", "nationality", "date_of_birth"]
            confidence_tier = ConfidenceTier.EXACT_MATCH
            confidence_score = 0.95
        # Tier 2: Strong alias match
        elif (
            name_sim > 0.85
            and candidate.nationality == known.nationality
            and candidate.division == known.division
        ):
            evidence.matching_fields = ["alias", "nationality", "division"]
            confidence_tier = ConfidenceTier.STRONG_ALIAS_MATCH
            confidence_score = 0.85
        # Tier 3: Likely same fighter
        elif (
            name_sim > 0.8
            and candidate.nationality == known.nationality
            and candidate.promotion == known.promotion
            and candidate.sport_ruleset == known.sport_ruleset
        ):
            evidence.matching_fields = ["name_similarity", "nationality", "promotion", "sport_ruleset"]
            confidence_tier = ConfidenceTier.LIKELY_SAME_FIGHTER
            confidence_score = 0.75
        # Tier 4: Possible duplicate (weak match)
        else:
            # Check for conflicts
            if candidate.nationality and candidate.nationality != known.nationality:
                evidence.conflicting_fields.append("nationality")
            if candidate.date_of_birth and candidate.date_of_birth != known.date_of_birth:
                evidence.conflicting_fields.append("date_of_birth")
            if candidate.sport_ruleset and candidate.sport_ruleset != known.sport_ruleset:
                evidence.conflicting_fields.append("sport_ruleset")

            if evidence.conflicting_fields:
                confidence_tier = ConfidenceTier.POSSIBLE_DUPLICATE
                confidence_score = 0.45
                evidence.matching_fields = ["name_similarity"]
            else:
                # Weak match, no conflicts
                confidence_tier = ConfidenceTier.POSSIBLE_DUPLICATE
                confidence_score = 0.55
                evidence.matching_fields = ["name_similarity"]

        # Only include matches above threshold
        if confidence_score > 0.40:
            match = CandidateMatch(
                fighter_global_id=known.fighter_global_id,
                full_name=known.full_name,
                confidence_tier=confidence_tier,
                confidence_score=confidence_score,
                evidence=evidence,
            )
            candidate_matches.append(match)

    # Phase 2: Rank and assess matches
    candidate_matches.sort(key=lambda m: m.confidence_score, reverse=True)
    for i, match in enumerate(candidate_matches):
        match.rank = i + 1

    result.candidate_matches = candidate_matches

    # Phase 3: Determine resolution outcome
    if not candidate_matches:
        # No matches
        result.conflict_type = "new_fighter"
        result.manual_review_required = True
        result.recommendation = (
            "No matching global fighters found. Queue for operator review and global database entry."
        )
    elif len(candidate_matches) == 1:
        # Single match
        top_match = candidate_matches[0]
        if top_match.confidence_tier == ConfidenceTier.EXACT_MATCH:
            result.conflict_type = None
            result.manual_review_required = False
            result.recommendation = f"Auto-assign to {top_match.full_name} (exact match, no review needed)."
        elif top_match.confidence_tier == ConfidenceTier.STRONG_ALIAS_MATCH:
            result.conflict_type = None
            result.manual_review_required = False
            result.recommendation = (
                f"Auto-assign to {top_match.full_name} (strong alias match, no review needed)."
            )
        elif top_match.confidence_tier == ConfidenceTier.LIKELY_SAME_FIGHTER:
            result.conflict_type = None
            result.manual_review_required = True
            result.recommendation = (
                f"Likely same fighter: {top_match.full_name}. Flag for spot-check review."
            )
        else:
            result.conflict_type = "incomplete_evidence"
            result.manual_review_required = True
            result.recommendation = (
                f"Possible duplicate: {top_match.full_name}. Queue for manual review."
            )
    else:
        # Multiple matches: could be same-name conflict
        top_scores = [m.confidence_score for m in candidate_matches[:2]]
        if abs(top_scores[0] - top_scores[1]) < 0.15:
            # Ambiguous: multiple candidates with similar confidence
            result.conflict_type = "same_name"
            result.manual_review_required = True
            result.recommendation = (
                "Ambiguous: multiple candidate fighters with similar confidence. "
                "Queue for manual review and disambiguation."
            )
        else:
            # Clear winner
            top_match = candidate_matches[0]
            if top_match.confidence_tier in (ConfidenceTier.EXACT_MATCH, ConfidenceTier.STRONG_ALIAS_MATCH):
                result.conflict_type = None
                result.manual_review_required = False
                result.recommendation = f"Auto-assign to {top_match.full_name} (clear winner)."
            else:
                result.conflict_type = "incomplete_evidence"
                result.manual_review_required = True
                result.recommendation = (
                    f"Possible match: {top_match.full_name}, but multiple candidates found. "
                    "Queue for manual review."
                )

    # Safety: All write flags remain False (preview-only)
    result.preview_only = True
    result.profile_create_performed = False
    result.profile_update_performed = False
    result.merge_performed = False
    result.database_write_performed = False
    result.ranking_write_performed = False
    result.learning_apply_performed = False
    result.calibration_write_performed = False

    return result
