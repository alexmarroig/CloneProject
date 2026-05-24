# GitHub backup notes

This repository was uploaded without large local artifacts because GitHub rejected
Git LFS uploads for this account/repository budget.

The GitHub copy includes source code, documentation, configuration, scripts, and
the app/frontend/backend project files.

Large generated or machine-local artifacts are intentionally excluded, including:

- Python virtual environments: `.venv/`, `venv/`, `venv_rvc/`
- Runtime environments and dependencies: `app/runtime/`, `node_modules/`
- Training logs and generated outputs: `logs/`, `output/`, `TEMP/`, `tmp/`
- Downloaded/model assets: `assets_dl/`, `.pth`, `.pt`, `.onnx`, `.index`, `.bin`
- Media and local binaries: `.wav`, `.mp3`, `.mp4`, `.exe`, `.zip`, `.7z`

To preserve the complete local state, archive those excluded folders/files outside
GitHub or restore Git LFS storage/quota before uploading them.
