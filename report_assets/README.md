# Report Assets Output Folder

This directory stores per-fixture visual assets (PNG charts) and their corresponding manifest files for AI-RISA report exports.

- Each fixture/report gets its own manifest (JSON) and chart PNGs.
- Asset filenames are deterministic: <fixture>_<slot>.png
- Manifests are named: <fixture>_visual_manifest.json
- Asset paths are resolved by the renderer/exporter using the manifest, never written back to engine outputs.

Example:
- van_taira_baseline_method_chart.png
- van_taira_baseline_visual_manifest.json

This folder is auto-managed by the report export layer.
