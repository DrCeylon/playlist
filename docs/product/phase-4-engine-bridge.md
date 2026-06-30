# Phase 4.2 — Engine Bridge protocol

JSON-lines bridge between future SwiftUI shells and the Python engine.

## Package

```text
playlist_builder/ui/bridge/
  commands.py    # BridgeCommand, request/response DTOs, parsers
  protocol.py    # EngineBridge + EngineBridgeBackend protocols
  json_rpc.py    # JsonRpcEngineBridge dispatcher
  events.py      # Streamable BridgeEvent types
  errors.py      # BridgeErrorCode + BridgeError
```

## Wire format

### Request (one JSON object per line)

```json
{"id": "req-1", "command": "list_providers", "params": {}}
```

### Response

```json
{"id": "req-1", "type": "response", "ok": true, "result": {"providers": []}}
```

### Event (streaming, long-running commands)

```json
{"id": "req-2", "type": "event", "event": "progress", "payload": {"processed_tracks": 3}}
```

### Error

```json
{"id": "req-3", "type": "response", "ok": false, "error": {"code": "validation_failed", "message": "..."}}
```

## Commands

| Command | Params | Result |
|---------|--------|--------|
| `list_providers` | — | `providers[]` |
| `validate_generation_request` | `request` | `valid`, `errors[]` |
| `generate_playlist` | `request` | `generation` (+ events) |
| `import_playlist` | `playlist`, `sync?`, `write_json_diagnostics?` | `import` (+ events) |
| `diagnostics` | — | `engine_version`, `events[]` |

## Provider neutrality

- No `integration/apple_music`, `core.applescript`, or `app.factory` imports in `ui/bridge/`.
- Engine-specific work is injected via `EngineBridgeBackend` (composition root outside bridge).
- `list_providers` defaults to `default_provider_options()` from `ui/shared`.

## SwiftUI compatibility

- Stable string command names and error codes.
- JSON-serializable payloads (enums as strings).
- Request `id` preserved on all response/event lines for correlation.

## Tests

- `tests/test_ui_bridge_commands.py`
- `tests/test_ui_bridge_json_rpc.py`
- `tests/test_ui_bridge_guard.py`

## Related

- [phase-4-ui-architecture.md](../architecture/phase-4-ui-architecture.md)
- [ADR-011](../architecture/ADR-011-cross-platform-product-ui.md)
