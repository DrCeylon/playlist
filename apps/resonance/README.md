# Resonance — macOS SwiftUI shell

Provider-neutral macOS application for the Resonance playlist platform (generation, import, playlist manager, sync).

## Structure

| Target | Role |
|--------|------|
| `ResonanceCore` | Shared routes, DTO mirrors, bridge client |
| `ResonanceDesign` | Theme engine (JSON tokens, `ThemeManager`) |
| `ResonanceMac` | macOS SwiftUI executable — AppShell, Home, Playlists, Sync, Providers, History, Settings |

Bundled themes live in `ResonanceDesign/Resources/themes/` and mirror
`playlist_builder/ui/shared/theme/themes/`.

## Build & run (macOS)

```bash
cd apps/resonance
swift build
swift test
swift run ResonanceMac
```

The Dock icon is applied at runtime from bundled assets. For a proper **Finder `.app`** with `.icns` (instead of the terminal executable icon):

```bash
./scripts/package-mac-app.sh
open dist/ResonanceMac.app
```

Regenerate icon sizes after editing the master artwork:

```bash
python3 scripts/generate-app-icon.py
```

Or use the helper script:

```bash
./scripts/build.sh
```

## Constraints

- No AppleScript or provider-specific UI code in screens/view models
- Python engine via `PythonEngineBridgeService` when repo root is discoverable
- Colors only via `ThemeManager` / design tokens
- Screen ViewModels (`SyncViewModel`, `ProvidersViewModel`, `HistoryViewModel`, `DiagnosticsViewModel`) are owned by `AppWorkflowCoordinator` and receive protocol-typed services at construction — views use `@ObservedObject` from the coordinator, not late `replaceService` swaps

## Related

- [phase-4-ui-architecture.md](../../docs/architecture/phase-4-ui-architecture.md)
- [phase-4-theme-engine.md](../../docs/product/phase-4-theme-engine.md)
