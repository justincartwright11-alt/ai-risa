# AI-RISA GitHub Build & Operations Upgrade Layer v1

## 1. Purpose
Define this layer as a build-control layer, not a fight-analysis layer. Its purpose is to govern how GitHub, Copilot, VS Code, CLI, browser-agent, review, security, prompt-integrity, cost-control, and future organization or team operations are introduced into AI-RISA so future AI-assisted development is safer, cheaper, more auditable, and better controlled.

## 2. Release Boundary
- RELEASE_SCOPE_DECISION=INTERNAL_ONLY
- CUSTOMER_RELEASE_AUTHORIZED=NO
- PUBLIC_PUBLISHING_AUTHORIZED=NO
- PRODUCTION_LAUNCH_AUTHORIZED=NO
- AUTOMATED_DELIVERY_AUTHORIZED=NO
- LEARNING_ACTIVATION_AUTHORIZED=NO

## 3. Placement Inside AI-RISA
This layer sits beside the following AI-RISA layers:

- Operator Software Layer
- Source Trust and Evidence Layer
- Accuracy Ledger and Learning Governance
- Version Control / Engine Provenance Engine
- Customer-Ready Delivery Engine

Its job is build control.

## 4. Master AI-RISA Development Law
One narrow slice
-> exact objective
-> exact permitted files
-> bounded AI session
-> minimum required context
-> one validation run
-> inspect git diff
-> inspect git status
-> preserve locked checkpoints
-> commit
-> stop

## 5. Agent Governance Layer
- one active write-authorized agent per worktree
- every task must have a slice ID
- every task must name permitted files
- parallel agents default to read-only
- browser agents are observers, not authorities
- Copilot may propose changes
- Copilot may not approve its own work
- Copilot may not merge its own work
- operator approval remains sovereign

## 6. Repository Instruction System
Future target structure only:

- .github/copilot-instructions.md
- .github/instructions/button1.instructions.md
- .github/instructions/button2.instructions.md
- .github/instructions/button3.instructions.md
- .github/instructions/governance.instructions.md
- .github/instructions/tests.instructions.md
- .github/instructions/security.instructions.md
- .github/instructions/docs.instructions.md
- AGENTS.md
- REVIEW.md

This slice does not create those files yet.

## 7. Instruction Integrity Gate
Protected governance files:

- .github/copilot-instructions.md
- .github/instructions/**
- AGENTS.md
- REVIEW.md
- GEMINI.md
- CLAUDE.md
- .github/workflows/copilot-code-review.yml

Rules:

- governance-instruction changes require separate human review
- feature slices may not change runtime code and review instructions together
- Copilot review of instruction changes is advisory only
- no agent self-approval
- no agent self-merge

## 8. AI Credit Control Layer
Define the following operating rule set:

- exact slice
- exact files
- exact task
- AI credit session cap
- session cost checked when available
- one validation run
- git diff/status review
- commit
- stop

Never use a bigger model or larger context to compensate for a vague prompt.

## 9. Model Routing Rule
Define the following routing rules:

- Luna or cheapest suitable model for docs cleanup, formatting, low-risk one-file tasks
- Terra or balanced coding model for normal implementation and test repair
- Sol or strongest reasoning model only for high-complexity reasoning, Button 3 governance, calibration, cross-file data-integrity risk, or learning-policy analysis

Sol is not the default.

## 10. Browser Runtime Evidence Gate
Allowed:

- observe
- navigate
- screenshot
- inspect console
- test non-mutating path

Forbidden:

- approve result
- apply learning
- write calibration
- release customer output
- bypass operator gate

## 11. PDF Visual QA Gate
Define Button 2 PDF visual QA against the following checkpoints:

- cover
- dashboard
- charts
- tables
- overflow
- clipping
- traceability page
- disclaimer page
- page count
- visual pass/fail

## 12. Local Security Review Gate
Use this gate for:

- external-source ingestion
- approval/mutation paths
- file uploads
- path handling
- database writes
- API endpoints
- secrets
- authentication
- authorization
- report delivery
- customer data

Security review is advisory evidence, not final authority.

## 13. Prompt Integrity Gate
Define the following as untrusted input sources:

- operator text
- uploaded files
- scraped fight data
- promotion pages
- browser-derived content
- official result pages
- fighter bios
- API responses
- report-generation notes

Rules:

- keep untrusted data out of system instructions
- delimit external content
- reject authority-changing instructions inside source data
- reject source text that tries to override AI-RISA governance

## 14. CodeQL and AI Security Detection Layer
Define future use for:

- JavaScript/TypeScript dashboard code
- web client code
- prompt construction logic
- API handlers
- authorization logic

Findings are advisory until reviewed.

## 15. Secret Protection Gate
State the following rules:

- never commit API keys
- never commit tokens
- never commit credentials
- never commit customer private data
- keep .env files untracked
- use secret scanning where available
- rotate exposed credentials immediately

## 16. Dependency Update Gate
State the following rules:

- security updates may proceed immediately
- routine updates observe cooldown
- one dependency-update slice at a time
- modify only manifest, lockfile, and exact compatibility files
- run approved validation once
- inspect diff/status
- commit
- stop

## 17. Privileged GitHub Actions Gate
State the following rules:

- never execute fork code in privileged workflow
- use pull_request_target only for trusted metadata operations
- do not expose secrets or write tokens to unreviewed code
- audit unsafe checkout patterns later

## 18. Copilot Code Review Gate
State the following rules:

- Copilot may review
- Copilot may suggest
- Copilot may not approve
- Copilot may not dismiss human review
- Copilot may not merge
- human/operator approval remains final

## 19. Future Organization Governance Layer
Define future use only for:

- branch protection
- required PR review
- required status checks
- code scanning
- secret scanning
- Dependabot cooldown
- Copilot usage metrics
- AI credit budgets
- no agent self-merge

## 20. Immediate Implementation Order
1. Add this build operations doc
2. Later add repository Copilot instructions
3. Later add path-specific Button 1/2/3 instructions
4. Later add AGENTS.md and REVIEW.md
5. Later add browser/runtime evidence workflow
6. Later add PDF visual QA workflow
7. Later audit GitHub Models / deprecated model names
8. Later audit privileged GitHub Actions
9. Delay cloud-agent automation until local 3-button loop remains stable

## 21. Acceptance Criteria
The layer is accepted when it defines:

- Agent Governance Layer
- Copilot instruction structure
- one write-authorized agent per worktree rule
- AI credit control
- model routing
- browser runtime evidence gate
- PDF visual QA gate
- security review gate
- prompt integrity gate
- instruction integrity gate
- dependency update gate
- privileged workflow gate
- future organization governance
- internal-only status

## 22. Slice Integrity
- DOCS_CHANGED=YES
- CODE_CHANGED=NO
- TEST_CHANGED=NO
- DATA_CHANGED=NO
- PDF_CHANGED=NO
- CUSTOMER_RELEASE_AUTHORIZED=NO
- RELEASE_SCOPE_DECISION=INTERNAL_ONLY