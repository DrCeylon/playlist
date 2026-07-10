# Plugin development guide

How to extend Resonance **today** without touching core modules. External packaged plugins are not loaded yet — this guide covers **in-repo** extensions.

Parent: [PLUGIN_PLATFORM_AUDIT.md](../PLUGIN_PLATFORM_AUDIT.md) · [ADR-020](../architecture/ADR-020-plugin-platform-foundations.md)

---

## Rules

1. **Never** import `playlist_builder.app.playlist_sync` or `playlist_library` from `integration/`.
2. **Never** add provider-specific logic to the sync engine or conflict detector.
3. Register only through an **extension point** (registry or constructor injection).
4. Declare a manifest (JSON) even for monorepo modules — validates contract early.
5. Bump `api_version` only when breaking manifest shape; host uses `EXTENSION_API_VERSION`.

---

## Extension point: music provider

### 1. Manifest (optional but recommended)

```json
{
  "id": "resonance.provider.example",
  "extension_point": "music_provider",
  "api_version": "1.0.0",
  "entry": "playlist_builder.integration.example.gateway:build_example_gateway",
  "display_name": "Example Music",
  "permissions": ["network", "provider.auth", "provider.library"]
}
```

Validate in tests:

```python
from playlist_builder.platform.manifest import parse_extension_manifest

manifest = parse_extension_manifest(manifest_dict)
```

### 2. Implement ports

Create `playlist_builder/integration/example/`:

- `gateway.py` — `ProviderGateway` with explicit `capabilities`
- Optional: `auth.py` (`ProviderAuthPort`), `read_port.py`, `write_port.py`, `catalog.py`

### 3. Register

In `app/factory.py`:

```python
registry.register(build_example_gateway(...))
```

### 4. Tests

- Gateway unit tests with mocks
- Bridge tests with `ProviderGatewayRegistry` injection
- Architecture test: no `integration.example` imports in `app/playlist_sync/`

### 5. Swift (if UI-facing)

- Add `ProviderID` case + label (until stringly-typed IDs ship in 2.0)
- Update `BridgeClientTests` contract test

---

## Extension point: theme

### 1. Manifest

```json
{
  "id": "resonance.theme.example",
  "extension_point": "theme",
  "api_version": "1.0.0",
  "entry": "playlist_builder/ui/shared/theme/themes/example.theme.json",
  "display_name": "Example Dark"
}
```

### 2. Register

```python
registry = ThemeRegistry.load_bundled()
# or load JSON and registry.register(theme)
```

Themes are validated before registration (`ThemeRegistry.validate`).

---

## Extension point: discovery candidate

Implement `CandidateProvider` in `discovery/providers.py` pattern. Wire in generation engine factory when a second catalog exists.

---

## Extension point: repository (advanced)

Inject alternate `ManagedPlaylistRepository` via `RepositoryProvider` subclass — for tests or custom storage. Not for music providers.

---

## Reserved extension points (do not implement loaders)

| ID | Earliest tier |
|----|---------------|
| `sync_strategy` | 2.0 |
| `conflict_resolver` | 2.0 |
| `automation_rule` | 2.0 |
| `ai_engine` | 2.0 |
| `export_format` / `import_format` | 2.0 |
| `dashboard_widget` / `analysis_tool` | 2030 |

---

## Security checklist

- [ ] Secrets stay in Keychain / local files — never bridge payloads
- [ ] Use `sanitize_user_message` for user-facing errors (provider integrations)
- [ ] Declare `permissions` in manifest for future enforcement
- [ ] No network calls outside `integration/<provider>/`

---

## API versions

Check host versions via `diagnostics` bridge command:

```json
{
  "extension_api_version": "1.0.0",
  "bridge_api_version": "1.0.0"
}
```

---

## References

- [ADR-014](../architecture/ADR-014-provider-gateway-architecture.md)
- [ADR-015](../architecture/ADR-015-provider-auth-boundary.md)
- [youtube-music-experimental.md](youtube-music-experimental.md) — example experimental gateway
