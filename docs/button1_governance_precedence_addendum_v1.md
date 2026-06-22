# Button 1 Governance Precedence Addendum v1

## Purpose
Define the authoritative order for resolving conflicting, stale, incomplete, or permissive AI-RISA instructions.

## Governance precedence rules

1. The newest valid tagged checkpoint on the active branch takes precedence over older checkpoints.
2. A fail-closed rule takes precedence over permissive or ambiguous language.
3. Explicit blocked scope takes precedence over implied, inferred, or general permission.
4. No-write and no-execution invariants are non-negotiable unless replaced by a newer explicitly approved tagged checkpoint.
5. A prompt containing an expected HEAD or tag must be rejected when the actual HEAD or tag does not match.
6. Stale prompts must never be adapted silently or executed against a newer checkpoint.
7. When governance documents disagree, the stricter rule remains active until a newer tagged artifact explicitly resolves the conflict.
8. Absence of approval is not approval.
9. Missing evidence, UNKNOWN status, or incomplete provenance must produce a fail-closed result.
10. Existing locked checkpoint documents remain immutable. Corrections or refinements must be created as new additive documents.
11. Pre-existing dirty files must remain unstaged and untouched unless explicitly included in an approved slice.
12. A new slice must define exact allowed files, blocked files, validation commands, staged-set guard, commit message, tag, and abort conditions.

## Authoritative resolution order
Use this order:

1. Current branch
2. Current HEAD
3. Tags at current HEAD
4. Newest applicable tagged checkpoint
5. Explicit fail-closed and blocked-scope rules
6. No-write/no-execution invariants
7. Approved slice-specific instructions
8. Older design notes and historical prompts

## Stale-prompt rejection rule
Reject the prompt and stop without edits when:

- expected HEAD differs from actual HEAD
- expected tag is missing from actual HEAD
- branch differs from the approved branch
- the requested artifact already exists
- the requested slice has already been committed
- the prompt attempts to modify an immutable locked checkpoint
- the staged set contains any unapproved file

## Required operator response
When rejecting a stale prompt, report:

- actual branch
- actual HEAD
- tags at HEAD
- expected branch, HEAD, and tag
- whether the requested artifact already exists
- confirmation that no edits, staging, commit, or tag occurred

## Final governance verdict
AI_RISA_NEWEST_TAGGED_FAIL_CLOSED_CHECKPOINT_GOVERNS
