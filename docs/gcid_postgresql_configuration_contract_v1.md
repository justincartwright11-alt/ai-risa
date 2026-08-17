# GCID PostgreSQL Configuration Contract v1

## 1. Purpose

This document defines the non-secret configuration inputs and validation rules required by a future GCID PostgreSQL storage adapter.

```text
CONFIGURATION_CONTRACT_AUTHORITY=True
POSTGRESQL_ADAPTER_IMPLEMENTATION_AUTHORIZED=False
POSTGRESQL_CONNECTION_AUTHORIZED=False
POSTGRESQL_MUTATION_AUTHORIZED=False
MIGRATION_EXECUTION_AUTHORIZED=False
```

This contract defines configuration semantics only. It does not authorize implementation, connection, authentication, mutation, migration, or runtime execution.

## 2. Configuration Principle

Configuration is declarative input. Configuration existence does not grant execution authority.

A syntactically valid DSN or equivalent configuration does not authorize connection, authentication, schema creation, transaction execution, or database mutation.

## 3. Secret-Handling Law

No database password, credential, token, certificate private key, or other secret may be committed to Git. No real secret value may appear in tracked source, tracked documentation, tests, fixtures, logs, exception text, or audit records.

Tracked artifacts may define names, shapes, and validation rules only. Secret values must enter through an operator-controlled runtime secret source in a later, separately governed execution design. This contract does not choose or configure a production secret manager.

## 4. Canonical Configuration Interface

The canonical future runtime variable is:

```text
AI_RISA_GCID_POSTGRES_DSN
```

It is a single operator-supplied PostgreSQL connection descriptor for the future GCID durable-storage adapter.

```text
EXAMPLE_ONLY=True
REAL_CREDENTIAL=False
postgresql://<user>:<password>@<host>:<port>/<database>
```

The example contains unmistakably non-secret placeholders and is not a real DSN.

## 5. Supported Scheme

The governed DSN scheme is:

```text
postgresql://
```

No competing canonical DSN variable or alternate scheme is defined by this contract.

## 6. Required Logical Fields

A future configuration parser must be able to resolve:

- `scheme`
- `host`
- `port`
- `database`
- `user`
- `credential` or a secret reference, without persisting resolved credentials

If the port is omitted, the future parser may apply PostgreSQL standard port `5432`. No default host, database, username, or password is permitted.

## 7. Environment Binding

```text
CONFIG_SOURCE_ENVIRONMENT_VARIABLE=True
CANONICAL_ENVIRONMENT_VARIABLE=AI_RISA_GCID_POSTGRES_DSN
CONFIG_FILE_FALLBACK_AUTHORIZED=False
HARDCODED_DSN_AUTHORIZED=False
HARDCODED_CREDENTIAL_AUTHORIZED=False
COMMAND_LINE_SECRET_ARGUMENT_AUTHORIZED=False
```

The future adapter must not silently search multiple ungoverned configuration sources.

## 8. Absent Configuration Behaviour

If `AI_RISA_GCID_POSTGRES_DSN` is absent or empty:

```text
CONFIGURATION_AVAILABLE=False
DATABASE_CONNECTION_ELIGIBLE=False
```

The future system must fail closed. Absence must not construct localhost defaults, invent credentials, connect to an embedded database, fall back to SQLite, use test credentials, or connect to PostgreSQL.

## 9. Invalid Configuration Behaviour

Malformed or incomplete configuration must produce a non-secret configuration failure state. The future implementation must not echo the complete DSN when reporting errors.

The configuration status vocabulary is:

```text
GCID_POSTGRES_CONFIG_ABSENT
GCID_POSTGRES_CONFIG_INVALID
GCID_POSTGRES_CONFIG_VALID
```

These are configuration states only. `GCID_POSTGRES_CONFIG_VALID` does not imply `CONNECTION_AUTHORIZED=True` or `MUTATION_AUTHORIZED=True`.

## 10. Secret Redaction

Future logging and diagnostic behaviour must redact passwords, secrets, tokens, private-key material, and credential-bearing URI components.

A diagnostic may identify the configuration variable name, scheme, host if governance later permits, port, and database identifier if governance later permits. It must never expose a password or the full credential-bearing DSN. This contract grants no logging implementation authority.

## 11. Configuration Validation Boundary

Future static validation may check environment-variable existence, non-empty value, URI parseability, PostgreSQL scheme, required logical components, valid port syntax and range, and absence of prohibited embedded defaults.

Static validation must not attempt network connection.

```text
CONFIGURATION_STATIC_VALIDATION_NETWORK_REQUIRED=False
CONFIGURATION_STATIC_VALIDATION_DATABASE_CONNECTION_REQUIRED=False
CONFIGURATION_STATIC_VALIDATION_PSYCOPG_IMPORT_REQUIRED=False
```

## 12. Connection Authority Separation

The following are separate governed predicates:

```text
CONFIG_PRESENT
!=
CONFIG_VALID
!=
CONNECTION_ELIGIBLE
!=
CONNECTION_AUTHORIZED
!=
MUTATION_AUTHORIZED
```

A future connection-lifecycle slice must define connection acquisition, connection timeout, connection close, failure handling, resource cleanup, connection reuse or non-reuse, and connection authority. This configuration contract does not define those runtime mechanics.

## 13. Transaction Authority Separation

```text
TRANSACTION_BOUNDARY_DEFINED=False
TRANSACTION_EXECUTION_AUTHORIZED=False
```

A separate future transaction contract must define transaction ownership, begin semantics, commit conditions, rollback conditions, exception behaviour, partial-write prevention, and exactly-once protections where required. Those details are not defined here beyond identifying the missing boundary.

## 14. Schema and Migration Separation

```text
OFFLINE_GCID_SCHEMA_CONTRACT_PRESENT=True
SCHEMA_EXECUTION_AUTHORIZED=False
MIGRATION_CONTRACT_PRESENT=False
MIGRATION_EXECUTION_AUTHORIZED=False
```

Existing offline schema artifacts do not authorize schema execution. `MIGRATION_CONTRACT_PRESENT=False` stands unless separate authoritative repository evidence later says otherwise.

## 15. Dry-Run Preservation

```text
GCID_DRY_RUN_CONTRACT_PRESENT=True
GCID_DRY_RUN_PERSISTENCE_AUTHORIZED=False
VALID_POSTGRES_CONFIG_MUST_NOT_BYPASS_DRY_RUN=True
```

Existing GCID dry-run behaviour remains non-persisting.

## 16. Mutation Authority

```text
GCID_DATABASE_MUTATION_AUTHORIZED=False
```

No part of this configuration contract may alter that value.

## 17. Future Adapter Configuration Input Contract

A future storage adapter may consume configuration only after separate implementation authority exists. It must receive configuration through the governed interface, fail closed when absent or invalid, avoid embedded fallback credentials, avoid implicit localhost or default-database assumptions, avoid secret persistence, avoid secret logging, and not connect merely because configuration validates.

## 18. Required Future Configuration Predicates

```text
GCID_POSTGRES_CONFIG_SOURCE_DEFINED=True
GCID_POSTGRES_DSN_VARIABLE_DEFINED=True
GCID_POSTGRES_SECRET_HANDLING_DEFINED=True
GCID_POSTGRES_CONFIG_ABSENCE_FAIL_CLOSED=True
GCID_POSTGRES_CONFIG_INVALID_FAIL_CLOSED=True
GCID_POSTGRES_CONFIG_STATIC_VALIDATION_DEFINED=True
GCID_POSTGRES_CONFIG_STATIC_VALIDATION_NETWORK_REQUIRED=False
GCID_POSTGRES_CONFIG_STATIC_VALIDATION_DATABASE_CONNECTION_REQUIRED=False
GCID_POSTGRES_CONFIG_STATIC_VALIDATION_PSYCOPG_IMPORT_REQUIRED=False
GCID_POSTGRES_CONFIG_VALID_DOES_NOT_AUTHORIZE_CONNECTION=True
GCID_POSTGRES_CONFIG_VALID_DOES_NOT_AUTHORIZE_MUTATION=True
```

## 19. Non-Goals

This slice does not define connection lifecycle, transactions, connection pooling, retry policy, database creation, schema application, migration execution, SQL, storage-adapter implementation, runtime execution, database mutation, fighter identity persistence, or ranking-ledger persistence.

## 20. Authority Boundary

```text
GCID_POSTGRESQL_CONFIGURATION_CONTRACT_LOCKED=True
GCID_POSTGRESQL_STORAGE_ADAPTER_IMPLEMENTATION_AUTHORITY_PRESENT=False
GCID_POSTGRESQL_STORAGE_ADAPTER_CODE_READY=False
GCID_POSTGRESQL_STORAGE_ADAPTER_EXECUTION_AUTHORIZED=False
GCID_DATABASE_CONNECTION_AUTHORITY_PRESENT=False
GCID_DATABASE_MUTATION_AUTHORIZED=False
GCID_FIGHTER_IDENTITY_RECORDS_ESTABLISHED=False
PROJECT_FIGHTER_RANKING_LEDGER_IMPLEMENTATION_AUTHORIZED=False
```

The next governed slice is `GCID_POSTGRESQL_CONNECTION_LIFECYCLE_CONTRACT`, authorized only to define a read-only connection lifecycle and failure contract without execution.
