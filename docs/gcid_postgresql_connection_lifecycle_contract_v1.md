# GCID PostgreSQL Connection Lifecycle Contract v1

## 1. PURPOSE

Define future connection lifecycle semantics for the GCID PostgreSQL durable-storage adapter.

The contract governs:

- connection eligibility;
- acquisition attempt boundary;
- ownership;
- bounded timeout requirement;
- successful acquisition state;
- acquisition failure state;
- connection usability state;
- cleanup;
- close;
- exception containment;
- secret-safe diagnostics;
- fail-closed behavior.

This document provides contract/design authority only.

## 2. AUTHORITY SEPARATION

CONNECTION_LIFECYCLE_CONTRACT_AUTHORITY=True

POSTGRESQL_CONNECTION_IMPLEMENTATION_AUTHORIZED=False

POSTGRESQL_CONNECTION_EXECUTION_AUTHORIZED=False

POSTGRESQL_STORAGE_ADAPTER_IMPLEMENTATION_AUTHORIZED=False

POSTGRESQL_TRANSACTION_EXECUTION_AUTHORIZED=False

POSTGRESQL_DATABASE_MUTATION_AUTHORIZED=False

MIGRATION_EXECUTION_AUTHORIZED=False

## 3. CONFIGURATION PREREQUISITE

The lifecycle contract consumes the already-governed configuration predicates.

Required before a future connection may even become eligible:

GCID_POSTGRES_CONFIG_SOURCE_DEFINED=True

GCID_POSTGRES_DSN_VARIABLE_DEFINED=True

GCID_POSTGRES_CONFIG_VALID=True

The canonical variable remains:

AI_RISA_GCID_POSTGRES_DSN

But:

GCID_POSTGRES_CONFIG_VALID=True

does not itself mean:

GCID_DATABASE_CONNECTION_ELIGIBLE=True

unless all future connection-authority predicates also pass.

## 4. CONNECTION STATE MODEL

Define a deterministic future state vocabulary:

- GCID_POSTGRES_CONNECTION_NOT_EVALUATED
- GCID_POSTGRES_CONNECTION_INELIGIBLE
- GCID_POSTGRES_CONNECTION_ELIGIBLE
- GCID_POSTGRES_CONNECTION_ATTEMPT_NOT_AUTHORIZED
- GCID_POSTGRES_CONNECTION_ATTEMPTING
- GCID_POSTGRES_CONNECTION_OPEN
- GCID_POSTGRES_CONNECTION_FAILED
- GCID_POSTGRES_CONNECTION_CLOSED

No state may imply mutation authority.

## 5. CONNECTION ELIGIBILITY

A future connection attempt may be eligible only when:

- configuration exists;
- configuration is statically valid;
- required configuration authority passes;
- separate connection execution authority is present;
- no governing fail-closed blocker exists.

CONFIG_VALID_DOES_NOT_EQUAL_CONNECTION_ELIGIBLE=True

CONNECTION_ELIGIBLE_DOES_NOT_EQUAL_CONNECTION_AUTHORIZED=True

CONNECTION_AUTHORIZED_DOES_NOT_EQUAL_MUTATION_AUTHORIZED=True

## 6. ACQUISITION OWNERSHIP

Each future connection acquisition must have one explicit owner.

The owner is responsible for:

- requesting the connection;
- receiving success/failure;
- ensuring cleanup;
- ensuring close;
- preventing orphaned connections.

No hidden global connection may be created by configuration parsing.

No import-time connection may occur.

IMPORT_TIME_CONNECTION_FORBIDDEN=True

CONFIG_PARSE_CONNECTION_FORBIDDEN=True

IMPLICIT_GLOBAL_CONNECTION_FORBIDDEN=True

## 7. ACQUISITION ATTEMPT BOUNDARY

A future acquisition attempt must be explicit.

It must not occur as a side effect of:

- module import;
- configuration validation;
- schema parsing;
- dry-run evaluation;
- report generation;
- fighter analysis;
- dashboard rendering.

CONNECTION_ACQUISITION_EXPLICIT_ONLY=True

## 8. TIMEOUT GOVERNANCE

Every future connection attempt must be bounded.

CONNECTION_TIMEOUT_REQUIRED=True

UNBOUNDED_CONNECTION_ATTEMPT_FORBIDDEN=True

This contract does not invent a numeric timeout. No numeric timeout is currently governed by this contract.

CONNECTION_TIMEOUT_VALUE_DEFINED=False

A later implementation/test slice must bind a finite positive timeout before execution authority. A missing timeout value must not silently become an unbounded attempt.

## 9. SUCCESS CONDITION

A future acquisition may transition to:

GCID_POSTGRES_CONNECTION_OPEN

only when the PostgreSQL driver reports successful connection establishment.

Connection-open state alone does not prove:

- schema compatibility;
- transaction readiness;
- write eligibility;
- mutation authority;
- migration authority.

CONNECTION_OPEN_DOES_NOT_AUTHORIZE_TRANSACTION=True

CONNECTION_OPEN_DOES_NOT_AUTHORIZE_MUTATION=True

## 10. FAILURE CONDITION

Any future acquisition error must transition to:

GCID_POSTGRES_CONNECTION_FAILED

The system must fail closed.

A failure must not trigger:

- SQLite fallback;
- in-memory persistence fallback;
- alternate credentials;
- localhost fallback;
- different database fallback;
- hidden retry loop;
- mutation through another storage backend.

CONNECTION_FAILURE_FAIL_CLOSED=True

STORAGE_BACKEND_FALLBACK_AUTHORIZED=False

## 11. FAILURE CLASSIFICATION

Define future non-secret failure categories sufficient for deterministic handling:

- GCID_POSTGRES_CONNECTION_CONFIG_INVALID
- GCID_POSTGRES_CONNECTION_NOT_AUTHORIZED
- GCID_POSTGRES_CONNECTION_TIMEOUT
- GCID_POSTGRES_CONNECTION_AUTHENTICATION_FAILED
- GCID_POSTGRES_CONNECTION_NETWORK_FAILED
- GCID_POSTGRES_CONNECTION_SERVER_REJECTED
- GCID_POSTGRES_CONNECTION_UNKNOWN_FAILURE

These categories are semantic contracts only.

Do not implement exception mapping in this slice.

## 12. SECRET-SAFE FAILURE REPORTING

Connection failure handling must never expose:

- password;
- full credential-bearing DSN;
- tokens;
- certificate private material;
- secret environment contents.

Error reporting may identify a governed failure category without returning raw credentials.

CONNECTION_FAILURE_SECRET_REDACTION_REQUIRED=True

## 13. RETRY BOUNDARY

Automatic retry is not authorized in this contract.

AUTOMATIC_CONNECTION_RETRY_AUTHORIZED=False

RETRY_POLICY_DEFINED=False

A later separately governed slice may define bounded retry behavior if actually required.

No implementation may invent retries.

## 14. CONNECTION REUSE / POOLING BOUNDARY

Pooling and persistent global reuse are not authorized.

CONNECTION_POOLING_AUTHORIZED=False

CONNECTION_POOLING_CONTRACT_PRESENT=False

GLOBAL_CONNECTION_REUSE_AUTHORIZED=False

A later contract must explicitly authorize pooling/reuse if required.

## 15. CONNECTION CLOSE CONTRACT

Every successfully opened future connection must have deterministic close ownership.

SUCCESSFUL_CONNECTION_MUST_BE_CLOSED=True

CONNECTION_CLOSE_OWNER_REQUIRED=True

ORPHANED_CONNECTION_ALLOWED=False

Close must be attempted when the owning operation completes or aborts.

This contract does not define transaction cleanup.

## 16. EXCEPTION CLEANUP

Future connection lifecycle implementation must preserve cleanup when an exception occurs after acquisition.

CONNECTION_EXCEPTION_CLEANUP_REQUIRED=True

CONNECTION_CLOSE_ON_FAILURE_PATH_REQUIRED=True

No exception path may intentionally leave an owned connection orphaned.

## 17. CONTEXT / RESOURCE OWNERSHIP

A future implementation should expose connection ownership through an explicit bounded operation scope rather than hidden process lifetime.

This contract does not mandate a Python implementation construct unless existing repository authority already requires one.

CONNECTION_RESOURCE_SCOPE_EXPLICIT=True

## 18. HEALTH CHECK BOUNDARY

This contract does not authorize a live connection health check.

LIVE_DATABASE_HEALTH_CHECK_AUTHORIZED=False

NETWORK_HEALTH_CHECK_AUTHORIZED=False

A future execution/test slice must separately govern any live connectivity proof.

## 19. DRY-RUN BOUNDARY

Existing GCID dry-run behavior remains non-persisting and must not silently acquire a database connection.

GCID_DRY_RUN_DATABASE_CONNECTION_REQUIRED=False

GCID_DRY_RUN_DATABASE_CONNECTION_AUTHORIZED=False

GCID_DRY_RUN_PERSISTENCE_AUTHORIZED=False

## 20. TRANSACTION SEPARATION

Connection lifecycle and transaction lifecycle are separate.

TRANSACTION_BOUNDARY_DEFINED=False

TRANSACTION_EXECUTION_AUTHORIZED=False

CONNECTION_OPEN_DOES_NOT_IMPLY_TRANSACTION_BEGIN=True

A future transaction contract must define:

- transaction ownership;
- begin semantics;
- commit conditions;
- rollback conditions;
- exception rollback;
- partial-write prevention.

Do not define those mechanics in this slice.

## 21. SCHEMA / MIGRATION SEPARATION

OFFLINE_GCID_SCHEMA_CONTRACT_PRESENT=True

CONNECTION_OPEN_DOES_NOT_AUTHORIZE_SCHEMA_EXECUTION=True

SCHEMA_EXECUTION_AUTHORIZED=False

MIGRATION_EXECUTION_AUTHORIZED=False

## 22. MUTATION SEPARATION

Preserve exactly:

GCID_DATABASE_MUTATION_AUTHORIZED=False

A valid configuration and open connection must not change this predicate.

## 23. FUTURE IMPLEMENTATION PREDICATES

GCID_POSTGRES_CONNECTION_STATE_MODEL_DEFINED=True

GCID_POSTGRES_CONNECTION_ELIGIBILITY_DEFINED=True

GCID_POSTGRES_CONNECTION_ACQUISITION_EXPLICIT_ONLY=True

GCID_POSTGRES_CONNECTION_OWNER_REQUIRED=True

GCID_POSTGRES_CONNECTION_TIMEOUT_REQUIRED=True

GCID_POSTGRES_UNBOUNDED_CONNECTION_FORBIDDEN=True

GCID_POSTGRES_CONNECTION_FAILURE_FAIL_CLOSED=True

GCID_POSTGRES_CONNECTION_SECRET_REDACTION_REQUIRED=True

GCID_POSTGRES_AUTOMATIC_RETRY_AUTHORIZED=False

GCID_POSTGRES_CONNECTION_POOLING_AUTHORIZED=False

GCID_POSTGRES_SUCCESSFUL_CONNECTION_MUST_CLOSE=True

GCID_POSTGRES_EXCEPTION_CLEANUP_REQUIRED=True

GCID_POSTGRES_LIVE_HEALTH_CHECK_AUTHORIZED=False

GCID_POSTGRES_DRY_RUN_CONNECTION_AUTHORIZED=False

GCID_POSTGRES_CONNECTION_OPEN_DOES_NOT_AUTHORIZE_TRANSACTION=True

GCID_POSTGRES_CONNECTION_OPEN_DOES_NOT_AUTHORIZE_MUTATION=True

## 24. NON-GOALS

This slice does not define:

- Psycopg implementation;
- connection invocation code;
- numeric timeout value unless already governed;
- transaction semantics;
- retry mechanics;
- connection pooling;
- SQL;
- schema execution;
- migration execution;
- durable writes;
- fighter identity persistence;
- ranking persistence;
- runtime proof.

## 25. AUTHORITY BOUNDARY

At completion:

GCID_POSTGRESQL_CONNECTION_LIFECYCLE_CONTRACT_LOCKED=True

GCID_POSTGRESQL_STORAGE_ADAPTER_IMPLEMENTATION_AUTHORITY_PRESENT=False

GCID_POSTGRESQL_STORAGE_ADAPTER_CODE_READY=False

GCID_POSTGRESQL_STORAGE_ADAPTER_EXECUTION_AUTHORIZED=False

GCID_DATABASE_CONNECTION_AUTHORITY_PRESENT=False

GCID_DATABASE_MUTATION_AUTHORIZED=False

TRANSACTION_BOUNDARY_DEFINED=False

PROJECT_FIGHTER_RANKING_LEDGER_IMPLEMENTATION_AUTHORIZED=False
