
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify
import subprocess
import os


app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUEUE_FILE = PROJECT_ROOT / 'event_coverage_queue.csv'
LIVE_LOG = PROJECT_ROOT / 'docs' / 'live_release_window_log.md'
MANIFEST = PROJECT_ROOT / 'docs' / 'runtime_release_manifest.md'
GO_NO_GO = PROJECT_ROOT / 'docs' / 'operator_release_go_no_go_note.md'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_local_ai', methods=['POST'])
def run_local_ai():
    args = [sys.executable, str(PROJECT_ROOT / 'ai_risa_local_agent.py'), '--execute']
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False, cwd=str(PROJECT_ROOT))
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/run_acceptance_test', methods=['POST'])
def run_acceptance_test():
    args = [sys.executable, str(PROJECT_ROOT / 'tests' / 'operator_acceptance.py'), '--execute']
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False, cwd=str(PROJECT_ROOT))
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# POST endpoint to open local files with default app (Windows only)
@app.route('/open_file', methods=['POST'])
def open_file():
    file_type = request.json.get('file')
    if file_type == 'queue':
        path = QUEUE_FILE
    elif file_type == 'log':
        path = LIVE_LOG
    elif file_type == 'manifest':
        path = MANIFEST
    elif file_type == 'go_no_go':
        path = GO_NO_GO
    else:
        return jsonify({'error': 'Invalid file type'}), 400
    try:
        os.startfile(str(path))
        return jsonify({'status': f'Opened {path.name}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
