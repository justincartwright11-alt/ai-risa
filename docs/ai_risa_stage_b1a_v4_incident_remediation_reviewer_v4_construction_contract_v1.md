# AI-RISA Stage B1A v4 Incident-Remediation Reviewer v4 Construction Contract v1

## 1. Contract Status

This is a documentation-only, non-executable construction contract. It records human-owner technical decisions for a future Python 3 read-only repository verifier. It authorizes no reviewer-v4 source construction, import, execution, receipt creation, or B1A work in this slice.

The discovery result is `REVIEWER_V4_CONSTRUCTION_CONTRACT_DISCOVERY_INCOMPLETE`: no reviewer-v3 or reviewer-v4 implementation baseline, receipt implementation, exact reviewer-v4 target path, source contract, tests, commit message, tag, or repository authority to construct or execute reviewer v4 was reachable. The human owner defines the missing technical contract here.

## 2. Repository Checkpoint

The required construction checkpoint is:

```text
branch=ai-risa-mainline
HEAD=ea93106715c7aea00b0aa09b2f88e987a7791228
parent=a67db4295eea0bb902fcdeacb18b616217581b74
HEAD_TREE_EQUALS_WRITE_TREE=True
CACHED_ENTRY_COUNT=0
STATUS_ENTRY_COUNT=360
STATUS_SHA256=A97C22360C30EF3AE4A4DFA3D3E32031C5ABFAF2814AA3B96DF5898C604AFFED
```

The future reviewer must independently verify branch, required HEAD and parent, HEAD-tree/write-tree equality, and empty cached index.

## 3. Reviewer Purpose

Reviewer v4 will independently audit the committed corrected-v2 artifact and determine whether it satisfies its complete identity, content, placement, commit, annotated-tag, source-preservation, and repository-preservation contracts.

The artifact type is a Python 3 read-only repository verifier. Its dependency boundary is Python standard library only, with no network access, no third-party runtime dependency, and no repository mutation.

## 4. Future Artifact Paths

Future source path:

`tools/ai_risa_stage_b1a_v4_incident_remediation_reviewer_v4.py`

Future test path:

`tests/test_ai_risa_stage_b1a_v4_incident_remediation_reviewer_v4.py`

The future construction slice may create only those future source and single targeted test artifacts within its separately authorized slice.

## 5. Source Evidence Contract

The audited corrected-v2 target is:

```text
path=docs/ai_risa_stage_b1a_v4_incident_remediation_reviewer_v3_prewrite_failure_record_corrected_v2.md
required_commit=ea93106715c7aea00b0aa09b2f88e987a7791228
required_blob=c73fd44189de9f6a3c84e77aeae94f206c4acdfb
required_size=3032
required_sha256=500F2BF426AF4CF766C10D1C4B76E8D5DDFCF4F25D20E73D6C2448786186E0AE
required_tag=ai-risa-stage-b1a-v4-incident-remediation-reviewer-v3-prewrite-failure-record-corrected-v2
```

The corrected-v2 working, index, current-HEAD, and historical-commit blobs must all match the required blob. Its tag must be an annotated tag whose peeled target is the required commit.

The canonical assignment source is `docs/ai_risa_stage_b1a_v4_incident_remediation_reviewer_v3_prewrite_failure_record_corrected_v1_construction_authorization.md`, blob `01786baab584b5398c4e0f457bc3e5de39dea111`, commit `df4a53188aab9569d4c7d19fb6f8867bba61f57b`. Sections 7-11 only are canonical; the assignment result is 35/60/60 and Section 12 assignments remain excluded.

The structural source is `docs/ai_risa_stage_b1a_v4_incident_remediation_reviewer_v3_prewrite_failure_record_corrected_v1_failed_candidate.md`, blob `1e599b75ad1359bd17bebd076304ca9216179db8`, commit `e1de41eea6d1d013163683b95d2189a693d7a65a`. It supplies 55 preserved-source placements.

The five human-owner placements are: `V3_SOURCE_CREATION_AUTHORIZED` to section 9; `V3_RECEIPT_CREATION_AUTHORIZED` to section 9; `V1_SOURCE_IDENTITY_PRESERVATION_REQUIRED` to section 10; `V2_SOURCE_IDENTITY_PRESERVATION_REQUIRED` to section 10; and `V3_PREWRITE_FAILURE_RECORD_COMPLETE` to section 13.

## 6. Reviewer Interface

The future reviewer must provide:

```text
python tools/ai_risa_stage_b1a_v4_incident_remediation_reviewer_v4.py
```

It may accept `--repo <repository-root>`. The default repository root may be the current working directory. No other required runtime argument is permitted.

## 7. Output and Exit Contract

The reviewer must emit a deterministic UTF-8 JSON object to standard output with these top-level fields:

```text
schema_version
reviewer
classification
failed_check_count
failed_checks
checks
evidence
repository_preserved
```

Required values are `schema_version=1` and `reviewer=AI-RISA Stage B1A v4 Incident-Remediation Reviewer v4`. Classifications are `INCIDENT_REMEDIATION_REVIEWER_V4_PASS`, `INCIDENT_REMEDIATION_REVIEWER_V4_FAIL`, and `INCIDENT_REMEDIATION_REVIEWER_V4_ERROR`. Exit codes are 0 for PASS, 1 for FAIL, and 2 for execution or evidence-collection error.

## 8. Required Check Families

The reviewer must expose individual Boolean checks for exactly these 40 families:

1. repository branch
2. required HEAD and parent
3. HEAD-tree/write-tree equality
4. empty cached index
5. corrected-v2 working blob
6. corrected-v2 index blob
7. corrected-v2 current-HEAD blob
8. corrected-v2 historical-commit blob
9. corrected-v2 size
10. corrected-v2 SHA-256
11. strict UTF-8
12. BOM absence
13. LF-only line endings
14. exact title
15. exact 13-heading sequence
16. canonical Section 7 count of 35
17. canonical total count of 60
18. canonical unique count of 60
19. exact exclusion of the seven Section 12 assignments
20. target assignment count of 60
21. zero missing literals
22. zero duplicate literals
23. zero duplicate keys
24. zero same-key contradictions
25. zero unexpected assignments
26. 55 preserved-source placements
27. five human-owner placements
28. zero unresolved placements
29. zero multiply placed assignments
30. corrected-v2 commit parent
31. corrected-v2 commit subject
32. single committed added path
33. committed target blob
34. annotated-tag object type
35. annotated-tag peeled target
36. exact one-line annotated-tag message
37. canonical-source preservation
38. structural-source preservation
39. exact downstream authority values
40. final repository status ordinal equality

Required downstream authority values are:

```text
V3_SOURCE_CREATION_AUTHORIZED=False
V3_RECEIPT_CREATION_AUTHORIZED=False
INCIDENT_REMEDIATION_REVIEWER_V4_CONSTRUCTION_AUTHORIZED=False
INCIDENT_REMEDIATION_REVIEWER_V4_STATIC_VALIDATION_AUTHORIZED=False
INCIDENT_REMEDIATION_REVIEWER_V4_EXECUTION_AUTHORIZED=False
INCIDENT_REMEDIATION_REVIEWER_V4_RECEIPT_CREATION_AUTHORIZED=False
B1A_V4_CREATION_AUTHORIZED=False
B1A_V4_EXECUTION_AUTHORIZED=False
READY_FOR_EXECUTION_AUTHORIZATION=False
AUTHORIZED_NEXT_B1A_SLICE=None
```

## 9. Failure and Mutation Boundary

Reviewer v4 must fail closed. Every check must be independently named. Final classification must derive exclusively from the complete failed-check list. No check result may be hard-coded, and PASS is forbidden when any required check is false or unavailable.

Reviewer v4 must never modify a repository file or index, create a commit or tag, clean, reset, or stash, create a receipt, execute another reviewer, or execute B1A. It must capture initial and final repository arrays in the same process and compare them ordinally.

## 10. Static Validation Contract

The future construction slice must run exactly:

```text
python -B -m py_compile tools/ai_risa_stage_b1a_v4_incident_remediation_reviewer_v4.py
```

No reviewer execution is authorized by static validation.

## 11. Targeted Test Contract

The future construction slice must create exactly one targeted test file and run exactly:

```text
python -B -m pytest -q tests/test_ai_risa_stage_b1a_v4_incident_remediation_reviewer_v4.py
```

The test must use an isolated temporary Git repository and must not execute against the live AI-RISA worktree. Required scenarios are exactly: (1) valid fixture PASS and exit 0; (2) one failed check FAIL and exit 1; (3) malformed or unavailable evidence ERROR and exit 2; (4) duplicate assignment key; (5) contradictory assignment; (6) wrong section placement; (7) extra tag-message content; (8) initial/final repository-status mismatch; (9) no live repository mutation.

## 12. Future Commit and Tag Contract

Future reviewer source-and-test commit message: `feat: add B1A incident-remediation reviewer v4`.

Future annotated tag: `ai-risa-stage-b1a-v4-incident-remediation-reviewer-v4`.

Future annotated-tag message: `feat: add B1A incident-remediation reviewer v4`.

These are future contract values only and do not authorize construction in this slice.

## 13. Construction and Execution Separation

Reviewer-v4 construction and reviewer-v4 execution must be separate governed slices. The future construction slice may create source, create the single targeted test, perform static validation, run the isolated targeted test, commit, and tag. It must not run reviewer v4 against the live AI-RISA repository.

`V3_PREWRITE_FAILURE_RECORD_COMPLETE=True` is a required human-owner placement in section 13. No reviewer-v4 construction or execution authority is claimed here.

## 14. Receipt Boundary

No receipt is created during reviewer-v4 construction. A receipt may be considered only after a separately authorized live execution slice completes. `V3_RECEIPT_CREATION_AUTHORIZED=False` and `INCIDENT_REMEDIATION_REVIEWER_V4_RECEIPT_CREATION_AUTHORIZED=False` remain required values.

## 15. B1A Boundary

Reviewer-v4 construction does not authorize B1A creation or execution. Reviewer-v4 execution does not automatically authorize B1A creation or execution. B1A requires a separate explicit human-owner decision after reviewer-v4 execution evidence is reviewed. `B1A_V4_CREATION_AUTHORIZED=False`, `B1A_V4_EXECUTION_AUTHORIZED=False`, `READY_FOR_EXECUTION_AUTHORIZATION=False`, and `AUTHORIZED_NEXT_B1A_SLICE=None` remain required values.

## 16. Final Declaration

This contract defines future intent and evidence requirements only. It does not authorize reviewer-v4 source construction, import, execution, receipt creation, repository mutation, or any B1A creation or execution. The current slice is limited to constructing, validating, committing, and tagging this one contract document.