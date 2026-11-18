# Desktop pet agent handoff

For the Yier & Bubu collection, start with [README.md](README.md) and [docs/MAINTENANCE.md](docs/MAINTENANCE.md). Treat the native Codex bundle and the standalone app as separate runtimes that share one atlas.

- Asset work starts in [docs/ASSETS.md](docs/ASSETS.md). Pick an original, verify the character visually, pin it with `pin_source.py`, then map it in `yier_bubu/actions.json`. The URLs and SHA-256 in `source-lock.json` are the reproducibility contract.
- Put source images, extracted frames, previews, and personal builds under ignored `runs/` or `dist/`. Keep credentials, user paths, chat logs, and artwork without redistribution permission out of commits and release assets.
- Preserve the standalone loop until a real completion or cancellation event. Do not switch to idle based on elapsed animation loops or a short inactivity timer. Do not patch the signed Codex client.
- Run `python -m unittest -v`, regenerate affected atlases, inspect the exported GIFs, and run `test_packaged_app.py` on each frozen artifact. Report physical Windows/macOS tests separately from CI and synthetic tests.
- Follow [docs/RELEASE.md](docs/RELEASE.md) for versioning, platform packaging, and publication. Do not say a platform is verified until its build and relevant checks ran on that platform.

Read README.md and WORKFLOW.md before creating or modifying a pet. Start by recording the target client, version, OS and a portable character brief. If the user only asked to validate, preview or package, finish that task without installing or uploading a pet.

- Use the target client's official skill and validation tools for production art. Use this repo's CLI for structural checks, previews, portable packaging and local install.
- Store per-run inputs in `runs/<pet-id>/`. Keep the reference provenance, original generated strips, approved versions and verification reports. Use relative project paths. Never commit credentials, upload session URLs, user data or unlicensed references.
- Fix the smallest failing stage. For a visual defect, regenerate its source row. For a layout defect, fix the extraction or registration, then rebuild and preview.
- Before handing off, rerun the portable checks, record the exact SHA-256, open the actual motion previews, and distinguish CI checks from manual checks on each target client.
- No baked-in account names, personal machine paths, emoji UI, or platform-specific dependencies in the portable Python CLI. Keep clickable UI and asset rights explicit.
- For changes to this repo, run `python -m unittest -v`. The CI matrix covers Windows and macOS.
