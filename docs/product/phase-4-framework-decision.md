# Phase 4.0 — Framework decision matrix

## Evaluation criteria

| Criterion | Weight | Notes |
|-----------|--------|-------|
| macOS quality | High | Primary ship platform v1 |
| Future iOS / iPadOS | **Critical** | Must not require rewrite |
| Premium Apple feel | High | Things / Fantastical bar |
| Python engine integration | High | Existing investment |
| Longevity (5 years) | High | Maintenance burden |
| Testability | High | ViewModels, contracts |
| Theming | Medium | Winamp-inspired skins |
| Packaging / notarization | Medium | macOS distribution |
| Performance | Medium | Background import |
| Community / hiring | Medium | Talent pool |
| Complexity / risk | High | Team size = small |
| Dependencies | Medium | Supply chain |
| Cost | Low | Mostly OSS |

Scoring : ⭐ (1) – ⭐⭐⭐⭐⭐ (5)

---

## Candidates

### 1. PySide6 / Qt for Python

| Criterion | Score | Comment |
|-----------|-------|---------|
| macOS | ⭐⭐⭐⭐ | Mature desktop |
| iOS | ⭐ | No credible iOS path |
| Premium Apple | ⭐⭐ | Looks cross-platform |
| Python integration | ⭐⭐⭐⭐⭐ | Native |
| Longevity | ⭐⭐⭐⭐ | Qt stable |
| Theming | ⭐⭐⭐⭐ | QSS |
| Risk | ⭐⭐⭐ | Dead-end for mobile |

**Verdict :** Excellent for internal tools, **rejected** for consumer product with iOS ambition.

---

### 2. BeeWare / Toga

| Criterion | Score | Comment |
|-----------|-------|---------|
| macOS | ⭐⭐⭐ | Improving |
| iOS | ⭐⭐⭐ | Theoretical Python on iOS |
| Premium Apple | ⭐⭐ | Widget set immature |
| Python integration | ⭐⭐⭐⭐⭐ | Same codebase |
| Longevity | ⭐⭐ | Smaller ecosystem |
| Theming | ⭐⭐ | Limited |
| Risk | ⭐⭐ | App Store + Python on iOS uncertain |

**Verdict :** Attractive on paper, **rejected** — visual quality and iOS policy risk too high.

---

### 3. Flet (Flutter + Python)

| Criterion | Score | Comment |
|-----------|-------|---------|
| macOS | ⭐⭐⭐ | Acceptable |
| iOS | ⭐⭐⭐⭐ | Flutter mobile |
| Premium Apple | ⭐⭐ | Material bias |
| Python integration | ⭐⭐⭐ | UI in Python, not engine merge |
| Theming | ⭐⭐⭐ | Flutter themes |
| Risk | ⭐⭐⭐ | Young project, Google stack |

**Verdict :** Fast prototype only, **rejected** for premium Apple positioning.

---

### 4. Flutter + Python backend

| Criterion | Score | Comment |
|-----------|-------|---------|
| macOS | ⭐⭐⭐⭐ | Flutter desktop OK |
| iOS | ⭐⭐⭐⭐⭐ | Strong mobile |
| Premium Apple | ⭐⭐⭐ | Needs heavy custom design |
| Python integration | ⭐⭐⭐ | Separate processes |
| Shared UI code | ⭐⭐⭐⭐⭐ | Dart everywhere |
| Risk | ⭐⭐⭐ | Two languages, engine/UI split |

**Verdict :** Viable for cross-platform startups, **not selected** — sacrifices native Apple HIG fidelity and duplicates design effort vs SwiftUI.

---

### 5. SwiftUI + Python engine (recommended)

| Criterion | Score | Comment |
|-----------|-------|---------|
| macOS | ⭐⭐⭐⭐⭐ | Native |
| iOS / iPadOS | ⭐⭐⭐⭐⭐ | First-class |
| Premium Apple | ⭐⭐⭐⭐⭐ | Best achievable |
| Python integration | ⭐⭐⭐⭐ | Engine bridge on Mac |
| Shared logic | ⭐⭐⭐ | Contract-first DTOs |
| Theming | ⭐⭐⭐⭐ | Asset catalogs + tokens |
| Packaging | ⭐⭐⭐⭐ | Xcode + notarization |
| Risk | ⭐⭐⭐ | Two runtimes on Mac |

**Verdict :** **Selected** — aligns with 5-year Apple-platform strategy.

---

### 6. Electron / Tauri + Python

| Criterion | Score | Comment |
|-----------|-------|---------|
| macOS | ⭐⭐⭐ | Web in shell |
| iOS | ⭐ | No real path |
| Premium Apple | ⭐⭐ | Never feels native |
| Python integration | ⭐⭐⭐⭐ | Sidecar |
| Risk | ⭐⭐ | Memory, updates |

**Verdict :** **Rejected** for product shell (CLI tools OK).

---

### 7. Native Swift only (no Python UI path)

| Criterion | Score | Comment |
|-----------|-------|---------|
| macOS + iOS | ⭐⭐⭐⭐⭐ | Single language UI |
| Python engine | ⭐⭐ | Full Swift port pressure |
| Time to market | ⭐⭐ | Large rewrite |

**Verdict :** Long-term iOS may port hot paths; **rejected** as sole Mac strategy — wastes existing Python engine.

---

## Decision summary

```text
┌─────────────────────────────────────────────────────────┐
│  RECOMMENDED STACK                                       │
├─────────────────────────────────────────────────────────┤
│  UI shell       : SwiftUI (macOS, iPadOS, iOS)          │
│  Shared contracts: JSON Schema + Python dataclasses      │
│  ViewModels     : Swift (prod) + Python (reference/tests)│
│  Engine (Mac)   : Python playlist_builder + Engine Bridge│
│  Engine (iOS)   : Swift use cases + MusicKit gateway     │
│  Themes         : JSON token files → SwiftUI ThemeManager│
│  CLI            : unchanged Python entry points            │
└─────────────────────────────────────────────────────────┘
```

## Why SwiftUI + Python backend (not the fastest path)

1. **iOS is not optional** in the vision — only SwiftUI delivers App Store quality.
2. **Python engine is proven** — subprocess bridge avoids rewriting scoring now.
3. **Premium feel** requires native materials, SF Symbols, vibrancy, accessibility.
4. **CLI parity** — same engine JSON API for automation and UI.
5. **5-year maintainability** — Apple platform APIs evolve inside SwiftUI; Qt/Electron lag HIG.

## Engine Bridge options (macOS)

| Option | Pros | Cons |
|--------|------|------|
| **stdin/stdout JSON-RPC** | Simple, testable, no port | Single client, parsing care |
| Local HTTP `127.0.0.1` | Multiple clients, streaming SSE | Port management |
| XPC service | Sandboxing, security | Complexity |

**Phase 4.2 recommendation :** JSON lines over stdin/stdout for v1; evaluate SSE HTTP for import streaming in 4.6.

## iOS Python limitation (explicit)

Embedded CPython on iOS consumer apps is **not** a viable App Store strategy. Therefore:

- macOS : full Python engine
- iOS : Swift `ResonanceCore` implements use cases against same DTO schema; MusicKit for delivery; generation/scoring ported incrementally or via precomputed packages (future)

## Alternatives considered but deferred

| Option | When to revisit |
|--------|-----------------|
| Rust shared core | If Swift port of scoring exceeds 3 months |
| Kotlin Multiplatform | If Android becomes a target |
| PySide6 admin tool | Internal diagnostics dashboard |

## Related

- [ADR-011](../architecture/ADR-011-cross-platform-product-ui.md)
- [phase-4-ui-architecture.md](../architecture/phase-4-ui-architecture.md)
