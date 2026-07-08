# Button 1 Packaged Runtime Production Target Definition v1

## Slice
- slice_id: button1-packaged-runtime-production-target-definition-v1
- phase: Production Target Definition
- authority: DOCS-ONLY OPERATOR TARGET DEFINITION

## Target Identity
- PRODUCTION_TARGET_ID=button1-local-operator-windows-v1
- DEPLOYMENT_CLASS=CONTROLLED_LOCAL_OPERATOR_PRODUCTION
- HOST_PLATFORM=EXISTING_WINDOWS_OPERATOR_WORKSTATION
- OPERATOR_ACCESS=LOCAL_ONLY
- NETWORK_EXPOSURE=LOOPBACK_ONLY
- PUBLIC_INTERNET_EXPOSURE=FORBIDDEN

This initial Button 1 packaged runtime production target is the existing Windows operator workstation with local operator-controlled execution only.

This target permits loopback-only access and forbids public internet exposure, external customer access, and any externally reachable production surface.

## Deployment Location
- DEPLOYMENT_ROOT=C:\AI-RISA\production\button1_packaged_runtime
- AUTHORIZED_RELEASE_DIRECTORY=C:\AI-RISA\production\button1_packaged_runtime\releases\e9d3491

The production deployment root and authorized release directory are separate from the OneDrive development worktree.

## Candidate Identity Lock
- AUTHORIZED_PRODUCTION_CANDIDATE=e9d3491
- AUTHORIZED_PRODUCTION_TAG=button1-packaged-runtime-operator-review-row-binding-remediation-v1

This production-target definition does not change, rebuild, amend, supersede, or reauthorize candidate e9d3491.

## Network Boundary
- loopback-only access is required
- public bind is not authorized
- LAN exposure is not authorized unless separately authorized
- cloud exposure is not authorized
- reverse proxy exposure is not authorized
- public DNS exposure is not authorized
- external customer access is not authorized

Any later move to server hosting, cloud hosting, container hosting, LAN exposure, internet exposure, or public customer access requires separate architecture and authorization.

## Service Model
- INITIAL_SERVICE_MODEL=CONTROLLED_LOCAL_PROCESS

Not authorized in this target definition:
- automatic operating-system startup
- background service installation
- Windows Service creation
- scheduled startup
- auto-restart

These capabilities require separate future authority.

## First-Production Rollback State
- PRIOR_PRODUCTION_BASELINE=NONE
- FAILED_FIRST_ACTIVATION_ROLLBACK=RETURN_TO_NO_ACTIVE_PRODUCTION_RUNTIME

For failed first activation:
- stop the candidate runtime
- confirm listener release
- preserve authorized candidate and evidence
- do not execute mutation rollback because activation has no mutation authority
- do not invent a prior production commit

## Authority Boundaries
This production-target definition grants no authority for:
- deployment
- file copying
- directory creation
- dependency installation
- runtime startup
- endpoint execution
- network execution
- queue writes
- database writes
- GCID writes
- learning writes
- calibration writes
- customer-output release
- automatic saving

## Next Required Slice
- NEXT_REQUIRED_SLICE=button1-packaged-runtime-production-deployment-activation-readiness-reentry-v1
