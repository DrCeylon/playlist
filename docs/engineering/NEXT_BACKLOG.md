# Next Backlog

Backlog priorisé. `P0` = le plus urgent. Chaque item : **objectif**, **critères
d'acceptation**, **hors scope**, **tests attendus**, **statut**.

Statuts possibles : `À faire` · `En cours` · `Bloqué` · `Fait`.

---

## P0 — Corriger définitivement la reprise d'acquisition manuelle

- **Objectif** : la reprise après acquisition manuelle est fiable et déterministe
  depuis **Nouvelle Playlist** et depuis **Historique**.
- **Critères d'acceptation** :
  - après confirmation manuelle, l'import reprend et se termine sans blocage ;
  - aucun double traitement ni perte de morceau lors de la reprise ;
  - comportement identique pour un nouvel import et pour la reprise d'une session
    historisée ;
  - le port d'import reste provider-neutral (pas de fuite Apple dans le bridge).
- **Hors scope** : Spotify/YouTube, changement UX, optimisation perf.
- **Tests attendus** : tests bridge/runtime sur la reprise manuelle (`tests/test_ui_bridge_*`,
  `test_e2e_import_mocked`, tests d'acquisition manuelle) ; cas nouveau + cas historique.
- **Statut** : En cours (phase 5.5.3, PR #45).

## P1 — Valider et merger la Phase 5.5

- **Objectif** : clôturer la phase 5.5 (`ProviderImportPort`) et la merger.
- **Critères d'acceptation** :
  - P0 résolu et couvert par des tests ;
  - suite `pytest` verte ; tests Swift verts si toolchain disponible ;
  - docs/ADR à jour ; checklist de revue satisfaite.
- **Hors scope** : commencer la phase 5.6.
- **Tests attendus** : suite complète `python3.12 -m pytest -q`.
- **Statut** : À faire.

## P2 — Phase 5.6 `IncrementalImportPort`

- **Objectif** : import **incrémental** non destructif (ajouter les manquants sans
  réordonner ni supprimer), via un port dédié provider-neutral.
- **Critères d'acceptation** :
  - port `IncrementalImportPort` défini côté Core/ports ;
  - implémentation Apple derrière le port, sans fuite dans le bridge ;
  - workflow par défaut non destructif préservé.
- **Hors scope** : nouveaux providers, refonte UX.
- **Tests attendus** : tests unitaires du port + tests d'intégration import incrémental.
- **Statut** : À faire (dépend de P1).

## P3 — Nettoyer le duck-typing d'`IntegrationGateway`

- **Objectif** : supprimer l'accès `applescript` duck-typé et le couplage Apple
  résiduel dans l'orchestration générique.
- **Critères d'acceptation** :
  - `IntegrationGateway` ne référence plus de logique Apple-spécifique en dur ;
  - sélection de provider via registre/ports uniquement ;
  - aucun changement de comportement observable.
- **Hors scope** : ajout de provider, changement de contrats publics.
- **Tests attendus** : tests gateway existants verts + tests ciblant l'orchestration.
- **Statut** : À faire.

## P4 — ADR-014 Spotify Provider

- **Objectif** : rédiger et faire accepter l'ADR d'un provider Spotify (auth,
  catalogue, résolution, livraison, acquisition).
- **Critères d'acceptation** :
  - ADR-014 au format standard (Status/Context/Decision/Consequences/References) ;
  - périmètre, non-goals et modèle d'identité (external_id par provider) explicités ;
  - **aucun code** provider tant que l'ADR n'est pas Accepted.
- **Hors scope** : implémentation Spotify, UI fournisseurs.
- **Tests attendus** : aucun (documentation) ; check de cohérence avec ADR-013.
- **Statut** : À faire.

## P5 — ADR-015 YouTube Music Provider

- **Objectif** : rédiger et faire accepter l'ADR d'un provider YouTube Music.
- **Critères d'acceptation** : identiques à P4, adaptés à YouTube Music.
- **Hors scope** : implémentation, UI.
- **Tests attendus** : aucun (documentation).
- **Statut** : À faire.

## P6 — `ProviderIdentityRegistry`

- **Objectif** : façade au-dessus d'`IdentityCache` exposant les identités provider
  de façon uniforme.
- **Critères d'acceptation** :
  - `get(track, provider_id) → ProviderIdentity | None` ;
  - **un** external_id par `(canonical_key, provider_id)` ;
  - **pas** d'équivalence cross-provider en v1 ;
  - `IdentityCache` reste la primitive de persistance (pas de changement de schéma).
- **Hors scope** : équivalence cross-provider, métadonnées d'acquisition avancées.
- **Tests attendus** : tests unitaires du registry + non-régression `IdentityCache`.
- **Statut** : À faire.

## P7 — UI fournisseurs connectés

- **Objectif** : afficher les providers connectés / disponibles dans l'UI.
- **Critères d'acceptation** :
  - UI provider-agnostique (via contrats canoniques / bridge) ;
  - couleurs via theme engine ; pas d'action destructive.
- **Hors scope** : logique métier provider dans l'UI, changement de flux non demandé.
- **Tests attendus** : tests de contrat UI/bridge (`tests/test_ui_*`).
- **Statut** : À faire (dépend d'au moins un second provider et de P6).

## P8 — Polish textes / couleurs

- **Objectif** : finitions de contenu et de thème.
- **Critères d'acceptation** : cohérence des textes ; couleurs via design tokens ;
  aucune régression fonctionnelle.
- **Hors scope** : refonte UX, nouveaux écrans.
- **Tests attendus** : tests de thème existants (`tests/test_ui_shared_theme.py`).
- **Statut** : À faire.
