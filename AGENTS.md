# Desktop pet agent handoff

Read README.md and WORKFLOW.md before creating or modifying a pet. Start by recording the target client, version, OS and a portable character brief. If the user only asked to validate, preview or package, finish that task without installing or uploading a pet.

- Use the target client's official skill and validation tools for production art. Use this repo's CLI for structural checks, previews, portable packaging and local install.
- Store per-run inputs in `runs/<pet-id>/`. Keep the reference provenance, original generated strips, approved versions and verification reports. Use relative project paths. Never commit credentials, upload session URLs, user data or unlicensed references.
- Fix the smallest failing stage. For a visual defect, regenerate its source row. For a layout defect, fix the extraction or registration, then rebuild and preview.
- Before handing off, rerun the portable checks, record the exact SHA-256, open the actual motion previews, and distinguish CI checks from manual checks on each target client.
- No baked-in account names, personal machine paths, emoji UI, or platform-specific dependencies in the portable Python CLI. Keep clickable UI and asset rights explicit.
- For changes to this repo, run `python -m unittest -v`. The CI matrix covers Windows and macOS.
