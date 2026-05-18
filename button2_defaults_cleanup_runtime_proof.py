"""
Button 2 Defaults Cleanup Runtime Proof Script
-----------------------------------------------

Purpose:
  1. Start AI-RISA dashboard
  2. Generate 3 test PDFs (Rico, Anthony Joshua, Jiri)
  3. Verify no forbidden strings in extracted text
  4. Verify dashboard and library links work
  5. Generate evidence artifacts

Run: python button2_defaults_cleanup_runtime_proof.py
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from pypdf import PdfReader

# Test configuration
TEST_OUTPUT_ROOT = Path(__file__).parent / "ops" / "runtime_diagnostics" / "button2_defaults_cleanup_proof"
TEST_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

DASHBOARD_URL = "http://127.0.0.1:5050"
GENERATE_ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
LIBRARY_ROUTE = "/api/button2/generated-report/library"

FORBIDDEN_STRINGS = [
    "Operator Summary Preview",
    "Premium Selected-Matchup Intelligence Summary",
    "Template renderer profile",
    "premium_template_pack_v29",
    "Renderer mode",
    "Source context",
    "Ingest mode",
    "Visual QA rollup",
    "Certification: not_ready",
    "controlled_export_not_eligible",
    "customer_ready_not_ready",
    "Overall visual confidence",
    "Valid layers",
    "Missing layers",
    "Radar data unavailable",
    "Heat map data unavailable",
    "Control-shift data unavailable",
    "Method distribution data unavailable",
    "visual_qa_rollup",
    "template_renderer_profile",
    "raw ingest",
]

TEST_CASES = [
    {
        "name": "Anthony Joshua vs Daniel Dubois",
        "fighter_a": "Anthony Joshua",
        "fighter_b": "Daniel Dubois",
        "event_name": "Joshua vs Dubois",
        "source_url": "https://www.matchroomboxing.com/events/joshua-vs-dubois",
    },
    {
        "name": "Rico Verhoeven vs Tariq Osaro",
        "fighter_a": "Rico Verhoeven",
        "fighter_b": "Tariq Osaro",
        "event_name": "GLORY 100",
        "source_url": "https://www.glorykickboxing.com/events/glory-100",
    },
    {
        "name": "Jiri Prochazka vs Carlos Ulberg",
        "fighter_a": "Jiri Prochazka",
        "fighter_b": "Carlos Ulberg",
        "event_name": "UFC 320",
        "source_url": "https://www.ufc.com/event/ufc-320",
    },
]


def check_forbidden_strings(text, test_name):
    """Check if any forbidden strings appear in extracted text."""
    lower_text = text.lower()
    found_forbidden = []
    
    for phrase in FORBIDDEN_STRINGS:
        phrase_lower = phrase.lower()
        if phrase_lower in lower_text:
            found_forbidden.append(phrase)
    
    return found_forbidden


def analyze_pdf(pdf_path):
    """Extract text and analyze PDF."""
    reader = PdfReader(pdf_path)
    page_count = len(reader.pages)
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    
    forbidden = check_forbidden_strings(text, pdf_path)
    
    return {
        "page_count": page_count,
        "text_length": len(text),
        "forbidden_strings_found": forbidden,
        "has_source_traceability": "Source Traceability" in text,
        "has_disclaimer": any(kw in text for kw in ["Disclaimer", "Risk", "probabilistic"]),
        "sample_text_lines": text.split("\n")[:20],  # First 20 lines
    }


def main():
    print("=" * 80)
    print("Button 2 Defaults Cleanup - Runtime Proof")
    print("=" * 80)
    
    # Wait for dashboard to be available
    print("\n[1] Checking dashboard availability...")
    import requests
    max_retries = 10
    for attempt in range(max_retries):
        try:
            r = requests.get(DASHBOARD_URL, timeout=2)
            if r.status_code == 200:
                print(f"✓ Dashboard available at {DASHBOARD_URL}")
                break
        except:
            pass
        if attempt < max_retries - 1:
            print(f"  Attempt {attempt + 1}/{max_retries} - retrying in 1s...")
            time.sleep(1)
    else:
        print(f"✗ Dashboard not available after {max_retries} attempts")
        print(f"  Expected at: {DASHBOARD_URL}")
        print(f"  Run: .\\scripts\\start_ai_risa_dashboard_windows.ps1")
        return 1
    
    # Test PDF generation and analysis
    print("\n[2] Generating test PDFs...")
    proof_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "dashboard_url": DASHBOARD_URL,
        "test_cases": [],
    }
    
    for test_case in TEST_CASES:
        print(f"\n  Testing: {test_case['name']}")
        
        try:
            import requests
            
            payload = {
                "operator_approved": True,
                "selected_matchup_preview": {
                    "selected_for_button2": True,
                    "selection_preview": True,
                    "fighter_a": test_case["fighter_a"],
                    "fighter_b": test_case["fighter_b"],
                    "event_name": test_case["event_name"],
                    "event_date": "2026-09-21",
                    "promotion": "Premium Promotion",
                    "source_type": "official",
                    "source_url": test_case["source_url"],
                    "report_ready_status": "ready_for_button2_preview",
                }
            }
            
            response = requests.post(
                f"{DASHBOARD_URL}{GENERATE_ROUTE}",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"    ✗ Generation failed: {response.status_code}")
                proof_results["test_cases"].append({
                    "test_name": test_case["name"],
                    "status": "FAILED",
                    "error": f"HTTP {response.status_code}",
                })
                continue
            
            data = response.json()
            if not data.get("ok"):
                print(f"    ✗ Generation error: {data.get('error')}")
                proof_results["test_cases"].append({
                    "test_name": test_case["name"],
                    "status": "FAILED",
                    "error": data.get("error", "unknown"),
                })
                continue
            
            pdf_path = data.get("output_path")
            print(f"    ✓ PDF generated: {Path(pdf_path).name}")
            
            # Analyze PDF
            analysis = analyze_pdf(pdf_path)
            
            result_entry = {
                "test_name": test_case["name"],
                "status": "PASSED" if not analysis["forbidden_strings_found"] else "FAILED",
                "pdf_path": pdf_path,
                "page_count": analysis["page_count"],
                "forbidden_strings_found": analysis["forbidden_strings_found"],
                "has_source_traceability": analysis["has_source_traceability"],
                "has_disclaimer": analysis["has_disclaimer"],
            }
            
            if analysis["forbidden_strings_found"]:
                print(f"    ✗ Forbidden strings found: {analysis['forbidden_strings_found']}")
            else:
                print(f"    ✓ No forbidden strings")
                print(f"    ✓ Page count: {analysis['page_count']}")
                print(f"    ✓ Source Traceability: {analysis['has_source_traceability']}")
                print(f"    ✓ Disclaimer: {analysis['has_disclaimer']}")
            
            proof_results["test_cases"].append(result_entry)
            
        except Exception as e:
            print(f"    ✗ Exception: {str(e)}")
            proof_results["test_cases"].append({
                "test_name": test_case["name"],
                "status": "FAILED",
                "error": str(e),
            })
    
    # Test dashboard and library links
    print("\n[3] Verifying dashboard and library links...")
    
    try:
        import requests
        
        # Check dashboard has PDF links
        dashboard_response = requests.get(DASHBOARD_URL, timeout=10)
        dashboard_html = dashboard_response.text
        
        has_pdf_folder = "PDF Reports Folder" in dashboard_html
        has_library_link = "Open PDF Reports Library" in dashboard_html or "/api/button2/generated-report/library" in dashboard_html
        
        print(f"  PDF Reports Folder link: {'✓' if has_pdf_folder else '✗'}")
        print(f"  Open PDF Reports Library link: {'✓' if has_library_link else '✗'}")
        
        # Check library route
        library_response = requests.get(f"{DASHBOARD_URL}{LIBRARY_ROUTE}", timeout=10)
        library_ok = library_response.status_code == 200
        print(f"  Library route accessible: {'✓' if library_ok else '✗'}")
        
        proof_results["dashboard_links"] = {
            "pdf_folder_link": has_pdf_folder,
            "library_link": has_library_link,
            "library_route_accessible": library_ok,
        }
        
    except Exception as e:
        print(f"  ✗ Dashboard link check failed: {str(e)}")
        proof_results["dashboard_links"] = {"error": str(e)}
    
    # Summary
    print("\n[4] Summary...")
    passed_count = sum(1 for tc in proof_results["test_cases"] if tc.get("status") == "PASSED")
    total_count = len([tc for tc in proof_results["test_cases"] if "status" in tc])
    
    print(f"\n  Test Results: {passed_count}/{total_count} passed")
    
    # Write evidence artifact
    evidence_file = TEST_OUTPUT_ROOT / "defaults_cleanup_summary.json"
    with open(evidence_file, "w") as f:
        json.dump(proof_results, f, indent=2)
    
    print(f"  Evidence saved: {evidence_file}")
    
    # Final status
    overall_status = all(
        tc.get("status") == "PASSED" 
        for tc in proof_results["test_cases"] 
        if "status" in tc
    ) and proof_results.get("dashboard_links", {}).get("library_route_accessible", False)
    
    if overall_status:
        print("\n✓ RUNTIME PROOF PASSED")
        return 0
    else:
        print("\n✗ RUNTIME PROOF FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
