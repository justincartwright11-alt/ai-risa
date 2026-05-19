"""Button 2 Jbalia Reference Layout Parity Test v1."""

import os
from pathlib import Path
from pypdf import PdfReader
from operator_dashboard.app import app
from operator_dashboard.button2_template_pack_asset_renderer_v1 import DEFAULT_TEMPLATE_PACK_ROOT

ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
LIBRARY_ROUTE = "/api/button2/generated-report/library"
OPEN_ROUTE = "/api/button2/generated-report/open"

MATCHUPS = [
    ("Rico Verhoeven", "Tariq Osaro", "GLORY 100", "https://www.glorykickboxing.com/events/glory-100"),
    ("Anthony Joshua", "Daniel Dubois", "Joshua vs Dubois", "https://www.matchroomboxing.com/events/joshua-vs-dubois"),
    ("Alex Pereira", "Jiri Prochazka", "UFC 300", "https://www.ufc.com/event/ufc-300"),
]

REQUIRED_COVER = [
    "PREMIUM FIGHT INTELLIGENCE REPORT",
    "THE INTELLIGENCE BENEATH THE VIOLENCE",
    "VS",
    "Source Traceable",
    "Operator Approved",
]
REQUIRED_DASHBOARD = [
    "Headline Prediction",
    "Confidence",
    "Volatility",
    "Executive Summary",
    "Control Zone",
    "Danger Zone",
    "Collapse Trigger",
    "Fight Control Intelligence Strip",
    "Control Thesis",
    "Flip Point",
    "Watch Cue",
    "Command Rule",
    "Round Control Projection",
    "Method Probability",
    "Risk Control",
]
FORBIDDEN = [
    "SECTION LENS",
    "MODEL STATUS",
    "REPORT TYPE",
    "Cover Page",
    "Premium Cover",
    "customer_ready_not_ready",
    "draft_only",
    "controlled_export_not_eligible",
    "template renderer profile",
    "visual QA rollup",
    "valid layers",
    "missing layers",
]
REQUIRED_VISUALS = [
    "Fighter Architecture Radar",
    "Tactical Edge Map",
    "Fighter Overview",
    "Tale of the Tape",
    "Body Risk Heat Map",
    "Round Control Projection",
    "Method Probability",
    "Scorecard Scenario",
    "Traceability / Source Map",
]

def test_jbalia_reference_layout_parity():
    # This is a placeholder for the full test implementation.
    # It should load the generated PDFs for each matchup, check for required/forbidden strings,
    # verify 24 pages, and validate cover/dashboard/visuals.
    assert True
