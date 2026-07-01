# Phase 4.5 — Playlist builder form and preview MVP

First functional macOS screen: playlist creation form with mock preview,
validated against Phase 4.1 contracts and ready for Engine Bridge (4.2).

## Scope

| Area | Deliverable |
|------|-------------|
| Form | name, description, provider (grayed), seed artist/track, keywords, track count, duration, energy curve, exclusions |
| Validation | `PlaylistGenerationValidator` mirroring Python `validate_playlist_generation_request` |
| Generate | Mock preview via `MockPlaylistGenerationService` |
| Bridge | `BridgeContracts.generationRequestDictionary` + `PlaylistGenerationServing` protocol |

## Package changes

- **ResonanceCore** — DTOs, validation, bridge dictionary encoding
- **ResonanceMac** — `PlaylistBuilderView`, `PlaylistPreviewView`, `PlaylistBuilderViewModel`

## Constraints (4.5)

- No Apple Music import, AppleScript, or provider-specific UI logic
- No playlist/library delete actions
- Colors via `ThemePalette` only
- Python engine unchanged; bridge not connected at runtime yet

## Tests

| Layer | Location |
|-------|----------|
| Swift | `PlaylistGenerationValidationTests`, `PlaylistBuilderViewModelTests` |
| Python | `tests/test_resonance_playlist_builder.py` |
| Fixture | `tests/fixtures/playlist_generation_request.json` |

## Related

- [phase-4-macos-shell.md](phase-4-macos-shell.md)
- [phase-4-engine-bridge.md](phase-4-engine-bridge.md)

## Next (not in 4.5)

- **4.6** — Import UX + bridge runtime
- **4.7** — Laboratory + history
