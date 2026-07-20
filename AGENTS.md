# AI-RISA Agent Operating Doctrine

## 1. Purpose
AGENTS.md governs AI-RISA agent behaviour across Copilot, VS Code AI, CLI agents, browser agents, review agents, and future automation agents.

## 2. Relationship to Global Instructions
AGENTS.md is subordinate to:

.github/copilot-instructions.md

and must align with:

.github/instructions/governance.instructions.md
.github/instructions/security.instructions.md
.github/instructions/tests.instructions.md
.github/instructions/docs.instructions.md

## 3. Release Boundary
RELEASE_SCOPE_DECISION=INTERNAL_ONLY

CUSTOMER_RELEASE_AUTHORIZED=NO

PUBLIC_PUBLISHING_AUTHORIZED=NO

PRODUCTION_LAUNCH_AUTHORIZED=NO

AUTOMATED_DELIVERY_AUTHORIZED=NO

LEARNING_ACTIVATION_AUTHORIZED=NO

## 4. One-Writer Law
Only one write-authorized agent may operate in one worktree at a time.

Parallel agents are read-only by default unless they are assigned:

- a separate worktree
- a separate slice ID
- exact permitted files
- explicit write authority

## 5. Slice Authority Rule
Every agent task must have:

- slice ID
- baseline commit or state
- exact objective
- exact permitted files
- forbidden files/actions
- validation command
- final response schema
- stop condition

No agent may infer authority from previous commits, design notes, test passes, or nearby files.

## 6. Agent Roles
Allowed roles:

- Write Agent
- Read-Only Reviewer
- Test Investigator
- Browser Evidence Agent
- Security Reviewer
- Documentation Agent

Only the Write Agent may edit files, and only files permitted by the current slice.

## 7. Browser Agent Authority
Allowed:

- observe
- navigate
- screenshot
- inspect console
- test non-mutating UI path

Forbidden:

- approve result
- apply learning
- write calibration
- release customer output
- bypass operator gate
- mutate data
- change repository files unless separately authorized

## 8. Review Agent Authority
Review agents may identify issues, summarize evidence, and recommend blockers.

They may not:

- approve their own changes
- dismiss human review
- merge
- elevate authority
- convert advisory findings into release authority

## 9. Stop Conditions
An agent must stop when:

- the exact task is complete
- the permitted file set would be exceeded
- a targeted validation fails
- authority is unclear
- customer release would be implied
- learning activation would be implied
- mutation authority is missing
- unrelated files would need repair
- secrets or credentials appear exposed
- the task becomes broader than the slice

## 10. Escalation Rules
Escalate to operator when:

- required authority is missing
- a blocker requires runtime changes outside the permitted files
- a security issue is found
- a result or source is contradictory
- a production/customer/learning gate would need to change
- a hidden write or mutation risk appears

## 11. Staged-Set Discipline
Agents must stage only files permitted by the current slice.

Agents must verify staged files with:

git diff --cached --name-status

Agents must not stage unrelated workspace changes.

## 12. Cost Discipline
Agents must use minimum necessary context.

Avoid:

- broad repo scans
- repeated rereads
- unnecessary transcript recovery
- broad test expansion
- large-model escalation for vague tasks

Use stronger models only when the slice requires complex reasoning, Button 3 governance, calibration, data-integrity, security, or learning-policy analysis.

## 13. No Agent Self-Approval
An agent may not approve its own work.

An agent may not merge its own work.

An agent may not convert its proof into release authority.

Human/operator approval remains final.

## 14. Final Rule
When agent authority is unclear, stop and request a narrower slice.