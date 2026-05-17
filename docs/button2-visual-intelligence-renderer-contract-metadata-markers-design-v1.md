# Button 2 Visual Intelligence Renderer Contract Metadata Markers Design (v1)

## 1. Purpose
Design the first real renderer/readiness metadata markers for overlap, off-page text, page-block boundaries, hierarchy, source traceability, and visual certification status before changing renderer layout.

## 2. Locked QA Chain Foundation
- Acceptance rules: ai-risa-button2-visual-intelligence-acceptance-rules-v1 (1793c33)
- Renderer test scaffold: button2-visual-intelligence-renderer-test-scaffold-v1 (d9f6f93)
- Sample contract: button2-visual-intelligence-renderer-sample-contract-v1 (4ccb9cc)
- Contract adapter: button2-visual-intelligence-renderer-contract-adapter-v1 (0fdfc02)
- Compatibility layer: button2-visual-intelligence-renderer-contract-compatibility-layer-v1 (fa1fa76)
- Fail-closed gap evidence: button2-visual-intelligence-renderer-contract-compatibility-smoke-v1 (624493f)

## 3. Current Fail-Closed Gap
- Current Button 2 output cannot pass visual certification.
- Adapter requires `no_overlap=true` and `no_off_page_text=true` for certification.
- Current output sets these to `False` (unavailable), so QA chain fails closed.

## 4. Required Metadata Markers
- All future renderer output must include explicit metadata fields for:
  - `page_marker`
  - `hierarchy` (section/block order)
  - `visual_blocks` (with bounds)
  - `source_trace_block` (source summary)
  - `no_overlap` (visual overlap proof)
  - `no_off_page_text` (off-page text proof)
  - `visual_block_density_ok` (density proof)
  - `certification_status` (see below)

## 5. Page-Block Boundary Marker Contract
- Each visual block must include:
  - Unique `id`
  - `type` (summary, evidence, scenario, risk, etc.)
  - `bounds`: [x, y, width, height]
  - `page_index` (if multi-page)

## 6. Overlap Proof Marker Contract
- `no_overlap` must be set to `True` only if:
  - All visual block bounds are non-overlapping (no intersection except at edges).
  - Automated or deterministic check is performed at render time.
  - If overlap is detected, set to `False` and include `overlap_blocks` list.

## 7. Off-Page Text Proof Marker Contract
- `no_off_page_text` must be set to `True` only if:
  - All text/labels are fully contained within their visual block bounds and page bounds.
  - Automated or deterministic check is performed at render time.
  - If off-page text is detected, set to `False` and include `off_page_blocks` list.

## 8. Hierarchy Marker Contract
- `hierarchy` must:
  - List all major report sections/blocks in order of appearance.
  - Include `block` name and `order` index.
  - Match the order and structure of `visual_blocks`.

## 9. Source Traceability Marker Contract
- `source_trace_block` must:
  - List all sources referenced in the report page.
  - Each source: `id`, `type`, `date`, and (if available) `confidence`.
  - All claims/blocks must be traceable to at least one source.

## 10. Certification Status Model
- `certification_status` field must be present:
  - `"uncertified"`: default, if any required proof is missing or `False`.
  - `"certified"`: only if all required markers are present and true.
  - `"fail_closed"`: if any marker is explicitly failed (e.g., overlap detected).
  - `"unavailable"`: if renderer cannot determine proof (should not be used for final output).

## 11. Fail-Closed Behavior
- If any required marker is missing or `False`, output must:
  - Set `certification_status` to `fail_closed` or `uncertified`.
  - Never set to `certified` unless all checks pass.
  - Never fake visual safety signals.

## 12. Future Implementation Tests
- All future renderer output must be tested for:
  - Presence and correctness of all metadata markers.
  - Adapter must pass only if `certification_status` is `certified`.
  - Fail-closed tests must remain in place.

## 13. Non-Goals
- No PDF layout or visual design changes in this slice.
- No dashboard or report-generation changes.
- No fake or placeholder certification.

## 14. Final Verdict
- This design locks the metadata marker contract for Button 2 visual intelligence QA.
- All future renderer/readiness work must implement these markers before visual certification is possible.
- No renderer or PDF layout changes are permitted until metadata proof is implemented and tested.
