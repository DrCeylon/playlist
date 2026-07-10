# Dette technique — état intégré (juillet 2026, pré-v1.0.0)

Document de référence pour la release engineering. Aucun marqueur `TODO` / `FIXME` / `HACK` / `XXX` / `TEMP` actif dans le code source applicatif (hors enums métier `PENDING`).

> **Vision produit :** [RESONANCE_VISION_2030.md](product/RESONANCE_VISION_2030.md) · **Paliers :** [ADR-019](architecture/ADR-019-resonance-product-tiers.md) · **Qualité :** [QUALITY_AUDIT.md](QUALITY_AUDIT.md)

| Sujet | Priorité | Impact | Estimation | Recommandation |
|-------|----------|--------|------------|----------------|
| Audit architecture v1.0 | — | Référence 5 ans | — | [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md) · [ADR-022](architecture/ADR-022-layering-and-future-readiness.md) |
| Warnings Sendable Swift 6 | Moyenne | Bruit CI / migration future | Modérée | Traiter par cible (`ResonanceCore` d'abord) |
| Bridge Python one-shot par commande | Moyenne | Latence import longue | Élevée | Transport persistant Swift ↔ `engine_bridge.py` |
| `PlaylistBuilderViewModel` hardcode `appleMusic` | Moyenne | Sélection provider UI non effective | Faible | Activer picker existant |
| Sync mirror / reorder Apple Music | Moyenne | push mirror et reorder non garantis | Modérée | Après validation Music.app |
| DTOs domaine sous `ui/shared/dto` | Moyenne | Couplage couches | Élevée | Extraire `domain/` provider-neutral |
| `backend.py` god object | Moyenne | Maintenabilité bridge | Modérée | Facades par domaine |
| Triple stack import (CLI / bridge / gateway) | Moyenne | Duplication Apple wiring | Élevée | Orchestrateur unique |
| YouTube write port | Basse | Expérimental lecture seule | Modérée | ADR-018 |
| Résolution conflits sync automatique en apply | Basse | Modèle prêt, moteur apply partiel | Élevée | Phase ultérieure |
| SQLite / scale repository | Basse | JSON SSOT limite concurrence | Élevée | Backend alternatif derrière protocol |
| i18n (FR uniquement) | Basse | Adoption OSS internationale | Élevée | Clés de messages |
| Resonance Identity / Cloud Sync | Future | Vision long terme | Élevée | Docs only — ADR-013 |

## Corrigé récemment (intégration)

| Sujet | Correctif |
|-------|-----------|
| `resolve_sync_conflicts` bridge cassé | `backend.py` — chargement `ManagedPlaylistDetail` |
| `sync` ignoré à l'import bridge | Paramètre transmis à `stream_import_playlist` |
| JSON repos sans verrou | `infrastructure/atomic_json.py` + RMW atomique |
| Schema version silencieux | `UnsupportedSchemaVersionError` — rejet explicite (ADR-022) |
| Snapshots sans verrou | `SnapshotArchive` : lock advisory + `os.replace` immuable (ADR-022) |
| `assert_bridge_safe_mapping` inutilisé | Vérification sorties `provider_account` |
| CI Python absente | `.github/workflows/python-ci.yml` |
| Multi-provider hardcoding | `provider_platform.py`, `parse_provider_id()` |
| Observability + plugin diagnostics | Union `diagnostics_snapshot.py` |

## Principes architecture (Phase 6+)

- **Local-first** : toutes les fonctionnalités actuelles fonctionnent sans compte Resonance.
- **Music Providers** (`ProviderGatewayRegistry`) ≠ **Resonance Services** (Identity, Cloud Sync — futur).
- Détail : [phase-6-provider-platform.md](product/phase-6-provider-platform.md), [ADR-013](architecture/ADR-013-multi-provider-platform-vision.md).

## Métriques qualité

| Métrique | Valeur |
|----------|--------|
| Tests Python | voir `python3.12 -m pytest -q` (~574 pass, 1 skip) |
| Tests Swift | ~135 (macOS CI) |
| Version cible release | 1.0.0 |
| LICENSE | MIT |
| CI Python | `python-ci.yml` |
| CI macOS | `resonance-macos.yml` |

## Dépendances

| Écosystème | État |
|------------|------|
| Python runtime | Stdlib uniquement |
| Python dev | `pytest>=8.0` |
| Swift SPM | `ResonanceCore`, `ResonanceDesign`, `ResonanceMac` — pas de deps externes |
| Scripts | `make check-all` → `scripts/check_all.sh` |

## Release engineering

Voir [RELEASE_PLAN.md](RELEASE_PLAN.md), [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md), [RELEASE_AUDIT.md](RELEASE_AUDIT.md).
