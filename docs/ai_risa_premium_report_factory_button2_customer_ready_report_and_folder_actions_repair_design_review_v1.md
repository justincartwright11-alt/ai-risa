# AI-RISA Premium Report Factory — Button 2 Customer-Ready Report and Folder Actions Repair: Design Review v1

Date: 2026-05-02
Slice type: docs-only design review
Target design baseline: e9a645b
Target design tag: ai-risa-premium-report-factory-button2-customer-ready-report-and-folder-actions-repair-design-v1

## Review Scope

Review only the locked design for Button 2 customer-safe generation and folder/path action reliability.

This review does not change implementation code.

## Reviewed Requirements Coverage

1. Customer mode default
- Covered: yes
- Design states customer mode is default and blocks customer generation when quality is not customer_ready.

2. Draft output explicit internal-only
- Covered: yes
- Design requires a secondary explicit option labeled internal-only.

3. Draft labeling/watermark
- Covered: yes
- Design requires DRAFT ONLY — NOT CUSTOMER READY marking.

4. Draft outputs not presented as customer exports
- Covered: yes
- Design separates draft behavior and customer-facing presentation semantics.

5. Blocked state message for missing analysis
- Covered: yes
- Required message text is explicitly included.

6. Missing sections shown before generation when possible
- Covered: yes
- Pre-generation readiness preview is specified.

7. Reliable Open Reports Folder on Windows
- Covered: yes
- Design specifies POST /api/premium-report-factory/reports/open-folder with success/failure response.

8. Open PDF may use download endpoint
- Covered: yes
- Design keeps download endpoint as acceptable PDF open/download path.

9. Copy PDF Path explicit confirmation
- Covered: yes
- Design requires visible copied-path confirmation text.

10. Separate result actions
- Covered: yes
- Download PDF, Open Reports Folder, Copy PDF Path remain independent controls.

11. No jammed action text
- Covered: yes
- Explicit hard rendering rule included.

12-17. Scope guards
- Covered: yes
- No Button 1, no Button 3, no result lookup, no learning/calibration, no billing, no uncontrolled writes.

## Design Quality Assessment

- Product safety objective is correctly prioritized: generated file is not automatically customer-ready.
- Operator error risk is materially reduced by default customer-mode blocking and explicit internal draft mode.
- UX reliability risk is addressed through backend-assisted folder open endpoint for Windows.
- The validation plan is actionable and aligned with observed field issues.

## Risks and Notes

- Residual risk: placeholder phrase coverage may miss edge wording variants.
  - Mitigation: implementation should keep a centralized placeholder detection list and surface missing_sections.

- Residual risk: local OS folder-open behavior can vary by environment policy.
  - Mitigation: endpoint should return explicit error payload and actionable UI feedback.

## Review Verdict

APPROVED.

The design is implementation-ready, bounded, and consistent with the locked product rule and safety constraints.
