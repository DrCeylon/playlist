# Phase 4.6 — Import UX + Engine Bridge runtime

Connects Resonance macOS to the Python engine via JSON-lines.

## Runtime entry point

```bash
python3 -m playlist_builder.cli.engine_bridge
```

Resonance launches this process from `apps/resonance` with the repository root as working directory.

## Implemented in 4.6

- `RuntimeEngineBridgeBackend` — generation via `GenerationSessionEngine`, import via streaming resolver
- `continue_manual_acquisition` — resumes imports paused for manual Music.app acquisition
- Swift `PythonEngineBridgeService` + import screens (progress, manual step, report)
- Mock fallbacks when the Python process is unavailable (dev/tests)

## Deferred to 4.6b

- Persistent bridge process (one-shot process per command today)
- Incremental import (`sync=false`) from the UI
- Live event streaming while Python is still running (events are returned when the process completes)

## Tests

```bash
python3 -m pytest tests/test_ui_bridge_runtime.py -q
cd apps/resonance && ./scripts/build.sh
```
