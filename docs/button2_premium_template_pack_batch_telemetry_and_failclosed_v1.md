# Button 2 Premium Template Pack Batch Telemetry and Fail-Closed v1

## Slice
- `button2-premium-template-pack-batch-telemetry-and-failclosed-v1`

## Objective
Add per-row renderer telemetry and strict fail-closed customer-ready gating to Button 2 batch generation so plain/fallback output cannot be accepted as customer-ready.

## Scope Lock
- Updated only batch generation behavior in `/api/button2/generate-selected-batch`.
- No changes to Button 1 flow, Button 3 flow, queue promotion behavior, or legacy bulk-generation semantics outside this route.

## Batch Route Changes
### 1) Per-row telemetry fields
Each row now reports:
- `renderer_route_used`
- `renderer_profile`
- `template_pack_root`
- `template_pack_asset_backed`
- `premium_template_confirmed`
- `customer_ready`
- `visual_gate_status`
- `content_gate_passed`

### 2) Fail-closed premium renderer gating
- Rows fail if generation is not premium template-pack routed.
- `customer_ready` is only true when premium renderer telemetry confirms an asset-backed premium profile.
- Missing template assets propagate explicit errors (for example `template_pack_unavailable`).

### 3) Strict PDF quality gate in batch
For successful premium-render rows, batch now runs strict text/page/content checks before accepting output:
- Selected fighters/event/source presence checks
- 24-page requirement
- Output path safety checks under configured root
- Premium marker requirements
- Stale template-name bleed rejection (including `Bahram Rajabzadeh vs Donovan Wisse` and `Anthony Joshua vs Daniel Dubois` for unrelated selections)

Rows failing this gate are rejected with:
- `error = "pdf_quality_gate_failed"`
- `content_gate_passed = false`
- `customer_ready = false`
- `visual_gate_status = "pdf_quality_gate_failed"`

## Validation
### Test Run
- `python -m pytest operator_dashboard/test_button2_premium_template_pack_binding_and_visual_upgrade_v1.py`
- Result: `10 passed`

### Behavior Verified
- Premium batch rows are accepted and counted as generated when telemetry + quality gates pass.
- Template-pack unavailable path is fail-closed with explicit error propagation.
- Stale sample-name bleed rows are fail-closed and counted as failures.
- Governance write/delivery/learning flags remain false in response contracts.

## Files Changed
- `operator_dashboard/app.py`
- `operator_dashboard/test_button2_premium_template_pack_binding_and_visual_upgrade_v1.py`
- `docs/button2_premium_template_pack_batch_telemetry_and_failclosed_v1.md`
- `ops/release_checks/button2_premium_template_pack_batch_telemetry_and_failclosed_v1/template_pack_batch_telemetry_summary.json`

## Final Verdict
Button 2 batch generation now emits row-level renderer telemetry and enforces strict fail-closed customer-ready gating, including stale template-name bleed rejection, with passing targeted regression tests.
