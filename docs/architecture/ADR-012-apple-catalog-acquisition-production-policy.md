# ADR-012 — Apple catalog acquisition production policy (Phase 5.3.3)

## Status

Accepted — supersedes the automatic acquisition steps in [ADR-009](ADR-009-apple-catalog-acquisition-workflow.md) for production imports.

## Context

Phase 5.3.2 instrumentation showed that catalog acquisition dominated import time (~90% of `resolve_total`). The monolithic AppleScript path (`open location` → poll → play → duplicate to Library → settle → search) averaged **~71 s per track** and often failed with AppleScript error **-10006** on subscription/catalog URLs.

Phase 5.3.3 macOS experiments on a real Apple Music track (*Dwayne Johnson — You're Welcome*, track `6779424544`) confirmed:

| Strategy | Result | Duration |
|----------|--------|----------|
| **S1** — `add URL` direct | Fail | 2.7 s |
| **S2** — open/play/duplicate (PR9) | Fail (-10006) | 84.2 s |
| **S4** — manual fallback (Resonance 5.2) | Success (persistent ID) | 33.3 s |

S2 is therefore **not viable** as the primary production path: it is slow, fragile, and fails on real catalog content. S4 is slower than a cache hit but **reliable** and yields an exploitable library `persistent ID`.

## Decision

### Production workflow (default)

When a track is missing from the local library but found in the catalog with sufficient confidence:

1. **Quick S1 probe** — try `add URL` for `itms://` and HTTPS variants (`try_add_catalog_url`). Typical cost: a few seconds.
2. If S1 succeeds, probe the local library **at most 2 times** (`PRODUCTION_ADDED_LIBRARY_PROBE_ATTEMPTS`) to absorb indexing latency.
3. If S1 fails, **open the catalog URL** (`open_catalog_url_for_manual`) and return `OPENED` status **immediately**.
4. When `wait_for_manual_catalog_add` is enabled (Resonance app / `--wait-for-acquisition` CLI), raise the manual acquisition gate **without** running S2 or waiting through automatic library retries first.
5. After user confirmation, probe the library up to 4 times (unchanged from Phase 5.2).
6. On success, store `IdentityCache` and deliver via `persistent ID` batch APIs.

### Deprecated for production

**S2 (open → play → duplicate to Library)** is **declassified** as a primary path:

- `ENABLE_PLAY_DUPLICATE_ACQUISITION_DEFAULT = False`
- `CatalogAcquisitionMode.PRODUCTION` is the default in `AppleMusicLibraryAcquisition`
- `acquire_song_from_url` / `_build_acquire_song_script` remain available under `CatalogAcquisitionMode.LEGACY_EXPERIMENTAL` for benchmarks and `scripts/perf/test_acquisition_strategies.py` only

### Unchanged

- Phase 5.2 manual acquisition UX (`ManualAcquisitionGate`, acquisition card in Resonance)
- Identity cache fast path when `persistent ID` is already known
- Delivery gateway (`add_tracks_by_persistent_id_batch`)
- Catalog fallback advisory (ADR-007)

## Consequences

Positive:

- Production imports no longer block **~80 s** on doomed S2 duplicate attempts before showing the manual card.
- Unresolved catalog tracks surface manual acquisition in **seconds**, not minutes.
- Cached tracks remain a fast path (no acquisition AppleScript).
- Experimental code and tests are preserved for future MusicKit evaluation.

Trade-offs:

- Automatic catalog-to-library acquisition is no longer attempted in production beyond the quick S1 probe.
- Users must confirm manual adds for most subscription catalog tracks (as in Phase 5.2), but without the prior silent wait.
- S1 may still succeed for some content types; when it does, the flow stays automatic.

## Future work

- **MusicKit** (paid developer program): evaluate `MusicLibrary.add(_:)` for reliable programmatic adds when a license is available. Do not block current shipping on MusicKit.
- **Multi-provider**: acquisition policy is Apple-provider-local; YouTube Music and other providers need separate ADRs.
- **S3 (System Events)**: remain experimental only; requires Accessibility permissions and locale-dependent menu labels.

## References

- `wiki/Phase-5-3-3-Acquisition-Experiments.md`
- `wiki/Phase-5-3-3-Acquisition-Decision.md`
- `playlist_builder/integration/apple_music/acquisition_policy.py`
- [Apple Developer Forums — Add songs to Library (-10006)](https://developer.apple.com/forums/thread/694200)
