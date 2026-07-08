# Button 1 Packaged Runtime Production Start Contract Remediation v1

## Failure Summary
- ACTIVATION_RESULT=BUTTON1_PACKAGED_RUNTIME_FIRST_PRODUCTION_ACTIVATION_FAIL
- FIRST_EXACT_FAILURE=START_CONTRACT_RELOADER_ACTIVE
- ACTIVATION_ATTEMPTS=1
- RUNTIME_STARTED=YES
- HEALTH_REQUEST_COUNT=0
- CONTROLLED_STOP_COMPLETED=YES
- PORT_5050_LISTEN=NO
- FINAL_RUNTIME_STATE=NO_ACTIVE_PRODUCTION_RUNTIME

## Failure Classification
- CANDIDATE_FAILURE=NO
- DEPLOYMENT_PROVENANCE_FAILURE=NO
- HEALTH_CHECK_FAILURE=NO
- START_CONTRACT_FAILURE=YES

The failure occurred because direct execution of `python runtime/app.py` activated Flask debug/watchdog reloader behavior.

## Candidate Preservation
- AUTHORIZED_PRODUCTION_CANDIDATE=e9d3491
- AUTHORIZED_PRODUCTION_TAG=button1-packaged-runtime-operator-review-row-binding-remediation-v1

The start-contract remediation does not modify, rebuild, supersede, or reauthorize software candidate e9d3491.

## Failed Command Retirement
- RETIRED_PRODUCTION_START_COMMAND=python runtime/app.py

This command must not be reused for production activation under the current package because it activates an unauthorized debug/watchdog reloader path.

## Corrected Start Contract
- STARTUP_COMMAND=python -c "from runtime.app import app; app.run(host='127.0.0.1', port=5050, debug=False, use_reloader=False)"
- WORKING_DIRECTORY=C:\AI-RISA\production\button1_packaged_runtime\releases\e9d3491
- EXPECTED_HOST=127.0.0.1
- EXPECTED_PORT=5050
- DEBUG_MODE=false
- USE_RELOADER=false
- WATCHDOG_RESTART=forbidden
- AUTOMATIC_RESTART=forbidden
- PROCESS_MODEL=single_controlled_local_process

This corrected contract is required because it:
- imports the existing authorized application
- does not execute the app.py main startup block
- explicitly binds to 127.0.0.1
- explicitly uses port 5050
- explicitly disables debug mode
- explicitly disables the reloader
- preserves a single controlled local process
- requires no candidate source-code modification

## Unchanged Stop Contract
- CONTROLLED_LOCAL_PROCESS_STOP=Ctrl+C
- POST_STOP_REQUIREMENT=CONFIRM_LISTENER_RELEASED
- FINAL_RUNTIME_STATE=NO_ACTIVE_PRODUCTION_RUNTIME

## Unchanged Health Contract
- AUTHORIZED_HEALTH_REQUESTS=1
- AUTHORIZED_HEALTH_METHOD=GET
- AUTHORIZED_HEALTH_PATH=/

No workflow-preview POST is authorized.

## Authority State
- ORIGINAL_ACTIVATION_ATTEMPT_CONSUMED=YES
- ACTIVATION_RETRY_AUTHORITY=NOT_GRANTED
- PERMANENT_RUNTIME_AUTHORITY=NOT_GRANTED
- PERMANENT_WRITE_AUTHORITY=NOT_GRANTED
- CUSTOMER_OUTPUT_RELEASE_AUTHORITY=NOT_GRANTED
- LEARNING_CALIBRATION_AUTHORITY=NOT_GRANTED

The corrected start contract does not itself authorize another activation attempt.

## Next Required Slice
- NEXT_REQUIRED_SLICE=button1-packaged-runtime-production-activation-retry-authorization-decision-v1
