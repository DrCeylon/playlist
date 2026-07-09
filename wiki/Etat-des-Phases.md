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
| **6.4** | Sync planning & dry-run (`PlaylistSyncEngine`, bridge `plan_sync`) | PR #64 |

## Phase en cours

| Phase | Statut | Référence |
|-------|--------|-----------|
| **6.2** — Remote Playlist Read | PR #62 ouverte (Apple Music read adapter + bridge) | [phase-6-provider-platform.md](../docs/product/phase-6-provider-platform.md) § 6.2 |
| **6.3+** — Import local provider | Planifié après 6.2 | § 6.3 |
| **6.5+** — Sync apply / publish | Après 6.2 + 6.3 | ADR-016 |

Correctifs en revue (non mergés) :

| PR | Sujet |
|----|-------|
| [#57](https://github.com/DrCeylon/playlist/pull/57) | Fix Swift — ignorer événements bridge tardifs après fin d'import |
| [#48](https://github.com/DrCeylon/playlist/pull/48) | Agent OS — `AGENTS.md` + handbook engineering |
| [#53](https://github.com/DrCeylon/playlist/pull/53) | Setup environnement Cursor Cloud |

## État courant (`main`)

- **425** tests Python (`pytest -q`), **1** skipped (Swift build sur macOS uniquement)
- **~135** tests Swift (`swift test` sur macOS, CI `resonance-macos.yml`)
- App macOS : génération, import robuste, historique, gestionnaire de playlists (preview), contrats provider platform (6.1), sync planning dry-run (6.4)
- Détail : [Phase Playlist Manager — clôture](Phase-Playlist-Manager-Cloture)

## Prochaine phase

| Phase | Thème | Référence |
|-------|-------|-----------|
| **6.2** | Lecture playlists distantes Apple Music | PR #62 |
| **6.3** | Import local depuis provider | [phase-6-provider-platform.md](../docs/product/phase-6-provider-platform.md) § 6.3 |
| **6.5** | Sync apply (après dry-run 6.4) | ADR-016 |
| **Post-6** | Resonance Identity & Cloud Sync (métadonnées, optionnel) | [ADR-013](../docs/architecture/ADR-013-multi-provider-platform-vision.md) |

## Branches Git (`origin`, juillet 2026)

| Branche | Justification |
|---------|---------------|
| `main` | Branche de référence |
| `cursor/phase-6-2-remote-playlist-read-ef21` | PR #62 — travail non intégré |
| `cursor/fix-post-import-late-events-ef21` | PR #57 — fix import + isolation tests |
| `cursor/resonance-agent-os-docs-c172` | PR #48 — documentation agent OS |
| `cursor/setup-dev-environment-62d3` | PR #53 — setup Cursor Cloud |

Les branches feature mergées sont supprimées après fast-forward. Les PR obsolètes (#46, #54, #56) doivent être fermées manuellement (permission GitHub App insuffisante pour l'agent Cloud).

## Validation qualité (`main`)

```bash
python3.12 -m pytest -q
cd apps/resonance && swift build && swift test && ./scripts/build.sh
```

425 tests Python ; `swift build` + `swift test` sur macOS (CI `resonance-macos.yml`).
