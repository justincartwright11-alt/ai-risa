# GCID Root Runtime Lock Artifact Contract v1

## 1. Purpose

The root-runtime lock artifact is the immutable,
checksum-bound representation of the governed direct
runtime dependency declarations in requirements.txt.

It is NOT a fully resolved transitive Python environment lock.

It MUST NOT be described as proof that every transitive
dependency or installed package version is frozen.

## 2. Authoritative Source

SOURCE_FILE=requirements.txt

SOURCE_BYTE_COUNT=226

SOURCE_SHA256=
d82e29c4d55e9a2c831d94af2d350fcd29440d799b53a63de4d8cbec6c9292f2

The artifact may be generated only when both byte count
and SHA-256 match exactly.

## 3. Artifact Path

ROOT_RUNTIME_LOCK_ARTIFACT_PATH=requirements.lock.txt

Exactly one root-runtime declaration lock artifact is governed
by this contract.

## 4. Artifact Encoding

ENCODING=UTF-8
UTF8_BOM=False
LINE_ENDINGS=LF
FINAL_NEWLINE=True

## 5. Artifact Semantics

The artifact locks direct root runtime declarations only.

LOCK_SCOPE=DIRECT_ROOT_RUNTIME_DECLARATIONS
TRANSITIVE_DEPENDENCY_LOCK=False
INSTALLED_ENVIRONMENT_SNAPSHOT=False
RESOLVER_OUTPUT=False

It must contain exactly these six governed declarations:

Flask==3.1.3
Pillow==12.3.0
pypdf==6.16.1
reportlab==5.0.0
WeasyPrint==69.0
psycopg[binary]==3.3.4

The declaration order in the generated artifact must follow
their order in the authenticated requirements.txt source.

No additional dependency declaration is permitted.

## 6. Deterministic Header

The artifact must begin with exactly these comment lines:

# AI-RISA GCID Root Runtime Lock Artifact
# Contract-Version: 1
# Source-File: requirements.txt
# Source-Byte-Count: 226
# Source-SHA256: d82e29c4d55e9a2c831d94af2d350fcd29440d799b53a63de4d8cbec6c9292f2
# Scope: direct-root-runtime-declarations-only
# Transitive-Dependency-Lock: false

Then one blank line.

Then the six authenticated declarations in source order.

No timestamps.
No machine-specific paths.
No usernames.
No environment-specific metadata.
No generated package inventory.

This ensures deterministic bytes from the same source contract.

## 7. Generation Method

Generation must be deterministic text transformation only.

Required sequence:

1. Read requirements.txt raw bytes.
2. Verify exact byte count 226.
3. Verify exact SHA-256.
4. Decode as UTF-8.
5. Extract non-empty, non-comment dependency declarations.
6. Require exactly six declarations.
7. Require the exact governed declaration set.
8. Preserve authenticated source declaration order.
9. Construct the exact governed header.
10. Add one blank line.
11. Add the six declarations.
12. Write UTF-8 without BOM using LF endings and one final newline.
13. Calculate resulting artifact byte count and SHA-256.
14. Validate its declaration set mechanically.

No package resolver may participate.

## 8. Explicit Forbidden Generation Methods

The contract must explicitly prohibit using these as the
generation mechanism:

pip freeze
pip list
pip install
pip download
pip-compile
uv lock
poetry lock
environment/package inventory
online package-index resolution
application imports
runtime startup

unless a future separately governed transitive-lock contract
authorizes one of them.

## 9. Network / Installation Contract

LOCK_GENERATION_NETWORK_REQUIRED=False
LOCK_GENERATION_INSTALL_REQUIRED=False
LOCK_GENERATION_RUNTIME_IMPORT_REQUIRED=False

Generation must succeed from tracked local source material only.

## 10. Transitive Dependency Boundary

This contract deliberately does NOT resolve or lock transitive
dependencies.

Therefore:

FULL_RUNTIME_ENVIRONMENT_REPRODUCIBILITY_PROVEN=False

If AI-RISA later requires a fully resolved environment lock,
that must be governed by a separate contract and separate slice.

The future contract must define:
- resolver
- Python version
- operating system/platform
- architecture
- package index/source authority
- hash policy
- transitive version policy
- environment marker handling

This root-runtime artifact must not silently acquire those semantics.

## 11. Mutation Boundary

Creating requirements.lock.txt in the later generation slice:

does not authorize package installation
does not authorize imports
does not authorize runtime execution
does not authorize PostgreSQL access
does not authorize GCID mutation
does not authorize storage-adapter implementation
does not establish fighter identity records
does not authorize fighter-ranking implementation

## 12. Required Future Generation Predicates

The later generation slice may PASS only if:

SOURCE_REQUIREMENTS_IDENTITY_MATCH=True
LOCK_ARTIFACT_PATH_DEFINED=True
LOCK_ARTIFACT_FORMAT_DEFINED=True
LOCK_GENERATION_METHOD_DEFINED=True
LOCK_GENERATION_OFFLINE_SAFE=True
LOCK_GENERATION_NETWORK_REQUIRED=False
LOCK_GENERATION_INSTALL_REQUIRED=False
LOCK_GENERATION_RUNTIME_IMPORT_REQUIRED=False
LOCK_CONTRACT_CONFLICT_FREE=True
LOCK_ARTIFACT_DECLARATION_COUNT=6
LOCK_ARTIFACT_DECLARATION_SET_EXACT=True
LOCK_ARTIFACT_SOURCE_ORDER_PRESERVED=True

## 13. Authority Boundary

This document provides design/contract authority only.

LOCK_ARTIFACT_GENERATION_AUTHORIZED=False

A separate generation slice is required after this contract
is checkpointed.

POSTGRESQL_STORAGE_ADAPTER_IMPLEMENTATION_AUTHORIZED=False
DATABASE_MUTATION_AUTHORIZED=False
FIGHTER_IDENTITY_RECORDS_ESTABLISHED=False
PROJECT_FIGHTER_RANKING_LEDGER_IMPLEMENTATION_AUTHORIZED=False
