# GCID PostgreSQL Transaction Boundary Contract v1

## 1. PURPOSE

Define the deterministic transaction boundary that a future GCID PostgreSQL durable-storage implementation must obey.

This contract governs:

- transaction eligibility
- transaction ownership
- explicit transaction start
- transaction scope
- commit eligibility
- rollback requirements
- exception behavior
- partial-write prevention
- connection/transaction ordering
- dry-run separation
- audit/provenance preservation

This contract provides design authority only.

## 2. AUTHORITY SEPARATION

TRANSACTION_BOUNDARY_CONTRACT_AUTHORITY=True

POSTGRESQL_TRANSACTION_IMPLEMENTATION_AUTHORIZED=False

POSTGRESQL_TRANSACTION_EXECUTION_AUTHORIZED=False

POSTGRESQL_CONNECTION_EXECUTION_AUTHORIZED=False

POSTGRESQL_STORAGE_ADAPTER_IMPLEMENTATION_AUTHORIZED=False

POSTGRESQL_DATABASE_MUTATION_AUTHORIZED=False

MIGRATION_EXECUTION_AUTHORIZED=False

## 3. TRANSACTION STATE MODEL

Define future semantic states:

- GCID_POSTGRES_TRANSACTION_NOT_EVALUATED
- GCID_POSTGRES_TRANSACTION_INELIGIBLE
- GCID_POSTGRES_TRANSACTION_ELIGIBLE
- GCID_POSTGRES_TRANSACTION_BEGIN_NOT_AUTHORIZED
- GCID_POSTGRES_TRANSACTION_ACTIVE
- GCID_POSTGRES_TRANSACTION_COMMIT_ELIGIBLE
- GCID_POSTGRES_TRANSACTION_COMMITTED
- GCID_POSTGRES_TRANSACTION_ROLLBACK_REQUIRED
- GCID_POSTGRES_TRANSACTION_ROLLED_BACK
- GCID_POSTGRES_TRANSACTION_FAILED

These are semantic states only.

No state defined here grants execution authority.

## 4. TRANSACTION ELIGIBILITY

A future transaction may become eligible only after:

- governed configuration is valid
- connection eligibility predicates pass
- an authorized connection is successfully open
- separate transaction execution authority exists
- required mutation eligibility predicates pass for the intended operation
- no fail-closed blocker is active

CONFIG_VALID_DOES_NOT_EQUAL_TRANSACTION_ELIGIBLE=True

CONNECTION_OPEN_DOES_NOT_EQUAL_TRANSACTION_ELIGIBLE=True

TRANSACTION_ELIGIBLE_DOES_NOT_EQUAL_TRANSACTION_AUTHORIZED=True

TRANSACTION_AUTHORIZED_DOES_NOT_EQUAL_MUTATION_AUTHORIZED=True

## 5. EXPLICIT TRANSACTION BEGIN

A future transaction must begin only through an explicit governed operation.

TRANSACTION_BEGIN_EXPLICIT_ONLY=True

IMPORT_TIME_TRANSACTION_FORBIDDEN=True

CONFIG_PARSE_TRANSACTION_FORBIDDEN=True

CONNECTION_ACQUISITION_AUTO_BEGIN_FORBIDDEN=True

DRY_RUN_TRANSACTION_BEGIN_FORBIDDEN=True

No hidden or implicit transaction may acquire write authority.

## 6. TRANSACTION OWNER

Every future transaction must have exactly one explicit owning operation.

TRANSACTION_OWNER_REQUIRED=True

TRANSACTION_SINGLE_OWNER_REQUIRED=True

ORPHANED_TRANSACTION_ALLOWED=False

The owning operation is responsible for:

- begin
- bounded mutation scope
- validation before commit
- commit or rollback
- cleanup
- final transaction state

## 7. TRANSACTION SCOPE

One transaction must correspond to one governed durable-storage operation unless a later contract explicitly authorizes broader grouping.

TRANSACTION_SCOPE_EXPLICIT=True

CROSS_OPERATION_IMPLICIT_TRANSACTION_FORBIDDEN=True

PROCESS_LIFETIME_TRANSACTION_FORBIDDEN=True

GLOBAL_TRANSACTION_FORBIDDEN=True

## 8. AUTOCOMMIT BOUNDARY

Automatic persistence must not bypass the governed commit decision.

UNCONTROLLED_AUTOCOMMIT_AUTHORIZED=False

IMPLICIT_COMMIT_AUTHORIZED=False

A future implementation must not rely on hidden commit behavior for governed writes.

Do not prescribe a specific Psycopg API in this contract.

## 9. COMMIT ELIGIBILITY

Future commit eligibility requires all of the following:

- transaction is active
- operation remains authorized
- every intended mutation in the operation succeeded
- all required invariant checks passed
- required provenance/audit material is available
- no rollback condition is present
- no exception escaped the governed operation
- no authority predicate was revoked during the operation

COMMIT_REQUIRES_COMPLETE_OPERATION_SUCCESS=True

COMMIT_REQUIRES_REQUIRED_INVARIANTS=True

COMMIT_REQUIRES_AUDIT_PROVENANCE_READINESS=True

PARTIAL_SUCCESS_COMMIT_AUTHORIZED=False

## 10. COMMIT AUTHORITY SEPARATION

State explicitly:

TRANSACTION_COMMIT_ELIGIBLE != TRANSACTION_COMMIT_AUTHORIZED != DATABASE_MUTATION_AUTHORIZED

This contract does not grant any of those runtime authorities.

## 11. ROLLBACK CONDITIONS

A future active transaction must become rollback-required when any governed operation fails before successful commit.

Rollback conditions include:

- SQL/storage operation failure
- invariant failure
- authority failure
- provenance/audit preparation failure
- unexpected exception
- incomplete intended write set
- explicit operator/governance abort
- future implementation-defined fail-closed condition

ROLLBACK_ON_OPERATION_FAILURE_REQUIRED=True

ROLLBACK_ON_INVARIANT_FAILURE_REQUIRED=True

ROLLBACK_ON_AUTHORITY_FAILURE_REQUIRED=True

ROLLBACK_ON_EXCEPTION_REQUIRED=True

ROLLBACK_ON_INCOMPLETE_WRITE_SET_REQUIRED=True

## 12. PARTIAL-WRITE PREVENTION

The transaction boundary must prevent a governed multi-record operation from being deliberately committed in a partially completed state.

PARTIAL_WRITE_COMMIT_FORBIDDEN=True

ATOMIC_GOVERNED_OPERATION_REQUIRED=True

A failed governed operation must not intentionally leave a subset of its intended durable mutations committed.

Do not claim crash-level durability beyond PostgreSQL/database guarantees not yet tested.

## 13. ROLLBACK FAILURE

If a future rollback itself fails:

- classify the transaction as failed
- fail closed
- do not claim successful restoration
- surface a secret-safe critical failure state
- do not proceed with another mutation automatically

ROLLBACK_FAILURE_FAIL_CLOSED=True

ROLLBACK_FAILURE_MUTATION_CONTINUATION_FORBIDDEN=True

## 14. EXCEPTION BOUNDARY

Exceptions must not silently convert into successful commits.

EXCEPTION_CANNOT_IMPLY_COMMIT=True

TRANSACTION_EXCEPTION_CONTAINMENT_REQUIRED=True

TRANSACTION_EXCEPTION_REQUIRES_ROLLBACK_ATTEMPT=True

## 15. CONNECTION / TRANSACTION ORDERING

The future lifecycle order is:

configuration eligibility -> connection eligibility -> authorized connection acquisition -> connection open -> transaction eligibility -> separately authorized transaction begin -> governed operation -> commit eligibility OR rollback requirement -> commit/rollback -> transaction terminal state -> connection cleanup/close

TRANSACTION_REQUIRES_OPEN_CONNECTION=True

CONNECTION_CLOSE_BEFORE_ACTIVE_TRANSACTION_COMPLETION_FORBIDDEN=True

CONNECTION_CLEANUP_AFTER_TRANSACTION_TERMINAL_STATE_REQUIRED=True

## 16. DRY-RUN SEPARATION

Existing GCID dry-run behavior remains non-persisting.

GCID_DRY_RUN_TRANSACTION_REQUIRED=False

GCID_DRY_RUN_TRANSACTION_AUTHORIZED=False

GCID_DRY_RUN_COMMIT_AUTHORIZED=False

GCID_DRY_RUN_ROLLBACK_EXECUTION_REQUIRED=False

VALID_CONFIGURATION_MUST_NOT_CAUSE_DRY_RUN_TRANSACTION=True

## 17. RETRY SEPARATION

Existing connection contract preserves:

AUTOMATIC_CONNECTION_RETRY_AUTHORIZED=False

This transaction contract must also define:

AUTOMATIC_TRANSACTION_RETRY_AUTHORIZED=False

TRANSACTION_RETRY_POLICY_DEFINED=False

No future implementation may silently retry a failed mutation/transaction.

Exactly-once/idempotency behavior, if required, must be separately governed.

## 18. NESTED TRANSACTION / SAVEPOINT BOUNDARY

Do not authorize nested transactions or savepoints.

NESTED_TRANSACTION_AUTHORIZED=False

SAVEPOINT_CONTRACT_PRESENT=False

SAVEPOINT_EXECUTION_AUTHORIZED=False

A future contract must explicitly authorize these if required.

## 19. TWO-PHASE / DISTRIBUTED TRANSACTION BOUNDARY

TWO_PHASE_COMMIT_AUTHORIZED=False

DISTRIBUTED_TRANSACTION_CONTRACT_PRESENT=False

The current GCID durable-storage contract does not silently acquire distributed transaction semantics.

## 20. AUDIT / PROVENANCE ORDERING

Existing GCID provenance/audit contracts remain applicable.

AUDIT_PROVENANCE_REQUIRED_BEFORE_COMMIT_ELIGIBILITY=True

AUDIT_RECORD_DOES_NOT_GRANT_COMMIT_AUTHORITY=True

AUDIT_RECORD_DOES_NOT_GRANT_MUTATION_AUTHORITY=True

Do not implement audit persistence in this slice.

## 21. SCHEMA / MIGRATION SEPARATION

OFFLINE_GCID_SCHEMA_CONTRACT_PRESENT=True

TRANSACTION_AUTHORITY_DOES_NOT_AUTHORIZE_SCHEMA_EXECUTION=True

SCHEMA_EXECUTION_AUTHORIZED=False

MIGRATION_EXECUTION_AUTHORIZED=False

Migration transactions require separate governance.

## 22. MUTATION AUTHORITY PRESERVATION

Preserve exactly:

GCID_DATABASE_MUTATION_AUTHORIZED=False

The presence of a locked transaction contract must not alter that predicate.

## 23. TRANSACTION TIMEOUT BOUNDARY

Do not invent a transaction timeout value.

TRANSACTION_TIMEOUT_VALUE_DEFINED=False

TRANSACTION_TIMEOUT_POLICY_PRESENT=False

The already locked connection timeout requirement remains separate.

If transaction timeout governance is later required, bind it in a separate bounded design/test slice.

## 24. FUTURE IMPLEMENTATION PREDICATES

GCID_POSTGRES_TRANSACTION_STATE_MODEL_DEFINED=True

GCID_POSTGRES_TRANSACTION_ELIGIBILITY_DEFINED=True

GCID_POSTGRES_TRANSACTION_BEGIN_EXPLICIT_ONLY=True

GCID_POSTGRES_TRANSACTION_OWNER_REQUIRED=True

GCID_POSTGRES_TRANSACTION_SINGLE_OWNER_REQUIRED=True

GCID_POSTGRES_TRANSACTION_SCOPE_EXPLICIT=True

GCID_POSTGRES_UNCONTROLLED_AUTOCOMMIT_AUTHORIZED=False

GCID_POSTGRES_COMMIT_REQUIRES_COMPLETE_SUCCESS=True

GCID_POSTGRES_PARTIAL_WRITE_COMMIT_FORBIDDEN=True

GCID_POSTGRES_ROLLBACK_ON_FAILURE_REQUIRED=True

GCID_POSTGRES_ROLLBACK_ON_EXCEPTION_REQUIRED=True

GCID_POSTGRES_ROLLBACK_FAILURE_FAIL_CLOSED=True

GCID_POSTGRES_AUTOMATIC_TRANSACTION_RETRY_AUTHORIZED=False

GCID_POSTGRES_NESTED_TRANSACTION_AUTHORIZED=False

GCID_POSTGRES_SAVEPOINT_EXECUTION_AUTHORIZED=False

GCID_POSTGRES_TWO_PHASE_COMMIT_AUTHORIZED=False

GCID_POSTGRES_AUDIT_PROVENANCE_REQUIRED_BEFORE_COMMIT_ELIGIBILITY=True

GCID_POSTGRES_DRY_RUN_TRANSACTION_AUTHORIZED=False

GCID_POSTGRES_TRANSACTION_OPEN_DOES_NOT_AUTHORIZE_MUTATION=True

## 25. NON-GOALS

This slice does not define or implement:

- Psycopg transaction APIs
- database connections
- SQL
- schema execution
- migrations
- transaction retries
- savepoints
- nested transactions
- two-phase commit
- mutation execution
- concrete adapter implementation
- implementation tests
- live database tests
- fighter identity writes
- ranking persistence

## 26. AUTHORITY BOUNDARY

At completion:

GCID_POSTGRESQL_TRANSACTION_BOUNDARY_CONTRACT_LOCKED=True

GCID_POSTGRESQL_STORAGE_ADAPTER_IMPLEMENTATION_AUTHORITY_PRESENT=False

GCID_POSTGRESQL_STORAGE_ADAPTER_CODE_READY=False

GCID_POSTGRESQL_STORAGE_ADAPTER_EXECUTION_AUTHORIZED=False

GCID_DATABASE_CONNECTION_AUTHORITY_PRESENT=False

GCID_DATABASE_MUTATION_AUTHORIZED=False

TRANSACTION_EXECUTION_AUTHORIZED=False

SCHEMA_EXECUTION_AUTHORIZED=False

MIGRATION_EXECUTION_AUTHORIZED=False

PROJECT_FIGHTER_RANKING_LEDGER_IMPLEMENTATION_AUTHORIZED=False
