# Phase 4.0 — UI architecture (target)

## Principles

1. **Product first** — UX drives structure, not framework convenience.
2. **Inward dependencies** — `ui/shared` never imports providers or native APIs.
3. **Contract first** — DTO shapes are the API between engine and shells.
4. **One engine, many shells** — CLI, SwiftUI, future web hook into same use cases.
5. **Destructive-free** — UI never exposes delete playlist/library actions.

---

## Target directory layout

```text
playlist_builder/
  app/                          # existing application layer
    use_cases/
    settings.py
    factory.py
  ui/
    README.md
    shared/
      dto/                      # PlaylistGenerationRequest, ImportProgressState, …
      state/                    # UiSessionState, ScreenState enums
      validation/               # pure validators, no I/O
      navigation/               # AppRoute, NavigationCoordinator (protocol)
      theme/
        tokens.py               # DesignTokens dataclass
        schema.json             # theme file JSON Schema
        registry.py             # ThemeRegistry
        manager.py              # ThemeManager
        themes/                 # bundled .theme.json files
      design_system/
        components.md           # component spec (implement in Swift)
      viewmodels/
        base.py                 # ViewModel protocol, UiEvent
        app_shell.py
        playlist_builder.py
        import_progress.py
        diagnostics.py
        settings.py
        theme.py
    bridge/
      protocol.py               # EngineBridge Protocol
      json_rpc.py               # JSON-lines adapter
      commands.py               # command enum
    # Runtime adapter (NOT in ui/bridge — provider imports allowed)
  app/
    bridge_runtime/             # Phase 4.6 — RuntimeEngineBridgeBackend
      backend.py
      import_stream.py
      mapping.py
    cli/
      engine_bridge.py          # stdin/stdout entry for Resonance

apps/
  resonance/                    # Phase 4.4+ (not in 4.0)
    Package.swift
    ResonanceCore/              # Swift DTO + ViewModels
    ResonanceMac/               # macOS SwiftUI app
    ResonanceIOS/               # iOS (Phase 4.9)
    ResonanceDesign/            # SwiftUI components + ThemeManager

docs/
  product/                      # this discovery pack
  architecture/
```

### iOS placeholder

```text
apps/resonance/ResonanceIOS/
  README.md
  planned_structure.md          # mirrors Mac routes → TabView/Stack
```

---

## MVVM — ViewModels

Python modules in `ui/shared/viewmodels/` are **reference implementations** with
full unit tests. Swift production ViewModels mirror the same public surface.

### AppShellViewModel

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Root navigation, provider health, engine lifecycle |
| **Inputs** | `LoadSettings`, `SelectRoute`, `RefreshProviderStatus` |
| **Outputs** | `currentRoute`, `providerStatus`, `engineVersion`, `lastSession` |
| **States** | `idle`, `loading`, `ready`, `engine_error` |
| **Errors** | Engine unreachable, provider missing |
| **Use cases** | `LoadSettingsUseCase`, `LoadProvidersUseCase` |

### ProviderSelectorViewModel

| Aspect | Detail |
|--------|--------|
| **Responsibility** | List/register providers, selection for session |
| **Inputs** | `SelectProvider(ProviderId)` |
| **Outputs** | `providers: list[ProviderOption]`, `selected` |
| **Use cases** | `LoadProvidersUseCase` |

### PlaylistBuilderViewModel (Swift — implemented)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Form state, validation, generation |
| **Services** | `PlaylistGenerationServing` — `PythonEngineBridgeService` or mock |
| **States** | `editing`, `generating`, `preview` |
| **Outputs** | `previewResult`, `previewSourceLabel`, `validationErrors` |

### ImportViewModel (Swift — Phase 4.6)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Import stream UX, manual acquisition, report |
| **Services** | `PlaylistImportServing` — same bridge service or mock |
| **States** | `idle`, `importing`, `waitingForManualAcquisition`, `report`, `failed` |
| **Bridge** | `import_playlist`, `continue_manual_acquisition` |

### PlaylistBuilderViewModel (Python reference — planned)

### EnergyCurveViewModel

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Energy profile + chapter preview |
| **Inputs** | `SelectProfile`, `AddChapter`, `SetPeak` |
| **Outputs** | `curve: EnergyCurveOption`, `previewPoints` |
| **Maps to** | `EnergyProfile` enum + future chapter model |

### ExclusionEditorViewModel

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Structured exclusion/inclusion rules |
| **Inputs** | `AddRule`, `RemoveRule`, `EditRule` |
| **Outputs** | `rules: list[ExclusionRule]`, kind filters |
| **Kinds** | artist, album, track, genre, mood, language |

### GenerationResultViewModel

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Preview generated playlist |
| **Inputs** | `Regenerate`, `EditConstraints`, `ExportJson`, `StartImport` |
| **Outputs** | `result: PlaylistGenerationResult`, section groups |
| **States** | `generated`, `regenerating` |

### ImportProgressViewModel (Python reference — planned)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Stream import events, manual acquisition UX |
| **Implemented in Swift** | `ImportViewModel` + `ImportProgressView` (4.6) |

### DiagnosticsViewModel (Swift — Phase 4.7)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Engine Bridge health, cache stats, diagnostic timeline |
| **Services** | `DiagnosticsServing` — `PythonEngineBridgeService` or mock |
| **States** | `disconnected`, `running`, `connected`, `completed`, `failed` |
| **Modes** | Simple / Architecte |
| **Bridge** | `diagnostics`, `list_providers` |

### HistoryViewModel (Swift — Phase 4.8)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Local session list, detail selection, replay/delete/clear |
| **Services** | `SessionHistoryServing` — `PythonEngineBridgeService` |
| **States** | `idle`, `loading`, `ready`, `failed` |
| **Bridge** | `list_history`, `get_history_session`, `delete_history_session`, `clear_history`, `replay_generation`, `export_history_session` |

### DiagnosticsViewModel (Python reference — planned)

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Pipeline timeline, export diagnostics |
| **Inputs** | `SelectSession`, `ToggleArchitectMode`, `Export` |
| **Outputs** | `events: list[DiagnosticEvent]`, `pipelineSummary` |
| **Use cases** | `ExportDiagnosticsUseCase` |

### SettingsViewModel

| Aspect | Detail |
|--------|--------|
| **Responsibility** | User preferences, cache management |
| **Inputs** | Field changes, `Save`, `ClearCache` |
| **Outputs** | `preferences: UserPreferences` |
| **Use cases** | `LoadSettingsUseCase`, `SaveSettingsUseCase` |

### ThemeViewModel

| Aspect | Detail |
|--------|--------|
| **Responsibility** | Theme list, preview, apply |
| **Inputs** | `SelectTheme`, `PreviewTheme` |
| **Outputs** | `themes: list[ThemeOption]`, `activeTheme` |
| **Use cases** | `LoadThemesUseCase` |

---

## Use cases

### Existing

| Use case | Status | Notes |
|----------|--------|-------|
| `ImportPlaylistUseCase` | ✅ | CLI + bridge via `stream_import_playlist` |
| `CheckCatalogUseCase` | ✅ | Used in lab / preflight |
| Generation (bridge) | ✅ | `RuntimeEngineBridgeBackend.generate_playlist` (4.6) |
| Import (bridge) | ✅ | `stream_import_playlist` + sessions (4.6) |
| Diagnostics (bridge) | ✅ | `RuntimeEngineBridgeBackend.diagnostics` (4.7) |
| Load providers (bridge) | ✅ | `list_providers` via Swift `DiagnosticsServing` (4.7) |
| Session history (bridge) | ✅ | local repository via `data/history/sessions.json` (4.8) |

### To create (Phase 4.8+)

| Use case | Responsibility |
|----------|----------------|
| `GenerateAndImportPlaylistUseCase` | Generate then import atomically (UI uses two steps today) |
| `LoadProvidersUseCase` | Read `ProviderGatewayRegistry` → `ProviderOption` list |
| `LoadThemesUseCase` | `ThemeRegistry.list()` |
| `LoadSettingsUseCase` | `AppSettings` + `UserPreferences` merge |
| `SaveSettingsUseCase` | Persist preferences JSON |
| `LoadHistoryUseCase` | Read generation/import history store |
| `SaveGenerationHistoryUseCase` | Append session metadata |
| `ExportDiagnosticsUseCase` | Package reports/JSON for UI export |

**Rule :** use cases accept/return DTOs or canonical types only — never `UIView`/`NSView`.

---

## DTO catalog

| DTO | Purpose |
|-----|---------|
| `PlaylistGenerationRequest` | Form → engine |
| `PlaylistGenerationResult` | Sections, tracks, scores, metadata |
| `ProviderOption` | id, name, capabilities, connected |
| `ThemeOption` | id, displayName, previewColors |
| `EnergyCurveOption` | profile + optional chapters/peaks |
| `ExclusionRule` | kind + value (+ reason) — mirrors planning |
| `ImportProgressState` | counts, current track, phase |
| `ImportResultState` | final aligned results |
| `DiagnosticEvent` | timestamp, phase, level, message, payload |
| `UserPreferences` | superset of `AppSettings` for UI |

---

## UI state machine

```text
idle
  → editing          (new playlist form)
  → generating       (async)
  → generated        (preview)
  → importing        (async stream)
  → waiting_for_manual_acquisition
  → completed | partial_success | failed
```

`UiSessionState` carries `screenState`, `sessionId`, `providerId`, `errorBanner`.

---

## Energy curve (UI + DTO)

```python
# Target shape (Phase 4.1)
@dataclass
class EnergyChapter:
    label: str
    profile: EnergyProfile  # rising, plateau, peak, cool_down
    track_count: int | None

@dataclass
class EnergyCurveOption:
    profile: EnergyProfile      # macro: rising, party, random, …
    chapters: tuple[EnergyChapter, ...] = ()
```

UI renders SVG/SwiftUI path from `previewPoints` computed by ViewModel.

Profiles mapping :

| UI label | Engine enum |
|----------|-------------|
| Montée progressive | `RISING` |
| Maximum immédiat | `MAX_FROM_START` |
| Aléatoire | `RANDOM` |
| Chapitres | custom chapters list |
| Pics / plateaux | chapter types `peak`, `plateau` |

---

## Exclusions (future-ready)

```python
@dataclass
class ExclusionRule:
    kind: ConstraintKind  # artist | album | track | genre | mood | language
    value: str
    reason: str = ""
```

UI : repeatable rows with kind picker + autocomplete (catalog search future).

Engine today : partial support via `GenerationConstraints` — UI exposes all kinds,
engine ignores unsupported with advisory badge.

---

## Diagnostics architecture

```text
ImportPlaylistUseCase / Resolver
        │ emits DiagnosticEvent
        ▼
DiagnosticBus (in-memory, async queue)
        │
        ├──► DiagnosticsViewModel (UI)
        ├──► JSON file (existing reports/)
        └──► Engine Bridge stream (macOS)
```

**Modes :**

- **Simple** — aggregated counts, last error, human summary
- **Architecte** — full event timeline, gateway method names, cache keys (hashed)

---

## Performance

| Concern | Approach |
|---------|----------|
| Long tasks | Engine subprocess async; UI main thread free |
| Progress | Stream `DiagnosticEvent` / import events |
| Cancel | Phase 4.6+ `CancellationToken` on bridge |
| Timeout | Per-track resolution timeout configurable |
| Retry | Visible in lab; automatic per provider rules |

---

## Packaging (future)

| Stage | Approach |
|-------|----------|
| Dev | `swift run ResonanceMac` + `python3 -m playlist_builder.cli.engine_bridge` |
| macOS dist | Signed .app, embedded Python venv or PyInstaller sidecar |
| Notarization | Apple notary service for engine binary |
| iOS | TestFlight → App Store, MusicKit entitlement |

---

## Test strategy (implementation phase)

| Layer | Tests |
|-------|-------|
| DTO | serde round-trip, schema validation |
| validation | pure functions, edge cases |
| ViewModels | pytest + mock use cases |
| ThemeRegistry | load all bundled themes, token completeness |
| ThemeManager | switch theme, no hardcoded colors in VM |
| Use cases | existing + new mock gateways |
| Bridge | JSON command fixtures |
| Navigation | route transitions |
| Swift ViewModels | XCTest against JSON fixtures from Python |
| UI widgets | snapshot tests selective |
| Guard | lint: no `applescript` import in `ui/` |

---

## Security & privacy

- Secrets in Keychain (MusicKit tokens) — never repo
- Caches local only (`~/Library/Application Support/Resonance/`)
- Logs : no PII, hash identity keys in architect mode option
- Engine subprocess : no network listen except localhost if HTTP bridge

---

## Implementation roadmap (PRs)

| PR | Title | Deliverables |
|----|-------|--------------|
| **4.0** | Product UI discovery | This doc pack |
| **4.1** | Shared DTO + validation | `playlist_builder/ui/shared/` — DTO, `AppRoute`, validators |
| **4.2** | Engine Bridge | `playlist_builder/ui/bridge/` — JSON-RPC protocol (**done**) |
| **4.3** | Theme engine (Python) | ThemeRegistry, 3 bundled themes (**done**) |
| **4.4** | macOS shell MVP | SwiftUI AppShell + Home + Settings (**done**) |
| **4.5** | Playlist builder UI | Form + generate + preview (**done**) |
| **4.6** | Import UX + bridge runtime | Python engine connection, import screens (**done**) |
| **4.6b** | Bridge hardening | Persistent process, live event stream |
| **4.7** | Laboratory | Diagnostics screens ✅ |
| **4.8** | History | Session list + detail + replay |
| **4.8** | iPadOS layout | Split view, adaptive navigation |
| **4.9** | iOS + MusicKit | Mobile delivery path |

---

## Acceptance criteria (Phase 4 implementation)

- [x] CLI unchanged and all pytest green (282+ tests)
- [x] No provider imports in `playlist_builder/ui/bridge/`
- [x] Runtime adapter in `app/bridge_runtime/` (composition root)
- [x] All colors via design tokens
- [x] ViewModels testable without SwiftUI
- [x] Engine Bridge documented and contract-tested
- [x] Manual acquisition flow — UX + session resume (4.6)
- [ ] FR + EN string catalog started
- [ ] VoiceOver labels on macOS MVP
- [ ] Live import event stream (4.6b)
- [x] No playlist/library delete actions in UI

## Related

- [ADR-011](ADR-011-cross-platform-product-ui.md)
- [design-system.md](../product/design-system.md)
- [theme-engine.md](../product/theme-engine.md)
