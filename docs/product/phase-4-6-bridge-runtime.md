# Phase 4.6 — Engine Bridge runtime (technical notes)

Companion to [phase-4-import-ux.md](phase-4-import-ux.md) — product/UX acceptance doc.

## Entry point

```bash
python3 -m playlist_builder.cli.engine_bridge
```

Reads JSON-lines from stdin, writes responses/events to stdout. Resonance `BridgeClient` spawns one process per command (limitation 4.6b).

## `app/bridge_runtime/`

| Module | Role |
|--------|------|
| `backend.py` | `RuntimeEngineBridgeBackend` implements `EngineBridgeBackend` |
| `mapping.py` | `PlaylistGenerationRequest` ↔ `PlaylistRequest`, result mapping |
| `import_stream.py` | Track-by-track resolve + delivery + events |
| `import_session.py` | Checkpoint files for manual acquisition resume |
| `manual_gate.py` | Hook raising `ManualAcquisitionInterrupted` |

Guard test `test_ui_bridge_guard.py` ensures `ui/bridge/` has no provider imports.

## Swift detection

`ResonancePaths.repoRoot()` walks up to find `playlist_builder/`. Override with `RESONANCE_REPO_ROOT`.

## 4.6b backlog

- Persistent `BridgeClient` session
- Incremental import (`sync=false`)
- Live stdout reader for progress events during long imports

## Tests

```bash
python3 -m pytest tests/test_ui_bridge_runtime.py tests/test_ui_bridge_json_rpc.py -q
```
