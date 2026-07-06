# Current Phase

> État vivant. Mettre à jour à chaque changement de phase, de branche ou de PR.

## Phase actuelle

**5.5.3 — Stabilisation de `ProviderImportPort` et de l'acquisition manuelle.**

## Branche actuelle

`cursor/phase-5-5-provider-import-port-ef21`

## PR actuelle

**#45**

## Objectif immédiat

Rendre la **reprise manuelle fiable** depuis **Nouvelle Playlist** et depuis
**Historique** : après une acquisition manuelle (l'utilisateur ajoute un titre du
catalogue à sa bibliothèque), l'import doit reprendre de façon déterministe, sans
blocage ni double traitement, quel que soit le point d'entrée (nouvel import ou
reprise d'une session historisée).

## Hors scope

- Spotify (aucune implémentation sans ADR-014 accepté).
- YouTube Music (aucune implémentation sans ADR-015 accepté).
- Tout **changement UX majeur** (mise en page, flux, écrans).
- **Optimisation de performance** (le goulot d'import n'est plus le sujet, cf. ADR-012/013).

## Prochaine phase probable

**5.6 — `IncrementalImportPort`** : import incrémental non destructif, préparé par
l'extraction de `ProviderImportPort` de la phase 5.5.

## Références

- `docs/engineering/NEXT_BACKLOG.md` (P0 / P1 / P2)
- `docs/architecture/ADR-012-apple-catalog-acquisition-production-policy.md`
- `docs/architecture/ADR-013-multi-provider-platform-vision.md`
