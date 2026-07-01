# Phase 4.5 — Playlist builder form and preview

macOS screen for playlist creation: form validated against Phase 4.1 contracts, preview via mock or Python engine (4.6).

## Scope (4.5)

| Area | Deliverable |
|------|-------------|
| Form | name, description, provider (grayed), seed artist/track, keywords, track count, duration, energy curve, exclusions |
| Validation | `PlaylistGenerationValidator` mirroring Python `validate_playlist_generation_request` |
| Generate | `PlaylistGenerationServing` protocol — mock or bridge (4.6) |
| Bridge contracts | `BridgeContracts.generationRequestDictionary` + snake_case keys |

## Phase 4.6 extension

Since PR #26, **Générer** can call the real Python engine:

| Service | When |
|---------|------|
| `PythonEngineBridgeService` | Default in `PlaylistBuilderView` — repo root detected or `RESONANCE_REPO_ROOT` |
| `MockPlaylistGenerationService` | Fallback when Python process unavailable |

Preview label:

- **« Aperçu moteur Python »** — bridge OK
- **« Aperçu mock »** — fallback (CI Linux, Python absent)

Import from preview → [phase-4-import-ux.md](phase-4-import-ux.md).

## Package layout

- **ResonanceCore** — DTOs, validation, `BridgeClient`, `ImportModels`
- **ResonanceMac** — `PlaylistBuilderView`, `PlaylistPreviewView`, `PlaylistBuilderViewModel`, `ImportViewModel`

## Constraints

- No Apple Music import logic, AppleScript, or MusicKit in SwiftUI
- No playlist/library delete actions
- Colors via `ThemePalette` only
- Python engine logic stays in Python — Swift only serializes DTOs

## Tests

| Layer | Location |
|-------|----------|
| Swift | `PlaylistGenerationValidationTests`, `PlaylistBuilderViewModelTests`, `BridgeClientTests` |
| Python | `tests/test_resonance_playlist_builder.py`, `tests/test_ui_bridge_runtime.py` |
| Fixture | `tests/fixtures/playlist_generation_request.json` |

## Related

- [phase-4-macos-shell.md](phase-4-macos-shell.md)
- [phase-4-engine-bridge.md](phase-4-engine-bridge.md)
- [phase-4-import-ux.md](phase-4-import-ux.md)
- [phase-4-diagnostics-lab.md](phase-4-diagnostics-lab.md)

## Status

| Phase | Statut |
|-------|--------|
| 4.5 form + validation | ✅ Done |
| 4.6 bridge runtime + import | ✅ Done (see import UX doc) |
| 4.7 laboratory | ✅ Done (see diagnostics lab doc) |
| 4.7 history | 📋 Planned |
