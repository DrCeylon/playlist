# Dette technique — état `main` (juillet 2026, post Phase 6.4)

Document de référence pour la release engineering. Aucun marqueur `TODO` / `FIXME` / `HACK` / `XXX` / `TEMP` actif dans le code source applicatif (hors enums métier `PENDING`).

| Sujet | Priorité | Impact | Estimation | Recommandation |
|-------|----------|--------|------------|----------------|
| Warnings Sendable Swift 6 | Moyenne | Bruit CI / migration future | Modérée | Traiter par cible (`ResonanceCore` d'abord) sans changer le comportement |
| Gateway YouTube Music réel | Haute | Sync/compare providers bloqués | Élevée | Voir [ADR-018](../architecture/ADR-018-experimental-youtube-music-gateway.md) — phase 6.6 |
| Sync provider apply (write réel) | Haute | UI affiche plan dry-run mais pas de pull/push réel | Élevée | [ADR-016](../architecture/ADR-016-playlist-sync-model.md) — phase 6.5+ (dry-run 6.4 ✅) |
| Lecture distante Apple Music (6.2) | Haute | Sync planning sans snapshot remote réel | Modérée | Merger PR #62 |
| Tracks vides dans `get_managed_playlist` | Moyenne | Détail playlist incomplet | Modérée | Hydrater depuis `import_result` historique |
| `PlaylistBuilderViewModel` hardcode `appleMusic` | Moyenne | Sélection provider UI non effective | Faible | Activer picker existant sans coupler l'UI à Apple |
| Import `sync: true` toujours côté Swift | Basse | Pas d'import incrémental UI | Faible | Exposer toggle dans preview/import |
| Résolution conflits sync automatique | Basse | Modèle prêt, pas de moteur apply | Élevée | Phase ultérieure après sync write |
| Bridge Python one-shot par commande | Moyenne | Latence import longue | Élevée | ADR dédiée si persistance process |
| Wiki / docs Phase 4.x « placeholder » | Basse | Onboarding développeur | Faible | Conserver archives ; lire `wiki/Phase-Playlist-Manager-Cloture.md` pour l'état courant |
| PR drafts obsolètes (#46, #54, #56) | Basse | Bruit process | Faible | Fermer manuellement — token Cloud Agent sans `pull_requests: write` |
| Branches `cursor/*` distantes (4 actives) | Basse | Normal — travail en cours | — | Supprimer uniquement après merge ou abandon |
| `AGENTS.md` absent de `main` | Moyenne | Onboarding agent / cloud | Faible | Merger PR #48 ou #53 après rebase |
| Fix import late events (#57) | Moyenne | Événements bridge tardifs en prod | Faible | Merger PR #57 |
| Resonance Identity / Cloud Sync | Future | Sync multi-Mac, préférences partagées | Élevée | **Docs only** — voir ADR-013 § Resonance Services ; ne pas modéliser comme `ProviderId` ; métadonnées uniquement, pas de musique |

## Principes architecture (Phase 6+)

- **Local-first** : toutes les fonctionnalités actuelles fonctionnent sans compte Resonance.
- **Music Providers** (`ProviderGatewayRegistry`) ≠ **Resonance Services** (Identity, Cloud Sync, AI Profile — futur).
- **OAuth provider** : Keychain local ; **cloud Resonance** (futur) : métadonnées utilisateur uniquement.
- Détail : [phase-6-provider-platform.md](../product/phase-6-provider-platform.md) § 2.0, [ADR-013](../architecture/ADR-013-multi-provider-platform-vision.md).

## Marqueurs techniques audités

- **Swift / Python sources** : aucun `TODO`, `FIXME`, `HACK`, `XXX`, `TEMP` commentaire trouvé.
- **`PENDING`** : enum métier (`ImportTrackStatus`, `PlaylistSyncStatus`) — conservé.
- **ADR-009** : mention historique `PENDING_ACQUISITION` — document d'architecture, pas dette code.

## Métriques qualité (`main`)

| Métrique | Valeur |
|----------|--------|
| Tests Python | 425 passed, 1 skipped |
| Tests Swift (macOS CI) | ~135 |
| Branches `origin` | `main` + 4 feature |
| PR ouvertes (pertinentes) | #62, #57, #48, #53 |

## Dépendances

| Écosystème | État |
|------------|------|
| Python runtime | Stdlib uniquement (`requirements.txt` vide volontairement) |
| Python dev | `pytest>=8.0` (`requirements-dev.txt`, `pyproject.toml`) |
| Swift SPM | `ResonanceCore`, `ResonanceDesign`, `ResonanceMac` — pas de dépendances externes |
| Scripts | `check_all.sh`, `setup_dev.sh`, `apps/resonance/scripts/build.sh` — tous référencés |
