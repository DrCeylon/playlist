# Contributing to Resonance

## What runs where

| Capability | Linux CI | macOS |
|------------|----------|-------|
| Python unit tests (`pytest`) | Yes | Yes |
| Playlist generation (catalog) | Yes | Yes |
| Bridge JSON-RPC contract tests | Yes | Yes |
| Sync planning / conflict resolution | Yes (mocks) | Yes |
| Apple Music import / AppleScript | No | Yes |
| Resonance macOS app build | No | Yes |

Install dev dependencies:

```bash
pip install -e ".[dev]"
python -m pytest -q
```

Optional YouTube Music experimental gateway:

```bash
pip install -e ".[dev,youtube]"
```

Full local gate (macOS):

```bash
make check-all
```

## Architecture boundaries

- **Domain / use cases** must not import provider-specific SDKs.
- **Provider code** lives under `playlist_builder/integration/<provider>/`.
- **Bridge DTOs** in `playlist_builder/ui/shared/dto/` mirror Swift `ResonanceCore` models.
- **Local repository** is the single source of truth for managed playlists.

See `docs/architecture/` ADRs and `docs/QUALITY_AUDIT.md` for the current quality baseline.

## Pull requests

1. Rebase on `main`.
2. Run `python -m pytest -q` (required).
3. On macOS, run `cd apps/resonance && ./scripts/build.sh` when touching Swift or bridge contracts.
4. One logical change per commit; reference the phase or audit item in the message.
