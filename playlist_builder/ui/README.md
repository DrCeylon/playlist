# UI layer (Phase 4+)

This package will contain the **shared, provider-neutral UI contract** for
Resonance — DTOs, ViewModels, validation, navigation, and theme engine.

**Phase 4.0 is documentation only.** Implementation starts in PR 4.1.

## Rules

1. No imports from `integration/apple_music`, `core.applescript`, or provider SDKs.
2. No hardcoded colors — use `DesignTokens` via `ThemeManager`.
3. ViewModels call application use cases — never UI frameworks.

## Documentation

- [Phase 4 UI architecture](../../docs/architecture/phase-4-ui-architecture.md)
- [Product brief](../../docs/product/phase-4-product-brief.md)
- [ADR-011](../../docs/architecture/ADR-011-cross-platform-product-ui.md)
