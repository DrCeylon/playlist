# Resonance — iOS / iPadOS (planned)

Phase 4.9 target. No code in Phase 4.0.

## Navigation mapping

| macOS sidebar | iPadOS | iPhone |
|---------------|--------|--------|
| Accueil | Sidebar | Tab |
| Nouvelle playlist | Sidebar | Tab + Stack |
| Historique | Sidebar | Tab |
| Diagnostics | Sidebar | Settings → Lab |
| Paramètres | Sidebar footer | Tab |

## Planned structure

```text
ResonanceIOS/
  App/
    ResonanceIOSApp.swift
  Navigation/
    RootTabView.swift
    ImportStack.swift
  Screens/
    HomeView.swift
    PlaylistBuilderView.swift
    ImportProgressView.swift
    ManualAcquisitionView.swift
    SettingsView.swift
  Services/
    MusicKitDeliveryAdapter.swift   # provider only — not in shared Python
```

## Engine

iOS does **not** embed Python. `ResonanceCore` Swift package implements use cases
against shared DTO schema. MusicKit handles delivery.

See [ios-roadmap.md](../../docs/ios-roadmap.md) and
[ADR-011](../../docs/architecture/ADR-011-cross-platform-product-ui.md).
