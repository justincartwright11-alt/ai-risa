# Button 2 Report Generation Route Render Gate Integration — Final Handoff (v1)

**Slice:** `button2-report-generation-route-render-gate-integration-final-handoff-v1`
**Date:** 2026-05-17
**Status:** LOCKED — docs-only, freezes complete integration chain before visual polish

---

## Summary

The Button 2 report-generation route render-gate integration is **complete, tested, and locked**. The
`/api/operator/button2/generate-report` POST endpoint now:

1. Enforces Gate 2 operator approval as the first non-negotiable guard
2. Validates fight_id and ingest payload
3. Builds report context via the locked composition pipeline
4. Produces safe HTML via the locked composition entry point
5. Calls the locked render gate with optional geometry extraction
6. Resolves output path server-side from fight_id only (no user-supplied paths)
7. Writes PDF file to the configured temp output root
8. Keeps visual QA as optional, best-effort, and fail-closed
9. Prevents partial writes on failure at any stage

**All prerequisites are met. The route is proof-locked and ready for next phase.**

---

## Integration Chain: Four Slices

### Slice 1: HTML Composition Entry Point Design + Implementation

**Commits:** `1c79d60` (design), `2e94a1b` (preview)
**Tags:** `button2-html-composition-entry-point-design-v1`, `button2-html-composition-entry-point-preview-v1`
**Tests:** 42 passed
**Scope:** Converts `report_context_preview` dict → safe HTML string for render gate

**Key Guarantees:**
- No external URL references in CSS
- All dynamic values HTML-escaped at composition time
- Proof fields rendered as labels only (no detail leakage)
- `preview_only=True`, `pdf_generation_performed=False`, `file_write_performed=False`
- Rejects malformed/wrong marker input with fail-closed errors

**Module:** `operator_dashboard/button2_html_composition_entry_point_v1.py`
**Public API:** `build_button2_report_html(report_context_preview) → {"ok", "error", "html_content", **flags}`

---

### Slice 2: PDF Output Root Configuration Design + Implementation

**Commits:** `ab71ada` (design), `300975b` (preview)
**Tags:** `button2-pdf-output-root-config-design-v1`, `button2-pdf-output-root-config-preview-v1`
**Tests:** 35 passed
**Scope:** Server-controlled output directory and safe fight_id → filename derivation

**Key Guarantees:**
- Configuration read from `BUTTON2_PDF_OUTPUT_ROOT` env var only (no default)
- Env var absent or relative path → `OutputRootNotConfiguredError` (fail-closed)
- fight_id allowlist: `[a-zA-Z0-9_-]` only, max 200 chars (rejects `/`, `\`, `..`, unicode)
- Output filename: `{fight_key}_premium.pdf` (server-derived only)
- Traversal guard: `os.path.realpath` + `startswith(root + os.sep)` check

**Module:** `operator_dashboard/button2_pdf_output_root_config_v1.py`
**Public API:**
- `get_pdf_output_root() → str` (raises if not configured)
- `resolve_pdf_output_path(fight_key: str) → str` (returns canonical absolute path)

---

### Slice 3: Report Generation Route Render Gate Integration Design + Implementation

**Commits:** `34aa896` (design-only, included in carryforward), `7b408f4` (preview)
**Tags:** `button2-report-generation-route-render-gate-integration-design-v1`, `button2-report-generation-route-render-gate-integration-preview-v1`
**Tests:** 30 focused tests, 98 total Button 2 tests passed
**Scope:** Wire HTML composition + render gate + output path resolution into the route

**Key Guarantees:**
- Gate 2 approval check first (non-negotiable, returns 403 if absent)
- fight_id required and validated
- Ingest payload required and validated
- Composition → Context → HTML → Render → Path → File (all or nothing)
- No render without composition success
- No path resolution without render success
- No file write without path resolution success
- File write only after all prior steps pass

**Module:** `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`
**Public API:** `generate_button2_report_render_gate_integration(request_data) → {"ok", "error"/"message", "output_path", "qa_summary", **telemetry}`

**Route Change:** `/api/operator/button2/generate-report` now calls the integration function instead of returning a stub pass.

---

### Slice 4: Route Integration Smoke Tests (Real File I/O)

**Commit:** `938a8d3`
**Tag:** `button2-report-generation-route-render-gate-integration-smoke-v1`
**Tests:** 13 smoke tests, 339 total Button 2 tests passed
**Scope:** Executable proof using real temp file I/O

**Test Coverage:**
- **Approval Guard + No Side Effects** (3 tests): No approval → 403 immediately, no composition/render/write
- **Approved Success + Real File I/O** (2 tests): Approved request writes PDF to temp output root
- **Failure Modes (No Partial Writes)** (3 tests): Invalid fight_id, missing output root, render failure → no write
- **Visual QA Optional + Best-Effort** (3 tests): Disabled by default, enabled via env var, failures don't crash
- **Telemetry Flags** (2 tests): Flags correctly reflect actual behavior

---

## Safety Constraints: All Locked

| Constraint | Implementation | Proof |
|-----------|-----------------|-------|
| **Gate 2 First** | Approval check before any function call | 3 approval guard tests |
| **No Approval = No Side Effects** | Returns 403 before composition/render/path/write | 3 smoke tests verify no calls made |
| **fight_id Validated** | Allowlist `[a-zA-Z0-9_-]` via regex, max 200 chars | 12 fight_key validation tests |
| **Output Path Server-Derived** | `resolve_pdf_output_path(fight_id)` only, no user input | 3 output path resolution tests |
| **No Partial Writes** | Composition fail → no render, render fail → no path, path fail → no write | 4 no-partial-writes tests |
| **PDF Generated Flag** | Set True only when render succeeds | 4 pdf_generation_performed tests |
| **File Write Flag** | Set True only when file write succeeds | 3 file_write_performed tests |
| **Visual QA Optional** | Disabled by default, best-effort, doesn't crash report | 3 visual QA optional tests |
| **No External URLs** | Inline CSS only, no `url()` references | 4 HTML composition escaping tests |
| **Escaping Safe** | All dynamic values HTML-escaped at composition time | 4 XSS probe tests |

---

## Integration Flow: Locked

```
POST /api/operator/button2/generate-report
├─ Request body: {operator_approved, fight_id, ingest_payload}
│
├─ [GATE 2] approval check
│  └─ if not approved → return 403 + {error: "operator_approval_required"}
│
├─ validate fight_id (required, non-empty string)
│  └─ if invalid → return 400 + {error: "fight_id_required"}
│
├─ validate ingest_payload (required, dict)
│  └─ if invalid → return 400 + {error: "ingest_payload_required"}
│
├─ build_button2_readonly_dossier_handoff_ingest_preview(ingest_payload)
│  └─ if fail → return 400 + {error: "ingest_context_invalid"}
│
├─ build_button2_dossier_handoff_report_context_preview(ingest_context)
│  └─ if fail → return 400 + {error: "report_context_invalid"}
│
├─ build_button2_report_html(report_context_preview)
│  └─ if fail → return 400 + {error: "html_composition_failed"}
│
├─ render_button2_pdf(html_content)
│  └─ if fail → return 500 + {error: "pdf_render_exception"}
│  └─ if success → set pdf_generation_performed=True
│
├─ resolve_pdf_output_path(fight_id)
│  └─ if fail → return 400 + {error: "output_path_invalid"}
│
├─ os.makedirs(output_dir, exist_ok=True)
│  └─ if fail → return 500 + {error: "file_write_failed"}
│
├─ write PDF to output_path
│  └─ if fail → return 500 + {error: "file_write_failed"}
│  └─ if success → set file_write_performed=True
│
├─ [OPTIONAL] if BUTTON2_VISUAL_QA=1 and geometry_data is not None:
│  └─ run_geometry_proof(geometry_data) → qa_summary
│  └─ (best-effort; failure doesn't crash report)
│
└─ return 200 + {ok: True, output_path, qa_summary, **telemetry}
```

---

## Test Evidence

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_button2_html_composition_entry_point_preview_v1.py` | 42 | Core success, routing, proof placement, validation, escaping, invariants |
| `test_button2_pdf_output_root_config_preview_v1.py` | 35 | Env var read, allowlist, length limit, traversal guard, symlink escape |
| `test_button2_report_generation_route_render_gate_integration_preview_v1.py` | 30 | Approval guard, fight selection, composition, render, path resolution, file write, no partial writes, visual QA, error handling |
| `test_button2_report_generation_route_render_gate_integration_smoke_v1.py` | 13 | Real temp file I/O, approval guard side effects, success writes, failure no-writes, visual QA optional, telemetry flags |
| **Total Button 2** | **339 tests** | Complete integration coverage |

---

## What Was NOT Changed

| Component | Status | Reason |
|-----------|--------|--------|
| Button 1 | Unchanged | No integration changes; Button 1 → Button 2 handoff unchanged |
| Button 3 | Unchanged | No integration changes; independent from Button 2 route |
| Dashboard UI | Unchanged | Route integration is API-only; UI will be separate slice |
| PDF rendering engine | Unchanged | Render gate is already locked, only called from route now |
| Visual QA infrastructure | Unchanged | Geometry extraction and proof instrumentation unchanged |
| Approval gate logic | Unchanged | Gate 2 check preserved exactly; only added downstream wiring |
| Customer PDF delivery | Unchanged | No file writes to production customers; temp output root only |

---

## What Comes Next: Two Ordered Slices

### Next Design Slice (Deferred)

```text
button2-customer-pdf-visual-polish-safe-roadmap-v1
```

**Purpose:** Define the visual/layout polish sequence now that the guarded generation path is proven.

**Scope:**
- CSS improvements for PDF rendering
- Typography polish
- Color/spacing refinement
- Page breaks and section layout
- Export format (watermarks, headers, footers)
- **All behind existing approval gates**

**Safety Constraint:** No changes to approval logic, no new file write paths, no customer data changes.

---

### Future Implementation Slices (Beyond This Handoff)

After the visual polish design is locked:

1. **Visual polish implementation** (CSS/layout only, behind gates)
2. **PDF export improvements** (format, compression, metadata)
3. **Advanced dashboard surface** (QA results, accuracy metrics, decision support)
4. **Customer delivery workflow** (not in scope yet; approval + QA signals only)

---

## Handoff Checklist

All items locked before next phase:

- [x] HTML composition entry point proven (42 tests)
- [x] Output root configuration proven (35 tests)
- [x] Route integration proven (30 + 13 = 43 tests)
- [x] Total Button 2 test coverage: 339 passed
- [x] Gate 2 approval non-negotiable (proven in all 3 failure scenarios)
- [x] No partial writes on failure (proven in 4 failure modes)
- [x] File write only after all stages pass (proven in real temp I/O tests)
- [x] Visual QA optional and best-effort (proven in 3 tests)
- [x] All escape/XSS probes passed (4 HTML tests)
- [x] All fight_key validation rules passed (12 tests)
- [x] Telemetry flags correct (2 tests)
- [x] Route integration locked in `app.py`
- [x] No changes to Button 1, Button 3, or approval logic
- [x] Docs-only design locked

---

## Key Commits in Chain

```
1c79d60  button2-html-composition-entry-point-design-v1
2e94a1b  button2-html-composition-entry-point-preview-v1
ab71ada  button2-pdf-output-root-config-design-v1
300975b  button2-pdf-output-root-config-preview-v1
34aa896  button2-report-generation-route-render-gate-integration-design-v1
7b408f4  button2-report-generation-route-render-gate-integration-preview-v1
938a8d3  button2-report-generation-route-render-gate-integration-smoke-v1
```

---

## Deployment Notes

When ready to move to production:

1. **Set env var:** `BUTTON2_PDF_OUTPUT_ROOT=/path/to/production/pdf/output`
   - Must be absolute path
   - Directory must be writable by application user
   - No default; absent var triggers safe error

2. **Visual QA disabled by default** — set `BUTTON2_VISUAL_QA=1` to enable

3. **Test before deploy:**
   - Run `pytest operator_dashboard/test_button2_*.py -v` (339 tests)
   - Verify temp file I/O tests pass
   - Verify approval gates in place

4. **Monitor:** File write errors, PDF generation exceptions, visual QA failures (best-effort, shouldn't fail)

---

## Sign-Off

This integration chain is **complete, tested, locked, and safe**. No changes to approval logic.
Gate 2 operator approval remains the first and non-negotiable guard. Output paths are server-derived only.
Visual QA is optional and fail-closed. All prerequisites met for next phase.

Ready for visual polish design and customer delivery workflow design.
