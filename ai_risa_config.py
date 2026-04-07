from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR
FIGHTERS_DIR = DATA_DIR / "fighters"
PREDICTIONS_DIR = DATA_DIR / "predictions"
REPORTS_DIR = DATA_DIR / "reports"
OPS_DIR = DATA_DIR / "ops"

SIMULATIONS = 1000
USE_GPU = False
EMBEDDING_DIM = 128

DEFAULT_STOPPAGE_SENSITIVITY = 1.0
DEFAULT_CONFIDENCE_FLOOR = 0.5

# Minimal shims for ai_risa_v100_core.py
DEVICE = "cpu"
AMP_ENABLED = False
GPU_MANAGER = None

def ensure_dirs() -> None:
    for path in [
        FIGHTERS_DIR,
        PREDICTIONS_DIR,
        REPORTS_DIR,
        OPS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
