# Phase 4.4 — macOS SwiftUI shell MVP

Minimal launchable macOS application shell for Resonance.

## Package

`apps/resonance/`

| Target | Role |
|--------|------|
| `ResonanceCore` | `AppRoute`, `SidebarItem`, `ThemeOption` mirrors |
| `ResonanceDesign` | Swift `ThemeRegistry` / `ThemeManager` loading bundled JSON tokens |
| `ResonanceMac` | Executable — `NavigationSplitView` AppShell |

## MVP screens

| Sidebar | Route | Phase |
|---------|-------|-------|
| Accueil | `home` | **4.4** |
| Nouvelle Playlist | `new_playlist` | placeholder → 4.5 |
| Historique | `history` | placeholder → 4.7 |
| Laboratoire | `diagnostics` | placeholder → 4.7 |
| Paramètres | `settings` | **4.4** (theme picker) |

## Theme integration

Bundled `.theme.json` files in `ResonanceDesign/Resources/themes/` are copies of
`playlist_builder/ui/shared/theme/themes/`.

`ThemeManager` loads, validates, and applies themes. SwiftUI views read colors via
`ThemePalette` — no hardcoded hex in views.

## Build & run (macOS)

```bash
cd apps/resonance
swift build
swift test
swift run ResonanceMac
```

Helper: `./scripts/build.sh`

## Constraints (4.4)

- No AppleScript or provider-specific UI
- No playlist/library delete actions
- Python engine unchanged
- Engine bridge optional at runtime (contracts preserved)

## Tests

| Layer | Location |
|-------|----------|
| Swift unit tests | `ResonanceDesignTests`, `ResonanceMacTests` |
| Python guards | `tests/test_resonance_mac_shell.py` |
| Full Python suite | `python -m pytest -q` |

`test_swift_package_build_and_tests` runs when a Swift toolchain is available.

## Related

- [phase-4-ui-architecture.md](../architecture/phase-4-ui-architecture.md)
- [phase-4-theme-engine.md](phase-4-theme-engine.md)
- [theme-engine.md](theme-engine.md)

## Next (not in 4.4)

- **4.5** — Playlist builder UI
- **4.7** — Laboratory + history
- **4.9** — iOS shell (`ResonanceIOS/`)
