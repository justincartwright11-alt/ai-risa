# AI-RISA Global Fighter Identity Resolver — Design v1

## 1. Purpose

The Global Fighter Identity Resolver is a deterministic, preview-only matching engine that ingests fighter data from sources (Button 1 discovery, Button 3 results, operator input) and matches identity records to the global fighter database. The resolver produces match confidence assessments, surfaces conflicts, and queues ambiguous cases for operator review. **No permanent identity writes, merges, or updates are permitted without explicit operator approval.**

---

## 2. Relationship to Global Fighter Database Schema

The Identity Resolver operates downstream of the Global Fighter Database schema (see `docs/global_fighter_database_master_schema_design_v1.md`). It consumes:
- Global fighter identity records (`fighter_global_id`, `full_name`, `known_aliases`, `confidence_grade`, `merge_history`)
- Source provenance tags
- Alias and confidence tables

The resolver produces:
- **Match evidence:** Matching fields, confidence scores, source alignment
- **Conflict alerts:** Ambiguous or contradictory matches
- **Manual review queue:** Cases requiring operator decision
- **Merge recommendations:** (Operator-approved only)

No resolver action directly modifies the global database. All writes pass through operator approval gates.

---

## 3. Fighter Identity Fields Used for Matching

### Tier 1 (Exact Match Criteria)
- `fighter_global_id` (if already known)
- Canonical name + nationality + birth date (exact match)
- Canonical name + nationality + active year range (exact match)

### Tier 2 (Strong Match Criteria)
- Alias + nationality + weight class
- Alias + nationality + promotion
- Canonical name + birth date (unique within 5-year window)

### Tier 3 (Supporting Evidence)
- Height + reach + stance
- Record (win/loss/draw counts, rough era)
- Promotion history
- Active years (overlapping)
- Sport/ruleset (Boxing, MMA, Kickboxing, etc.)
- Social media / official website references

### Tier 4 (Weak Evidence, Manual Review)
- Name similarity (Levenshtein distance)
- Weight class proximity
- Rough record estimate
- Operator/user note fields

---

## 4. Match Confidence Model

### Exact Match (A / 0.95+)
- **Criteria:**
  - `fighter_global_id` already known from prior ingestion.
  - OR: Canonical name + nationality + birth date + record all align to single global fighter.
  - OR: Alias + promotion + active years + record all align to single global fighter.
- **Action:** Auto-assign, no review needed.
- **Probability of false merge:** < 1%

### Strong Alias Match (A / 0.85+)
- **Criteria:**
  - Alias + nationality + promotion + weight class + active years all align.
  - OR: Canonical name + nationality + multiple source corroboration (2+ official sources).
  - OR: Alias + birth date + nationality + record strongly align.
- **Action:** Auto-assign with evidence, log source alignment, no review needed.
- **Probability of false merge:** 1–5%

### Likely Same Fighter (B / 0.65–0.84)
- **Criteria:**
  - Alias + nationality + weight class align, but promotion or active years differ.
  - OR: Canonical name + nationality align, but birth date unknown.
  - OR: Canonical name + record + active years align, but nationality uncertain.
  - OR: Two independent sources (one official, one secondary) both identify same fighter.
- **Action:** Auto-assign with reduced confidence, flag for spot-check, log evidence.
- **Probability of false merge:** 5–15%

### Possible Duplicate (C / 0.40–0.64)
- **Criteria:**
  - Name similarity (Levenshtein > 0.8) + nationality + weight class, but record/active years conflict.
  - OR: Alias match only, weak corroboration.
  - OR: Alias + nationality match, but promotion/active years differ significantly.
  - OR: Single source (unverified) claims match, no corroboration.
- **Action:** Queue for manual review, display all evidence, do not auto-assign.
- **Probability of false merge:** 15–40%

### Conflict / Manual Review (F / < 0.40)
- **Criteria:**
  - Multiple candidate fighters with overlapping evidence (same-name fighters).
  - OR: Conflicting source claims (official source A says fighter X, official source B says fighter Y).
  - OR: Evidence insufficient to disambiguate (no nationality, no birth date, no record).
  - OR: Known error or blacklist flag on candidate.
- **Action:** Queue for mandatory operator review, display all candidates, do not auto-assign.
- **Probability of false merge:** > 40% (unacceptable)

### No Match (None / 0.0)
- **Criteria:**
  - Exhaustive search of aliases, promotions, nationalities, weight classes yields zero candidates.
  - OR: All candidates fail to meet minimum evidence threshold (< 0.40 confidence).
  - OR: Operator explicitly rejects all candidates (soft delete from resolver).
- **Action:** Flag as new fighter, queue for operator review and global database entry, do not auto-create.
- **Probability of false merge:** N/A (no merge attempted)

---

## 5. Duplicate Detection Rules

### Rule 1: Exact Name + Exact Nationality + Exact Birth Date
- **Trigger:** Three fields match exactly to a single global fighter.
- **Action:** Exact match (A / 0.95+), auto-assign.
- **Exception:** If global database has explicit conflict flag, escalate to manual review.

### Rule 2: Alias + Nationality + Promotion + Active Years
- **Trigger:** All four fields align to a single global fighter.
- **Action:** Strong match (A / 0.85+), auto-assign.
- **Exception:** If more than one global fighter matches, escalate to conflict review.

### Rule 3: Name Similarity (Levenshtein > 0.85) + Nationality + Same Weight Class
- **Trigger:** Name distance < 0.15 (high similarity) + nationality matches + weight class matches.
- **Action:** If active years overlap: Likely same fighter (B), flag for review.
  If active years do not overlap: Possible different fighter, manual review.
- **Exception:** If birth date differs by > 10 years, escalate to conflict.

### Rule 4: Multiple Source Corroboration
- **Trigger:** Two or more independent sources (official > secondary priority) both claim same identity.
- **Action:** If sources are aligned: Strong match (A / 0.85+), auto-assign.
  If sources conflict: Conflict, manual review.

### Rule 5: Same-Name Fighters in Overlapping Promotion/Division
- **Trigger:** Two or more global fighters share name + nationality + overlapping active years + same promotion + same weight class.
- **Action:** Always escalate to manual review; do not auto-merge.
- **Prevention:** Must disambiguate on birth date, height, reach, or source URL.

### Rule 6: Record Mismatch Escalation
- **Trigger:** Candidate match on alias + nationality, but record win/loss counts differ by > 20%.
- **Action:** Escalate to manual review; do not auto-merge if primary evidence is record.

---

## 6. False-Merge Prevention Rules

### Prevention 1: Fail Closed on Incomplete Evidence
- **Rule:** If identity evidence is insufficient (missing 2+ of: nationality, birth date, promotion, active years), fail closed to manual review.
- **Exception:** Exact `fighter_global_id` or name + nationality + promotion + active years all present.

### Prevention 2: Mandatory Source Provenance
- **Rule:** Any match recommendation must include source tags for all supporting evidence fields.
- **Enforcement:** Resolver rejects matches with missing source fields.

### Prevention 3: Nationality Mismatch = Manual Review
- **Rule:** If nationality differs, escalate to manual review unless corroborated by 2+ official sources.
- **Exception:** Known nationality mistakes (e.g., Sherdog lists wrong country) documented in source provenance.

### Prevention 4: Active Years Non-Overlap = Manual Review
- **Rule:** If candidate's active years do not overlap with ingested fighter's estimated era, escalate to manual review.
- **Exception:** If name + birth date are exact matches.

### Prevention 5: Rollback on Operator Reject
- **Rule:** If operator rejects a match recommendation, store the rejection in `merge_history` and do not re-recommend the same merge.
- **Enforcement:** Prevent loop-merge on future ingestions.

### Prevention 6: Conflict Flag Propagation
- **Rule:** If global fighter record has conflict flag, resolver never auto-merges; always escalates to operator.
- **Exception:** Operator explicitly clears conflict flag.

---

## 7. Same-Name Fighter Handling

### Challenge
Multiple fighters share the same or very similar names (e.g., John Silva, Multiple boxers named "Muhammad").

### Disambiguation Strategy
1. **Nationality + Promotion + Weight Class:** If all three differ, treat as distinct fighters.
2. **Birth Date:** If known, use as primary disambiguator.
3. **Height + Reach:** If known, use as secondary disambiguator.
4. **Record Era:** If record win counts and estimated era differ significantly, treat as distinct.
5. **Source URL:** If sources explicitly reference different pages/fighters, trust source separation.

### Resolver Behavior
- **Auto-Assign:** Only if exact match on birth date OR nationality + promotion + active years + record all align.
- **Manual Review:** If two or more candidates meet minimum threshold (0.40+), surface all candidates and require operator decision.
- **Escalation Rule:** Always fail closed; never auto-merge same-name fighters without explicit disambiguation.

---

## 8. Alias Handling

### Alias Types
- **Ring Names:** Preferred battle/professional name (e.g., "The Spider" Silva)
- **Nicknames:** Common short forms (e.g., "Anderson" vs. "A. Silva")
- **Transliteration Variants:** Cyrillic, Arabic, etc. (e.g., "Aleksandr" vs. "Alexander")
- **Misspellings:** Known common errors, flagged with note
- **Historical Names:** Name changes from early career

### Resolver Matching on Aliases
1. **Exact Alias Match:** If ingested name matches known alias exactly, auto-assign (A / 0.95+).
2. **Alias Similarity (Levenshtein > 0.85):** If ingested name is similar to known alias + nationality + promotion match, strong match (A / 0.85+).
3. **Alias Not in Database:** If ingested fighter's name does not match any global alias, escalate to manual review (no match or new fighter).

### Alias Conflict Resolution
- **Rule:** If ingested name matches 2+ global fighters via different aliases, escalate to conflict review.
- **Example:** "Silva" could match both Anderson Silva and Chris Silva; operator disambiguates.

### Alias Approval Gate
- **New Aliases:** Operator approval required to add new alias to global fighter record.
- **Source Requirement:** New alias must include source tag (e.g., Tapology, Sherdog).

---

## 9. Cross-Promotion Identity Handling

### Challenge
Same fighter may compete in multiple promotions (e.g., boxing then MMA, or multi-org MMA).

### Resolver Strategy
1. **Promotion Change Allowed:** If same fighter migrates promotions over time, treat as identity continuity (same global fighter).
2. **Overlapping Promotions:** If fighter competes in multiple promotions simultaneously, treat as distinct identities only if corroborated by official sources.
3. **Record Continuity:** If fight records are disjoint (no overlap in date ranges), treat as distinct identities unless name + nationality + birth date are exact matches.

### Approval Gate
- **Cross-Promotion Merge:** Requires explicit operator approval and source citation.

---

## 10. Sport/Ruleset Handling

### Challenge
Same fighter may compete in multiple sports (Boxing, MMA, Kickboxing, Wrestling, etc.).

### Resolver Strategy
1. **Same Sport, Different Org:** Treat as same global fighter.
2. **Different Sports:** By default, treat as separate identities unless name + nationality + birth date are exact matches.
3. **Sport Code Field:** Each global fighter record has primary sport + optional secondary sports.

### Approval Gate
- **Cross-Sport Identity:** Requires explicit operator approval and source evidence (official biography, social media, etc.).

---

## 11. Source Provenance Requirements

### Mandatory Source Tags
- All identity evidence must include:
  - `source_name` (e.g., Sherdog, Tapology, ESPN)
  - `source_url` (if available)
  - `source_type` (official, secondary, user, operator)
  - `source_date` (ISO date)

### Source Priority for Tie-Breaking
1. **Official:** Promotion website, fighter official website
2. **Trusted Secondary:** ESPN, Tapology, Sherdog (established databases)
3. **User/Operator:** Manual input, user-submitted
4. **Unverified:** Unknown sources, unconfirmed claims

### Source Conflict Resolution
- **Same Priority:** Escalate to manual review.
- **Different Priority:** Use higher-priority source.

---

## 12. Manual Review Queue Design

### Queue Entry Structure
```json
{
  "review_id": "uuid",
  "ingested_fighter": {
    "name": "string",
    "aliases": ["list"],
    "nationality": "string",
    "promotion": "string",
    "division": "string",
    "record": "object",
    "birth_date": "iso_date or null",
    "source_tags": ["list"]
  },
  "candidate_matches": [
    {
      "fighter_global_id": "uuid",
      "confidence": "float 0.0–1.0",
      "match_evidence": {
        "matching_fields": ["list"],
        "conflicting_fields": ["list"],
        "source_alignment": "object"
      },
      "rank": "integer"
    }
  ],
  "conflict_type": "enum: same_name, source_conflict, incomplete_evidence, new_fighter, operator_reject_previous",
  "recommendation": "string",
  "operator_decision_required": "bool",
  "created_at": "iso_datetime",
  "decided_at": "iso_datetime or null",
  "operator_decision": "enum: auto_assign_to_<global_id>, create_new_fighter, reject_all, merge_candidates, <other>"
}
```

### Manual Review Statuses
- **Pending:** Awaiting operator review
- **Operator Assigned:** Operator chose a merge/assignment
- **Operator Rejected:** Operator rejected all candidates (soft delete from resolver)
- **Escalated to Design Review:** Potential policy change needed

---

## 13. Identity Conflict Statuses

### Status: Known Duplicate (Awaiting Merge)
- **Trigger:** Two global fighter records identified as same person, pending merge.
- **Resolver Behavior:** Flag both records, do not use either in rankings until merge approved.

### Status: Known Distinct (Different Fighters, Same Name)
- **Trigger:** Operator confirms two records are different fighters (despite name similarity).
- **Resolver Behavior:** Always disambiguate on secondary criteria (nationality, promotion, birth date); never merge.

### Status: Disputed Identity
- **Trigger:** Sources conflict on identity or record.
- **Resolver Behavior:** Surface all evidence, queue for manual review, never auto-assign.

### Status: Unverified (New Fighter, Awaiting Approval)
- **Trigger:** No global fighter record exists; ingested fighter is new.
- **Resolver Behavior:** Queue for operator review before creating global record.

### Status: Blacklist
- **Trigger:** Operator explicitly rejects a fighter record (e.g., known spam, fake profile).
- **Resolver Behavior:** Never match ingested fighters to blacklist record; skip.

---

## 14. Approval-Gated Merge Rules

### Merge Approval Gate
- **Requirement:** All permanent merges (combining two or more global fighter records) require explicit operator approval.
- **Evidence Requirement:** Operator must review match evidence and source tags before approving.

### Merge Audit Trail
- **Logging:** All merges logged with:
  - Operator name and timestamp
  - Candidate records and confidence scores
  - Match evidence displayed
  - Approval decision rationale (if provided)
  - Reversibility flag (can merge be rolled back?)

### Merge Reversibility
- **Requirement:** All merges must be reversible for up to 90 days after approval.
- **Rollback:** Operator can split merged record back into constituent records.

---

## 15. Rollback Requirements

### Rollback Scope
- **Identity Merges:** Can be rolled back within 90 days of approval.
- **Alias Additions:** Can be rolled back at any time (permanent deletion not allowed).
- **Conflict Flag Changes:** Can be rolled back at any time.

### Rollback Audit
- **Logging:** All rollbacks logged with operator name, timestamp, reason, and impact scope.
- **Notification:** Dependent systems (rankings, reports, digital doubles) notified of rollback.

---

## 16. Audit Record Requirements

### Audit Entry Structure
```json
{
  "audit_id": "uuid",
  "timestamp": "iso_datetime",
  "operator_user_id": "string or null (null if automated)",
  "action": "enum: identity_match, manual_assign, merge_approved, merge_rolled_back, alias_added, conflict_flag_set, etc.",
  "global_fighter_id": "uuid",
  "evidence_snapshot": "object (copy of all evidence at time of action)",
  "impact_scope": ["list of downstream systems affected: rankings, reports, digital_doubles, etc."],
  "reversible": "bool",
  "reason": "string (operator note if provided)"
}
```

### Audit Trail Immutability
- **Rule:** Once written, audit entries cannot be modified or deleted.
- **Enforcement:** Audit logs stored in append-only storage.

---

## 17. Future Implementation Tests

### Unit Tests (Preview-Only)
- `test_identity_match_exact_name_nationality_birthdate`
- `test_identity_match_alias_promotion_active_years`
- `test_identity_conflict_same_name_fighters`
- `test_identity_false_merge_prevention_incomplete_evidence`
- `test_identity_source_provenance_validation`
- `test_identity_rollback_logic`

### Integration Tests (Preview-Only)
- `test_identity_resolver_end_to_end_preview_mode`
- `test_identity_resolver_with_operator_decision_override`
- `test_identity_resolver_conflict_detection_accuracy`
- `test_identity_resolver_audit_trail_completeness`

### Regression Tests (Preview-Only)
- `test_identity_resolver_no_write_side_effects`
- `test_identity_resolver_no_database_mutations`
- `test_identity_resolver_no_global_fighter_db_writes`

---

## 18. Non-Goals

### Not in Scope
- **Automatic Merge Behavior:** Resolver never automatically merges global fighters; all merges require operator approval.
- **Automatic Global Database Writes:** Resolver never writes to global fighter database; all writes require operator approval gate.
- **Record Updates:** Resolver never updates fighter records (wins, losses, rankings); only identity matching.
- **Historical Rewrite:** Resolver never rewrites past matches or historical records.
- **Self-Learning:** Resolver does not learn from operator decisions without explicit operator approval and design review.

---

## 19. Final Verdict

### Explicit Constraints
1. **Preview-Only:** Resolver may preview identity matches automatically.
2. **No Permanent Writes:** Resolver may **not** permanently create, merge, or update fighter profiles without operator approval.
3. **Fail Closed on Ambiguity:** Same-name fighters must fail closed into manual review when identity evidence is incomplete.
4. **Source Provenance Mandatory:** Source provenance is mandatory for any future permanent identity write.

### Safety Posture
- **Fail-Closed Design:** All ambiguous cases escalate to manual review; never auto-merge.
- **Operator Control:** All permanent changes require explicit operator decision.
- **Audit Trail:** All actions logged and reversible.
- **No Hidden Behavior:** Resolver behavior is deterministic and fully explainable.

### Readiness for Implementation
- **Design Locked:** This design is complete and ready for operator review.
- **No Implementation Permitted:** No code, dashboard, or database changes in this slice.
- **Next Phase:** Operator review, then docs-only API/preview design, then implementation.

---

**Status:**
- Docs-only, architecture lock.
- No code, dashboard, or route changes.
- No database writes opened.
- No automatic merge behavior opened.
- Operator-approved governance preserved.
- Ready for review and next slice.
