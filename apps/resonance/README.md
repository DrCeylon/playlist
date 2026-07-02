# Resonance — macOS SwiftUI shell (Phase 4.4)

Provider-neutral macOS application shell for the Resonance playlist platform.

## Structure

| Target | Role |
|--------|------|
| `ResonanceCore` | Shared routes and DTO mirrors (`AppRoute`, `ThemeOption`) |
| `ResonanceDesign` | Theme engine (JSON tokens, `ThemeManager`) |
| `ResonanceMac` | macOS SwiftUI executable — AppShell, Home, Settings |

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

## Constraints (Phase 4.4)

- No AppleScript or provider-specific UI code
- No playlist/library delete actions
- Python engine unchanged; bridge not required at runtime yet
- Colors only via `ThemeManager` / design tokens

## Related

- [phase-4-ui-architecture.md](../../docs/architecture/phase-4-ui-architecture.md)
- [phase-4-theme-engine.md](../../docs/product/phase-4-theme-engine.md)
