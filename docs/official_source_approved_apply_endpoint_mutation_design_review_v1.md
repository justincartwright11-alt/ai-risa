# official-source-approved-apply-endpoint-mutation-design-review-v1

## Review scope

This is a docs-only review of the approved-apply endpoint-mutation design.

Reviewed inputs:

- `official_source_approved_apply_endpoint_mutation_design_v1`
- `official_source_approved_apply_mutation_adapter_design_v1`
- `official_source_approved_apply_mutation_adapter_v1`
- `official_source_approved_apply_contract_v1`
- `official_source_approved_apply_endpoint_integration_design_v1`

Out of scope:

- No implementation changes.
- No endpoint code changes.
- No mutation logic changes.
- No token consume persistence changes.
- No UI/template changes.
- No batch changes.
- No scoring changes.

---

## Findings

### 1. Blocking — implementation ordering currently allows a write-capable endpoint before token-consume design exists

Severity: blocking

The reviewed design correctly states that token consume remains deferred and that the endpoint-
mutation implementation slice would still return `token_consume_performed=false`. However, the
future micro-slice ordering still places:

1. `official-source-approved-apply-endpoint-mutation-implementation-v1`
2. `official-source-approved-apply-token-consume-design-v1`

That ordering would permit a runtime write-capable endpoint before token-consume behavior is fully
designed. In practical terms, the same approval token could remain reusable across requests after a
successful write until a later slice defines the consume model.

Why this matters:

- the adapter is already write-capable
- the endpoint design is the final bridge into runtime mutation
- without a consumed-token design, repeated use of the same approval token remains underspecified

Required correction:

- Either move `official-source-approved-apply-token-consume-design-v1` ahead of any runtime
  endpoint-mutation implementation slice, or
- explicitly constrain the future endpoint-mutation implementation slice to remain non-routable /
  dark until the token-consume design is approved.

Without one of those two corrections, this design should not be used to authorize live endpoint
wiring.

### 2. Blocking — authoritative preview source is required but not specified as a fail-closed contract

Severity: blocking

The reviewed design correctly requires the adapter to receive an authoritative preview result,
not the raw client-submitted `preview_snapshot`. But it does not define:

- the exact trusted source from which that authoritative preview is rebuilt
- the minimum fields that source must provide
- the fail-closed outcome when the authoritative preview cannot be reconstructed server-side
- the deterministic reason code for that condition

Why this matters:

- the current locked endpoint stub still synthesizes `authoritative_preview_result` from the client
  `preview_snapshot`
- the main safety property of the endpoint-mutation design is that mutation input becomes server-
  authoritative before adapter invocation
- without a defined source contract and deny classification, an implementation could silently fall
  back to the current client-echo pattern

Required correction:

- Define the authoritative preview source contract in docs before endpoint implementation.
- Require a fail-closed deny path when authoritative preview reconstruction is unavailable or
  incomplete.
- Add a deterministic deny classification, for example:
  - `authoritative_preview_unavailable`, or
  - `authoritative_preview_revalidation_failed`

Until that is documented, the endpoint-mutation design is incomplete for implementation.

---

## Non-blocking notes

- The additive response-field plan is sound and preserves the existing normalized envelope.
- The ban on direct `_upsert_single_manual_actual_result` use is explicit and correctly protects
  the locked adapter boundary.
- The pass-through requirement for adapter reason codes is correct and should remain unchanged.

---

## Guardrail consistency check

The reviewed design remains directionally consistent with locked safety boundaries:

- adapter is called only after `guard_allowed=true`
- authoritative preview is treated as mandatory
- legacy `_upsert_single_manual_actual_result` is not part of this endpoint path
- mutation audit fields are additive only
- adapter reason codes are preserved unchanged
- token consume remains deferred in this design stage
- batch, UI, and scoring changes remain out of scope

The two findings above do not contradict the intent of the design. They identify missing closure
conditions required before runtime implementation can be authorized.

---

## GO/NO-GO recommendation

Recommendation: NO-GO for endpoint-mutation implementation until both blocking findings are closed.

Allowed next step:

- A docs-only amendment or replacement of `official_source_approved_apply_endpoint_mutation_design_v1`
  that closes the two blockers.

Not allowed under this review:

- Any endpoint-mutation implementation.
- Any runtime call from the endpoint into the adapter.
- Any live write-capable endpoint activation.

---

## Required closure items

Before implementation is allowed, the design set must explicitly close:

1. token-consume design sequencing relative to runtime endpoint wiring
2. authoritative preview source contract and fail-closed deny classification

---

## Slice status

Design review status: REVIEW BLOCKED (docs-only)

Implementation status: NOT AUTHORIZED