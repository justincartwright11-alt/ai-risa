# Copilot Model Routing and Local Security Review Governance v1

## 1. Purpose
Define a docs-only governance update for AI-RISA model routing, cost controls, and local security-review usage boundaries.

## 2. Effective updates
- GPT-5.6 Luna: use for routine documentation, small fixes, simple tests.
- GPT-5.6 Terra: use for normal narrow-slice implementation.
- GPT-5.6 Sol: use only for architecture, difficult defects, complex governance analysis, or large-codebase reasoning.
- Do not use Sol as the default.

## 3. AI-RISA plan decision
- Current recommendation remains GitHub Free + Copilot Pro+.
- Copilot Pro+ gives access to Sol without moving to Max.
- Pro+ allowance: 7,000 monthly AI credits.
- Pro allowance: 1,500 monthly AI credits.
- Max allowance: 20,000 monthly AI credits.
- Move to Max only if AI-RISA continues exhausting 7,000 credits after Luna/Terra routing and bounded sessions.

## 4. Model-routing rule
- Routine documentation, small fixes and simple tests: GPT-5.6 Luna.
- Normal narrow-slice implementation: GPT-5.6 Terra.
- Architecture, difficult defects and complex governance analysis: GPT-5.6 Sol.
- Sol is non-default and should be invoked only by exception based on slice complexity.

## 5. Cost-control rule
- Use exact slice boundaries and exact files.
- Keep sessions bounded.
- Check session and subagent credit usage after substantial sessions.
- Perform one validation path per slice.
- Stop after commit.

## 6. Security-review gate
AI-RISA LOCAL SECURITY REVIEW GATE

Complete exact approved slice
→ run required tests
→ run /security-review against current changes
→ inspect high-confidence findings
→ correct or formally record each finding
→ rerun affected tests
→ inspect git diff and git status
→ commit
→ stop

## 7. Slices that require security review
- Button 1 external-source ingestion
- Button 3 approval or mutation paths
- file uploads and path handling
- database writes
- authentication or authorization
- API endpoints
- secrets, credentials, or configuration
- report delivery and customer data

## 8. Security-review authority boundary
- /security-review is advisory evidence, not automatic authority.
- Copilot must not apply broad fixes.
- Copilot must not modify unrelated files.
- Copilot must not override AI-RISA approval gates.
- Copilot must not convert an advisory finding into a mutation without explicit operator approval.

## 9. Billing-monitoring migration
- Billing monitoring should move to GitHub built-in AI usage and billing settings.
- Copilot Billing Preview app retirement date: 2026-08-03.

## 10. Prohibited Copilot behavior
- Do not default to Sol for routine work.
- Do not run broad scans outside the exact approved slice.
- Do not execute broad, unbounded multi-file refactors for advisory findings.
- Do not bypass explicit operator approval controls.
- Do not continue past slice completion and commit stop point.

## 11. Required operator checklist
- Confirm slice scope and file list.
- Select model tier by routing rule (Luna/Terra/Sol).
- Run bounded implementation only for approved scope.
- Run required validation.
- For covered security-sensitive slices, execute the local security-review gate.
- Inspect credits after substantial sessions.
- Inspect git diff and git status.
- Commit and stop.

## 12. Final operating rule
Routine documentation, small fixes and simple tests
→ GPT-5.6 Luna

Normal narrow-slice implementation
→ GPT-5.6 Terra

Architecture, difficult defects and complex governance analysis
→ GPT-5.6 Sol

Always:
exact slice → exact files → bounded session
→ inspect credit cost → one validation
→ git diff/status → commit → stop

## 13. Stop condition
Stop after this memo. Do not run additional implementation, scans, tests, or governance expansions in this slice.
