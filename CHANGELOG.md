# Changelog

All notable changes to this project are documented here.  
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-07-10

First public release of **Resonance** (macOS app + Python engine).

### Added

- CLI: `generate_playlist`, `check_catalog`, `create_playlist` with pip entry points
- Resonance macOS app: generation, import, session history, Playlist Manager
- Provider-neutral architecture (Phases 6.1–6.7)
- Local playlist repository (SSOT) with remote snapshot archive
- Sync: plan (dry-run), apply push append_only, conflict resolution preview
- Apple Music gateway: catalog, import, remote playlist read, delivery
- YouTube Music experimental gateway (read/import, opt-in `ytmusicapi`)
- Bridge JSON-RPC runtime for Swift ↔ Python
- Diagnostics lab, themes, smart input framework
- Release documentation: plan, checklist, limitations, migration, compatibility matrix
- OSS foundations: MIT license, SECURITY.md, CONTRIBUTING.md, Python CI

### Known limitations

See [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md).

### Migration

See [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md).

## [0.8.2] - historical

Pre-release packaging version (`pyproject.toml` only). Functionality lived on `main` through Phase 6.x without tagged releases.

[1.0.0]: https://github.com/DrCeylon/playlist/releases/tag/v1.0.0
