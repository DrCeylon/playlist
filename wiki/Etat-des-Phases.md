# État des phases (juillet 2026)

Tableau de référence pour l'avancement du projet Resonance / playlist-builder.

## Phases terminées (mergées sur `main`)

| Phase | Contenu | Merge |
|-------|---------|-------|
| **1** | Fondations CLI, JSON playlist, Apple Music | Historique |
| **2** | Génération intelligente (seeds, énergie, scoring) | PR #5, #8 |
| **3** | Gateway enterprise, intégration Apple Music | PR #17 |
| **4.0–4.3** | Discovery UI, DTO, bridge, thèmes | PR #18–#21 |
| **4.4–4.5** | Shell macOS, formulaire playlist | PR #22–#23 |
| **4.6** | Bridge runtime, import streaming | PR #26 |
| **4.7** | Laboratoire diagnostics | PR #27 |
| **4.7a–4.7b** | Excellence Swift, environnement reproductible | PR #29–#31 |
| **4.8** | Historique sessions | PR #30 |
| **4.8A** | Stabilisation UX macOS, thèmes, import | PR #32 |
| **5.1** | Smart Input Framework (autocomplete, refs canoniques) | PR #33 |
| **5.1.1** | UX import Apple Music (progression live, Music deep links, acquisition auto) | PR #36 |
| **5.2–5.5** | Workflow coordinator, historique live, ProviderImportPort, acquisition manuelle SSOT | PR #43–#52 |
| **Playlist Manager** | Dashboard, Playlists / Sync / Providers, DTO library, YouTube expérimental | Tag `phase-playlist-manager-complete` — [clôture](Phase-Playlist-Manager-Cloture) |
| **6.1** | Contrats provider platform (ports read/write/auth, DTO remote playlist) | PR #61 |
| **6+ docs** | Vision Resonance Identity — Music Providers vs Resonance Services | PR #63 |
| **6.2** | Remote Playlist Read Apple Music (`list_remote_playlists`, `get_remote_playlist`) | `main` @ `32be564` |
| **6.4** | Sync planning & dry-run (`PlaylistSyncEngine`, bridge `plan_sync`) | PR #64 |
| **6.3** | Local Playlist Repository (SSOT, `import_remote_playlist`, migration history) | `main` @ `79bee3e` |
| **6.5** | Provider Playlist Sync Apply (`apply_sync`, opérations journalisées) | `main` @ `5052aea` — PR #66 |
| **6.6** | YouTube Music experimental gateway (lecture, auth, fallback fichier) | `main` @ `7383b78` — PR #67 |
| **6.7** | Intelligent conflict resolution (`resolve_sync_conflicts`) | `main` @ `a5874c7` — PR #68 |

## Phase en cours

| Phase | Statut | Référence |
|-------|--------|-----------|
| **6.8** — Product Experience (UX macOS) | En cours | `docs/product/phase-6-8-product-experience.md` |

PR ouvertes (non fonctionnelles) :

| PR | Sujet |
|----|-------|
| [#48](https://github.com/DrCeylon/playlist/pull/48) | Agent OS — `AGENTS.md` + handbook engineering |
| [#53](https://github.com/DrCeylon/playlist/pull/53) | Setup environnement Cursor Cloud |

## État courant (`main`, juillet 2026 — pré-v1.0.0)

- **486** tests Python (`pytest -q`), **1** skipped
- App macOS : sync apply (6.5), **YouTube Music expérimental** lecture/import (6.6)
- Release engineering : [docs/RELEASE_PLAN.md](../docs/RELEASE_PLAN.md)
- Détail : [Phase Playlist Manager — clôture](Phase-Playlist-Manager-Cloture)

## Limitations connues

- Mirror / reorder / remove provider Apple Music non fiables (hors append_only 6.5)
- Pas de YouTube Music réel (6.6)
- Resonance Identity : vision long terme (docs uniquement)

## Prochaine phase

| Phase | Thème | Référence |
|-------|-------|-----------|
| **6.8** | UX wizard sync + comparateur providers | Phase 6 product doc |
| **Post-6** | Resonance Identity & Cloud Sync (métadonnées, optionnel) | [ADR-013](../docs/architecture/ADR-013-multi-provider-platform-vision.md) |

## Branches Git (`origin`, juillet 2026)

| Branche | Justification |
|---------|---------------|
| `main` | Branche de référence |
| `cursor/resonance-agent-os-docs-c172` | PR #48 — documentation agent OS |
| `cursor/setup-dev-environment-62d3` | PR #53 — setup Cursor Cloud |

Les branches feature mergées sont supprimées après fast-forward.

## Validation qualité (`main`)

```bash
python3.12 -m pytest -q
cd apps/resonance && swift build && swift test && ./scripts/build.sh
```

486 tests Python ; `swift build` + `swift test` sur macOS (CI `resonance-macos.yml` + `python-ci.yml`).
