import os
from datetime import datetime

def get_generated_at():
    fixed = os.environ.get("AI_RISA_FIXED_TIMESTAMP")
    if fixed:
        return fixed
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def get_version_tag():
    return "ai-risa-phase3"
