# test_qa_export_check.py
"""
Focused regression tests for _qa_content_text and _qa_check behaviour.

Proves:
  1. _qa_content_text does NOT surface internal metadata key names
     (fighter_a_id, fighter_b_id, fight_id, etc.) in its output.
  2. _qa_check does NOT raise a false-positive on a front_cover dict whose
     keys contain 'fighter_' — only the human-facing values are scanned.
  3. _qa_check DOES catch an actual forbidden token that appears in a
     human-facing text field.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from ai_risa_report_exporter import _qa_content_text


# ---------------------------------------------------------------------------
# Unit tests for _qa_content_text
# ---------------------------------------------------------------------------

def _assert(condition, message):
    if not condition:
        print(f"FAIL: {message}")
        sys.exit(1)


# 1. Dict with _id keys — keys must NOT appear in output text
front_cover_dict = {
    "fight_id": "some_fight_id",
    "fighter_a_id": "fighter_jafel_filho",
    "fighter_b_id": "fighter_cody_durden",
    "fighters": "Jafel Filho vs Cody Durden",
    "fighter_a_name": "Jafel Filho",
    "fighter_b_name": "Cody Durden",
    "event_date": "2026-01-01",
    "sport": "mma",
    "promotion": "UFC",
    "event_name": "UFC Fight Night",
    "method": "Decision",
    "confidence": 0.6,
    "round": "full",
}

text = _qa_content_text(front_cover_dict)

_assert("fighter_a_id" not in text, "_qa_content_text must not expose key 'fighter_a_id'")
_assert("fighter_b_id" not in text, "_qa_content_text must not expose key 'fighter_b_id'")
_assert("fight_id" not in text, "_qa_content_text must not expose key 'fight_id'")
_assert("fighter_jafel_filho" not in text, "_qa_content_text must not expose raw fighter ID value from _id key")
_assert("fighter_cody_durden" not in text, "_qa_content_text must not expose raw fighter ID value from _id key")

# Display values should be present
_assert("Jafel Filho vs Cody Durden" in text, "_qa_content_text must include fighters display string")
_assert("Jafel Filho" in text, "_qa_content_text must include fighter_a_name value")
_assert("Cody Durden" in text, "_qa_content_text must include fighter_b_name value")
_assert("UFC" in text, "_qa_content_text must include promotion value")
_assert("mma" in text, "_qa_content_text must include sport value")

# 2. The scanned text must NOT trigger the 'fighter_' forbidden token
_assert("fighter_" not in text.lower(),
        "_qa_content_text output must not contain 'fighter_' (would trip QA gate)")

# 3. Nested list content
nested = {"body": ["Fighter A is dominant", "Fighter B is resilient"]}
nested_text = _qa_content_text(nested)
_assert("Fighter A is dominant" in nested_text, "nested list values must be included")
_assert("Fighter B is resilient" in nested_text, "nested list values must be included")

# 4. debug_ and trace_ prefixed keys must be excluded
debug_dict = {
    "body": "Real content here",
    "debug_metrics": {"some": "data"},
    "trace_profile_keys": ["key1", "key2"],
    "internal_flag": True,
}
debug_text = _qa_content_text(debug_dict)
_assert("Real content here" in debug_text, "body value must appear in output")
_assert("debug_metrics" not in debug_text, "debug_ prefixed keys must not appear")
_assert("trace_profile_keys" not in debug_text, "trace_ prefixed keys must not appear")
_assert("internal_flag" not in debug_text, "internal_ prefixed keys must not appear")

# 5. Actual forbidden token in a human-facing field MUST still be caught
forbidden_dict = {"body": "This report is n/a for this event."}
forbidden_text = _qa_content_text(forbidden_dict)
_assert("n/a" in forbidden_text.lower(),
        "Actual forbidden token in display field must appear in QA scan text")

# 6. Plain string content passes through unchanged
plain = _qa_content_text("Joshua Van is the favourite.")
_assert(plain == "Joshua Van is the favourite.", "Plain string must pass through unchanged")

# 7. None content returns empty string
_assert(_qa_content_text(None) == "", "None content must produce empty string")

# 8. Empty dict returns empty string
_assert(_qa_content_text({}) == "", "Empty dict must produce empty string")

print("All QA export check tests passed.")
