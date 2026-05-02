# AI-RISA Premium Report Factory - Button 2 Real Analysis Content Engine: Design Review v1

Date: 2026-05-02
Slice type: docs-only design review
Target design baseline: 8705e0d
Target design tag: ai-risa-premium-report-factory-button2-real-analysis-content-engine-design-v1

## Review Scope

Review only the locked design for Button 2 real analysis content generation and customer-ready gating.

This review does not change implementation code.

## Reviewed Requirements Coverage

1. Build content before PDF export
- Covered: yes
- Design defines content engine pipeline before export.

2. 14 premium sections supported
- Covered: yes
- Design lists all required sections and requires canonical section mapping.

3. Source hierarchy enforcement
- Covered: yes
- Design defines Source 1 to Source 4 fallback and blocked behavior when no usable analysis exists.

4. Queue fight linkage keys
- Covered: yes
- Design requires linkage attempts by fighter names, normalized matchup_id, event metadata, and source reference.

5. Existing record mapping into premium sections
- Covered: yes
- Design includes explicit premium section mapper responsibilities.

6. No record found -> block customer PDF unless explicit internal draft
- Covered: yes
- Design preserves block-first customer rule with explicit internal draft option.

7. Internal draft must generate real section text via AI-RISA lenses
- Covered: yes
- Design requires generated narrative content across all analytical lenses.

8. Draft remains not customer-ready until review/approval
- Covered: yes
- Design enforces draft_only state and non-auto-upgrade behavior.

9. customer_ready must not contain major placeholder phrases
- Covered: yes
- Design includes placeholder phrase rejection gate for customer mode.

10. customer_ready gating requirements
- Covered: yes
- Design requires all 14 sections, no major placeholders, and operator approval.

11. UI state visibility requirements
- Covered: yes
- Design includes source found/not found, linked record ID, missing sections, quality state, and approval state.

12. Content preview before export
- Covered: yes
- Design specifies headline/executive preview and missing section visibility prior to export.

13-19. Scope and governance guards
- Covered: yes
- No Button 1, no Button 3, no result lookup changes, no learning/calibration, no billing, no uncontrolled writes, no operator-approval bypass.

## Design Quality Assessment

- Correctly identifies missing product layer: analysis content engine, not file action plumbing.
- Introduces deterministic source resolution and canonical section mapping, improving consistency and explainability.
- Keeps customer safety first: customer export is gated by quality and approval.
- Preserves internal productivity path with explicit draft mode without weakening customer-ready rules.
- Adds preview-driven operator clarity before export to reduce failed attempts and confusion.

## Risks and Notes

- Residual risk: linkage ambiguity when multiple historical records are partial matches.
  - Mitigation: deterministic priority and linkage confidence metadata in resolver output.

- Residual risk: placeholder phrase detection may miss novel wording.
  - Mitigation: centralized phrase list plus required-section completeness checks.

- Residual risk: draft generator quality drift over time.
  - Mitigation: keep draft/customer gates strict and require operator approval for customer export.

## Review Verdict

APPROVED.

The design is implementation-ready, bounded, and aligned with locked safety rules.