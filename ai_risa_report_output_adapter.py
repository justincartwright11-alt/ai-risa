# ai_risa_report_output_adapter.py
"""
Adapter to map engine output (result_dict) to the master report template structure.
This module does not alter engine logic or scoring.
"""

def map_engine_output_to_report(engine_output):
    # Example: flatten or reorder fields, add template sections, etc.
    # This is a stub; fill in with real template logic as needed.
    report = {
        "winner": engine_output.get("predicted_winner_id"),
        "confidence": engine_output.get("confidence"),
        "method": engine_output.get("method"),
        "round": engine_output.get("round"),
        "debug_metrics": engine_output.get("debug_metrics"),
        # Add more template fields/sections as needed
    }
    return report
