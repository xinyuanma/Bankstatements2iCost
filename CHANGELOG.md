# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-01-18
- Initial public release
- Features:
  - Rule-driven CSV converter (`src/transform_prelim.py`) with `mappings.yaml` support
  - CLI entrypoint `bank2csv` (installed via `pyproject.toml`)
  - Defaults override via `.env` or CLI flags
  - Example `mappings.yaml` rules for categories, labels, and date-based vacation tagging
  - Added `README.md`, `.gitignore`, `COMMIT_CHECKLIST.md`, and `requirements.txt`
