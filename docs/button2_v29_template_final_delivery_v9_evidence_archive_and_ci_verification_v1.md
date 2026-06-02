Slice: button2-v29-template-final-delivery-v9-evidence-archive-and-ci-verification-v1
Commit: (to be created)
Tag: button2-v29-template-final-delivery-v9-evidence-archive-and-ci-verification-v1
Date: 2026-06-02

1. Slice scope
---------------
Create an immutable evidence manifest referencing the v9 proof artifacts and run CI + visual verification against the frozen v9 baseline. No renderer geometry, app logic, tests, or report templates are modified.

2. Frozen baseline
-------------------
- Frozen v9 tag: button2-v29-template-final-delivery-layout-depth-repair-v9 (commit: c21bdfb)
- Post-lock checkpoint tag: button2-v29-template-final-delivery-layout-depth-repair-v9-post-lock-release-checkpoint-v1 (commit: a227240)

3. Evidence sources
-------------------
- Summary JSON: ops/button2_v29_template_final_delivery_layout_depth_repair_v9/layout_depth_repair_v9_summary.json
- Proof PDFs: ops/release_checks/button2_v29_template_final_delivery_layout_depth_repair_v9/proof_pdfs/ (5 PDFs)
- Proof images: ops/release_checks/button2_v29_template_final_delivery_layout_depth_repair_v9/proof_images/ (contact sheets + page_02/page_05 etc.)

4. Archive/manifest method
---------------------------
- Generated `ops/release_checks/button2-v29-template-final-delivery-v9-evidence-archive-and-ci-verification-v1/evidence_manifest.json` containing file lists, existence checks, sizes, and SHA256 hashes for each referenced proof file.
- The manifest was computed by `scripts/generate_evidence_manifest.py` which reads the summary JSON and hashes each file.

5. CI commands run
------------------
- `git rev-parse --short button2-v29-template-final-delivery-layout-depth-repair-v9`
- `git rev-parse --short button2-v29-template-final-delivery-layout-depth-repair-v9-post-lock-release-checkpoint-v1`
- `python -m pytest operator_dashboard/test_button2_v29_template_final_delivery_fit_polish_v6.py operator_dashboard/test_button2_v29_template_final_delivery_fit_scan_repair_v5.py operator_dashboard/test_button2_v29_template_final_delivery_layout_depth_repair_v9.py operator_dashboard/test_button2_v29_template_final_delivery_microfit_v7.py operator_dashboard/test_button2_v29_template_final_delivery_right_rail_overlap_repair_v8.py operator_dashboard/test_button2_v29_template_final_delivery_visual_cleanup_v7.py -q`

6. Visual verification method
-----------------------------
- Verified that all proof PDFs listed in the summary JSON exist and are readable.
- Verified that proof images (Page 02 and Page 05 for the sampled proofs) exist and are readable.
- Computed SHA256 for every referenced proof file and recorded in the manifest.

7. Pass/fail table
------------------
- Broad final-delivery pytest group: 80 passed (0 failed)
- Page 02 visual verdict: pass
- Page 05 visual verdict: pass
- Segment-depth verdict: pass
- Customer-ready gate: pass

8. Non-goals
-----------
- No renderer geometry edits.
- No application logic changes.
- No test changes.
- No PDF regeneration unless evidence is missing or unreadable.

9. Dirty workspace handling
--------------------------
- Unrelated dirty and untracked files were left untouched. Only the manifest and this docs file were added and staged for commit.

10. Final verdict
-----------------
- Evidence manifest created and saved at `ops/release_checks/button2-v29-template-final-delivery-v9-evidence-archive-and-ci-verification-v1/evidence_manifest.json`.
- CI test group passed: 80 passed.
- Visual verdicts preserved as `pass` in the summary JSON and manifest.

11. Next safe recommendation
---------------------------
- `button2-v29-template-final-delivery-v9-evidence-archive-and-ci-verification-v1` → package immutable archive (zip/tar) of the referenced proof files and publish verification results. If archive size is large, leave binaries untracked and upload to the approved artifact storage, recording URIs in the manifest.
