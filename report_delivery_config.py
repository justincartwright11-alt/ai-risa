# report_delivery_config.py
"""
Delivery and packaging configuration for standardized report outputs.
"""

import os
from datetime import datetime

# Output root for all deliveries
DELIVERY_ROOT = os.path.join(os.path.dirname(__file__), "deliveries")

# Version string for this report pipeline
REPORT_VERSION = "v100-template-standardized"

# Timestamp policy: ISO date only (YYYYMMDD)
def get_today_str():
    return datetime.utcnow().strftime("%Y%m%d")

# Filename template
# Example: fighter_joshua_van_vs_fighter_tatsuro_taira__Premium_Fight_Intelligence_Brief__v100-template-standardized.json
def make_report_filename(fixture_slug, report_type, ext):
    return f"report.{ext}"

# Bundle folder layout
def get_report_output_dir(fixture_slug):
    return os.path.join(DELIVERY_ROOT, REPORT_VERSION, fixture_slug)

# Manifest filename
def get_manifest_filename():
    return "manifest.json"
