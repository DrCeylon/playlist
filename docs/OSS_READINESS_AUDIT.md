# Open Source Readiness Audit — Resonance

**Audience:** maintainers preparing public GitHub launch  
**Date:** July 2026  
**Posture:** Functional foundations complete (Phases 1–6.8); focus on contributor experience.

---

## Executive summary

| Area | Grade | Blocker for contributors? |
|------|-------|-------------------------|
| Repository tree | C+ | Yes — dual identity (CLI vs Resonance), scattered docs |
| Module separation | B− | Partial — `playlist_builder/` clear; Swift in `apps/` |
| Naming conventions | C | README title ≠ product name; phase jargon everywhere |
| Dependencies | A− | Stdlib Python; SPM zero external deps — excellent |
| Dev scripts | B | `setup_dev.sh` good; macOS-only paths in README |
| Tests | B+ | ~490 Python; Linux CI; macOS Swift separate |
| Documentation | C+ | Rich but fragmented, stale wiki, no single story |
| Environment reproducibility | B | `setup_dev.sh` + `check_environment.py`; venv required |
| First-hour onboarding | C | No `AGENTS.md`; README leads with Orlando CLI |

**Verdict:** Technically contributable today on Python/Linux; **narrative and navigation** will confuse newcomers until documentation is unified.

---

## 1. Repository tree

```
playlist/                          # GitHub repo name ≠ product name "Resonance"
├── apps/resonance/                # macOS app (Swift SPM)
├── playlist_builder/              # Python engine (package name ≠ Resonance)
├── tests/                         # Python tests (good)
├── docs/                          # ADRs + phase docs (dense)
├── wiki/                          # French user docs (duplicate overlap)
├── scripts/                       # setup, check_all, perf
├── *.py wrappers                  # Legacy CLI entry at root
├── playlists/                     # Sample JSON
├── data/ cache/ reports/          # Runtime artifacts (gitignored mostly)
└── tools/                         # macOS helpers
```

### Friction points

| Issue | Impact |
|-------|--------|
| Repo named `playlist`, package `playlist-builder`, product `Resonance` | Search, PyPI, mental model |
| Root-level `check_catalog.py` wrappers | Unclear what's "the product" |
| `docs/product/phase-*` (20+ files) | Historical value; overwhelming for newcomers |
| Wiki duplicates `docs/` partially | Two sources of truth |
| No `docs/README.md` index until this audit | No map |

### Recommendations (applied)

- Hub documents: `ARCHITECTURE.md`, `PROVIDER_PLATFORM.md`, `PRODUCT_VISION.md`, `ROADMAP.md`
- Root `README.md` leads with **Resonance**, CLI as secondary path
- `docs/README.md` documentation map
- Wiki `Home.md` links to GitHub docs for contributors

---

## 2. Module separation

| Layer | Path | Contributor rule |
|-------|------|------------------|
| Canonical | `playlist_builder/canonical/` | Provider-neutral types |
| Application | `playlist_builder/app/` | Use cases, sync, repository |
| Integration | `playlist_builder/integration/<provider>/` | Provider SDKs / AppleScript |
| Bridge | `playlist_builder/ui/bridge/`, `app/bridge_runtime/` | JSON-RPC; no business in handlers |
| Swift UI | `apps/resonance/ResonanceMac/` | Views + ViewModels; delegate to bridge |
| Swift DTOs | `apps/resonance/ResonanceCore/` | Mirror Python DTOs |

**Leak:** domain logic imports `ui/shared/dto` — documented in `QUALITY_AUDIT.md`, not fixed (behavior risk).

---

## 3. Naming conventions

| Context | Convention | Problem |
|---------|------------|---------|
| Python modules | `snake_case` | Consistent ✅ |
| Swift | `PascalCase` / `camelCase` | Consistent ✅ |
| Bridge JSON | `snake_case` keys | Consistent ✅ |
| Phases | `6.7`, `4.8A` | Opaque to external contributors |
| French UI strings | Product copy | Fine for users; confuse EN contributors reading code comments |

---

## 4. Dependencies

| Stack | Policy | Contributor note |
|-------|--------|----------------|
| Python runtime | Stdlib only | `pip install -e ".[dev]"` |
| Python optional | `[youtube]` → `ytmusicapi` | Documented in CONTRIBUTING |
| Swift | Zero external SPM packages | Only Apple SDKs |
| System | macOS for Apple Music import | Linux sufficient for engine work |

**Strength:** minimal dependency surface — rare for projects this size.

---

## 5. Scripts & developer workflow

| Script | Role | Gap |
|--------|------|-----|
| `scripts/setup_dev.sh` | venv + dev install | macOS-centric (`python3.12` via brew hint) |
| `scripts/check_environment.py` | Python 3.12 gate | No optional extras check |
| `scripts/check_all.sh` | pytest + Swift build | Requires macOS for full pass |
| `Makefile` | `test`, `check-all` | No `lint` target |
| `apps/resonance/scripts/build.sh` | Swift CI parity | Buried path |

**Git workflow:** feature branches `cursor/<name>-ef21`; many historical branches on remote — document cleanup in GOVERNANCE.

---

## 6. CI

| Workflow | Trigger | Gap |
|----------|---------|-----|
| `python-ci.yml` | `playlist_builder/`, `tests/` | ✅ |
| `resonance-macos.yml` | Swift + bridge paths | ✅ |
| No lint/format job | — | Acceptable (stdlib project) |
| No PR template | — | Added in this PR |
| No issue templates | — | Added in this PR |

---

## 7. Documentation audit

### Exists and valuable
- 18 ADRs in `docs/architecture/`
- `docs/product/phase-6-provider-platform.md`
- `wiki/` French user guides
- `QUALITY_AUDIT.md`, `TECHNICAL_DEBT.md`

### Missing before this PR
- `AGENTS.md` (AI / cloud agents)
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `SUPPORT.md`
- `GOVERNANCE.md`
- Unified `ROADMAP.md`
- Hub `ARCHITECTURE.md` / `PROVIDER_PLATFORM.md` / `PRODUCT_VISION.md`
- Contributor story in README

### Stale content
- `wiki/README.md` — "323 tests", old PR numbers
- `wiki/Home.md` — "444 tests", Phase 4.9 "à faire" without Phase 6
- `docs/architecture/README.md` — migration table outdated
- README title "Apple Music Playlist Builder"

---

## 8. Reproducibility checklist

| Step | Linux | macOS |
|------|-------|-------|
| Clone repo | ✅ | ✅ |
| `pip install -e ".[dev]"` | ✅ | ✅ |
| `pytest -q` | ✅ (~490) | ✅ |
| `swift build` | ❌ | ✅ |
| Apple import E2E | ❌ | ✅ |

Documented in `CONTRIBUTING.md` capability matrix.

---

## 9. Proposed documentation architecture (implemented)

| Document | Location | Audience |
|----------|----------|----------|
| README.md | root | Everyone — product entry |
| CONTRIBUTING.md | root | Contributors |
| CODE_OF_CONDUCT.md | root | Community |
| SECURITY.md | root | Security reporters |
| SUPPORT.md | root | Users & contributors |
| GOVERNANCE.md | docs/ | Maintainers |
| ROADMAP.md | docs/ | Product & contributors |
| ARCHITECTURE.md | docs/ | Engineers |
| PROVIDER_PLATFORM.md | docs/ | Provider integrators |
| PRODUCT_VISION.md | docs/ | Product context |
| AGENTS.md | root | AI agents / automation |
| OSS_READINESS_AUDIT.md | docs/ | This audit |
| wiki/ | French | End users |

---

## 10. What will still complicate growth (deferred)

1. Repo/package/product name mismatch (`playlist` vs `Resonance`)
2. Phase-numbered internal vocabulary in commits and docs
3. French-only wiki vs English ADRs — intentional split, needs clear signposting
4. Domain DTO layer inversion (technical debt)
5. macOS-required paths for full validation
6. No Discord/forum — GitHub Issues only (documented in SUPPORT)

---

## References

- [QUALITY_AUDIT.md](QUALITY_AUDIT.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [GOVERNANCE.md](GOVERNANCE.md)
