Slice: button2-v29-template-final-delivery-v9-artifact-uri-manifest-template-v1
Date: 2026-06-02

Purpose
-------
Provide an operator-friendly template for recording external artifact storage URIs for the v9 proof PDFs and images without adding binaries to Git.

Usage
-----
1. Upload proof PDFs/images to the approved artifact storage (S3/GCS/Internal NAS).
2. Populate the JSON manifest template below with final URIs and minimal metadata.
3. Save the populated manifest as `ops/release_checks/button2-v29-template-final-delivery-v9-artifact-uri-manifest-v1/artifact_uri_manifest.json` and record the manifest revision with operator approval.

Fields
------
- `slice_name`: the release slice name
- `frozen_v9_commit` / `frozen_v9_tag` / `checkpoint_commit` / `checkpoint_tag`
- `artifacts`: list of artifact entries with fields:
  - `file_name` (e.g., max_holloway_justin_gaethje_premium_test.pdf)
  - `artifact_type` (`pdf` or `image`)
  - `storage_uri` (e.g., s3://bucket/path/file.pdf)
  - `sha256` (optional, recommended)
  - `size_bytes` (optional)
  - `uploaded_by` (operator username)
  - `uploaded_at_utc` (ISO8601)
  - `access_notes` (ACL / public link / expiry)

Policy
------
- Do NOT commit binaries to Git. Record external URIs only. If small, short-lived debug archives may be stored in repo with explicit operator approval.

Example template file path
--------------------------
`ops/release_checks/button2-v29-template-final-delivery-v9-artifact-uri-manifest-template-v1/artifact_uri_manifest_template.json`
