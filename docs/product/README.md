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
- Commands : `list_providers`, `validate_generation_request`, `generate_playlist`, `import_playlist`, `diagnostics`
- `EngineBridgeBackend` injection for engine-specific work

Doc : [phase-4-engine-bridge.md](phase-4-engine-bridge.md)  
Tests : `tests/test_ui_bridge_*.py`

Architecture :

- [ADR-011](../architecture/ADR-011-cross-platform-product-ui.md)
- [phase-4-ui-architecture.md](../architecture/phase-4-ui-architecture.md)
