# Dette technique — état au tag `phase-playlist-manager-complete`

Document de référence pour la release candidate. Aucun marqueur `TODO` / `FIXME` / `HACK` / `XXX` / `TEMP` actif dans le code source applicatif (hors enums métier `PENDING`).

| Sujet | Priorité | Impact | Estimation | Recommandation |
|-------|----------|--------|------------|----------------|
| Warnings Sendable Swift 6 | Moyenne | Bruit CI / migration future | Modérée | Traiter par cible (`ResonanceCore` d'abord) sans changer le comportement |
| Gateway YouTube Music réel | Haute | Sync/compare providers bloqués | Élevée | Voir [ADR-018](../architecture/ADR-018-experimental-youtube-music-gateway.md) — phase 6.6 |
| Sync provider réelle (stub `pending`) | Haute | Playlists tab affiche statut mais pas de pull/push réel | Élevée | [ADR-016](../architecture/ADR-016-playlist-sync-model.md) — phase 6.4 |
| Tracks vides dans `get_managed_playlist` | Moyenne | Détail playlist incomplet | Modérée | Hydrater depuis `import_result` historique |
| `PlaylistBuilderViewModel` hardcode `appleMusic` | Moyenne | Sélection provider UI non effective | Faible | Activer picker existant sans coupler l'UI à Apple |
| Import `sync: true` toujours côté Swift | Basse | Pas d'import incrémental UI | Faible | Exposer toggle dans preview/import |
| Résolution conflits sync automatique | Basse | Modèle prêt, pas de moteur | Élevée | Phase ultérieure après sync réelle |
| Bridge Python one-shot par commande | Moyenne | Latence import longue | Élevée | ADR dédiée si persistance process |
| Wiki / docs Phase 4.x « placeholder » | Basse | Onboarding développeur | Faible | Conserver archives ; lire `wiki/Phase-Playlist-Manager-Cloture.md` pour l'état courant |
| PR drafts orphelines (#46–#57) | Basse | Bruit process | Faible | Fermer manuellement après revue |
| Branches `cursor/*` distantes résiduelles | Basse | Bruit Git | Faible | Supprimer après `git merge-base --is-ancestor` |
| `SessionDetailView` supprimé (clôture) | Nulle | — | — | Remplacé par `HistoryWorkflowResumeView` |

## Marqueurs techniques audités

- **Swift / Python sources** : aucun `TODO`, `FIXME`, `HACK`, `XXX`, `TEMP` commentaire trouvé.
- **`PENDING`** : enum métier (`ImportTrackStatus`, `PlaylistSyncStatus`) — conservé.
- **ADR-009** : mention historique `PENDING_ACQUISITION` — document d'architecture, pas dette code.

## Dépendances

| Écosystème | État |
|------------|------|
| Python runtime | Stdlib uniquement (`requirements.txt` vide volontairement) |
| Python dev | `pytest>=8.0` (`requirements-dev.txt`, `pyproject.toml`) |
| Swift SPM | `ResonanceCore`, `ResonanceDesign`, `ResonanceMac` — pas de dépendances externes |
| Scripts | `check_all.sh`, `setup_dev.sh`, `apps/resonance/scripts/build.sh` — tous référencés |
