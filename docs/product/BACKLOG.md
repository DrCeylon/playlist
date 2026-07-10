# Product backlog

Epics and features organized by tier. Priorities: **P0** (must) · **P1** (should) · **P2** (nice).

Parent: [RESONANCE_VISION_2030.md](RESONANCE_VISION_2030.md) · [ROADMAP.md](../ROADMAP.md)

---

## MVP — remaining

| ID | Epic | Priority | Notes |
|----|------|----------|-------|
| MVP-01 | Sync wizard UX (plan → conflicts → apply) | P0 | Phase 6.8 |
| MVP-02 | Provider connect/disconnect UI | P0 | Bridge commands exist |
| MVP-03 | Provider picker in generation | P0 | Remove hardcoded Apple |
| MVP-04 | OSS documentation package | P0 | README, CONTRIBUTING, governance |
| MVP-05 | CI baseline Linux + macOS | P0 | python-ci + resonance-macos |
| MVP-06 | YouTube experimental limits documented | P1 | No write until stable |

---

## Version 1.0

### Providers

| ID | Feature | Priority | Acceptance |
|----|---------|----------|------------|
| 10-P01 | Spotify gateway — OAuth | P0 | Connect via bridge; tokens in Keychain |
| 10-P02 | Spotify — playlist read | P0 | `list_remote_playlists`, `get_remote_playlist` |
| 10-P03 | Spotify — append_only write | P0 | `apply_sync` push adds tracks |
| 10-P04 | YouTube production OR Deezer stub | P1 | Second non-Apple path |
| 10-P05 | Provider capability matrix in UI | P1 | Show what each provider can do |

### Library & sync

| ID | Feature | Priority | Acceptance |
|----|---------|----------|------------|
| 10-L01 | Managed playlist dashboard | P0 | All SSOT playlists visible with status |
| 10-L02 | Import from remote provider UI | P0 | Browse → import → local SSOT |
| 10-L03 | Sync dry-run default | P0 | User sees plan before apply |
| 10-L04 | Conflict resolution UI complete | P0 | All conflict kinds actionable |
| 10-L05 | Per-track match confidence in report | P1 | Score visible post-import |
| 10-L06 | Basic collections (folders) | P2 | Group playlists locally |

### Quality & OSS

| ID | Feature | Priority | Acceptance |
|----|---------|----------|------------|
| 10-Q01 | Public GitHub launch | P0 | MIT, CODE_OF_CONDUCT, SECURITY |
| 10-Q02 | Contributor onboarding < 1 h | P0 | Documented in CONTRIBUTING |
| 10-Q03 | Architecture guard tests expanded | P1 | No provider branches in sync core |

---

## Version 2.0

### Rules & automation

| ID | Feature | Priority | Acceptance |
|----|---------|----------|------------|
| 20-R01 | Rules DSL (declarative) | P0 | YAML/JSON rules; local evaluation |
| 20-R02 | Trigger: schedule (cron) | P0 | Sync or refresh on schedule |
| 20-R03 | Trigger: new release by artist | P1 | Poll catalog; add to playlist |
| 20-R04 | Trigger: webhook / file drop | P2 | External automation |
| 20-R05 | Action: add/remove/reorder local | P0 | Mutates SSOT only |
| 20-R06 | Action: sync to provider(s) | P0 | Invokes existing plan/apply |

### Multi-provider sync

| ID | Feature | Priority | Acceptance |
|----|---------|----------|------------|
| 20-S01 | One playlist → N providers | P0 | Multiple `LinkedRemoteRef` |
| 20-S02 | Pull merge from multiple sources | P1 | Aggregated plan |
| 20-S03 | Scheduled sync jobs | P0 | Local scheduler; no cloud |
| 20-S04 | Sync health dashboard | P1 | Last success, error rate per link |

### Versioning & history

| ID | Feature | Priority | Acceptance |
|----|---------|----------|------------|
| 20-V01 | Undo last N local mutations | P0 | Reversible without provider round-trip |
| 20-V02 | Playlist diff (v1 vs v2) | P0 | Added/removed/reordered tracks |
| 20-V03 | Temporal snapshot browser | P1 | Pick date → view playlist state |
| 20-V04 | Full audit log export | P1 | JSON export of all operations |
| 20-V05 | Timeline visualization | P2 | Chart of playlist evolution |

### Taxonomy & metadata

| ID | Feature | Priority | Acceptance |
|----|---------|----------|------------|
| 20-T01 | Tags on playlists and tracks | P1 | Local tags; filter by tag |
| 20-T02 | Favorites (tracks/artists) | P1 | Reusable in generation rules |
| 20-T03 | MusicBrainz enrichment | P1 | ISRC, MBID in metadata refs |
| 20-T04 | Unified library view | P1 | All tracks across playlists searchable |

### Match quality

| ID | Feature | Priority | Acceptance |
|----|---------|----------|------------|
| 20-M01 | User feedback « wrong match » | P0 | Improves local cache |
| 20-M02 | Match explanation UI | P1 | Why this track was chosen |
| 20-M03 | Batch re-resolve | P2 | Re-run resolution with new rules |

### Integrations

| ID | Feature | Priority | Acceptance |
|----|---------|----------|------------|
| 20-I01 | Local HTTP API v1 | P1 | CRUD library + trigger sync |
| 20-I02 | Apple Shortcuts actions | P2 | Generate, sync, export |
| 20-I03 | CLI stable subcommands | P1 | `resonance sync`, `resonance rules` |
| 20-I04 | AI seed suggestions (opt-in) | P2 | User brings API key |

### Providers (2.0)

| ID | Feature | Priority | Acceptance |
|----|---------|----------|------------|
| 20-P01 | Deezer gateway | P1 | Read + append write |
| 20-P02 | Plex or Jellyfin gateway | P1 | Library browse + sync |
| 20-P03 | Local files gateway | P1 | Scan + metadata from files |
| 20-P04 | Navidrome/Subsonic adapter | P2 | Shared media server protocol |

---

## Five-year vision (2030)

| ID | Feature | Priority | Notes |
|----|---------|----------|-------|
| 30-A01 | Public API with auth | P0 | Metadata only; rate limited |
| 30-A02 | Webhooks | P1 | sync.completed, rule.triggered |
| 30-A03 | Plugin SDK | P0 | Gateways, rules, exporters |
| 30-A04 | Home Assistant integration | P1 | Official repo |
| 30-A05 | iOS app | P1 | Shared ResonanceCore |
| 30-A06 | Collaborative collections | P2 | Resonance Services; optional cloud |
| 30-A07 | Rule template marketplace | P2 | Community sharing |
| 30-A08 | Match quality public benchmark | P2 | Open dataset |
| 30-A09 | 15+ community gateways | P1 | Plugin ecosystem |

---

## Explicitly out of backlog

| Item | Reason |
|------|--------|
| Audio streaming player | Providers' job |
| Music hosting / CDN | Scope, legal |
| Social feed / discovery TikTok-style | Not differentiating |
| DRM removal | Illegal |
| Centralized OAuth broker | Violates local-first trust |
| Blockchain / NFT playlists | — |

---

## Backlog hygiene

- New epics require tier label (MVP / 1.0 / 2.0 / 2030)
- P0 items need acceptance criteria before implementation
- Features touching frozen contracts need ADR
- Defer anything without a second real use case (YAGNI)
