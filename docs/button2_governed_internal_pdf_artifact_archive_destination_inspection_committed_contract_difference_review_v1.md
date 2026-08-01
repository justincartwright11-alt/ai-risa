# Button 2 Governed Internal PDF Artifact Archive Destination-Inspection Committed Contract Difference Review v1

## 1. Executive verdict

`COMMITTED_CONTRACT_DIFFERENCES_CONFIRMED_REMEDIATION_REQUIRED`

The committed adapter contains confirmed response and enforcement differences against the locked contracts. This review classifies those differences and corrects proof expectations. It authorizes no remediation by itself.

## 2. Locked baseline

- implementation commit: `336c79df2bb8e1d8c4b580ccec6687a1b0fb4654`;
- implementation-readiness verdict: `READY_FOR_READ_ONLY_DESTINATION_INSPECTION_ADAPTER_IMPLEMENTATION`;
- two-file verdict: `TWO_FILE_SCOPE_CONFIRMED_WITH_TEST_ONLY_PRIVATE_CAPABILITIES`;
- direct-proof status: `PROOF_HARNESS_FAILURE`;
- harness-readiness verdict: `DIRECT_PROOF_HARNESS_NOT_READY`;
- no confirmed direct-proof PASS;
- no endpoint, dashboard, production parser, producer, or mutation authority.

The initial baseline was captured with exactly these commands before inspection:

```text
git rev-parse HEAD
git branch --show-current
git status --short
git diff --name-status
git diff --cached --name-status
```

The result was HEAD `336c79df2bb8e1d8c4b580ccec6687a1b0fb4654`, branch `ai-risa-mainline`, an empty staged set, and a pre-existing dirty worktree. The complete tracked and untracked path listing from that command is preserved as the baseline; no pre-existing path is modified, staged, or discarded by this review. The dirty set includes modified/untracked Python bytecode under `operator_dashboard/__pycache__`, modified unrelated Button 2 test and proof-summary files, modified Button 3 runtime evidence, generated report PDFs, temporary scripts/text, evidence directories, runtime caches, and `tmp_pdf_output/`.

## 3. Review purpose

This review compares:

A. locked normative contracts;

B. committed adapter behavior;

C. committed focused-test expectations; and

D. direct-proof requirements.

Implementation behavior is not treated as authoritative where it conflicts with a locked contract. This is a documentation-only classification review.

## 4. Difference classification system

Every finding uses exactly one classification:

- `CONFIRMED_ADAPTER_DEFECT`;
- `CONFIRMED_TEST_EXPECTATION_DEFECT`;
- `CONFIRMED_DOCUMENTATION_CONFLICT`;
- `MISSING_CONTRACT_ENFORCEMENT`;
- `IMPLEMENTATION_CHOICE`;
- `PROOF_HARNESS_AUTHORITY`;
- `NOT_A_DEFECT`.

## 5. Absent-destination success behavior

The exact committed target-absence branch returns:

```text
status=DESTINATION_INSPECTION_COMPLETE
destination_status=DESTINATION_ABSENT
blocked_reason=invalid_destination_inspection_contract
inspection_completed=True
```

The branch returns before parser invocation, hashing, and trusted metadata validation. It preserves false safety flags and does not require destination metadata. The locked behavior is the same except that the successful no-reason representation must be empty. Therefore this is `CONFIRMED_ADAPTER_DEFECT`: the committed use of `invalid_destination_inspection_contract` is not a valid success response reason.

Exact remediation, when separately authorized: change only the absent-target response reason to the canonical empty no-reason representation; preserve status, destination status, inspection completion, parser prohibition, hashing prohibition, metadata prohibition, containment evidence, safety flags, and all other fields.

The existing focused test is also incomplete because it does not assert `blocked_reason == ""`; this is `CONFIRMED_TEST_EXPECTATION_DEFECT` for the missing assertion, not permission to change the test in this slice.

## 6. Parent-missing behavior

The committed parent loop maps `FileNotFoundError` to `_response(request, reason="parent_missing")`. The response therefore has the default `DESTINATION_INSPECTION_BLOCKED`, empty destination status, `inspection_completed=False`, and `action_performed=False`; the parser is not invoked.

The locked Windows capability/file-identity contract requires `DESTINATION_INSPECTION_UNAVAILABLE`, `parent_missing`, `inspection_completed=False`, and `action_performed=False`. This is `CONFIRMED_ADAPTER_DEFECT`, not a documentation conflict. Exact remediation, when separately authorized: change only the parent-missing response status to `DESTINATION_INSPECTION_UNAVAILABLE`; preserve the reason, empty destination status, completion flag, safety flags, and parser prohibition.

## 7. Remaining parent mappings

The committed mappings are:

| Condition | Committed reason/status | Classification |
|---|---|---|
| parent non-directory | `parent_non_directory` / blocked | `NOT_A_DEFECT` |
| parent link/reparse | `parent_link_or_reparse` / blocked | `NOT_A_DEFECT` |
| parent access denied | `parent_access_denied` / blocked | `NOT_A_DEFECT` |
| other parent inspection failure | `parent_inspection_failed` / blocked | `NOT_A_DEFECT` |

The locked contract requires these reasons and does not require a status change for these mappings in this review. No remediation is widened beyond parent missing.

## 8. Concrete conflict semantics

The committed path to `CONFLICTING_ARCHIVE_PRESENT` is after valid root, parent, target, regular-file, identity, signature, parser-result, page-count, SHA-256, and trusted-metadata validation. It compares source SHA-256, source size, and source page count with destination evidence. A valid destination whose file evidence differs concretely is therefore a concrete conflict. The expected result is:

```text
status=DESTINATION_INSPECTION_COMPLETE
destination_status=CONFLICTING_ARCHIVE_PRESENT
blocked_reason=""
inspection_completed=True
parser_invoked=True
hashing_performed=True
metadata_validated=True
```

The valid conflict fixture should alter exactly one concrete source-versus-destination evidence value, such as source SHA-256, source file size, or source page count, while retaining a valid request SHA-256 for the destination, valid parser result, valid trusted destination metadata, valid signature, valid file identity, and valid provenance. It must not use invalid or mismatched trusted metadata. This distinction is `NOT_A_DEFECT` in the adapter’s classification logic, subject to the missing schema enforcement findings below.

The successful existing-target response also passes `invalid_destination_inspection_contract` as the internal `reason` argument and then overwrites `blocked_reason` with `""`; this is the same `CONFIRMED_ADAPTER_DEFECT` as the absent-success no-reason defect. Exact remediation changes only the success response reason representation.

## 9. Classification-mismatch behavior

`classification_mismatch` is an evidence failure, not a concrete archive conflict. It must produce `DESTINATION_INSPECTION_BLOCKED`, empty destination status, and must not produce `CONFLICTING_ARCHIVE_PRESENT`. The earlier proof expectation that used classification mismatch as a concrete conflict is a `CONFIRMED_TEST_EXPECTATION_DEFECT`. The adapter’s `_metadata_valid` mapping to `classification_mismatch` is correct for that case.

## 10. Request closed-field enforcement

The request validator correctly enforces the exact top-level request field set, rejects unexpected and missing fields through set equality, checks contract version and action, validates bounded strings, lowercase SHA-256, strict integer types, non-negative size, and page-count bounds. No request enforcement difference is confirmed. Classification: `NOT_A_DEFECT`.

## 11. Source-evidence enforcement findings

The committed source validator rejects unknown fields but does not require the normative exact field set. The following are separate `MISSING_CONTRACT_ENFORCEMENT` findings:

- `inspection_contract_version` is not required or checked against its normative version;
- `source_boundary_id` is checked only after other checks but requiredness is not independently enforced;
- `source_identity` is not required as a complete normalized identity schema;
- `source_artifact_version_token` is not required and is not bound;
- `sha256` is not required or independently validated as normalized source evidence;
- `file_size_bytes` is not required or independently bounded;
- `page_count` is not required or independently bounded;
- `customer_ready_possible`, `customer_release_authorized`, `queue_write_performed`, `pdf_generation_performed`, `artifact_archived`, `artifact_removed`, `artifact_overwritten`, `permanent_mutation_performed`, and `action_performed` are not required as explicit false safety fields; `.get()` defaults can let missing evidence pass;
- source classification, warning, signature, parse, identity, and inspection fields are checked for true values when present but missing-field behavior is not closed-schema enforcement.

The committed subset check also means a source dictionary with omitted normative fields can pass the field-shape gate and be rejected or accepted based on later `.get()` behavior rather than the exact contract.

## 12. Composite-capability enforcement findings

The committed capability validator rejects unknown fields but does not require the normative exact field set. These are separate `MISSING_CONTRACT_ENFORCEMENT` findings:

- capability contract version is checked, but the complete required composite field set is not enforced;
- bounded capability ID and source ID/version validation is absent;
- `filesystem_policy_id`, `sanitization_policy_id`, `capability_source_id`, `capability_source_version`, and `expiry_or_validity_evidence` are accepted as absent;
- `root_configuration_fingerprint` and complete `root_identity` validation are not enforced;
- `root_observer`, `filesystem_observer`, and `identity_observer` callable validation is incomplete; the adapter invokes some callables without a complete capability schema guard;
- parser capability presence is checked only later and its nested closed schema is not enforced;
- `safety_flags` is accepted as absent and is not validated as the exact all-false structure;
- root identity completion/support and test-only authority are not fully validated;
- `internal_test_only`, `fixture_only`, and `production_capable` are checked only as selected booleans, not as a complete nested authority contract;
- `enabled`, `configured`, and isolation fields are read through `.get()` and missing values are collapsed into generic invalid/disabled outcomes rather than distinct missing-contract outcomes.

These are core contract-enforcement defects, not implementation choices. The locked test-only capability remains sufficient as a fixture shape only after exact validation is added.

## 13. Parser-capability findings

The normative parser-capability contract requires an exact field set, version, source identity/version, enabled/supported state, action false, bounded authority flags, parser callable, resource policy, and trusted metadata location. The committed checks only verify the version, then treat missing, disabled, and unsupported states together:

- exact parser-capability field set is not enforced: `MISSING_CONTRACT_ENFORCEMENT`;
- required capability source/version, action, authority, resource, and safety fields are not independently required: `MISSING_CONTRACT_ENFORCEMENT`;
- callable parser validation exists, but only after enabled/supported checks and without complete nested-schema validation: `MISSING_CONTRACT_ENFORCEMENT`;
- trusted metadata is retrieved from `parser_capability`, which is the locked location: `NOT_A_DEFECT`;
- unsupported versus disabled capability conditions require separate reasons under the normative contract. The committed condition maps both to `parser_capability_disabled`: `CONFIRMED_ADAPTER_DEFECT` requiring reason-registry/status-preserving remediation;
- parser capability missing, invalid, disabled, and unsupported must remain distinct from parser-result outcomes: `MISSING_CONTRACT_ENFORCEMENT` where those states are not independently validated.

## 14. Parser-result closed-schema enforcement

The normative parser-result schema is closed: all required fields must be present, optional fields are limited, and unknown fields are rejected. The committed `_result_valid` function checks only a small subset and reads other values later with `.get()`. The following are separate `MISSING_CONTRACT_ENFORCEMENT` findings:

- required fields such as completion, parser source/version/policy, resource policy, signature/parse booleans, content-safety booleans, isolation claims, timeout/memory/resource fields, freshness fields, evidence version, and safety structure are not all required;
- unknown fields are currently ignored;
- missing request and identity bindings can be represented through `.get()` and are not rejected as missing schema;
- production-isolation fields are not validated;
- timeout and resource fields are not independently validated;
- parser safety structure is not fully validated as an exact all-false schema;
- parser status is checked, but status-specific blocked reason and completion semantics are not fully enforced;
- page-count field type is validated only after the result passes the incomplete contract check.

These are core security-contract defects requiring remediation before direct proof. The test-only capability does not authorize weakening the production schema; production isolation remains a later dependency.

## 15. Trusted-metadata closed-schema enforcement

The normative trusted metadata envelope is exact and includes evidence completion, producer/source/version, integrity token, all request/root/policy/boundary/destination bindings, provenance, freshness, and action false. The committed `_metadata_valid` function checks only version, action false, selected request bindings, calculated hash/size/page, classification, warning, provenance booleans, and root ID/version. The findings are:

- exact metadata field set and unknown-field rejection are missing: `MISSING_CONTRACT_ENFORCEMENT`;
- `evidence_completed`, metadata source type/ID/version, and metadata integrity token are not validated: `MISSING_CONTRACT_ENFORCEMENT`;
- archive policy, archive boundary, destination-relative ID, and destination evidence token are not bound: `MISSING_CONTRACT_ENFORCEMENT`;
- source artifact version binding is not enforced: `MISSING_CONTRACT_ENFORCEMENT`;
- freshness and evaluated-at validation are absent: `MISSING_CONTRACT_ENFORCEMENT`;
- integrity-token enforcement is absent: `MISSING_CONTRACT_ENFORCEMENT`;
- provenance source type/ID and exact fixture/report/version provenance binding are absent: `MISSING_CONTRACT_ENFORCEMENT`;
- classification, warning, and provenance value checks that are present are not a substitute for the missing closed schema.

The missing integrity, identity, freshness, and closed-field checks block direct proof of the locked metadata contract. A production metadata producer and cryptographic integrity mechanism remain later production-integration dependencies.

## 16. Response closed-schema enforcement

The response builder establishes the complete stable top-level response shape and exact safety-key set for responses it creates. It uses `blocked_reason` as a bounded reason and preserves false safety flags. The confirmed response defect is the non-empty reason on successful absent and existing-target responses. Classification: `CONFIRMED_ADAPTER_DEFECT`.

No additional top-level response-shape defect is confirmed from the authorized files. Blocked results preserve an empty destination status by default, except explicit object classifications such as directory collision; that is consistent with the locked representation. `ok` is false for blocked responses and true only on the successful existing-target classification path; absent success is currently not setting `ok=True`, which is a further `CONFIRMED_ADAPTER_DEFECT` because the locked successful `DESTINATION_ABSENT` response requires successful semantics. Exact remediation must set only the absent success `ok` field to the canonical successful value while preserving all other absent response fields.

## 17. Validation-order consistency

The committed order matches the locked material first-failure sequence through request, source, capability, platform, components, root, parents, target, identity, size, signature, parser, parser-result, page count, hash, metadata, and classification. Parser invocation, hashing, and metadata evaluation are correctly prohibited for absent and unsafe targets.

Material differences are:

- parent missing has the wrong response status, but not wrong first-failure precedence;
- parser capability unsupported and disabled are collapsed into one reason;
- incomplete nested schemas allow missing evidence to reach later stages instead of failing at the owning contract boundary;
- successful no-reason and absent `ok` response semantics are wrong.

Classification: these are `CONFIRMED_ADAPTER_DEFECT` for status/response/reason behavior and `MISSING_CONTRACT_ENFORCEMENT` for nested schemas. No broad order rewrite is supported.

## 18. Direct-proof expectation corrections

The next proof, after separately authorized remediation and focused tests, must apply these corrections:

- absent destination expects `DESTINATION_INSPECTION_COMPLETE`, `DESTINATION_ABSENT`, `blocked_reason == ""`, successful `ok`, no parser, no hashing, and no metadata requirement;
- parent missing expects `DESTINATION_INSPECTION_UNAVAILABLE` with `parent_missing`, completion false, action false, and no parser;
- concrete conflict changes source-versus-destination evidence, while destination request SHA-256, parser result, metadata, signature, identity, and provenance remain valid;
- classification mismatch remains blocked evidence failure with empty destination status and never `CONFLICTING_ARCHIVE_PRESENT`;
- parser-result contract tests use the exact committed/normative schema after remediation;
- missing-field and unknown-field cases are added wherever closed-schema enforcement is introduced;
- direct proof remains blocked until harness authority and focused contract tests are corrected.

## 19. Oversized-file targeted stat authority

Classification: `PROOF_HARNESS_AUTHORITY`.

`TARGETED_PATH_STAT_PROOF_AUTHORIZED`

The future proof-only technique is authorized at the evidence-design level: patch `Path.stat`; intercept only the exact deterministic target path; delegate all other paths to the original method; return a complete stat-compatible result; change only `st_size`; record invocation count; restore before the tree after-snapshot and cleanup; affect no repository path; and modify no adapter. This authorizes no proof execution in this slice and does not authorize a broad filesystem patch.

## 20. Hash-observability authority

The lowest-authority option is:

A. rely on validation-stage precedence without instrumenting hashing.

This is sufficient for proving that oversize, invalid signature, parser gating, and earlier contract failures prevent hashing when the adapter’s validation order is the subject. A broad global hash patch is not authorized. A narrow adapter-module `hashlib.sha256` patch or a new implementation seam is unnecessary unless a later proof has a specific, separately authorized need to count hashing.

Classification: `PROOF_HARNESS_AUTHORITY`.

## 21. Minimum remediation scope

`TWO_FILE_REMEDIATION_SCOPE_CONFIRMED`

The smallest safe runtime and focused-test scope is exactly:

- `operator_dashboard/button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`
- `operator_dashboard/test_button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`

No third file is evidenced or authorized.

## 22. Exact remediation items

### A. Response corrections

- Owning branch: final-target `FileNotFoundError` branch. Current behavior: complete absent response with non-empty invalid-contract reason and unsuccessful `ok`. Required behavior: complete absent response with empty reason and successful `ok`; preserve all other fields, parser/hash/metadata sequencing, and false safety flags.
- Owning branch: successful existing-target classification response. Current behavior: passes an invalid-contract reason internally before overwriting it. Required behavior: use the canonical empty no-reason representation directly; preserve classification, evidence, and all other fields.
- Owning branch: parent `FileNotFoundError` mapping. Current behavior: blocked status. Required behavior: unavailable status with `parent_missing`; preserve all other fields.

### B. Nested schema enforcement

In the adapter, enforce exact required and optional fields for source evidence, composite capability, parser capability, parser request/result, and trusted metadata; reject unknown fields; validate strict types, bounds, bindings, freshness, integrity, authority, and safety structures; preserve first-failure precedence.

### C. Reason registry corrections

Add or preserve distinct canonical reasons for parser capability unsupported versus disabled, and map them without changing unrelated branches. Do not use the success no-reason path to carry a blocked reason.

### D. Precedence tests

Add focused tests proving contract failures occur at their owning boundary, parser invocation is prohibited for absent/unsafe/oversize/signature failures, page-limit failure precedes hash mismatch, hash mismatch precedes metadata classification mismatch, and classification mismatch cannot become concrete conflict.

## 23. Required focused tests

The required focused command remains sufficient:

```text
py -m pytest -q operator_dashboard/test_button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py
```

Before direct proof may resume, that command must include focused coverage for:

- absent destination empty reason and successful `ok`;
- parent missing unavailable status;
- valid concrete conflicting archive;
- classification mismatch remaining blocked;
- source missing required field;
- source unexpected field;
- capability missing required field;
- parser capability unsupported versus disabled;
- parser result missing required field;
- parser result unexpected field;
- parser result missing safety or authority field;
- metadata missing required field;
- metadata unexpected field;
- metadata identity and freshness binding where required;
- unchanged valid absent result;
- unchanged valid identical result;
- unchanged parser gating;
- unchanged path non-disclosure;
- unchanged safety flags;
- static no-mutation authority.

## 24. Existing implementation baseline status

`IMPLEMENTATION_BASELINE_REQUIRES_NARROW_REMEDIATION`

The committed implementation remains a usable baseline for a narrow two-file remediation and focused-test expansion. It is not a direct-proof-ready or production-ready baseline.

## 25. Direct-proof status after review

`DIRECT_PROOF_BLOCKED_PENDING_REMEDIATION`

## 26. Endpoint, dashboard, and archive-mutation status

- Endpoint: `NOT_READY_FOR_ENDPOINT`
- Dashboard: `NOT_READY_FOR_DASHBOARD`
- Archive mutation: `NOT_READY_FOR_ARCHIVE_MUTATION`

## 27. Smallest safe next slice

Button 2 governed internal PDF archive destination-inspection committed-contract remediation.

Proposed files:

- `operator_dashboard/button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`
- `operator_dashboard/test_button2_governed_internal_pdf_archive_destination_inspection_adapter_v1.py`

No endpoint, dashboard, or mutation work is recommended.

## 28. Explicit non-authorization

This review does not authorize runtime remediation; test remediation; proof execution; parser worker; process creation; producers; root configuration; endpoint; dashboard; directory creation; file creation; PDF generation; copy; archive; removal; quarantine; restoration; deletion; rename; overwrite; customer release; queue; learning; calibration; ledger; GCID; deployment; or any filesystem mutation.

## 29. Final verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_ARCHIVE_DESTINATION_INSPECTION_COMMITTED_CONTRACT_DIFFERENCE_REVIEW=COMMITTED_CONTRACT_DIFFERENCES_CONFIRMED_REMEDIATION_REQUIRED`
