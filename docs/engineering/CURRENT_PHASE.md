# Current phase

**Active phase** : **5.5 — Stabilisation & validation**  
**Branch de référence** : `cursor/phase-5-5-validation`  
**Statut** : stabilisation macOS / tests Swift — **ne pas démarrer Phase 6 runtime**

## Objectif Phase 5.5

Consolider et valider l'ensemble des travaux 5.5 (ProviderImportPort, acquisition manuelle, SSOT workflow, traçage) sur une branche unique avant merge vers `main`.

### Livrables attendus (5.5)

- [x] Branche de validation consolidée (`cursor/phase-5-5-validation`)
- [x] Traçage bouton « J'ai ajouté le morceau » (5.5.6)
- [ ] Build macOS vert (`swift build`, `swift test`, `./scripts/build.sh`)
- [ ] `pytest` vert
- [ ] Merge PR validation → `main`

### Hors périmètre (tant que 5.5 non mergée)

- Implémentation Répertoire (Phase 6)
- Modification `ProviderImportPort`
- Modification workflow manuel (ADR-012)
- Modification UX produit

## Phase suivante (préparée, non démarrée)

**Phase 6 — Répertoire** : documentation posée (ADR-014 à ADR-017, `docs/product/phase-6-repertoire.md`). Implémentation après merge 5.5.

Voir [NEXT_BACKLOG.md](NEXT_BACKLOG.md).

## Références

- [phase-6-repertoire.md](../product/phase-6-repertoire.md)
- [ADR-013](../architecture/ADR-013-multi-provider-platform-vision.md)
