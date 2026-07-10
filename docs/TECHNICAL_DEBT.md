# Dette technique — état `main` (juillet 2026, pré-v1.0.0)

Document de référence pour la release engineering. Aucun marqueur `TODO` / `FIXME` / `HACK` / `XXX` / `TEMP` actif dans le code source applicatif (hors enums métier `PENDING`).

| Sujet | Priorité | Impact | Estimation | Recommandation |
|-------|----------|--------|------------|----------------|
| Warnings Sendable Swift 6 | Moyenne | Bruit CI / migration future | Modérée | Traiter par cible (`ResonanceCore` d'abord) sans changer le comportement |
| Gateway YouTube Music write | Moyenne | Lecture exp. livrée ; write non fiable | Modérée | ADR-018 — write reporté ; comparateur UX 6.8 |
| Sync mirror / reorder Apple Music | Moyenne | push mirror et reorder non garantis | Modérée | Phase ultérieure après validation Music.app |
| Résolution conflits sync automatique en apply | Basse | Modèle prêt, moteur apply partiel | Élevée | Phase ultérieure après sync write |
| `PlaylistBuilderViewModel` hardcode `appleMusic` | Moyenne | Sélection provider UI non effective | Faible | Activer picker existant sans coupler l'UI à Apple |
| Import `sync: true` toujours côté Swift | Basse | Pas d'import incrémental UI | Faible | Exposer toggle dans preview/import |
| Bridge Python one-shot par commande | Moyenne | Latence import longue | Élevée | ADR dédiée si persistance process |
| Wiki / docs Phase 4.x « placeholder » | Basse | Onboarding développeur | Faible | Archives ; lire `wiki/Phase-Playlist-Manager-Cloture.md` |
| Observability merge (#75) | Basse | Timeline sync structurée | Faible | Merger après gel v1.0 si validé |
| Resonance Identity / Cloud Sync | Future | Sync multi-Mac, préférences partagées | Élevée | Docs only — ADR-013 ; pas de `ProviderId` |

## Principes architecture (Phase 6+)

- **Local-first** : toutes les fonctionnalités actuelles fonctionnent sans compte Resonance.
- **Music Providers** (`ProviderGatewayRegistry`) ≠ **Resonance Services** (Identity, Cloud Sync, AI Profile — futur).
- **OAuth provider** : Keychain local ; **cloud Resonance** (futur) : métadonnées utilisateur uniquement.
- Détail : [phase-6-provider-platform.md](product/phase-6-provider-platform.md) § 2.0, [ADR-013](architecture/ADR-013-multi-provider-platform-vision.md).

## Marqueurs techniques audités

- **Swift / Python sources** : aucun `TODO`, `FIXME`, `HACK`, `XXX`, `TEMP` commentaire trouvé.
- **`PENDING`** : enum métier (`ImportTrackStatus`, `PlaylistSyncStatus`) — conservé.
- **ADR-009** : mention historique `PENDING_ACQUISITION` — document d'architecture, pas dette code.

## Métriques qualité (`main`, juillet 2026)

| Métrique | Valeur |
|----------|--------|
| Tests Python | 488 passed, 1 skipped |
| Tests Swift (macOS CI) | ~135 |
| Version cible release | 1.0.0 |
| CI Python | `python-ci.yml` (Linux) |
| CI macOS | `resonance-macos.yml` |

## Dépendances

| Écosystème | État |
|------------|------|
| Python runtime | Stdlib uniquement (`requirements.txt` vide volontairement) |
| Python dev | `pytest>=8.0` (`requirements-dev.txt`, `pyproject.toml`) |
| Swift SPM | `ResonanceCore`, `ResonanceDesign`, `ResonanceMac` — pas de dépendances externes |
| Scripts | `check_all.sh`, `setup_dev.sh`, `apps/resonance/scripts/build.sh` — tous référencés |

## Release engineering

Voir [RELEASE_PLAN.md](RELEASE_PLAN.md), [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md), [RELEASE_AUDIT.md](RELEASE_AUDIT.md).
