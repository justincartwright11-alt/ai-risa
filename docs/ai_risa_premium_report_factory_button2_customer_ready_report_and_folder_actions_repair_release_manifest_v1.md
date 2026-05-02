# AI-RISA Premium Report Factory - Button 2 Customer-Ready Report and Folder Actions Repair: Release Manifest v1

Date: 2026-05-02
Scope: Button 2 only

## Release Summary

This release hardens customer-ready behavior and action clarity for Button 2 premium report generation.

Key delivered behavior:

- Customer mode is default:
  - draft output is OFF by default
  - missing-analysis blocks customer PDF generation
- Internal draft mode is explicit and operator-visible.
- Draft-only PDF labeling is embedded in generated artifact:
  - DRAFT ONLY - NOT CUSTOMER READY
- Action controls remain separate and clear:
  - Download PDF
  - Open Reports Folder
  - Copy PDF Path
- Folder opening is backend-driven via:
  - POST /api/premium-report-factory/reports/open-folder
- Copy-path confirmation shows full exact copied path string.

## Smoke-Verified Outcomes

- Customer-mode default run:
  - missing-analysis generation blocked with required message
  - accepted_count=0, rejected_count=1
- Internal draft run:
  - report_quality_status=draft_only
  - customer_ready=false
  - missing_sections populated
  - generated PDF produced
- Draft artifact proof:
  - extracted PDF text contains DRAFT ONLY - NOT CUSTOMER READY
- Action proof:
  - Download PDF available as separate endpoint action
  - Open Reports Folder returns success and opened path
  - Copy PDF Path status includes exact copied path

## Scope Boundary Confirmation

- No Button 1 changes
- No Button 3 changes
- No result lookup changes
- No learning/calibration changes
- No billing changes
- No uncontrolled writes

## Lock Chain

- Design: e9a645b
- Design review: da6a5ff
- Implementation: 6eadd2b
- Post-freeze smoke: fd03f6b
- Final review: bb7836a

## Release Verdict

RELEASE READY.