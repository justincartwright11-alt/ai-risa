import os
import subprocess
import sys
from pathlib import Path


def test_packaged_runtime_startup_import_closure_from_isolated_package_root():
    package_root = Path(__file__).resolve().parents[1]
    repo_root = package_root.parents[1]

    code = """
import os
import sys

repo_root = os.path.normcase(os.path.normpath(os.environ['AI_RISA_REPO_ROOT']))
paths = {
    os.path.normcase(os.path.normpath(p if p else os.getcwd()))
    for p in sys.path
}
if repo_root in paths:
    raise SystemExit('REPO_ROOT_ON_SYSPATH')

from runtime.app import app
assert app is not None
print('PACKAGED_RUNTIME_IMPORT_PASS')
"""

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["AI_RISA_REPO_ROOT"] = str(repo_root)

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(package_root),
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "PACKAGED_RUNTIME_IMPORT_PASS" in result.stdout
