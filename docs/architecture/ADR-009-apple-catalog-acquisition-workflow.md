# ADR-007 — Apple catalog acquisition workflow

## Status

Accepted

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

1. Open/add the catalog URL through Music.app.
2. If Music.app returns a local item immediately, resolve it and cache the persistent ID.
3. If Music.app only opens the URL, pause the interactive CLI and ask the user to add the track to the Music library.
4. After confirmation, retry local library resolution.
5. If the track is now present, store the identity in `IdentityCache` and deliver it.
6. If not, keep a controlled `NOT_FOUND` result with an explicit acquisition message.

The CLI exposes `--no-wait-for-acquisition` to preserve non-interactive execution.

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
- Non-interactive runs remain possible with `--no-wait-for-acquisition`.

Trade-offs:

- The default CLI can pause when manual acquisition is required.
- Fully automated catalog-to-library acquisition remains limited by Music.app behavior and Apple account permissions.

## Future work

- Add a dedicated `PENDING_ACQUISITION` canonical status once the UI needs to display unresolved acquisition states.
- Add batch acquisition prompts rather than one prompt per track.
- Replace AppleScript acquisition with MusicKit if a paid developer license becomes available.
