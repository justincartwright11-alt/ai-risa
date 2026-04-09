import os
import json
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

ASSET_DIR = os.path.join(os.path.dirname(__file__), "report_assets")
os.makedirs(ASSET_DIR, exist_ok=True)

def get_fixture_id(report_payload):
    # Use a deterministic fixture id from packaging or headline
    packaging = report_payload.get("packaging", {})
    headline = report_payload.get("headline", {})
    # Prefer a unique id if present, else fallback to winner+opponent
    return packaging.get("fixture_id") or packaging.get("report_id") or headline.get("winner","unknown")

def get_manifest_path(fixture_id):
    return os.path.join(ASSET_DIR, f"{fixture_id}_visual_manifest.json")

def get_asset_path(fixture_id, slot):
    return os.path.join(ASSET_DIR, f"{fixture_id}_{slot}.png")

def produce_method_chart(report_payload):
    """Generate method_chart PNG if data is available. Returns asset_path or None."""
    fixture_id = get_fixture_id(report_payload)
    asset_path = get_asset_path(fixture_id, "method_chart")
    # Try to get method distribution from adapter payload
    core = None
    for section in report_payload.get("sections", []):
        if section.get("title","").lower().startswith("prediction core"):
            core = section.get("content", {})
            break
    method_dist = None
    if core and "method_distribution" in core:
        method_dist = core["method_distribution"]
    elif "method_distribution" in report_payload:
        method_dist = report_payload["method_distribution"]
    if not method_dist or not isinstance(method_dist, dict) or not method_dist:
        return None
    # Plot
    methods = list(method_dist.keys())
    values = [method_dist[m] for m in methods]
    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    bars = ax.bar(methods, values, color="#2a3a5e")
    ax.set_title("Method of Victory Distribution", fontsize=24)
    ax.set_ylabel("Probability", fontsize=18)
    ax.set_xlabel("Method", fontsize=18)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(0, max(values)*1.1 if values else 1)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{v:.2f}", ha='center', va='bottom', fontsize=14)
    fig.tight_layout()
    fig.patch.set_facecolor('white')
    plt.savefig(asset_path, format="png", dpi=100, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    return asset_path

def build_visual_manifest(report_payload):
    """Build and write the per-fixture manifest for all visual slots."""
    fixture_id = get_fixture_id(report_payload)
    manifest = {}
    # Only method_chart for now
    method_chart_path = produce_method_chart(report_payload)
    if method_chart_path:
        manifest["method_chart"] = {"asset_path": method_chart_path, "caption": "Method of victory distribution"}
    # Other slots remain empty (placeholders)
    for slot in ["radar", "heat_map", "control_shift"]:
        manifest[slot] = None
    # Write manifest
    manifest_path = get_manifest_path(fixture_id)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest_path, manifest
