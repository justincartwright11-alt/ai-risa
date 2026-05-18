# AI-RISA Premium Report Factory - Button 3 Smaller-Promotion Result Source Reachability Design v1

**Document Type:** Product Surface Design (Docs-Only)  
**Date:** 2026-05-10  
**Status:** Draft for Review  
**Scope:** Button 3 result discovery and citation completeness only

---

## 1. Purpose

Button 3 must reliably find complete result citations for smaller promotions without weakening governance.

This slice is not about more winner parsing. It is about:
- finding the right result pages,
- deciding which sources are trusted enough to use,
- and preserving conservative classification when the citation is thin or incomplete.

The target is smaller-promotion fights such as Ares FC where generic discovery often lands on broad aggregator pages or partial result summaries instead of complete citations.

---

## 2. Evidence From Recent Trials

The current evidence shows two distinct failure modes:

- Winner extraction improvements did not increase yield on the real cohort.
- Discovery query expansion from fight name and event name did not increase yield on the same cohort.

Observed real-trial outcome:
- 3 fights tested
- 0/3 matched_ready
- 2 citation_incomplete
- 1 no_result_found
- 0 durable applies
- 0 result rows
- 0 audit rows
- 0 rollback rows

Interpretation:
- Button 3 is now reaching the source lookup layer.
- The remaining bottleneck is source reachability and citation completeness for smaller promotions.
- The system should stay conservative until a complete citation can be proven.

---

## 3. Design Principles

1. Never weaken governance to force a matched_ready result.
2. Prefer official promoter sources when they exist and are complete.
3. Use aggregators as discovery aids or trusted secondary sources only when they provide a complete citation.
4. Keep citation_incomplete when winner, source, method, or round cannot be proven.
5. Treat smaller-promotion coverage as a policy problem first, not a parsing problem.

---

## 4. Source Tier Policy

### 4.1 Tier A0: Official Primary

Examples:
- UFC official pages
- ONE Championship official pages
- Glory official pages
- Smaller-promotion official result pages when the promotion domain is direct and explicit

Use for matched_ready when all of the following are present:
- explicit result page or scorecard page
- title and publisher are clearly aligned with the promotion
- event or fight identity is explicit
- winner is explicit
- method is explicit
- round or time is explicit when available
- source date is present or derivable

### 4.2 Tier A1: Official Secondary

Examples:
- promoter subpages
- results pages under official event domains
- official watch/result recap pages that still clearly belong to the promoter

Use when the citation is still complete and the page clearly identifies the fight.

### 4.3 Tier B: Trusted Secondary

Examples:
- Tapology
- Sherdog
- Boxing/MMA result aggregators already allowed by policy

Use only when the page is complete enough to prove the result and the fight identity.

For smaller promotions, Tier B should not be treated as an automatic matched_ready fallback.
It should be accepted only when the page is fight-specific and citation-complete.

---

## 5. When Tapology or Sherdog Are Enough

Tapology or Sherdog can be enough for matched_ready only when the page is all of the following:
- clearly the result page for the specific fight or event,
- contains both fighters or an unambiguous fighter identity match,
- contains the winner,
- contains the method,
- contains the round or time,
- and provides a usable title and source date.

They remain manual review only when any of the following apply:
- the page is a generic home page or broad index,
- the source date is missing,
- the method or round is missing,
- the winner is only partially identifiable,
- the page cannot be tied to the exact fight without inference.

They remain citation_incomplete when the system can see a likely result but cannot prove the full citation.

---

## 6. Smaller-Promotion Reachability Strategy

### 6.1 Discovery Query Strategy

For smaller promotions, discovery should build query terms from:
- fight name,
- event name,
- promotion name when known,
- and result keywords such as result, results, official result, scorecard, winner.

The query strategy should be layered:
1. exact fight name + event name
2. exact fight name + event name + official result
3. promotion name + event name + result keyword
4. fallback aggregator discovery only if no official page is found

The design goal is not to increase breadth endlessly.
The goal is to get to the right event result page faster and with fewer generic hits.

### 6.2 URL Trust Strategy

For smaller promotions, candidate URLs should be ranked by explicitness, not by generic domain popularity.

Preferred ordering:
1. official promoter result page
2. official promoter event page that links to results
3. trusted secondary fight-specific result page
4. generic aggregator page only as a last discovery step

Generic home pages should not be treated as evidence of a complete citation.

### 6.3 Promotion Awareness

Known promotions with direct first-party coverage should still get promotion-specific discovery rules.
Unknown promotions should not be forced into a UFC-style search pattern.
They should get exact fight/event search terms and a conservative fallback policy.

---

## 7. Citation Completeness Requirements

A citation should be considered complete enough for matched_ready only if the system can prove:
- source_url
- source_title
- source_date or a reliable published date
- publisher_host
- extracted_winner
- method or an equivalent result descriptor
- round or time when the source provides it
- identity match to the selected fight card

If any of the above are missing, the result should remain conservative.

Recommended status mapping:
- matched_ready: complete citation, identity proven, source trusted
- needs_manual_review: result is likely correct but incomplete or low confidence
- citation_incomplete: result text exists but cannot prove the full citation
- no_result_found: no usable result page discovered
- ambiguous_result: conflicting sources or conflicting identity proof

---

## 8. Ares-Style Source Policy

Ares FC and similar smaller promotions should be handled as follows:

- First try official or direct promoter pages.
- If no official page is found, use fight/event-specific discovery queries.
- If the discovered page is a thin aggregator page, do not promote it to matched_ready unless it contains a complete citation.
- If the page can identify the winner but not the source or result detail, keep citation_incomplete or needs_manual_review.
- If the discovery path only reaches generic aggregator pages, keep the result conservative and avoid false certainty.

This is intentionally stricter than the UFC/ONE/Glory path.

---

## 9. Fixture Coverage Needed Before Implementation

Before any implementation slice, the fixture set should cover:

1. Ares-style official or near-official result page that is complete enough to prove matched_ready.
2. Ares-style aggregator result page that is discoverable but still thin enough to remain manual review or citation_incomplete.
3. Smaller-promotion generic result page that should remain no_result_found or needs_manual_review, not matched_ready.
4. A source-discovery fixture that proves fight name + event name are used in the query.
5. A source-discovery fixture that proves generic fallback does not override a better discovered result page.

The current fixture set already covers some of this behavior, but the next implementation pass should explicitly separate:
- discovery success,
- citation completeness,
- and conservative rejection.

---

## 10. Non-Goals

This slice does not include:
- winner parsing changes,
- auto-apply changes,
- durable apply changes,
- rollback changes,
- learning or calibration changes,
- metrics changes.

---

## 11. Recommended Implementation Slice After Review

If this design is approved, the next implementation slice should be small and isolated:

1. Add smaller-promotion discovery rules.
2. Add a stricter citation completeness policy for generic aggregator pages.
3. Add fixtures for Ares-style official, aggregator, and thin-result pages.
4. Validate that the result remains conservative unless the citation is complete.

---

## 12. Acceptance Criteria

This design is good if it can answer these questions without ambiguity:
- Which smaller-promotion sources are trusted?
- Which search terms does Button 3 use first?
- When is a result complete enough to be matched_ready?
- When must the system stop and require manual review?
- Which fixtures will prove the policy before implementation?

If these questions are not answerable from the design, the slice is not ready for code.
