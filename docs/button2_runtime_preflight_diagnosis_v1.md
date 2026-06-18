# Button 2 Runtime Preflight Diagnosis v1

Slice: button2-runtime-preflight-diagnosis-v1  
Date: 2026-06-18  
Status: Diagnosis-only

## Goal

Diagnose current Button 2 runtime preflight failures shown in the Operator Dashboard without applying repairs.

## Scope Covered

1. BUTTON2_PDF_OUTPUT_ROOT resolution
2. MSYS2 / GTK PATH readiness
3. WeasyPrint import/runtime readiness

## Hard-Boundary Confirmation

This slice is diagnosis-only.

No PDF generation.  
No report delivery.  
No Button 1 provider/authorization changes.  
No Button 3 learning/calibration changes.  
No customer output changes.  
No queue/database writes.  
No runtime behavior changes.

## Current Preflight Field Values (Observed)

Observed from dashboard preflight panel and matching backend logic:

- BUTTON2_PDF_OUTPUT_ROOT: MISSING / value: unset
- MSYS2 / GTK DLL path: MISSING / value: C:\\msys64\\ucrt64\\bin / path exists: yes / in PATH: no
- WeasyPrint render readiness: MISSING / value: import_error:OSError
- reports output directory: READY / exists: yes / writable: yes
- safe PDF open route availability: READY / route: /api/button2/generated-report/open
- current server port: READY / value: 5050

## Files / Functions Inspected

- operator_dashboard/app.py
- operator_dashboard/button2_pdf_output_root_config_v1.py
- operator_dashboard/test_button2_pdf_output_root_config_preview_v1.py
- operator_dashboard/test_operator_dashboard_runtime_preflight_status_panel_v1.py
- scripts/start_ai_risa_dashboard_windows.ps1
- operator_dashboard/templates/index.html

Key backend functions:

- _build_runtime_preflight_status(host_value)
- _path_is_in_process_path(target_path)
- get_pdf_output_root()
- button2_generated_report_open_v1()
- button2_generated_report_library_v1()

## Diagnosis Findings

### 1) BUTTON2_PDF_OUTPUT_ROOT resolution

Classification: Configuration not loaded into running process.

Evidence:

- Preflight reads BUTTON2_PDF_OUTPUT_ROOT directly from process env and marks ready only if non-empty and existing directory.
- Value is currently unset in the running process.
- reports directory is independently checked and is READY, but this does not act as fallback for BUTTON2_PDF_OUTPUT_ROOT.
- get_pdf_output_root() is strict and raises when env var is absent/empty; tests confirm no default substitution behavior.

Root-cause summary:

- Runtime expects explicit env var injection.
- Current server process was started without BUTTON2_PDF_OUTPUT_ROOT set.

### 2) MSYS2 / GTK PATH readiness

Classification: Dependency path present on disk but missing from process PATH.

Evidence:

- Preflight target path is hardcoded to C:\\msys64\\ucrt64\\bin.
- Path-exists check passes; in-process-PATH check fails.
- scripts/start_ai_risa_dashboard_windows.ps1 explicitly prepends this folder to PATH, indicating intended startup contract.

Root-cause summary:

- Server process not launched with expected PATH injection contract.

### 3) WeasyPrint import/runtime readiness

Classification: Native runtime dependency load failure (import_error:OSError).

Evidence:

- Preflight attempts import weasyprint and records exception class only.
- Current value is import_error:OSError, consistent with missing native DLL runtime chain on Windows.
- Given GTK path is not in process PATH, unresolved native dependencies are the most likely proximate cause.

Root-cause summary:

- WeasyPrint import is failing due to unresolved native runtime dependencies in the active process environment.

## Cross-Check: Fallback Behavior

- reports output directory READY does not override missing BUTTON2_PDF_OUTPUT_ROOT.
- Safe open route can be READY while output-root preflight is MISSING; route existence and runtime root config are separate checks.

## Recommended Repair Order (Not Applied Here)

1. Output-root resolution first
- Ensure BUTTON2_PDF_OUTPUT_ROOT is set in the same process that runs Flask.
- Confirm preflight flips from MISSING to READY.

2. MSYS2/GTK PATH injection second
- Ensure C:\\msys64\\ucrt64\\bin is present in process PATH (or equivalent DLL directory handling in process startup).
- Confirm preflight path check flips to READY.

3. WeasyPrint import proof third
- Re-check preflight for import_ok.
- Capture explicit proof artifact after dependency chain is resolved.

## Verdict

Diagnosis completed with no runtime changes applied.

- No-runtime-change verdict: PASS
- Button 1 governance untouched verdict: PASS
- Button 3 learning/calibration untouched verdict: PASS
