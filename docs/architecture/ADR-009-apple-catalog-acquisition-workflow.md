# ADR-009 — Apple catalog acquisition workflow

## Status

Accepted — **production automatic S2 steps superseded by [ADR-012](ADR-012-apple-catalog-acquisition-production-policy.md)** (Phase 5.3.3, July 2026). Manual acquisition and identity cache behaviour remain valid. See [ADR-013](ADR-013-multi-provider-platform-vision.md) for multi-provider scope.

## Context

The Apple Music provider can now search the local Music.app library and fall back to the iTunes/Apple catalog. Real E2E tests showed a new state:

- the catalog lookup finds the correct track with high confidence;
- Music.app opens the catalog URL;
- the track is not yet present in the local library;
- delivery cannot add it to the playlist because AppleScript delivery needs a local `persistent ID`.

This is not a resolution failure. It is an acquisition workflow gap.

## Decision

Model acquisition as an explicit provider-local workflow inside `playlist_builder/integration/apple_music/`.

When a track is missing from the local library but found in the catalog:

1. Try automatic acquisition through Music.app (`add URL`, then `play` + `duplicate to Library`).
2. Retry local library resolution up to six times (5 s apart) to absorb indexing latency.
3. If automatic acquisition fails and `--wait-for-acquisition` is set, pause the interactive CLI and ask the user to add the track manually.
4. After confirmation, retry local library resolution again.
5. If the track is now present, store the identity in `IdentityCache` and deliver it.
6. If not, keep a controlled `NOT_FOUND` result with an explicit acquisition message.

The CLI exposes:

- `--wait-for-acquisition` — opt in to manual confirmation when automatic acquisition fails
- `--no-wait-for-acquisition` — explicit non-interactive mode (default behaviour)

## Why this belongs in the Apple provider

The canonical application should not know how Apple Music acquires catalog tracks. The provider owns:

- Apple catalog URLs;
- Music.app behavior;
- AppleScript `add` / `open location` behavior;
- local `persistent ID` lookup.

The core application still receives canonical import results.

## Consequences

Positive:

- E2E runs can complete after the user adds tracks to Music.app without restarting the command.
- `IdentityCache` is populated after successful acquisition.
- Future runs can skip catalog lookup and use the cached persistent ID.
- Non-interactive runs remain the default; use `--no-wait-for-acquisition` to make that explicit in scripts.

Trade-offs:

- The default CLI can pause when manual acquisition is required.
- Fully automated catalog-to-library acquisition remains limited by Music.app behavior and Apple account permissions.

## Future work

- Add a dedicated `PENDING_ACQUISITION` canonical status once the UI needs to display unresolved acquisition states.
- Add batch acquisition prompts rather than one prompt per track.
- Replace AppleScript acquisition with MusicKit if a paid developer license becomes available.
