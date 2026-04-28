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


def produce_radar_chart(report_payload):
    """Generate radar chart PNG if radar_metrics is available. Returns asset_path or None."""
    fixture_id = get_fixture_id(report_payload)
    asset_path = get_asset_path(fixture_id, "radar")
    radar = report_payload.get("radar_metrics")
    if not radar or not isinstance(radar, dict):
        return None
    labels = radar.get("labels")
    series = radar.get("series") or []
    values = radar.get("values")
    scale_min = radar.get("scale_min", 0.0)
    scale_max = radar.get("scale_max", 1.0)
    if not labels:
        return None
    import numpy as np
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += [angles[0]]
    fig, ax = plt.subplots(figsize=(16, 9), subplot_kw=dict(polar=True), dpi=100)
    if series:
        palette = ["#b22222", "#2a3a5e"]
        for index, entry in enumerate(series[:2]):
            series_values = entry.get("values") or []
            if len(series_values) != len(labels):
                plt.close(fig)
                return None
            series_values = list(series_values) + [series_values[0]]
            color = palette[index % len(palette)]
            ax.plot(angles, series_values, color=color, linewidth=2, label=entry.get("label", f"Series {index + 1}"))
            ax.fill(angles, series_values, color=color, alpha=0.20)
        ax.legend(loc="upper right")
    else:
        if not values or len(labels) != len(values):
            plt.close(fig)
            return None
        values = list(values) + [values[0]]
        ax.plot(angles, values, color="#2a3a5e", linewidth=2)
        ax.fill(angles, values, color="#2a3a5e", alpha=0.25)
    ax.set_yticks(np.linspace(scale_min, scale_max, 5))
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=18)
    ax.set_title("Fighter Attribute Radar", fontsize=24, pad=24)
    ax.set_ylim(scale_min, scale_max)
    fig.tight_layout()
    fig.patch.set_facecolor('white')
    plt.savefig(asset_path, format="png", dpi=100, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    return asset_path


def produce_heat_map(report_payload):
    """Generate heat map PNG if heat_map_data is available. Returns asset_path or None."""
    fixture_id = get_fixture_id(report_payload)
    asset_path = get_asset_path(fixture_id, "heat_map")
    heat_map = report_payload.get("heat_map_data") or {}
    values = heat_map.get("values")
    x_labels = heat_map.get("x_labels") or []
    y_labels = heat_map.get("y_labels") or []
    if not values or not x_labels or not y_labels:
        return None
    import numpy as np
    array = np.array(values, dtype=float)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    heat = ax.imshow(array, cmap="coolwarm", vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, fontsize=14)
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels, fontsize=14)
    ax.set_title(heat_map.get("title", "Round Heat Map"), fontsize=24, pad=24)
    for row_index in range(array.shape[0]):
        for col_index in range(array.shape[1]):
            ax.text(col_index, row_index, f"{array[row_index, col_index] * 100:.0f}%", ha="center", va="center", fontsize=12)
    fig.colorbar(heat, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.patch.set_facecolor('white')
    plt.savefig(asset_path, format="png", dpi=100, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    return asset_path


def produce_control_shift_chart(report_payload):
    """Generate control shift PNG if control_shift_data is available. Returns asset_path or None."""
    fixture_id = get_fixture_id(report_payload)
    asset_path = get_asset_path(fixture_id, "control_shift")
    control_shift = report_payload.get("control_shift_data") or {}
    rounds = control_shift.get("rounds") or []
    series = control_shift.get("series") or []
    if not rounds or len(series) < 2:
        return None
    x = list(range(len(rounds)))
    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    palette = ["#b22222", "#2a3a5e"]
    for index, entry in enumerate(series[:2]):
        series_values = entry.get("values") or []
        if len(series_values) != len(rounds):
            plt.close(fig)
            return None
        color = palette[index % len(palette)]
        ax.plot(x, series_values, marker="o", linewidth=2, color=color, label=entry.get("label", f"Series {index + 1}"))
    ax.set_xticks(x)
    ax.set_xticklabels(rounds, fontsize=14)
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("Control Share", fontsize=18)
    ax.set_title(control_shift.get("title", "Control Shift Graph"), fontsize=24, pad=24)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.patch.set_facecolor('white')
    plt.savefig(asset_path, format="png", dpi=100, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    return asset_path

def build_visual_manifest(report_payload):
    """Build and write the per-fixture manifest for all visual slots."""
    fixture_id = get_fixture_id(report_payload)
    manifest = {}
    # method_chart
    method_chart_path = produce_method_chart(report_payload)
    if method_chart_path:
        manifest["method_chart"] = {"asset_path": method_chart_path, "caption": "Method of victory distribution"}
    # radar
    radar_chart_path = produce_radar_chart(report_payload)
    if radar_chart_path:
        manifest["radar"] = {"asset_path": radar_chart_path, "caption": "Fighter attribute radar"}
    else:
        manifest["radar"] = None
    heat_map_path = produce_heat_map(report_payload)
    manifest["heat_map"] = {"asset_path": heat_map_path, "caption": "Round leverage heat map"} if heat_map_path else None
    control_shift_path = produce_control_shift_chart(report_payload)
    manifest["control_shift"] = {"asset_path": control_shift_path, "caption": "Projected control share by round"} if control_shift_path else None
    # Write manifest
    manifest_path = get_manifest_path(fixture_id)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest_path, manifest
