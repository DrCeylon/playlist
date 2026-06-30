# UI layer (Phase 4+)

This package contains the **shared, provider-neutral UI contract** for
Resonance — DTOs, ViewModels, validation, navigation, and theme engine.

## Layout

```text
ui/shared/
  dto/           # Contract DTOs (Phase 4.1+)
  state/         # UiScreenState
  validation/    # Pure validators
  navigation/    # AppRoute
  viewmodels/    # Reference VMs (Phase 4.4+)
  theme/         # Theme engine (Phase 4.3+)
bridge/          # JSON Engine Bridge (Phase 4.2+)
  commands.py
  protocol.py
  json_rpc.py
  events.py
  errors.py
```

## Rules

1. No imports from `integration/apple_music`, `core.applescript`, or provider SDKs.
2. No hardcoded colors — use `DesignTokens` via `ThemeManager` (Phase 4.3+).
3. ViewModels call application use cases — never UI frameworks.

## Documentation

- [Phase 4 UI architecture](../../docs/architecture/phase-4-ui-architecture.md)
- [Product brief](../../docs/product/phase-4-product-brief.md)
- [ADR-011](../../docs/architecture/ADR-011-cross-platform-product-ui.md)
