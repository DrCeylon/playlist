# Product documentation

Phase 4 — Product discovery & UI contracts.

| Document | Purpose |
|----------|---------|
| [phase-4-product-brief.md](phase-4-product-brief.md) | Vision, identity, scope |
| [phase-4-ux-flows.md](phase-4-ux-flows.md) | User flows and navigation |
| [phase-4-wireframes.md](phase-4-wireframes.md) | Text wireframes (7 screens) |
| [phase-4-framework-decision.md](phase-4-framework-decision.md) | Technology matrix + recommendation |
| [design-system.md](design-system.md) | Tokens, components, a11y |
| [theme-engine.md](theme-engine.md) | ThemeRegistry, ThemeManager, skin format |
| [phase-4-macos-shell.md](phase-4-macos-shell.md) | macOS SwiftUI shell MVP (Phase 4.4) |
| [phase-4-playlist-builder.md](phase-4-playlist-builder.md) | Playlist builder form + preview (Phase 4.5) |
| [phase-4-import-ux.md](phase-4-import-ux.md) | Import UX + bridge runtime (Phase 4.6) |
| [phase-4-diagnostics-lab.md](phase-4-diagnostics-lab.md) | Diagnostics laboratory (Phase 4.7) |
| [phase-4-session-history.md](phase-4-session-history.md) | Session history (Phase 4.8) |
| [phase-4-6-bridge-runtime.md](phase-4-6-bridge-runtime.md) | Bridge runtime technical notes |
| [ios-planned-structure.md](ios-planned-structure.md) | Future iOS layout |

## Phase 4.1 — Shared contracts (code)

Python package `playlist_builder/ui/shared/` :

- **dto/** — `PlaylistGenerationRequest`, `ImportProgressState`, `ProviderOption`, …
- **state/** — `UiScreenState`
- **navigation/** — `AppRoute`
- **validation/** — pure validators (no I/O, no provider imports)

Tests : `tests/test_ui_shared_*.py`

## Phase 4.2 — Engine Bridge (code)

Package `playlist_builder/ui/bridge/` :

- JSON-lines requests/responses/events
- Commands : `list_providers`, `validate_generation_request`, `generate_playlist`, `import_playlist`, `diagnostics`, `list_history`, `get_history_session`, `delete_history_session`, `clear_history`, `replay_generation`, `export_history_session`
- `EngineBridgeBackend` injection for engine-specific work

Doc : [phase-4-engine-bridge.md](phase-4-engine-bridge.md)  
Tests : `tests/test_ui_bridge_*.py`

## Phase 4.3 — Theme engine (code)

Package `playlist_builder/ui/shared/theme/` :

- **tokens** — `DesignTokens` (colors, typography, spacing, radius, shadows)
- **registry** — `ThemeRegistry` with bundled `themes/*.theme.json`
- **manager** — `ThemeManager` (active theme, apply, subscribe)
- **validation** — mandatory token set from design system
- **loader** — JSON parsing and `extends` merge

Doc : [phase-4-theme-engine.md](phase-4-theme-engine.md)  
Tests : `tests/test_ui_shared_theme.py`

## Phase 4.4 — macOS SwiftUI shell (code)

Package `apps/resonance/` :

- **ResonanceCore** — `AppRoute`, `SidebarItem`, `ThemeOption`
- **ResonanceDesign** — Swift theme engine (JSON tokens)
- **ResonanceMac** — AppShell, Accueil, Paramètres

Doc : [phase-4-macos-shell.md](phase-4-macos-shell.md)  
Tests : `tests/test_resonance_mac_shell.py` + Swift `swift test`

## Phase 4.5 — Playlist builder (code)

Screens `PlaylistBuilderView` + `PlaylistPreviewView` in `ResonanceMac` :

- Form fields aligned with `PlaylistGenerationRequest`
- Validation via `PlaylistGenerationValidator` (Phase 4.1 contract)
- Mock generation service; bridge-ready `PlaylistGenerationServing`

Doc : [phase-4-playlist-builder.md](phase-4-playlist-builder.md)  
Tests : `tests/test_resonance_playlist_builder.py`

Architecture :

- [ADR-011](../architecture/ADR-011-cross-platform-product-ui.md)
- [phase-4-ui-architecture.md](../architecture/phase-4-ui-architecture.md)
