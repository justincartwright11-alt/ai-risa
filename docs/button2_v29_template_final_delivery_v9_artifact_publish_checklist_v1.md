Slice: button2-v29-template-final-delivery-v9-artifact-publish-checklist-v1
Date: 2026-06-02

Purpose
-------
Operator checklist for publishing v9 proof artifacts to approved external storage and finalizing the artifact-URI manifest. This slice adds no binaries and makes only docs/manifest changes.

Checklist (Operator)
--------------------
1. Confirm approved storage target (S3 / GCS / Internal NAS) and get upload credentials.
2. Prepare a single archive or per-file upload for the proofs located under `ops/release_checks/button2_v29_template_final_delivery_layout_depth_repair_v9/`.
3. Upload the 5 proof PDFs first. Record each resulting `storage_uri` (s3://..., gs://..., or file://...) and note any public/signed link requirements.
4. Compute SHA-256 and file size for each uploaded file; verify checksums match local copies using `Get-FileHash -Algorithm SHA256` (PowerShell) or `sha256sum` (Unix).
5. Upload proof images (contact sheets and per-page PNGs). Record URIs and checksums as above.
6. Populate the artifact URI manifest by copying the template at `ops/release_checks/button2-v29-template-final-delivery-v9-artifact-uri-manifest-template-v1/artifact_uri_manifest_template.json` into the target path below and filling `storage_uri`, `sha256`, `size_bytes`, `uploaded_by`, and `uploaded_at_utc` fields.
   - Save as: `ops/release_checks/button2-v29-template-final-delivery-v9-artifact-publish-checklist-v1/artifact_uri_manifest.json`
7. Run a quick verification: ensure every `storage_uri` resolves and each remote file checksum equals the manifest `sha256`.
8. Obtain operator approval (sign-off) by committing the populated manifest and creating a release tag for the manifest revision.
9. Record the manifest commit SHA and tag in the operator release notes for traceability.

Verification commands (PowerShell examples)
-----------------------------------------
Get SHA256 for a local file:

    Get-FileHash -Path "path\to\file.pdf" -Algorithm SHA256 | Select-Object -ExpandProperty Hash

Compare remote checksum (if storage supports checksum querying) or re-download to verify:

    # Example: download and check
    Invoke-WebRequest -Uri "<public-or-signed-uri>" -OutFile tmp_download.pdf
    Get-FileHash -Path tmp_download.pdf -Algorithm SHA256

Operator notes
--------------
- Do NOT commit or add binary files to Git. Only commit the populated JSON manifest and small docs.
- If any artifact is private or uses signed URLs, record expiry and access_notes in the manifest.
- When ready, commit the manifest and create the tag `button2-v29-template-final-delivery-v9-artifact-publish-checklist-v1`.
