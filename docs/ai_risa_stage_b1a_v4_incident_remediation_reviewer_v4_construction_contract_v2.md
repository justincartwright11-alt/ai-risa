# AI-RISA Stage B1A v4 Incident-Remediation Reviewer v4 Construction Contract v2

## 1. Contract Status

This documentation-only contract is the corrected v2 successor to the immutable v1 construction contract. It is non-executable and records future technical intent only.

PRIOR_V1_CONTRACT_CONTENT_RESULT=FAIL
PRIOR_V1_CONTRACT_CONSTRUCTION_PROTOCOL_RESULT=FAIL
PRIOR_V1_CONTRACT_SUPERSEDED_FOR_FUTURE_IMPLEMENTATION=True

The committed v1 contract remains immutable historical evidence. It is superseded for future implementation only; this document does not authorize source construction, static validation, testing, import, execution, receipt creation, or B1A work.

## 2. Repository Checkpoint

Required construction checkpoint:

branch=ai-risa-mainline
HEAD=5b9a4948354bc7cf8648550460ff22510fc555ac
parent=ea93106715c7aea00b0aa09b2f88e987a7791228
HEAD_TREE_EQUALS_WRITE_TREE=True
CACHED_ENTRY_COUNT=0
STATUS_ENTRY_COUNT=360
STATUS_SHA256=A97C22360C30EF3AE4A4DFA3D3E32031C5ABFAF2814AA3B96DF5898C604AFFED

## 3. Reviewer Purpose

Reviewer v4 is a Python 3 read-only repository verifier. It independently audits the corrected-v2 artifact for identity, content, placement, commit, annotated-tag, source-preservation, and repository-preservation contracts. It uses Python standard library only, no network, no third-party runtime dependency, and no repository mutation.

## 4. Future Artifact Paths

Future source path: tools/ai_risa_stage_b1a_v4_incident_remediation_reviewer_v4.py
Future test path: tests/test_ai_risa_stage_b1a_v4_incident-remediation_reviewer_v4.py
The separately authorized future construction slice may create only those two files.

## 5. Source Evidence Contract

Corrected-v2 evidence: docs/ai_risa_stage_b1a_v4_incident-remediation-reviewer-v3-prewrite-failure-record-corrected-v2.md; commit ea93106715c7aea00b0aa09b2f88e987a7791228; blob c73fd44189de9f6a3c84e77aeae94f206c4acdfb; size 3032; SHA-256 500F2BF426AF4CF766C10D1C4B76E8D5DDFCF4F25D20E73D6C2448786186E0AE; tag ai-risa-stage-b1a-v4-incident-remediation-reviewer-v3-prewrite-failure-record-corrected-v2.

Canonical assignment source: docs/ai_risa_stage_b1a_v4_incident_remediation_reviewer_v3_prewrite_failure_record_corrected_v1_construction_authorization.md; blob 01786baab584b5398c4e0f457bc3e5de39dea111; commit df4a53188aab9569d4c7d19fb6f8867bba61f57b; canonical range Sections 7–11 only; required result 35/60/60. The seven assignments in Section 12 remain excluded.
Structural source: docs/ai_risa_stage_b1a_v4_incident_remediation_reviewer_v3_prewrite_failure_record_corrected_v1_failed_candidate.md; blob 1e599b75ad1359bd17bebd076304ca9216179db8; commit e1de41eea6d1d013163683b95d2189a693d7a65a; required mapping 55 preserved-source placements.
Human-owner placements: V3_SOURCE_CREATION_AUTHORIZED and V3_RECEIPT_CREATION_AUTHORIZED -> section 9; V1_SOURCE_IDENTITY_PRESERVATION_REQUIRED and V2_SOURCE_IDENTITY_PRESERVATION_REQUIRED -> section 10; V3_PREWRITE_FAILURE_RECORD_COMPLETE -> section 13.

## 6. Reviewer Interface

Future invocation: python tools/ai_risa_stage_b1a_v4_incident_remediation_reviewer_v4.py
Optional argument: --repo. The default repository root may be the current working directory. No other required runtime argument is permitted.

## 7. Output and Exit Contract

The reviewer emits one deterministic UTF-8 JSON object with top-level fields schema_version, reviewer, classification, failed_check_count, failed_checks, checks, evidence, repository_preserved.
schema_version=1
reviewer=AI-RISA Stage B1A v4 Incident-Remediation Reviewer v4
Classifications: INCIDENT_REMEDIATION_REVIEWER_V4_PASS; INCIDENT_REMEDIATION_REVIEWER_V4_FAIL; INCIDENT_REMEDIATION_REVIEWER_V4_ERROR.
Exit codes: 0 = PASS; 1 = FAIL; 2 = execution or evidence-collection error.

## 8. Required Check Families

The reviewer must encode exactly these 40 check families:
1. repository branch;
2. required HEAD and parent;
3. HEAD-tree/write-tree equality;
4. empty cached index;
5. corrected-v2 working blob;
6. corrected-v2 index blob;
7. corrected-v2 current-HEAD blob;
8. corrected-v2 historical-commit blob;
9. corrected-v2 size;
10. corrected-v2 SHA-256;
11. strict UTF-8;
12. BOM absence;
13. LF-only line endings;
14. exact title;
15. exact 13-heading sequence;
16. canonical Section 7 count of 35;
17. canonical total count of 60;
18. canonical unique count of 60;
19. exact exclusion of the seven Section 12 assignments;
20. target assignment count of 60;
21. zero missing literals;
22. zero duplicate literals;
23. zero duplicate keys;
24. zero same-key contradictions;
25. zero unexpected assignments;
26. 55 preserved-source placements;
27. five human-owner placements;
28. zero unresolved placements;
29. zero multiply placed assignments;
30. corrected-v2 commit parent;
31. corrected-v2 commit subject;
32. single committed added path;
33. committed target blob;
34. annotated-tag object type;
35. annotated-tag peeled target;
36. exact one-line annotated-tag message;
37. canonical-source preservation;
38. structural-source preservation;
39. exact downstream authority values;
40. final repository-status ordinal equality;
Do not add another numbered entry inside Section 8.

## 9. Failure and Mutation Boundary

Reviewer v4 fails closed. Every check is independently named, and final classification derives exclusively from the complete failed-check list. It never modifies files or the index, creates commits or tags, cleans, resets, stashes, creates receipts, executes another reviewer, or executes B1A. It captures initial and final repository arrays in one process and compares them ordinally.

REVIEWER_V4_SOURCE_CONSTRUCTION_AUTHORIZED=False
REVIEWER_V4_STATIC_VALIDATION_AUTHORIZED=False
REVIEWER_V4_IMPORT_AUTHORIZED=False
REVIEWER_V4_EXECUTION_AUTHORIZED=False
REVIEWER_V4_RECEIPT_CREATION_AUTHORIZED=False
B1A_V4_CREATION_AUTHORIZED=False
B1A_V4_EXECUTION_AUTHORIZED=False
READY_FOR_EXECUTION_AUTHORIZATION=False
AUTHORIZED_NEXT_B1A_SLICE=None

## 10. Static Validation Contract

Future static validation command only:
python -B -m py_compile tools/ai_risa_stage_b1a_v4_incident_remediation_reviewer_v4.py
This future command is not authorized in this slice.

## 11. Targeted Test Contract

The future targeted test contract encodes exactly these nine scenarios:
1. valid fixture returns PASS and exit code 0;
2. one failed check returns FAIL and exit code 1;
3. malformed or unavailable evidence returns ERROR and exit code 2;
4. duplicate assignment key is detected;
5. contradictory assignment is detected;
6. wrong section placement is detected;
7. extra tag-message content is detected;
8. initial/final repository-status mismatch is detected;
9. live repository mutation is not performed;
Do not encode these scenarios inline or use parenthesized markers. The future test uses an isolated temporary Git repository and never executes against the live worktree.

## 12. Future Commit and Tag Contract

Future source-and-test commit: feat: add B1A incident-remediation reviewer v4
Future reviewer tag: ai-risa-stage-b1a-v4-incident-remediation-reviewer-v4
Future reviewer tag message: feat: add B1A incident-remediation reviewer v4

## 13. Construction and Execution Separation

Reviewer-v4 construction and live execution remain separate governed slices. The future construction slice may create only the specified source and test, perform only the specified static validation and isolated targeted test, and must not execute Reviewer v4 against the live repository.
V3_PREWRITE_FAILURE_RECORD_COMPLETE=True

## 14. Receipt Boundary

No receipt is created during construction. Receipt creation requires a separate decision after separately authorized live execution and reviewed evidence. Receipt creation remains false in the authority block.

## 15. B1A Boundary

Reviewer-v4 construction and execution do not authorize B1A. B1A requires a separate explicit human-owner decision after execution evidence is reviewed. The B1A and readiness values remain false or unset in the authority block.

## 16. Final Declaration

This contract defines future intent and evidence requirements only. It authorizes no runtime change, mutation, customer release, production launch, automated delivery, learning activation, reviewer import or execution, receipt creation, or B1A work. Only this one contract document is within the current documentation-only slice.
