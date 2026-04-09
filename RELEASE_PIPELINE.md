# RELEASE_PIPELINE.md

## Fixture Discovery Contract
- Prediction fixtures must be committed under `predictions/` and match the glob patterns:
  - `predictions/*_baseline.json`
  - `predictions/*_sens2.json`
- Each fixture must be valid JSON and contain these top-level fields:
  - `predicted_winner_id`
  - `confidence`
  - `method`
  - `round`

## Smoke Mode Behavior
- Run `python batch_export_reports.py --smoke` to export only the first valid fixture and exit 0 on success.
- Used in CI to prove the pipeline can export at least one valid fixture before full packaging.

## Output Root and Bundle Structure
- All outputs are generated under `deliveries/v100-template-standardized/<fixture_slug>/`.
- Each bundle contains:
  - `report.json`, `report.md`, `report.pdf`
  - `manifest.json`, `README.md`, `checksums.txt`
  - Zipped bundle: `<fixture_slug>.zip`

## Windows Path-Length Guard
- All output paths are validated to not exceed 220 characters.
- Exports fail fast if any planned path is too long.

## Git Tracking Policy
- Generated `deliveries/` artifacts are not tracked in Git.
- Only committed prediction fixtures are versioned.

## Local Validation Commands
```bash
py -3.10 -m py_compile batch_export_reports.py release_reports.py report_delivery_config.py
py -3.10 batch_export_reports.py --smoke
py -3.10 batch_export_reports.py
py -3.10 release_reports.py
```

## CI Success Criteria
- CI is green if:
  - The smoke export step passes (at least one fixture exports successfully)
  - The full release pipeline runs and uploads artifacts from `deliveries/v100-template-standardized/`
  - No path-length or fixture-contract errors occur
