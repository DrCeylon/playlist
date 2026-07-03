# Phase 5.1.2 — Stabilisation UX produit

Phase de stabilisation après tests réels sur macOS. Aucune nouvelle fonctionnalité majeure, pas de démarrage Phase 5.2.

## Objectifs

1. Corriger le bug bloquant d'import (`ImportTrackStatus`)
2. Repenser l'écran Historique comme centre de reprise de workflow
3. Clarifier le Laboratoire (modes Simple / Architecte)
4. Améliorer la lisibilité des thèmes (WCAG AA)
5. Humaniser toutes les erreurs utilisateur vs techniques
6. Renforcer la cohérence du flux Créer → Preview → Import → Historique

## P0 — Bug import Apple Music

### Cause racine

Dans `playlist_builder/app/bridge_runtime/import_stream.py`, la fonction `stream_import_playlist` importait `ImportTrackStatus` **localement** dans le bloc `except ManualAcquisitionInterrupted` (ligne ~259), alors que le symbole était déjà utilisé plus haut dans la même fonction (résolution des morceaux).

En Python, un `import` dans une fonction rend le nom **local pour toute la fonction**. Les usages précédents du bloc `except` provoquaient :

```
cannot access local variable 'ImportTrackStatus' where it is not associated with a value
```

### Correctif

Suppression de l'import redondant ; conservation de l'import module-level unique.

### Tests

- `tests/test_import_stream_track_status.py` — flux mocké + garde AST
- `tests/test_error_humanizer.py` — humanisation côté Python

## P4 — Politique d'erreurs

| Couche | Comportement |
|--------|--------------|
| Python bridge (`error_humanizer.py`, `json_rpc.py`) | Message utilisateur + détail `technical` en `details` |
| Swift (`ImportErrorHumanizer.swift`) | Filtre erreurs Python, stack traces, noms de variables |
| Mode Architecte | Détail technique visible (`architectErrorDetail`) |

**Exemple utilisateur :**

> L'importation a échoué pendant la préparation. Vous pouvez réessayer ou consulter le détail technique.

## P1 — Historique

### Actions principales

| Action | Effet |
|--------|-------|
| **Voir la playlist** | Sheet avec preview complète des morceaux |
| **Modifier cette playlist** | Recharge Nouvelle Playlist (nom, artiste, morceau, mots-clés, nombre, options) |
| **Importer** | Réimport Apple Music depuis la preview enregistrée |
| **Réessayer** | Relance la génération Python |

### États affichés (FR)

- Générée
- Importée
- Partielle
- Échec
- Action manuelle requise

Les actions techniques (export rapport) sont regroupées sous **Diagnostic** en mode Architecte.

## P2 — Laboratoire

### Mode Simple

- Statut Apple Music
- Statut bridge
- Dernier import
- Dernier problème détecté
- Actions : Rafraîchir, Tester Apple Music, Ouvrir les rapports

### Mode Architecte

- Version moteur, plateforme, Python, working directory
- Providers, cache, événements, rapports
- Diagnostic brut

## P3 — Thèmes

Tokens `color.text.tertiary` renforcés sur les thèmes bundled. Tests de contraste étendus :

- `textSecondary` vs `background`
- `textTertiary` vs `surface`

Labels de formulaire : utilisation de `textSecondary` au lieu de `.secondary` système ou `textTertiary` trop pâle.

## P5 — Workflow

```
Créer playlist → Prévisualiser → Importer → Rapport → Historique → Modifier / Réessayer / Réimporter
```

Libellés harmonisés : **Modifier**, **Voir**, **Importer**, **Réessayer**.

## Limites connues Apple Music

- Import nécessite macOS + Music.app ouvert et autorisé (Automatisation)
- Morceaux absents du catalogue → acquisition manuelle ou signalement
- Réimport depuis Historique ne gère pas l'acquisition manuelle interactive (utiliser Nouvelle Playlist)

## Validation

```bash
python3 -m pytest -q
cd apps/resonance && ./scripts/build.sh && swift test && swift build   # macOS
```

**Ne pas merger sans validation macOS réelle.**

## Recommandations Phase 5.2

- `ImportCoordinator` unifié pour reprise depuis Historique avec acquisition manuelle
- Templates de playlist et édition post-génération
- Apprentissage utilisateur (hors scope 5.1.2)
