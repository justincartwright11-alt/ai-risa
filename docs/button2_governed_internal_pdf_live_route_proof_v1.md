# Button 2 Governed Internal PDF Live-Route Proof v1

## Purpose and Scope

This record locks live localhost evidence for the governed internal PDF backend route. The proof covers one fictional internal fixture request, deterministic artifact generation, collision protection, artifact inspection, containment, cleanup, and preservation of the pre-existing worktree state.

## Locked Implementation

- Route commit: `9f7a824`
- Branch: `ai-risa-mainline`
- Endpoint: `POST /api/button2/governed-internal-pdf/generate-v1`

## Environment Gates

The live proof required:

- `AI_RISA_LOCAL_FIXTURE_MODE=1`;
- the governed fixture path;
- an explicit external internal-output root;
- explicit internal-test-artifact acknowledgement.

## First-Request Proof

The first valid request returned HTTP 200 with `ok=true` and generated exactly one PDF. The deterministic fixture and report identity were preserved. The artifact classification was `governed_internal_test_pdf`.

The first response recorded:

- `customer_ready_possible=false`;
- `customer_release_authorized=false`;
- `queue_write_performed=false`;
- `permanent_mutation_performed=false`.

## Artifact Verification

Independent inspection confirmed:

- file size: `11,094 bytes`;
- page count: `1`;
- valid `%PDF-` signature;
- SHA-256: `8b9ba89a04b2884313605b1c48e551ce8dc6176d3c2f228eea8587c0b8b19533`;
- independent SHA-256 matched the response;
- required internal/test labels were present, including the internal fixture, non-customer-release label, both fictional fighter names, report ID, and report version.

## Collision and Overwrite Proof

The second identical request returned HTTP 422 and was blocked with reason `proposed_output_target_exists`.

The blocked response recorded:

- `pdf_generation_performed=false`;
- `pdf_generation_count=0`;
- `artifact_overwritten=false`.

The original artifact size and hash remained unchanged, and no second PDF was created.

## Safety Evidence

The live proof recorded the following safety flags:

- `customer_ready_possible=false`;
- `customer_release_authorized=false`;
- `queue_write_performed=false`;
- `learning_applied=false`;
- `calibration_applied=false`;
- `accuracy_ledger_written=false`;
- `gcid_written=false`;
- `model_weights_changed=false`;
- `fighter_ratings_changed=false`;
- `prediction_logic_changed=false`;
- `artifact_overwritten=false`;
- `permanent_mutation_performed=false`.

## Containment and Cleanup

- The output root was outside the repository.
- Exactly one PDF was written.
- The temporary output root was removed after inspection.
- Flask was stopped.
- Port 5050 was cleared.
- No repository file was created, edited, staged, or committed during proof execution.

## Limitations

This proof is limited to:

- a fictional fixture only;
- an internal/test route only;
- no dashboard control;
- no customer-ready authority;
- no customer release;
- no production authority;
- no bulk generation;
- no canonical output authority;
- no queue or ledger persistence;
- no learning, calibration, accuracy-ledger, or GCID authority;
- no deployment authority.

## Closure Verdict

BUTTON2_GOVERNED_INTERNAL_PDF_LIVE_ROUTE_PROOF=PASS
