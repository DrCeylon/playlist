# Roadmap

Strategic milestones aligned with [RESONANCE_VISION_2030.md](product/RESONANCE_VISION_2030.md).

**Last updated:** July 2026

---

## Tier overview

| Tier | Target | Promise |
|------|--------|---------|
| **MVP** | Now (2026) | Compose + deliver on Apple Music; sync foundations |
| **1.0** | 2027 | Public Open Source; 2 production providers; polished sync UX |
| **2.0** | 2028 | Personal music library OS: rules, undo, multi-destination sync |
| **2030** | 2030 | Open standard for playlist portability; ecosystem + API |

---

## MVP — current (2026)

### Shipped

| Area | Status |
|------|--------|
| Playlist generation & scoring engine | ✅ |
| macOS app (generation, import, history) | ✅ |
| Local playlist repository (SSOT) | ✅ |
| Remote playlist snapshots | ✅ |
| Sync plan / apply / conflict resolution | ✅ |
| Apple Music gateway (catalog, import, read, write) | ✅ |
| YouTube Music experimental (read) | 🔄 |
| Provider platform architecture | ✅ |
| Conflict resolution engine (6.7) | ✅ |

### In progress

| Epic | Status | Reference |
|------|--------|-----------|
| Product UX polish (sync wizard, providers) | 🔄 | Phase 6.8 |
| OSS documentation & governance | 🔄 | PR #71 |
| Multi-provider assumption cleanup | 🔄 | PR #72 |

### MVP exit criteria

- [ ] Sync wizard UX complete (plan → conflicts → apply)
- [ ] Provider connect/disconnect UI
- [ ] 500+ Python tests green on CI
- [ ] Contributor docs unified (README, CONTRIBUTING, wiki links)
- [ ] YouTube experimental documented with clear limits

---

## Version 1.0 — first public release (2027)

### Theme: *Trustworthy multi-provider foundation*

| Epic | Priority | Outcome |
|------|----------|---------|
| **E1 — Second production provider** | P0 | Spotify OR YouTube write path production-ready |
| **E2 — Provider UX** | P0 | Global provider picker; generation + import + sync use selected provider |
| **E3 — Sync reliability** | P0 | Append-only push/pull reliable on 2 providers; dry-run default |
| **E4 — Match quality visibility** | P1 | Per-track confidence in import report |
| **E5 — Library dashboard** | P1 | Managed playlists with origin, sync status, last sync time |
| **E6 — OSS launch** | P0 | LICENSE, governance, issue templates, stable `main` |
| **E7 — Collections (basic)** | P2 | Folder grouping for managed playlists |

### 1.0 exit criteria

- [ ] 2 providers production-ready (read + write append_only)
- [ ] New contributor: clone → pytest in < 5 min documented
- [ ] Zero Apple-only assumptions in sync engine (verified by arch tests)
- [ ] User wiki covers full sync workflow in French

---

## Version 2.0 — Resonance 2.0 (2028)

### Theme: *Your personal music library OS*

| Epic | Priority | Outcome |
|------|----------|---------|
| **E10 — Smart rules engine** | P0 | Declarative rules: triggers + filters + actions on local library |
| **E11 — Scheduled sync** | P0 | Local cron scheduler; notifications |
| **E12 — Multi-destination sync** | P0 | One local playlist → N provider targets |
| **E13 — Undo & versioning** | P0 | Rollback N mutations; diff between versions |
| **E14 — Temporal snapshots** | P1 | Point-in-time playlist state; timeline UI |
| **E15 — Tags & favorites** | P1 | Cross-playlist taxonomy |
| **E16 — Metadata enrichment** | P1 | MusicBrainz / ISRC references (no audio) |
| **E17 — 5+ providers** | P0 | Spotify, Deezer, Plex or Jellyfin, local files |
| **E18 — Local HTTP API** | P1 | Documented localhost API for library CRUD + sync trigger |
| **E19 — Apple Shortcuts** | P2 | Sync, generate, export actions |
| **E20 — AI assist (opt-in)** | P2 | Seed suggestions, conflict hints — user API key or local model |
| **E21 — Statistics dashboard** | P2 | Library-wide stats and sync health |

### 2.0 exit criteria

- [ ] Rules engine runs locally without cloud
- [ ] Undo used in production without data loss
- [ ] 5 registered gateways with tests
- [ ] Local API documented and stable v1

---

## Five-year vision — 2030

### Theme: *Open infrastructure for playlist portability*

| Epic | Priority | Outcome |
|------|----------|---------|
| **E30 — Public API** | P0 | Authenticated API + webhooks (metadata only) |
| **E31 — Plugin system** | P0 | Third-party gateways, rules, exporters |
| **E32 — Home Assistant** | P1 | Official integration |
| **E33 — iOS / iPadOS** | P1 | Feature parity with macOS shell |
| **E34 — Collaborative metadata** | P2 | Shared collections via Resonance Services (optional account) |
| **E35 — Rule marketplace** | P2 | Community templates |
| **E36 — Match quality benchmark** | P2 | Public dataset and leaderboard |
| **E37 — 15+ providers** | P1 | Community-maintained gateways |

---

## Engineering tracks (cross-cutting)

| Track | MVP | 1.0 | 2.0 | 2030 |
|-------|-----|-----|-----|------|
| Python engine | ✅ | Harden | Rules engine | Plugin host |
| macOS app | ✅ | Polish | Library UX | + iOS |
| Bridge protocol | ✅ | Stable v1 | + local API | Public API |
| CI / tests | ✅ | 500+ | 800+ | Fuzz + benchmark |
| Documentation | 🔄 | OSS complete | API docs | Ecosystem docs |

---

## What we defer (intentionally)

| Item | Earliest tier | Reason |
|------|---------------|--------|
| Resonance cloud account | 2030 | Local-first is the moat |
| Audio hosting | Never | Legal, scope, not differentiating |
| Real-time collab editing | 2030 | Metadata async is sufficient |
| Mirror/reorder sync | 1.0–2.0 | Provider write semantics vary |
| LLM required features | Never | Opt-in only |

---

## References

- [BACKLOG.md](product/BACKLOG.md) — detailed epics
- [RESONANCE_VISION_2030.md](product/RESONANCE_VISION_2030.md) — full vision
- [TARGET_ARCHITECTURE.md](architecture/TARGET_ARCHITECTURE.md) — technical target
- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) — known debt
