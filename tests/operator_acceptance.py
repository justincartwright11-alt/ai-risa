import os
import shutil
import tempfile
import csv
import subprocess
import sys
from pathlib import Path
import json

# Repo root and agent script path
REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_SCRIPT = REPO_ROOT / "ai_risa_local_agent.py"

# Operator-layer files to copy
OPERATOR_FILES = [
    'ai_risa_local_agent.py',
    'agent_task_dispatcher.py',
    'agent_queue_reader.py',
    'agent_reporter.py',
]

def copy_operator_runtime(temp_dir):
    for fname in OPERATOR_FILES:
        shutil.copy2(os.path.join(os.path.dirname(__file__), '..', fname), temp_dir)
    # Copy handlers/
    src_handlers = os.path.join(os.path.dirname(__file__), '..', 'handlers')
    dst_handlers = os.path.join(temp_dir, 'handlers')
    if os.path.exists(dst_handlers):
        shutil.rmtree(dst_handlers)
    shutil.copytree(src_handlers, dst_handlers)
    # Copy domain/
    src_domain = os.path.join(os.path.dirname(__file__), '..', 'domain')
    dst_domain = os.path.join(temp_dir, 'domain')
    if os.path.exists(dst_domain):
        shutil.rmtree(dst_domain)
    shutil.copytree(src_domain, dst_domain)

# Helpers
def write_queue_csv(path, fieldnames, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def run_operator(temp_dir, args=None, env=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    # Use the agent script from the temp_dir, not the repo root
    agent_script_path = os.path.join(temp_dir, "ai_risa_local_agent.py")
    cmd = [sys.executable, agent_script_path]
    if args:
        cmd += args
    result = subprocess.run(
        cmd,
        cwd=temp_dir,
        env=merged_env,
        capture_output=True,
        text=True,
    )
    return result

def read_queue_row(path):
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def assert_true(cond, msg):
    if not cond:
        print(f'ASSERTION FAILED: {msg}', file=sys.stderr)
        sys.exit(1)

def assert_file_exists(path, should_exist=True):
    if should_exist:
        assert_true(os.path.exists(path), f'File should exist: {path}')
    else:
        assert_true(not os.path.exists(path), f'File should NOT exist: {path}')

# Scenario 1: Success path
def test_success_path(temp_dir):
    queue_file = os.path.join(temp_dir, 'event_coverage_queue.csv')
    fieldnames = ['event_name', 'status', 'retry_count']
    event_name = 'acceptance_success_1'
    write_queue_csv(queue_file, fieldnames, [{
        'event_name': event_name,
        'status': 'queued',
        'retry_count': '0',
    }])
    # Prepare a clean environment (no simulation vars)
    env = os.environ.copy()
    env.pop('AI_RISA_SIM_ARTIFACT_FAIL', None)
    env.pop('AI_RISA_SIM_QUEUE_ACK_FAIL', None)
    # Run operator --execute
    result = run_operator(temp_dir, ['--execute'], env=env)
    print(result.stdout)
    if result.returncode != 0:
        print('--- Operator subprocess environment ---')
        for k in sorted(env):
            if k.startswith('AI_RISA'):
                print(f'{k}={env[k]}')
        print('--- Operator subprocess stderr ---')
        print(result.stderr)
    assert_true(result.returncode == 0, 'Operator did not exit cleanly on success path')
    rows = read_queue_row(queue_file)
    assert_true(rows[0]['status'] == 'completed', f"Expected status 'completed', got {rows[0]['status']}")
    assert_true(rows[0]['retry_count'] == '0', f"Expected retry_count '0', got {rows[0]['retry_count']}")
    artifact = os.path.join(temp_dir, f'event_decomposition_{event_name}.json')
    assert_file_exists(artifact)

# Scenario 2: Artifact-failure retry path to blocked
def test_artifact_failure_retry_path():
    temp_dir = tempfile.mkdtemp(prefix='operator_artifactfail_')
    try:
        # Copy operator files
        copy_operator_runtime(temp_dir)
        queue_file = os.path.join(temp_dir, 'event_coverage_queue.csv')
        fieldnames = ['event_name', 'status', 'retry_count']
        event_name = 'acceptance_artifactfail_1'
        write_queue_csv(queue_file, fieldnames, [{
            'event_name': event_name,
            'status': 'queued',
            'retry_count': '0',
        }])
        env = os.environ.copy()
        env['AI_RISA_SIM_ARTIFACT_FAIL'] = '1'
        env.pop('AI_RISA_SIM_QUEUE_ACK_FAIL', None)
        artifact = os.path.join(temp_dir, f'event_decomposition_{event_name}.json')
        # Run 1
        result1 = run_operator(temp_dir, ['--execute'], env=env)
        print(result1.stdout)
        rows = read_queue_row(queue_file)
        assert_true(rows[0]['retry_count'] == '1', f"Run 1: Expected retry_count '1', got {rows[0]['retry_count']}")
        assert_true(rows[0]['status'] == 'queued', f"Run 1: Expected status 'queued', got {rows[0]['status']}")
        assert_file_exists(artifact, should_exist=False)
        # Run 2
        result2 = run_operator(temp_dir, ['--execute'], env=env)
        print(result2.stdout)
        rows = read_queue_row(queue_file)
        assert_true(rows[0]['retry_count'] == '2', f"Run 2: Expected retry_count '2', got {rows[0]['retry_count']}")
        assert_true(rows[0]['status'] == 'queued', f"Run 2: Expected status 'queued', got {rows[0]['status']}")
        assert_file_exists(artifact, should_exist=False)
        # Run 3
        result3 = run_operator(temp_dir, ['--execute'], env=env)
        print(result3.stdout)
        rows = read_queue_row(queue_file)
        assert_true(rows[0]['retry_count'] == '3', f"Run 3: Expected retry_count '3', got {rows[0]['retry_count']}")
        assert_true(rows[0]['status'] == 'blocked', f"Run 3: Expected status 'blocked', got {rows[0]['status']}")
        assert_file_exists(artifact, should_exist=False)
        print('SUCCESS: Artifact-failure retry path to blocked passed.')
    finally:
        shutil.rmtree(temp_dir)

# Scenario 3: Queue-ack partial-success retry path to blocked
def test_queue_ack_retry_path():
    temp_dir = tempfile.mkdtemp(prefix='operator_queueackfail_')
    try:
        # Copy operator files
        copy_operator_runtime(temp_dir)
        queue_file = os.path.join(temp_dir, 'event_coverage_queue.csv')
        fieldnames = ['event_name', 'status', 'retry_count']
        event_name = 'acceptance_queueackfail_1'
        write_queue_csv(queue_file, fieldnames, [{
            'event_name': event_name,
            'status': 'queued',
            'retry_count': '0',
        }])
        env = os.environ.copy()
        env['AI_RISA_SIM_QUEUE_ACK_FAIL'] = '1'
        env.pop('AI_RISA_SIM_ARTIFACT_FAIL', None)
        artifact = os.path.join(temp_dir, f'event_decomposition_{event_name}.json')
        artifact_names = []
        # Run 1
        result1 = run_operator(temp_dir, ['--execute'], env=env)
        print(result1.stdout)
        rows = read_queue_row(queue_file)
        assert_true(rows[0]['retry_count'] == '1', f"Run 1: Expected retry_count '1', got {rows[0]['retry_count']}")
        assert_true(rows[0]['status'] == 'queued', f"Run 1: Expected status 'queued', got {rows[0]['status']}")
        assert_file_exists(artifact, should_exist=True)
        artifact_names.append(artifact)
        # Run 2
        result2 = run_operator(temp_dir, ['--execute'], env=env)
        print(result2.stdout)
        rows = read_queue_row(queue_file)
        assert_true(rows[0]['retry_count'] == '2', f"Run 2: Expected retry_count '2', got {rows[0]['retry_count']}")
        assert_true(rows[0]['status'] == 'queued', f"Run 2: Expected status 'queued', got {rows[0]['status']}")
        assert_file_exists(artifact, should_exist=True)
        artifact_names.append(artifact)
        # Run 3
        result3 = run_operator(temp_dir, ['--execute'], env=env)
        print(result3.stdout)
        rows = read_queue_row(queue_file)
        assert_true(rows[0]['retry_count'] == '3', f"Run 3: Expected retry_count '3', got {rows[0]['retry_count']}")
        assert_true(rows[0]['status'] == 'blocked', f"Run 3: Expected status 'blocked', got {rows[0]['status']}")
        assert_file_exists(artifact, should_exist=True)
        artifact_names.append(artifact)
        # Assert artifact filename is identical across all runs and only one file exists
        unique_artifacts = set(artifact_names)
        assert_true(len(unique_artifacts) == 1, f"Artifact filename changed across retries: {unique_artifacts}")
        print('SUCCESS: Queue-ack partial-success retry path to blocked passed.')
    finally:
        shutil.rmtree(temp_dir)

# Fixture-driven regression scenario runner
def run_fixture_scenario(fixture_dir):
    temp_dir = tempfile.mkdtemp(prefix='operator_fixture_')
    try:
        # Copy operator files
        copy_operator_runtime(temp_dir)
        # Copy input queue(s)
        for f in os.listdir(fixture_dir):
            if f.endswith('.csv') and not f.startswith('expected'):
                shutil.copy2(os.path.join(fixture_dir, f), os.path.join(temp_dir, f))
        # Load expected state
        with open(os.path.join(fixture_dir, 'expected.json'), encoding='utf-8') as f:
            expected = json.load(f)

        # Set up simulation environment variables for failure-path fixtures
        fixture_name = os.path.basename(fixture_dir)
        env = os.environ.copy()
        if fixture_name in ("artifact_fail_block", "event_batch_artifact_fail_block", "fighter_gap_artifact_fail_block"):
            env["AI_RISA_SIM_ARTIFACT_FAIL"] = "1"
            env.pop("AI_RISA_SIM_QUEUE_ACK_FAIL", None)
        elif fixture_name in ("queue_ack_block", "event_batch_queue_ack_block", "fighter_gap_queue_ack_block"):
            env["AI_RISA_SIM_QUEUE_ACK_FAIL"] = "1"
            env.pop("AI_RISA_SIM_ARTIFACT_FAIL", None)
        else:
            env.pop("AI_RISA_SIM_ARTIFACT_FAIL", None)
            env.pop("AI_RISA_SIM_QUEUE_ACK_FAIL", None)

        # Run operator --execute (simulate up to 3 times for retries)
        for i in range(3):
            result = run_operator(temp_dir, ['--execute'], env=env)
            print(result.stdout)
        # Compare resulting queue(s)
        for f in os.listdir(fixture_dir):
            if f.startswith('expected') and f.endswith('.csv'):
                expected_path = os.path.join(fixture_dir, f)
                actual_path = os.path.join(temp_dir, f.replace('expected_', ''))
                with open(expected_path, encoding='utf-8') as ef, open(actual_path, encoding='utf-8') as af:
                    expected_lines = [line.strip() for line in ef if line.strip()]
                    actual_lines = [line.strip() for line in af if line.strip()]
                    assert_true(expected_lines == actual_lines, f"Fixture {fixture_dir}: Queue mismatch\nExpected: {expected_lines}\nActual:   {actual_lines}")
        # Compare artifacts
        for artifact in expected.get('artifacts', []):
            artifact_path = os.path.join(temp_dir, artifact)
            assert_file_exists(artifact_path)
        # Ensure no unexpected artifacts
        for f in os.listdir(temp_dir):
            if f.endswith('.json') and f not in expected.get('artifacts', []):
                assert_true(False, f"Fixture {fixture_dir}: Unexpected artifact {f}")
        print(f'SUCCESS: Fixture {os.path.basename(fixture_dir)} regression scenario passed.')
    finally:
        shutil.rmtree(temp_dir)

def main():
    temp_dir = tempfile.mkdtemp(prefix='operator_acceptance_')
    try:
        # Copy operator files
        copy_operator_runtime(temp_dir)
        print(f'Acceptance test temp dir: {temp_dir}')
        # --- Update: seed all required queue CSVs with correct full schema headers ---
        required_queues = [
            ('event_coverage_queue.csv', ['event_name', 'status', 'event_date', 'sport', 'ruleset', 'retry_count', 'last_error']),
            ('fixture_gap_queue.csv', ['fixture_id', 'status', 'retry_count', 'last_error']),
            ('fixture_gap_queue_ranked.csv', ['status', 'fixture_id', 'artifact_trail_exists', 'missing_fixture_fields_count', 'result_linkage_present', 'one_pass_recovery_likelihood', 'priority']),
            ('fighter_gap_queue.csv', ['fighter_id', 'status', 'retry_count', 'last_error']),
            ('fighter_gap_queue_ranked.csv', ['status', 'fighter_id', 'event_name', 'artifact_trail_exists', 'source', 'coverage_status', 'priority']),
            ('event_batch_queue.csv', ['event_batch', 'status', 'retry_count', 'last_error']),
        ]
        for fname, headers in required_queues:
            queue_path = os.path.join(temp_dir, fname)
            with open(queue_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
        test_success_path(temp_dir)
        print('SUCCESS: Operator acceptance success path passed.')
        test_artifact_failure_retry_path()
        print('SUCCESS: Operator artifact-failure retry scenario passed.')
        test_queue_ack_retry_path()
        print('SUCCESS: Operator queue-ack retry scenario passed.')
    finally:
        # Clean up unless failure (sys.exit called on failure)
        shutil.rmtree(temp_dir)

    # Run all golden regression fixtures, including new fighter-gap real grounding
    fixture_root = os.path.join(os.path.dirname(__file__), 'fixtures', 'operator')
    for fixture in sorted(os.listdir(fixture_root)):
        fixture_dir = os.path.join(fixture_root, fixture)
        if os.path.isdir(fixture_dir):
            # Only run fighter_gap_* fixtures for fighter-gap scenarios
            if fixture.startswith('fighter_gap_') or fixture in [
                'success_event', 'artifact_fail_block', 'queue_ack_block', 'no_valid_task', 'event_batch_success', 'event_batch_artifact_fail_block', 'event_batch_queue_ack_block']:
                run_fixture_scenario(fixture_dir)
    print('SUCCESS: All golden regression fixtures passed.')

if __name__ == '__main__':
    main()
