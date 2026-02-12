# Changelog

## [0.5.0] - 2026-02-12

Big performance and UX update.

### Added
- Parallel scanning with ThreadPoolExecutor (2-4x faster on SSDs)
- Background scanning in GUI - window appears instantly
- Progress indicator during scan
- Rescan button to manually trigger scans
- Rust CLI (`dswp`) for fast command-line operations
  - Shared config with Python app (data/default_rules.yaml)
  - JSON output support
  - Dry-run mode
  - Instant startup (~10ms vs ~300ms Python)

### Changed
- GUI no longer blocks on startup waiting for scan
- Scan runs in QThread after window appears
- Better status messages showing selected items count
- Version bumped from 0.4.3 to 0.5.0

### Fixed
- CLI import isolation - prevents GUI dependencies from leaking into CLI

## [0.4.3] - 2025-11-30

Initial public release.

### Added
- PySide6 GUI with dark/light theme toggle
- Severity-based cleanup (safe/moderate/aggressive)
- CLI interface (report, clean, deep modes)
- Dynamic browser cache discovery (Edge, Chrome)
- Progress dialog with abort button
- CSV export functionality
- Menu bar with rule reload, log folder access
- PyInstaller build setup with icon
- Issue templates for GitHub

### Features
- YAML-based rule configuration
- Age and size filtering for cleanup candidates
- Checkbox selection with "Select All" and "Invert"
- Admin privilege detection for WinSxS cleanup
- Logging to %LOCALAPPDATA%\DiskSweeper\logs
- Cross-profile browser cache detection

### License
- Apache 2.0 (switched from MIT)
