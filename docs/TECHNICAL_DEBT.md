# Dette technique — état `main` (juillet 2026, post phases fonctionnelles)

Document de référence pour la release engineering. Aucun marqueur `TODO` / `FIXME` / `HACK` / `XXX` / `TEMP` actif dans le code source applicatif (hors enums métier `PENDING`).

| Sujet | Priorité | Impact | Estimation | Recommandation |
|-------|----------|--------|------------|----------------|
| Warnings Sendable Swift 6 | Moyenne | Bruit CI / migration future | Modérée | Traiter par cible (`ResonanceCore` d'abord) |
| Bridge Python one-shot par commande | Moyenne | Latence import longue | Élevée | Transport persistant Swift ↔ `engine_bridge.py` |
| `PlaylistBuilderViewModel` hardcode `appleMusic` | Moyenne | Sélection provider UI non effective | Faible | Activer picker existant |
| Sync mirror / reorder Apple Music | Moyenne | push mirror et reorder non garantis | Modérée | Après validation Music.app |
| DTOs domaine sous `ui/shared/dto` | Moyenne | Couplage couches | Élevée | Extraire `domain/` provider-neutral |
| `backend.py` god object | Moyenne | Maintenabilité bridge | Modérée | Facades par domaine |
| Triple stack import (CLI / bridge / gateway) | Moyenne | Duplication Apple wiring | Élevée | Orchestrateur unique |
| YouTube write port | Basse | Expérimental lecture seule | Modérée | ADR-018 |
| SQLite / scale repository | Basse | JSON SSOT limite concurrence | Élevée | Backend alternatif derrière protocol |
| i18n (FR uniquement) | Basse | Adoption OSS internationale | Élevée | Clés de messages |
| `AGENTS.md` absent de `main` | Moyenne | Onboarding agent | Faible | Merger PR #48 ou #53 |
| Resonance Identity / Cloud Sync | Future | Vision long terme | Élevée | Docs only — ADR-013 |

## Corrigé récemment (audit qualité)

| Sujet | Correctif |
|-------|-----------|
| `resolve_sync_conflicts` bridge cassé | `backend.py` — chargement `ManagedPlaylistDetail` comme `plan_sync` |
| `sync` ignoré à l'import bridge | Paramètre transmis à `stream_import_playlist` |
| JSON repos sans verrou | `infrastructure/atomic_json.py` + RMW atomique |
| `assert_bridge_safe_mapping` inutilisé | Vérification sorties `provider_account` |
| CI Python absente | `.github/workflows/python-ci.yml` |
| Historique / labo : bridge isolé | `replaceServices` + `workflow.engineBridge` |
| Contrat bridge incomplet | Tests parité Python/Swift (`CaseIterable`) |

## Principes architecture (Phase 6+)

- **Local-first** : toutes les fonctionnalités actuelles fonctionnent sans compte Resonance.
- **Music Providers** (`ProviderGatewayRegistry`) ≠ **Resonance Services** (Identity, Cloud Sync — futur).
- Détail : [phase-6-provider-platform.md](../product/phase-6-provider-platform.md), [QUALITY_AUDIT.md](QUALITY_AUDIT.md).

## Métriques qualité

| Métrique | Valeur |
|----------|--------|
| Tests Python | voir `pytest -q` sur CI |
| Tests Swift | ~135 (macOS CI) |
| LICENSE | MIT (`LICENSE`) |
| Contributing | `CONTRIBUTING.md` |

## Dépendances

| Écosystème | État |
|------------|------|
| Python runtime | Stdlib uniquement |
| Python dev | `pytest>=8.0` |
| Swift SPM | `ResonanceCore`, `ResonanceDesign`, `ResonanceMac` — pas de deps externes |
| Scripts | `make check-all` → `scripts/check_all.sh` |
