# Button 2 Report Generation Route — Render Gate Prerequisite Discovery (v1)

**Slice:** `button2-report-generation-route-render-gate-prerequisite-discovery-v1`
**Date:** 2026-05-17
**Status:** LOCKED — discovery-only, no implementation changes

---

## Purpose

Discover and lock the exact implementation prerequisites before the `generate_report` route in `operator_dashboard/app.py` may call `render_button2_pdf()`.

All five required proofs are documented below.

---

## Proof 1 — Composition Pipeline Entry Point

**Finding: DOES NOT EXIST — BLOCKER**

No `build_report_html` or equivalent HTML-generating function exists anywhere in the operator dashboard codebase.

The existing Button 2 composition pipeline (`button2_dossier_handoff_report_context_preview.py`) produces a `report_context_preview` dict — structured metadata, not HTML. This dict is the input to a further step that would render HTML via a Jinja template or equivalent, but that HTML-rendering step has not been built.

**Evidence:**
- Searched all `operator_dashboard/*.py` for: `build_report_html`, `generate_report_html`, `compose_report`, `report_html`, `render_report` — zero matches.
- `build_button2_dossier_handoff_report_context_preview()` returns a dict with `report_context_preview` key containing fight metadata, section content, flags, and proof fields.
- No template rendering call (`render_template`, `jinja2.Template`) appears in the Button 2 composition chain.

**Blocker consequence:** The route integration slice (`button2-report-generation-route-render-gate-integration-preview-v1`) cannot proceed until an HTML composition entry point is built and its contract locked in its own slice.

**Required prior slice:**
```text
button2-html-composition-entry-point-design-v1
→ button2-html-composition-entry-point-preview-v1
```

---

## Proof 2 — Output Root Configuration

**Finding: DOES NOT EXIST — BLOCKER**

No configured PDF output root exists in the operator dashboard. No `OUTPUT_DIR`, `REPORTS_DIR`, `PDF_OUTPUT`, or equivalent constant, env var, or config object is present in any `operator_dashboard/*.py` file.

**Evidence:**
- Searched all Python files for `output_dir`, `output_root`, `OUTPUT_DIR`, `REPORTS_DIR`, `PDF_OUTPUT` — zero matches in `operator_dashboard/`.
- `search_pdf.py` (a standalone utility script, not dashboard code) references `C:\ai_risa_data\reports\` as a hardcoded path. This is not a configuration — it is a local test path in an unrelated script and must not be treated as the configured output root.
- The local AI orchestrator uses `workspace_root` for queue/state file resolution, not for PDF output.

**Blocker consequence:** Any file write requires a safe, server-controlled output root. Without a configured root, `_resolve_output_path(fight_key)` cannot be implemented safely. A hardcoded path must not be introduced.

**Required prior slice:**
```text
button2-pdf-output-root-config-design-v1
→ button2-pdf-output-root-config-preview-v1
```

The config must:
- Read from an env var (e.g., `BUTTON2_PDF_OUTPUT_ROOT`)
- Have no default that writes to a system path
- Raise a configuration error if the var is absent and a write is attempted
- Be validated before any `open()` call

---

## Proof 3 — fight_key Format and Safe Path Derivation Rules

**Finding: KNOWN — READY**

The `fight_key` identifier format is established across the codebase. Path derivation rules can be written without further discovery.

**Evidence:**
- Primary identifier field: `fight_key` (used in queue rows, runtime context, save-selected flow)
- Secondary aliases resolved in priority order by `_candidate_identifier()` in `local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview.py`:
  ```python
  for key in ("candidate_id", "fight_id", "fight_key", "matchup_key", "id", "fight_name"):
  ```
- Observed fight_key values across tests and scripts:
  - `bahram_rajabzadeh_vs_donovan_wisse` (from `search_pdf.py`)
  - `jiri_vs_ankalaev` (from Button 3 live executor tests)
  - `song_vs_figueiredo`, `prochazka_vs_ulberg` (from event anomaly tests)
  - `f1`, `f2` (synthetic test keys)

**Safe path derivation rules (locked):**

A `fight_key` is safe for use in a file path if and only if:
1. It is a non-empty string
2. It contains only characters matching `[a-z0-9_-]` (lowercase alphanumeric, underscore, hyphen)
3. It does not contain `.`, `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`
4. It does not start or end with `-` or `_`
5. After stripping, it resolves to a path component only (no directory separators)
6. `os.path.basename(fight_key) == fight_key` (final safety check after join)

Output filename convention: `{fight_key}_premium.pdf`

Example:
- `bahram_rajabzadeh_vs_donovan_wisse` → `bahram_rajabzadeh_vs_donovan_wisse_premium.pdf` ✓
- `../../etc/passwd` → REJECTED (path traversal) ✓
- `fight/one` → REJECTED (separator) ✓

---

## Proof 4 — Existing Route Approval Behavior

**Finding: CONFIRMED — CORRECT**

The `generate_report` route in `operator_dashboard/app.py` (line 186–204) enforces Gate 2 approval correctly.

**Current implementation:**
```python
@app.route("/api/operator/button2/generate-report", methods=["POST"])
def generate_report():
    data = request.get_json(silent=True) or {}
    approved = data.get("operator_approved", False)
    if not approved:
        return jsonify({
            "ok": False,
            "error": "operator_approval_required",
            "message": "PDF generation must be approved by operator."
        }), 403
    return jsonify({"ok": True, "message": "gate_passed_no_fight_selected"})
```

**Confirmed behaviors:**
- `operator_approved` absent or `False` → 403, no further processing
- `operator_approved: true` → stub pass, no render, no composition, no file write
- No fight selection happens today
- No HTML composition happens today
- No WeasyPrint call happens today
- No file write happens today

**Ruling:** The gate is correct. It must not be weakened. The stub response `gate_passed_no_fight_selected` is the correct placeholder until both blockers are resolved.

---

## Proof 5 — Should the Route-to-Render Write Path Open Now?

**Finding: NO — BLOCKED**

Two hard blockers prevent the implementation slice from proceeding:

| Blocker | Status |
|---------|--------|
| HTML composition entry point | Does not exist |
| PDF output root configuration | Does not exist |

Opening the route-to-render write path without resolving both blockers would require either:
- Hardcoding an HTML string inline in the route (violates composition-pipeline architecture)
- Hardcoding an output path (OWASP path traversal risk, non-configurable)

Neither is acceptable. The route must remain a stub until both blockers are resolved in their own design + implementation slices.

---

## Revised Implementation Order

The original next slice (`button2-report-generation-route-render-gate-integration-preview-v1`) is **deferred** until both blockers are cleared. Revised order:

```
1. button2-html-composition-entry-point-design-v1          [design]
2. button2-html-composition-entry-point-preview-v1         [impl]
3. button2-pdf-output-root-config-design-v1                [design]
4. button2-pdf-output-root-config-preview-v1               [impl]
5. button2-report-generation-route-render-gate-integration-preview-v1   [impl — now unblocked]
```

Slices 1–2 and 3–4 are independent and may be designed in parallel.

---

## What Has NOT Changed

| Scope | Status |
|-------|--------|
| `operator_dashboard/app.py` | Unchanged — `generate_report` is still a stub |
| Gate 2 approval flow | Unchanged |
| Button 2 composition pipeline | Unchanged |
| Customer PDF output | No change — no PDF generated |
| Dashboard UI | Unchanged |
| Visual certification | Still `not_certified` — no approval given |
