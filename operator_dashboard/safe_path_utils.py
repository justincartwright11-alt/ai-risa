import os
from pathlib import Path

# Add a hack for testing to allow dynamic roots
EXTRA_ROOTS = []

PROJECT_ROOTS = [
    Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))),
    Path(os.path.abspath(os.path.dirname(__file__)))
]

ALLOWED_ARTIFACT_DIRS = [
    'artifacts', 'outputs', 'results', 'docs', ''
]

def is_safe_artifact_path(artifact_value):
    if not artifact_value or not isinstance(artifact_value, str):
        return False, 'No artifact path provided.'
    try:
        norm = os.path.normpath(artifact_value)
        # Disallow traversal or absolute paths
        if os.path.isabs(norm) or '..' in norm.split(os.sep) or norm.startswith(os.sep):
            return False, 'Artifact path contains traversal or is absolute.'
        # Only allow under allowed dirs (must match exactly or as subdir)
        allowed = any(norm == d or norm.startswith(d + os.sep) for d in ALLOWED_ARTIFACT_DIRS if d)
        if not allowed and norm not in ALLOWED_ARTIFACT_DIRS:
            return False, 'Artifact path not under allowed directories.'
        # Must resolve under project root and exist
        for root in (PROJECT_ROOTS + EXTRA_ROOTS):
            try:
                # Use resolve on both and check if the resolved path is still under the root
                root_path = Path(root).resolve()
                resolved = (root_path / norm).resolve()
                if str(resolved).startswith(str(root_path)) and resolved.exists():
                    return True, str(resolved)
            except:
                continue
        return False, 'Artifact file does not exist under allowed roots.'
    except Exception as e:
        return False, f'Artifact path error: {e}'
