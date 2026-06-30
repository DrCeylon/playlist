# ADR-011 — Cross-platform product UI architecture

## Status

Accepted (Phase 4.0 — discovery)

> **Note on numbering:** ADR-008 is already allocated to *Application platform + acquisition*.
> This document is ADR-011 as requested by the product brief (*Cross Platform Product UI Architecture*).

## Context

Phases 1–3 delivered a provider-neutral engine:

- canonical model, unified scoring, identity cache
- generic integration gateway + Apple Music provider gateway
- observable resolution, catalog fallback, acquisition workflows
- CLI entry points (`create_playlist.py`, `generate_playlist.py`, `check_catalog.py`)

The product ambition exceeds a CLI utility. The long-term target is a **premium,
cross-platform application** (macOS → iPadOS → iOS) for intelligent playlist
composition, resolution, acquisition, and import.

Constraints:

1. Core business logic must never depend on UI frameworks or provider SDKs.
2. Apple Music is the only active provider today; Spotify, MusicKit, YouTube Music,
   Deezer must be pluggable without rewriting composition or import use cases.
3. Python remains the reference implementation of the engine on macOS.
4. iOS App Store policy makes an embedded Python interpreter impractical for the
   consumer app; UI and orchestration on Apple mobile must be Swift-native.
5. We refuse a “Mac now, iOS later” shortcut that would require a full rewrite.

## Decision

Adopt a **Product-first, contract-first, SwiftUI-native UI** architecture with a
**Python engine backend** on macOS and a **shared contract layer** that both
runtimes implement.

### Layering

```text
┌─────────────────────────────────────────────────────────────┐
│  Native shell (SwiftUI)                                     │
│  macOS / iPadOS / iOS — rendering, gestures, accessibility  │
└───────────────────────────┬─────────────────────────────────┘
                            │ binds to
┌───────────────────────────▼─────────────────────────────────┐
│  Platform ViewModels (Swift) — mirror Python reference spec │
└───────────────────────────┬─────────────────────────────────┘
                            │ calls
┌───────────────────────────▼─────────────────────────────────┐
│  Application services / Use cases (Python on Mac; Swift port) │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  Canonical model + Integration gateway + Providers          │
└─────────────────────────────────────────────────────────────┘
```

### Shared vs platform-specific

| Concern | Shared contract | macOS | iOS / iPadOS |
|---------|-----------------|-------|----------------|
| DTO / state shapes | JSON Schema + Python dataclasses | Python | Swift structs (generated) |
| ViewModel logic | Python reference + spec doc | Python VM OK for v1 | Swift ViewModels |
| Use cases | Python (source of truth) | subprocess / in-process | Swift orchestration + MusicKit |
| Theme tokens | JSON / YAML theme files | SwiftUI ThemeManager | same |
| Navigation model | abstract `AppRoute` enum | `NavigationSplitView` | `TabView` / `NavigationStack` |
| Rendering | — | SwiftUI | SwiftUI |

### UI technology choice

**SwiftUI** for all Apple-platform rendering. **Python** remains the engine on
macOS, invoked via a local **Engine Bridge** (structured JSON over stdin/stdout
or local HTTP on `127.0.0.1`). See
[phase-4-framework-decision.md](../product/phase-4-framework-decision.md).

PySide6, Flet, Electron, and BeeWare are **rejected** for the primary product
shell (rationale in framework decision doc). They may be used for internal tools
only if ever needed.

### Folder target

```text
playlist_builder/
  ui/
    shared/           # Python: DTO, state, validation, VM reference, theme schema
      dto/
      state/
      validation/
      navigation/
      theme/
      design_system/
      viewmodels/
    bridge/           # Python: EngineBridge protocol, JSON-RPC adapter
    README.md
apps/
  resonance/          # Swift Package + macOS/iOS targets (Phase 4.2+)
    ResonanceUI/
    ResonanceCore/    # Swift DTO + ViewModels
```

`playlist_builder/ui/shared` must not import AppKit, SwiftUI, or provider SDKs.

### Engine Bridge (macOS)

The macOS app does not embed business rules in Swift. It:

1. Spawns or reuses a long-lived `playlist_builder` engine process.
2. Sends JSON commands (`generate`, `import`, `diagnostics`, `list_providers`).
3. Receives structured events (progress, partial results, terminal state).
4. Maps responses to Swift ViewModels.

This preserves CLI parity and enables headless CI of the engine independent of UI.

### iOS strategy

Phase 4 does **not** ship iOS. The architecture prepares it by:

1. Defining DTOs and UI states in a language-neutral schema.
2. Implementing SwiftUI navigation patterns that map 1:1 to macOS sidebar flows.
3. Planning a **Swift use-case port** for generation/scoring hot paths, or a
   shared Rust/Kotlin core only if Swift port cost proves excessive (deferred).

MusicKit becomes the iOS delivery provider; Python AppleScript paths are macOS-only.

## Consequences

### Positive

- Premium native feel on all Apple platforms.
- Engine remains testable without UI (existing pytest suite).
- CLI unchanged; UI is an additional shell.
- Themes and design tokens portable as data files.
- Clear boundary: no `persistent_id` or AppleScript in `ui/shared`.

### Negative

- Two ViewModel implementations (Python reference + Swift production) until
  codegen or shared core matures.
- macOS v1 requires process management (engine lifecycle, errors, updates).
- iOS delivery requires MusicKit / Apple Developer investment.

### Risks

| Risk | Mitigation |
|------|------------|
| Swift/Python drift | Contract tests: JSON fixtures generated from Python, consumed by Swift tests |
| Engine subprocess fragility | Health check, restart, timeout, structured error codes |
| iOS port scope creep | Phase 4.8+ only after macOS MVP; MusicKit isolated in provider gateway |
| Theme explosion | ThemeRegistry with validation; max token set enforced by schema |

## Implementation roadmap (summary)

| PR | Scope |
|----|-------|
| 4.0 | This discovery pack (docs only) |
| 4.1 | `ui/shared` DTO + state + validation skeleton |
| 4.2 | Engine Bridge protocol + JSON adapter |
| 4.3 | Theme schema + ThemeRegistry (Python) |
| 4.4 | macOS SwiftUI shell — AppShell + Home |
| 4.5 | Playlist builder flow (generate + preview) |
| 4.6 | Import progress + manual acquisition UX |
| 4.7 | Diagnostics / Laboratory |
| 4.8 | iPadOS navigation adaptation |
| 4.9 | iOS target + MusicKit delivery path |

Full detail: [phase-4-ui-architecture.md](phase-4-ui-architecture.md).

## Related documents

- [phase-4-product-brief.md](../product/phase-4-product-brief.md)
- [phase-4-framework-decision.md](../product/phase-4-framework-decision.md)
- [phase-4-ui-architecture.md](phase-4-ui-architecture.md)
- [design-system.md](../product/design-system.md)
- [theme-engine.md](../product/theme-engine.md)
