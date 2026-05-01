# AI-RISA Premium Report Factory MVP Phase 2 Dashboard Runtime Mismatch Diagnostic Design v1

## 1. Diagnostic Purpose

This diagnostic design defines a runtime-only investigation for the Phase 2 live dashboard interaction mismatch where the preview and save flow does not complete through browser interaction.

The purpose is to preserve the archived baseline while identifying the exact failure point before any implementation change is considered.

This design enforces a no-patch-first rule: no code fixes are allowed until evidence proves the specific failing boundary in the frontend interaction or render path.

## 2. Known Good Evidence

The following evidence is already confirmed and considered reliable:

1. Local file tokens for Phase 2 controls and queue endpoints are present.
2. Served Advanced Dashboard HTML contains the expected Phase 2 tokens.
3. Backend endpoint probes pass for preview, save-selected, and queue list behavior.
4. Temporary queue override works and isolates writes away from real queue runtime paths.
5. Browser DOM nodes for Phase 2 controls are present.
6. Repository returned to clean state after triage.

## 3. Failure Evidence

The following runtime mismatch evidence is confirmed:

1. Live browser action enters loading state for preview.
2. Flask does not receive `POST /api/premium-report-factory/intake/preview` from the browser session during the failed interaction path.
3. Preview and save UI flow does not complete through browser interaction.
4. Expected matchup rows do not render via the live browser interaction path.

## 4. Ruled-Out Cases

The following triage cases are explicitly ruled out by evidence:

1. Case A ruled out: local checkout missing Phase 2 tokens.
2. Case B ruled out: Flask serving stale or wrong checkout.
3. Case C ruled out: browser missing Phase 2 DOM nodes.

## 5. Active Case

Case D is active: frontend interaction or render path issue.

## 6. Proposed Diagnostic Checks For Future Runtime-Only Slice

The future diagnostic execution slice should run these checks in order:

1. Capture browser console errors during preview click.
2. Inspect fetch call construction before network boundary.
3. Confirm event listener binding on the Preview Event Card button.
4. Confirm no JavaScript exception occurs before fetch.
5. Confirm whether connection-reset dashboard background polling interferes.
6. Verify form or button default behavior does not interrupt fetch.
7. Verify script execution order and duplicate element IDs.
8. Verify the exact button selector and handler attachment.
9. Check network request events for blocked or canceled fetch calls.
10. Compare forced DOM click versus normal click behavior.

## 7. Proposed Evidence Commands

Use runtime-only evidence collection with commands and probes such as:

1. Playwright console listener.
2. Playwright `page.on('request')` listener.
3. Playwright `page.on('requestfailed')` listener.
4. `page.evaluate` handler-presence checks.
5. DOM button event-listener inspection if available.
6. Direct fetch from page context: `fetch('/api/premium-report-factory/intake/preview', ...)`.
7. Direct invocation of any exposed preview handler if globally reachable.
8. Flask log observation during each click-path attempt.

## 8. Proposed Decision Tree

Decision logic for diagnostic interpretation:

1. If direct page-context fetch works, the handler or event path is faulty.
2. If direct page-context fetch fails, browser or network or runtime context is faulty.
3. If handler is bound but fetch is not called, a JavaScript exception occurs before fetch.
4. If fetch is called but request fails, a network or CORS or session issue exists.
5. If fetch succeeds but render fails, render-function or state-update path is faulty.

## 9. Safety And Governance Guardrails

This diagnostic design preserves strict governance:

1. No implementation patch in this diagnostic slice.
2. No endpoint changes.
3. No dashboard changes.
4. No queue persistence changes.
5. No token, scoring, ledger, or report-behavior changes.
6. Clean runtime artifacts after any diagnostic run.

## 10. Explicit Non-Goals

This diagnostic slice does not include:

1. No Phase 3 work.
2. No PDF generation.
3. No result lookup.
4. No learning or calibration changes.
5. No web discovery.
6. No customer billing.
7. No save-queue redesign.
8. No speculative patching.

## 11. Final Diagnostic Design Verdict

Diagnostic design is approved only as a docs-only boundary for runtime mismatch investigation.

Implementation or fix work remains blocked until diagnostic evidence identifies the exact cause and a separate fix-design slice is explicitly opened.