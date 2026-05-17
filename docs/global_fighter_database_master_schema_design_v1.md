# AI-RISA Global Fighter Database — Master Schema Design v1

## Purpose
Design the global fighter database, identity model, alias handling, source provenance, duplicate/conflict rules, confidence grades, ranking hooks, digital-double hooks, and future approval-gated write rules before implementation. No global fighter database writes are permitted in this slice. This is a docs-only, architecture lock.

---

## 1. Global Fighter Identity Model
- **Primary Key:** `fighter_global_id` (UUID, never reused)
- **Core Fields:**
  - `full_name` (canonical, normalized)
  - `known_aliases` (list, all known ring names, nicknames, alternate spellings)
  - `birth_date` (ISO, optional)
  - `nationality` (ISO country code)
  - `gender` (enum)
  - `weight_classes` (list, normalized)
  - `active_years` (range)
  - `retired` (bool)
  - `official_records` (list, source-tagged)
  - `source_provenance` (see below)
  - `confidence_grade` (A/B/C/D/F, see below)
  - `merge_history` (list, all merges, splits, or corrections)
  - `digital_double_refs` (future, see below)

---

## 2. Alias Handling
- **Alias Table:**
  - Each alias links to a single `fighter_global_id`.
  - Aliases include:
    - Ring names
    - Nicknames
    - Alternate spellings
    - Transliteration variants
    - Known misspellings (with flag)
  - **Alias Provenance:** Each alias is source-tagged (e.g., Sherdog, Tapology, ESPN, user, operator).
  - **Alias Confidence:** Each alias has a confidence grade (see below).
  - **Alias Approval:** Operator approval required for new/controversial aliases.

---

## 3. Source Provenance
- **Source Table:**
  - Each fighter and alias is tagged with all known sources (site, API, operator, user, etc.).
  - **Source Priority:** Official > Trusted Secondary > User/Operator > Unverified
  - **Source Record:**
    - `source_name`
    - `source_url` (if available)
    - `source_type` (official, secondary, user, operator, unknown)
    - `source_date`
    - `source_confidence`

---

## 4. Duplicate/Conflict Rules
- **Duplicate Detection:**
  - Automated and operator-reviewed matching on name, alias, birth date, record, and source.
  - **Merge Policy:**
    - Only operator-approved merges allowed.
    - All merges are logged in `merge_history`.
    - No destructive deletes; all merges are reversible.
  - **Conflict Resolution:**
    - Conflicting records flagged for operator review.
    - Confidence grades and source priority guide resolution.

---

## 5. Confidence Grades
- **Grades:**
  - A: Official, multi-source, operator-verified
  - B: Trusted secondary, strong match, operator-reviewed
  - C: User/operator submitted, weak match, not operator-verified
  - D: Unverified, single-source, possible error
  - F: Known error, rejected, or blacklisted
- **Usage:**
  - All core fields, aliases, and sources are graded.
  - Confidence grades drive ranking, display, and write approval gates.

---

## 6. Ranking Hooks
- **Ranking Table:**
  - Each fighter record can be linked to ranking engines (global, promotion, weight class, etc.).
  - **Ranking Provenance:** All rankings are source-tagged and confidence-graded.
  - **Ranking Approval:** Operator approval required for global or official rankings.

---

## 7. Digital-Double Hooks
- **Digital Double Table:**
  - Each fighter can be linked to one or more digital double models (simulation, video, stats, etc.).
  - **Digital Double Provenance:** All digital doubles are source-tagged and confidence-graded.
  - **Approval:** Operator approval required for digital double creation or merge.

---

## 8. Future Approval-Gated Write Rules
- **No Writes in This Slice:**
  - This schema is docs-only. No global fighter database writes are permitted.
- **Approval Gates:**
  - All writes (create, update, merge, alias, ranking, digital double) must pass operator approval.
  - All changes are logged and reversible.
  - No destructive deletes.
- **Audit Trail:**
  - Every change is logged with timestamp, operator/user, and reason.

---

## 9. Governance and Safety
- **Fail-Closed:**
  - No write, merge, or alias action is permitted without explicit operator approval.
  - All automated actions are preview-only until approved.
- **Operator Review:**
  - All high-impact changes (merges, splits, new aliases, digital double links) require operator review and sign-off.
- **No Production Writes:**
  - This schema is for design and review only. No implementation or production writes are allowed in this slice.

---

## 10. Next Steps
- Review and lock schema.
- Implement preview-only API and dashboard evidence for identity, alias, and provenance checks.
- Design operator review UI for merges, conflicts, and digital double links.
- Plan migration and integration with existing fight queue, ranking, and report engines.

---

**Status:**
- Docs-only, architecture lock.
- No code, dashboard, or route changes.
- No implementation behavior opened.
- Ready for review and next slice.
